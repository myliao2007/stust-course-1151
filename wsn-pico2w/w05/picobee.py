# picobee.py：PicoBee，讓 Pico 2 W 的行為像一顆 ZigBee 模組（XBee 風格的 AT／API 介面）
#
# 主題 5 老師提供，同學不用改。兩片板子都要存：myid.py、cfg.py、wsnproto.py、wsntree.py、picobee.py。
#   * A 板開 AP（cfg.SSID），B 板連上去；兩片之間的「空氣」是 Wi-Fi UDP，
#     裡面裝的是真的 IEEE 802.15.4 MAC 訊框（含 2 位元組 FCS），可以貼到電腦的 wsn_decode.py 驗證。
#   * 頻道 CH（11～26）只是模擬欄位：CH 對到 UDP 埠 5400＋CH；電波實際走的是 A 的 Wi-Fi 頻道（cfg.CHANNEL）。
#   * 主控 MCU 和模組之間的序列線用函式模擬：bee.write(位元組)＝送進模組（DIN），bee.read()＝模組送出來（DOUT）。
#   * bee.term() 是互動的「PicoBee 終端機」：+++、AT 指令、聊天；API 模式時改打十六進位。
# 和真的 XBee 不同：沒有 ZigBee 網路層（NWK）、應用支援層（APS）與加密，所以不做多跳轉送；
#   MAC 酬載的第一個位元組是 PicoBee 類型（# 資料、% I/O 取樣、! 遠端 AT、= 遠端 AT 回應、? 找位址、+ 位址回覆）。
import time, json, math, random
import wsnproto as w
try:
    import machine
except ImportError:                      # 電腦上測試時沒有 machine
    machine = None
try:
    import micropython
except ImportError:
    micropython = None

VERSION = '2026-10-11'
CFG_FILE = 'picobee.json'                # ATWR 存設定的檔案
BIND_IP = '0.0.0.0'
PINS = (26, 27, 28, 14, 15)              # DIO0～DIO4 對到的 Pico 腳位（DIO0～2 可以當類比 AD0～AD2）
CAPACITY = 10                            # 一個父節點最多收幾個子節點（Faludi 書上的 XBee 約 8～10 個）
MAXDATA = 115                            # 一包最多帶的資料：127 − MAC 標頭 9 − FCS 2 − 類型 1
ACK_MS = 150                             # 等 MAC ACK 多久（毫秒）
RETRIES = 3                              # 沒等到 ACK 最多重送幾次（802.15.4 的 macMaxFrameRetries）
SCAN_MS = 150                            # 入網掃描：每個頻道聽多久
POLL_MS = 100                            # 終端裝置醒著的時候，多久問一次父節點
FIND_MS = 800                            # 找 16 位元位址最多等多久
HOLD = 2.5                               # 父節點替睡著的孩子保管訊息：2.5 × 父節點的 SP
OWN_AP_DBM = -30                         # 能量掃描時，把自己旁邊的 AP 當成 −30 dBm 的雜訊
T_DATA, T_IO, T_RAT, T_RATR, T_AQ, T_AR = 0x23, 0x25, 0x21, 0x3D, 0x3F, 0x2B
BCAST64 = b'\x00\x00\x00\x00\x00\x00\xff\xff'
COORD64 = bytes(8)
UNKNOWN64 = b'\xff' * 8
ROLE = ('協調器', '路由器', '終端裝置')

DEFAULTS = {'ID': 0, 'CE': 0, 'SM': 0, 'SP': 0x20, 'ST': 0x1388, 'SC': 0x7FFF, 'AP': 0, 'DH': 0, 'DL': 0,
            'NI': '', 'NJ': 0xFF, 'NT': 0x3C, 'CT': 0x64, 'GT': 0x3E8, 'IR': 0, 'BD': 3,
            'D0': 0, 'D1': 0, 'D2': 0, 'D3': 0, 'D4': 0}
# AT 參數：名稱 → (API 回傳幾個位元組（0＝文字）, 最小值, 最大值, 改了要不要重新建網／入網)；最小值 None＝唯讀
PARAM = {'ID': (8, 0, 0xFFFFFFFFFFFFFFFF, 1), 'SC': (2, 1, 0xFFFF, 1), 'CE': (1, 0, 1, 1), 'SM': (1, 0, 4, 1),
         'DH': (4, 0, 0xFFFFFFFF, 0), 'DL': (4, 0, 0xFFFFFFFF, 0), 'SP': (2, 0x20, 0xAF0, 0), 'ST': (2, 1, 0xFFFE, 0),
         'AP': (1, 0, 2, 0), 'NJ': (1, 0, 0xFF, 0), 'NT': (1, 0x20, 0xFF, 0), 'CT': (2, 2, 0x1770, 0),
         'GT': (2, 2, 0xCE4, 0), 'IR': (2, 0, 0xFFFF, 0), 'BD': (4, 0, 7, 0), 'NI': (0, 0, 20, 0),
         'D0': (1, 0, 5, 0), 'D1': (1, 0, 5, 0), 'D2': (1, 0, 5, 0), 'D3': (1, 0, 5, 0), 'D4': (1, 0, 5, 0),
         'OI': (2, None, 0, 0), 'OP': (8, None, 0, 0), 'CH': (1, None, 0, 0), 'MY': (2, None, 0, 0),
         'SH': (4, None, 0, 0), 'SL': (4, None, 0, 0), 'AI': (1, None, 0, 0), 'NC': (1, None, 0, 0),
         'VR': (2, None, 0, 0), 'NP': (2, None, 0, 0), 'MP': (2, None, 0, 0)}
_LAST = [None]                           # 上一次建立的 PicoBee（重跑程式時先把它停掉）


def now_ms():
    # 現在的毫秒數（測試時會換成虛擬時鐘）
    return w.now_ms()


def since(t0):
    # 從 t0 到現在過了幾毫秒（會處理 ticks 繞回）
    return w.ms_since(t0)


def _sleep_ms(ms):
    if hasattr(time, 'sleep_ms'):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000)


def _ib(v, n):
    # 整數 → n 個位元組（大端序）
    return bytes([(v >> (8 * (n - 1 - i))) & 0xFF for i in range(n)])


def _bi(b):
    # 位元組（大端序）→ 整數
    v = 0
    for x in b:
        v = (v << 8) | x
    return v


def _rand(bits):
    return random.getrandbits(bits)


# ---------------- 能量掃描：用 Wi-Fi 掃描結果估計每個 802.15.4 頻道有多吵 ----------------
def wifi_mhz(n):
    # Wi-Fi 第 n 頻道的中心頻率（MHz）
    return 2484 if n == 14 else 2407 + 5 * n


def ch_mhz(ch):
    # 802.15.4 頻道 11～26 的中心頻率（MHz）：2405＋5×（CH−11）
    return 2405 + 5 * (ch - 11)


def energy(seen, own=None):
    # seen＝wlan.scan() 的結果（第 3、4 個值是 Wi-Fi 頻道與 RSSI）；own＝(自己 AP 的頻道, dBm)
    # Wi-Fi 一個頻道約 20 MHz 寬（左右各 10）、802.15.4 約 2 MHz 寬（左右各 1）：中心差不到 11 MHz 就算撞到
    aps = [(e[2], e[3]) for e in seen]
    if own:
        aps.append(own)
    out = []
    for ch in range(11, 27):
        mw = 1e-10                               # 雜訊底 −100 dBm
        for n, rssi in aps:
            if abs(ch_mhz(ch) - wifi_mhz(n)) < 11:
                mw += 10 ** (rssi / 10)
        out.append((ch, int(round(10 * math.log10(mw)))))
    return out


def pick_channel(table, sc):
    # 在 SC 遮罩允許的頻道裡挑最安靜的（一樣安靜就挑編號小的）
    best = None
    for ch, dbm in table:
        if (sc >> (ch - 11)) & 1 and (best is None or dbm < best[1]):
            best = (ch, dbm)
    return best[0] if best else None


# ---------------- 空氣：Wi-Fi UDP ----------------
class UdpAir:
    # STA（B 板）：每個訊框交給 hub（A 的 IP）；AP（A 板）：自己當 hub，把聽到的訊框轉給其他 STA，大家才聽得到彼此
    def __init__(self, ip, hub, port0):
        import socket
        self.socket = socket
        self.ip = ip
        self.hub = hub
        self.port0 = port0
        self.peers = []
        self.s = None
        self.ch = None

    def tune(self, ch):
        # 換頻道＝換 UDP 埠
        if ch == self.ch and self.s:
            return
        self.close()
        s = self.socket.socket(self.socket.AF_INET, self.socket.SOCK_DGRAM)
        s.bind((BIND_IP, self.port0 + ch))
        s.settimeout(0)
        self.s, self.ch = s, ch

    def send(self, f):
        if not self.s:
            return
        to = [self.hub] if self.hub else self.peers
        for ip in to:
            try:
                self.s.sendto(f, (ip, self.port0 + self.ch))
            except OSError:
                pass

    def recv(self):
        if not self.s:
            return None
        try:
            f, addr = self.s.recvfrom(256)
        except OSError:
            return None
        if not self.hub:
            ip = addr[0]
            if ip not in self.peers:
                self.peers.append(ip)
                if len(self.peers) > 10:
                    self.peers.pop(0)
            for p in self.peers:
                if p != ip:
                    try:
                        self.s.sendto(f, (p, self.port0 + self.ch))
                    except OSError:
                        pass
        return f

    def close(self):
        if self.s:
            try:
                self.s.close()
            except OSError:
                pass
        self.s = None
        self.ch = None


def wifi_up(join_group=None, quiet=False):
    # 開 Wi-Fi：自己組的 A 板開 AP；其他（B 板，或 Lab 4 加入別組的板子）連上那一組的 AP。回傳 (空氣, Wi-Fi 掃描結果, AP 頻道)
    import network, myid, cfg
    g = join_group or cfg.GROUP
    ssid, pw = cfg.ap_of(g)
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    try:
        seen = sta.scan()                        # 開機先掃一次 Wi-Fi，給協調器的「能量掃描」用
    except OSError:
        seen = []
    ap_ch = (1, 6, 11)[(g - 1) % 3]
    if myid.BOARD == 'A' and g == cfg.GROUP:
        sta.active(False)
        ap = network.WLAN(network.AP_IF)
        ap.config(ssid=ssid, key=pw, channel=ap_ch)
        ap.active(True)
        while not ap.active():
            _sleep_ms(100)
        ip = ap.ifconfig()[0]
        if not quiet:
            print('PicoBee：A 板開 AP', ssid, '（Wi-Fi 頻道', ap_ch, '），IP', ip)
        return UdpAir(ip, None, cfg.AIR_PORT), seen, ap_ch
    sta.config(pm=0xa11140)                      # 關閉 Wi-Fi 省電，廣播與回應才不會延遲
    sta.connect(ssid, pw)
    t0 = now_ms()
    while not sta.isconnected():
        if since(t0) > 30000:
            raise RuntimeError('連不上 ' + ssid + '：A 板的 PicoBee 有沒有先跑？（status=%d）' % sta.status())
        _sleep_ms(200)
    ip, _, gw, _ = sta.ifconfig()
    if not quiet:
        print('PicoBee：已連上', ssid, '，IP', ip, '，A 的 IP', gw)
    return UdpAir(ip, gw, cfg.AIR_PORT), seen, ap_ch


class _NoPin:
    # 沒有 machine 模組時（電腦上測試）的假腳位
    def __init__(self, *a, **k):
        self.v = 0

    def value(self, v=None):
        if v is None:
            return self.v
        self.v = v

    def read_u16(self):
        return 32768


class PicoBee:
    def __init__(self, air=None, seen=None, ap_ch=1, ext=None, join_group=None, load=True, quiet=False, board=None):
        # air／seen／ext 給測試用；平常什麼都不用給
        if _LAST[0]:
            _LAST[0].stop()
        _LAST[0] = self
        self.quiet = quiet
        self.on_out = None                       # 模組送出東西時呼叫（終端機用）
        self.on_event = None                     # 入網、睡醒這類事件（終端機用）
        self.sniff = 0                           # 0 不印、1 每個空中訊框印一行摘要＋十六進位、2 再加欄位樹
        self._waiter = None                      # 測試用：虛擬時鐘
        self._timer = None
        self._sched = False
        self._busy = False
        self._ps = self._poll_s
        self._inq = []
        self._out = bytearray()
        if ext is None:
            ext = machine.unique_id() if machine else b'\x00\x13\xa2\x00\x00\x00\x00\x01'
        self.ext = bytes(ext)[:8]                # 64 位元位址（SH＋SL）＝machine.unique_id()
        if air is None:
            air, seen, ap_ch = wifi_up(join_group, quiet)
        self.air = air
        self.seen = seen or []
        self.ap_ch = ap_ch
        self.board = board
        if self.board is None:
            try:
                import myid
                self.board = myid.BOARD
            except ImportError:
                self.board = '?'
        self.c = dict(DEFAULTS)
        if load:
            self._load()
        if machine:
            self.led = machine.Pin('LED', machine.Pin.OUT)
        else:
            self.led = _NoPin()
        self.pins = [None] * 5
        self._t0 = now_ms()
        self.cmd = False                         # 在命令模式嗎（+++ 之後）
        self.line = ''
        self.plus = b''
        self.t_plus = None
        self.t_in = None                         # 主控最後一次送字進來的時間
        self.t_cmd = now_ms()
        self.tx_buf = b''
        self.apibuf = b''
        self._api_fid = 0
        self._err = ('', 0)
        self._reset_net()
        self._apply_pins()
        self._dirty = False
        self.ed_table = []
        self.ap = self.c['AP']                   # 現在序列線用的模式（ATAP 改了，離開命令模式才生效）
        if self.ap:
            self._modem(0x00)                    # 0x8A：開機
        self._restart_net()

    # ================= 設定檔 =================
    def _load(self):
        try:
            f = open(CFG_FILE)
            d = json.load(f)
            f.close()
        except (OSError, ValueError):
            return
        for k in DEFAULTS:
            if k in d:
                self.c[k] = d[k]

    def _save(self):
        f = open(CFG_FILE, 'w')
        json.dump(self.c, f)
        f.close()

    # ================= 主控端（序列線）=================
    def write(self, data):
        # 主控送進模組（DIN）
        self._inq.append((now_ms(), bytes(data)))

    def read(self):
        # 模組送出來的位元組（DOUT），讀了就清掉
        out = self._out
        self._out = bytearray()
        return bytes(out)

    def joined(self):
        return self.state == 'joined'

    def wait(self, ms):
        # 等 ms 毫秒（等的時候模組照樣在跑）
        if self._waiter:
            return self._waiter(ms)
        t0 = now_ms()
        while since(t0) < ms:
            if not self._timer:
                self.poll()
            _sleep_ms(10)

    def start(self, period=20):
        # 讓模組在背景每 period 毫秒跑一次（Pico 的 machine.Timer）
        if self._timer or not machine or not hasattr(machine, 'Timer'):
            return False
        T = machine.Timer
        self._timer = T(period=period, mode=T.PERIODIC, callback=self._tick)
        return True

    def stop(self):
        if self._timer:
            self._timer.deinit()
            self._timer = None
        self.air.close()
        self.led.value(0)

    def _tick(self, t):
        if not self._sched and micropython:
            self._sched = True
            micropython.schedule(self._ps, 0)

    def _poll_s(self, _):
        self._sched = False
        self.poll()

    def _put(self, b):
        self._out.extend(b)

    def _event(self, t):
        if self.on_event:
            self.on_event(t)

    def _modem(self, st):
        if self.ap:
            self._put(self._api(w.xb_modem(st)))

    def _api(self, f):
        return w.xb_escape(f) if self.ap == 2 else f

    # ================= 網路狀態 =================
    def role(self):
        # 現在生效的角色（ATCE、ATSM 改了，要 ATCN 重新入網之後才生效）
        r = getattr(self, '_role', None)
        return self._want_role() if r is None else r

    def _want_role(self):
        return 0 if self.c['CE'] == 1 else (2 if self.c['SM'] else 1)

    def _reset_net(self):
        self.state = 'idle'
        self.ai = 0xFF
        self.ch = None
        self.oi = 0xFFFF
        self.op = 0
        self.my = 0xFFFE
        self.parent = None
        self.depth = 0
        self.children = {}                       # 16 位元 → {'ext', 'sleepy'}
        self.ext_of = {}                         # 16 位元 → 64 位元
        self.short_of = {}                       # 64 位元 → 16 位元
        self.txs = []                            # 等 ACK 的訊框
        self.indq = {}                           # 父節點信箱：孩子 16 位元 → 一則訊息
        self.finds = {}                          # 找位址中：64 位元 → [等著的函式]
        self.rats = []                           # 等遠端 AT 回應
        self.nd = None
        self.last_rx = None
        self.dup = {}
        self.asleep = False
        self.held = []                           # 終端裝置睡著時，主控要送的東西先留著
        self.poll_fail = 0
        self.t_form = now_ms()
        self.seq = _rand(8)
        self.t_led = now_ms()
        self.t_io = now_ms()
        self.t_poll = now_ms()
        self.t_act = now_ms()
        self.t_retry = None
        self.poll_wait = False

    def _restart_net(self):
        # 離開目前的網路，照角色重新建網或入網
        was = self.state == 'joined'
        self._reset_net()
        if was:
            self._modem(0x03)
        self._role = self._want_role()
        self.asleep = False
        if self.role() == 0:
            self._form()
        else:
            self._scan_start()

    def _form(self):
        # 協調器建網：能量掃描 → 挑頻道 → 決定 16 位元 PAN ID
        self.ed_table = energy(self.seen, (self.ap_ch, OWN_AP_DBM))
        ch = pick_channel(self.ed_table, self.c['SC'])
        if ch is None:
            self.ai = 0x25
            self._event('建網失敗：SC 遮罩裡沒有可用的頻道')
            return
        self.ch = ch
        self.air.tune(ch)
        idv = self.c['ID']
        lo = idv & 0xFFFF
        self.oi = lo if lo not in (0, 0xFFFF) else _rand(16) % 0xFFFE + 1
        self.op = idv if idv else _rand(32) << 32 | _rand(32)
        self.my = 0x0000
        self.state = 'joined'
        self.ai = 0
        self.t_form = now_ms()
        self._modem(0x06)
        quiet = [d for c, d in self.ed_table if c == ch][0]
        self._event('協調器建網完成：能量掃描挑 CH %d（0x%X，約 %d dBm），PAN 0x%04X，MY 0x0000' % (ch, ch, quiet, self.oi))

    def _scan_start(self):
        self.state = 'scan'
        self.ai = 0xFF
        self.scan_chs = [c for c in range(11, 27) if (self.c['SC'] >> (c - 11)) & 1]
        self.scan_i = -1
        self.t_scan = now_ms() - SCAN_MS
        self.beacons = []

    def _scan_step(self):
        if since(self.t_scan) < SCAN_MS:
            return
        self.scan_i += 1
        if self.scan_i < len(self.scan_chs):
            ch = self.scan_chs[self.scan_i]
            self.air.tune(ch)
            self.t_scan = now_ms()
            self._send(w.mac_frame(w.FT_CMD, self._seq(), 0xFFFF, 0xFFFF, None, b'\x07'))   # 信標請求
            return
        self._choose()

    def _choose(self):
        idv = self.c['ID']
        ok = [b for b in self.beacons if idv == 0 or b['epid'] == idv]
        if not ok:
            self._fail(0x21 if not self.beacons else 0x22,
                       '找不到網路' if not self.beacons else '找到網路，可是延伸 PAN ID（ATID）都不對')
            return
        cap = 'rc' if self.role() == 1 else 'ec'
        ok2 = [b for b in ok if b['permit'] and b[cap]]
        if not ok2:
            self._fail(0x23, '找到網路，可是父節點不開放加入（NJ）或滿了')
            return
        b = sorted(ok2, key=lambda x: x['depth'])[0]
        self.join_b = b
        self.air.tune(b['ch'])
        self.state = 'assoc'
        self.t_assoc = now_ms()
        capb = 0x8E if self.role() == 1 else 0x80        # 路由器：要配位址、插電、一直聽、全功能；終端裝置：只要配位址
        f = w.mac_frame(w.FT_CMD, self._seq(), b['pan'], b['src'], self.ext, bytes([1, capb]), ar=True, src_pan=0xFFFF)
        self._send_tx(f, None)

    def _fail(self, ai, why):
        self.state = 'idle'
        self.ai = ai
        self.t_retry = now_ms()
        self._event('入網失敗（AI＝0x%02X）：%s，5 秒後重試' % (ai, why))

    def _joined(self, short, b):
        self.state = 'joined'
        self.my = short
        self.oi = b['pan']
        self.op = b['epid']
        self.ch = b['ch']
        self.parent = b['src']
        self.depth = b['depth'] + 1
        self.ai = 0
        self.t_act = now_ms()
        self.t_form = now_ms()
        self.t_poll = now_ms() - POLL_MS
        self._modem(0x02)
        self._event('已入網：CH %d、PAN 0x%04X、父節點 0x%04X、拿到 MY 0x%04X（%s）' % (self.ch, self.oi, self.parent, short, ROLE[self.role()]))

    def _seq(self):
        self.seq = (self.seq + 1) & 0xFF
        return self.seq

    # ================= 空中收發 =================
    def _send(self, f):
        self.air.send(f)
        self._sniff(f, True)

    def _send_tx(self, f, cb):
        # 要 ACK 的訊框：最多重送 RETRIES 次；cb(成功?, 重送次數, ACK 的 pending 位元)
        self._send(f)
        self.txs.append({'f': f, 'seq': f[2], 't': now_ms(), 'n': 1, 'cb': cb})

    def _sniff(self, f, tx):
        if not self.sniff:
            return
        try:
            d = w.decode(f)
            print(('送出 ' if tx else '收到 ') + w.summary(d))
            print('  ' + w.hexs(f))
            if self.sniff >= 2 and not tx and d.get('next') is not None:
                w.tree(d)
        except Exception as e:
            print('（解碼失敗：', e, '）')

    def _rx(self, f):
        if self.asleep:
            return                               # 睡著：收發器關掉，什麼都聽不到
        d = w.parse_mac(f)
        if d['err'] or not d.get('fcs_ok'):
            return                               # FCS 不對：整個訊框丟掉
        self._sniff(f, False)
        ft = d['ftype']
        if ft == w.FT_ACK:
            self._on_ack(d)
        elif ft == w.FT_BEACON:
            if self.state == 'scan':
                self._on_beacon(d)
        elif ft == w.FT_CMD:
            self._on_cmd(d, f)
        elif ft == w.FT_DATA and self.state == 'joined':
            if d.get('dpan') != self.oi or d['dst'] not in (self.my, 0xFFFF, self.ext):
                return
            if d['ar']:
                self._send(w.mac_ack(d['seq']))
            key = d['src'] if isinstance(d['src'], int) else bytes(d['src'])
            last = self.dup.get(key)
            if last and last[0] == d['seq'] and since(last[1]) < 2000:
                return                           # 重送的同一包（ACK 掉了）：回 ACK 就好，不重複交給主控
            self.dup[key] = (d['seq'], now_ms())
            self.last_rx = f
            self.t_act = now_ms()
            if d['payload']:
                self._on_app(d)

    def _on_ack(self, d):
        for t in self.txs:
            if t['seq'] == d['seq']:
                self.txs.remove(t)
                if t['cb']:
                    t['cb'](True, t['n'] - 1, d['pending'])
                return

    def _on_beacon(self, d):
        p = d['payload']
        if len(p) < 19 or p[4] != 0:
            return
        sf = p[0] | (p[1] << 8)
        z = p[4:]
        self.beacons.append({'ch': self.air.ch, 'pan': d['span'], 'src': d['src'], 'permit': (sf >> 15) & 1,
                             'rc': (z[2] >> 2) & 1, 'ec': (z[2] >> 7) & 1, 'depth': (z[2] >> 3) & 0xF,
                             'epid': _bi(bytes(reversed(z[3:11])))})

    def _beacon(self):
        # 回信標：superframe 規格＋GTS＋pending＋ZigBee 信標酬載（協定 0、堆疊 2、容量、深度、延伸 PAN ID…）
        permit = self.c['NJ'] == 0xFF or since(self.t_form) < self.c['NJ'] * 1000
        room = len(self.children) < CAPACITY
        sf = 0x0FFF | ((self.role() == 0) << 14) | ((permit and room) << 15)
        z = bytes([0x00, 0x22, (room << 2) | (self.depth << 3) | (room << 7)])
        z += bytes(reversed(_ib(self.op, 8))) + b'\xff\xff\xff\x00'
        return w.mac_frame(w.FT_BEACON, self._seq(), self.oi, None, self.my, bytes([sf & 0xFF, sf >> 8, 0, 0]) + z)

    def _router(self):
        return self.state == 'joined' and self.role() != 2

    def _on_cmd(self, d, f):
        cmd = d.get('cmd')
        if cmd == 7:                                           # 信標請求
            if self._router():
                self._send(self._beacon())
            return
        if d['dst'] not in (self.my, self.ext):
            return
        if d['ar']:
            pend = cmd == 4 and isinstance(d['src'], int) and d['src'] in self.indq
            self._send(w.mac_ack(d['seq'], pend))
        if cmd == 1 and self._router() and d.get('dpan') == self.oi:   # 入網請求
            self._on_assoc_req(d)
        elif cmd == 2 and self.state == 'assoc':                 # 入網回應
            p = d['payload']
            if len(p) >= 4:
                short = p[1] | (p[2] << 8)
                if p[3] == 0:
                    self.ext_of[self.join_b['src']] = bytes(d['src'])
                    self.short_of[bytes(d['src'])] = self.join_b['src']
                    self._joined(short, self.join_b)
                else:
                    self._fail(0x27, '父節點拒絕（狀態 %d）' % p[3])
        elif cmd == 3 and self.state == 'joined' and d['src'] in (self.parent, self.ext_of.get(self.parent)):
            self._event('父節點要我離開（它不認得我了）：重新掃描入網')
            self._restart_net()
        elif cmd == 4 and self._router():                       # 資料請求：孩子醒來問信
            src = d['src']
            if isinstance(src, int) and src not in self.children:
                self._send_tx(w.mac_cmd(self._seq(), self.oi, src, self.my, 3, b'\x01'), None)   # 離網通知：請你重新入網
                return
            q = self.indq.pop(src, None) if isinstance(src, int) else None
            if q:
                f2 = w.mac_data(self._seq(), self.oi, src, self.my, q['p'], ar=True)
                cb = q['cb']
                self._send_tx(f2, lambda good, n, pend: cb(0x00 if good else 0x01, n))

    def _on_assoc_req(self, d):
        ext = bytes(d['src'])
        capb = d['payload'][1] if len(d['payload']) > 1 else 0
        permit = self.c['NJ'] == 0xFF or since(self.t_form) < self.c['NJ'] * 1000
        short = None
        for s in self.children:                                 # 同一顆模組重新入網：沿用原來的位址
            if self.children[s]['ext'] == ext:
                short = s
        st = 0
        if not permit:
            st = 2
        elif short is None or short not in self.children:
            if len(self.children) >= CAPACITY:
                st = 1
            else:
                short = _rand(16) % 0xFFF6 + 1
                while short in self.children or short == self.my:
                    short = _rand(16) % 0xFFF6 + 1
        if st == 0:
            self.children[short] = {'ext': ext, 'sleepy': not (capb & 0x08)}
            self.ext_of[short] = ext
            self._event('子節點 0x%04X 入網（%s，64 位元 %s）' % (short, '會睡覺的終端裝置' if not (capb & 0x08) else '路由器', w.hexs(ext, '').upper()))
        s16 = short if st == 0 else 0xFFFF
        f = w.mac_frame(w.FT_CMD, self._seq(), self.oi, ext, self.ext, bytes([2, s16 & 0xFF, s16 >> 8, st]), ar=True)
        self._send_tx(f, None)

    # ================= 應用資料（PicoBee 類型）=================
    def _src64(self, s):
        if s == self.parent and self.parent is not None and s in self.ext_of:
            return self.ext_of[s]
        return self.ext_of.get(s, UNKNOWN64)

    def _on_app(self, d):
        p = d['payload']
        t = p[0]
        src = d['src']
        bc = d['dst'] == 0xFFFF
        if isinstance(src, int):
            s16, s64 = src, self._src64(src)
        else:
            s64 = bytes(src)
            s16 = self.short_of.get(s64, 0xFFFE)
        if t == T_DATA:
            if self.ap:
                self._put(self._api(w.xb_rx(s64, s16, p[1:], 0x02 if bc else 0x01)))
            else:
                self._put(p[1:])
        elif t == T_IO and len(p) >= 5:
            if self.ap:
                dm, am = (p[2] << 8) | p[3], p[4]
                q = 5
                ds = 0
                if dm:
                    ds = (p[5] << 8) | p[6]
                    q = 7
                an = [(p[q + 2 * i] << 8) | p[q + 2 * i + 1] for i in range(bin(am).count('1'))]
                self._put(self._api(w.xb_io(s64, s16, dm, am, ds, an, 0x02 if bc else 0x01)))
        elif t == T_RAT and len(p) >= 5:
            fid, opts, cmd, prm = p[1], p[2], p[3:5].decode(), p[5:]
            if cmd == 'ND':
                self._nd_answer(s16, fid)
                return
            keep, self.on_event = self.on_event, None   # 先印「收到」，再印 LED 改變
            try:
                st, val = self._at(cmd, prm, True)
            finally:
                self.on_event = keep
            self._event('收到遠端 AT：AT%s %s → 狀態 %d' % (cmd, w.hexs(prm, '').upper(), st))
            if cmd == 'D4' and st == 0 and len(prm) and prm[-1] in (4, 5):
                self._event('DIO4（GP15）＝%d：LED %s' % (prm[-1], '亮' if prm[-1] == 5 else '熄'))
            if opts & 2:
                self._apply()
            if fid:
                self._app_send(s16, bytes([T_RATR, fid]) + cmd.encode() + bytes([st]) + (val or b''), None)
        elif t == T_RATR and len(p) >= 5:
            fid, cmd, st, val = p[1], p[2:4].decode(), p[4], p[5:]
            if cmd == 'ND':
                self._nd_got(val)
                return
            for r in self.rats:
                if r['fid'] == fid and r['s16'] in (s16, 0xFFFE):
                    self.rats.remove(r)
                    self._put(self._api(w.xb_remote_resp(fid, s64, s16, cmd, st, val)))
                    return
        elif t == T_AQ and len(p) >= 9:
            if bytes(p[1:9]) == self.ext and isinstance(src, int):
                self._app_send(src, bytes([T_AR]) + self.ext, None)
        elif t == T_AR and len(p) >= 9 and isinstance(src, int):
            e = bytes(p[1:9])
            self.ext_of[src] = e
            self.short_of[e] = src
            for fn in self.finds.pop(e, []):
                fn(src)

    def _app_send(self, dst16, payload, cb, discovery=0):
        # 送一包 PicoBee 資料到 16 位元位址 dst16；cb(遞送狀態, 重送次數)
        if self.state != 'joined':
            if cb:
                cb(0x22, 0)
            return
        if dst16 == self.my:
            if cb:
                cb(0x23, 0)
            return
        if len(payload) > MAXDATA + 1:
            if cb:
                cb(0x74, 0)
            return
        if dst16 == 0xFFFF:
            self._send(w.mac_data(self._seq(), self.oi, 0xFFFF, self.my, payload))
            if cb:
                cb(0x00, 0)
            return
        ch = self.children.get(dst16)
        if ch and ch['sleepy']:                                 # 孩子在睡覺：放進父節點信箱，等它來問
            old = self.indq.get(dst16)
            if old and old['cb']:
                old['cb'](0x75, 0)
            self.indq[dst16] = {'p': payload, 't': now_ms(), 'cb': cb or (lambda s, n: None)}
            return
        self._send_tx(w.mac_data(self._seq(), self.oi, dst16, self.my, payload, ar=True),
                      lambda good, n, pend: cb and cb(0x00 if good else 0x01, n))

    def _resolve(self, d64, d16, fn):
        # 把目的地換成 16 位元位址：fn(16 位元或 None, 探索狀態)
        if d64 == BCAST64 or d16 == 0xFFFF:
            fn(0xFFFF, 0)
        elif d64 == COORD64:
            fn(0x0000, 0)
        elif d16 != 0xFFFE:
            fn(d16, 0)
        elif d64 == self.ext:
            fn(self.my, 0)
        elif self._sleepy_child(d64) is not None:               # 睡覺的孩子：父節點自己知道它的位址
            fn(self._sleepy_child(d64), 0)
        elif d64 in self.short_of:
            fn(self.short_of[d64], 0)
        else:                                                   # 不知道 16 位元位址：廣播問「誰是這個 64 位元？」
            if self.state != 'joined':
                fn(None, 0)
                return
            lst = self.finds.setdefault(d64, [])
            lst.append(lambda s: fn(s, 1))
            if len(lst) == 1:
                self.t_find = now_ms()
                self._send(w.mac_data(self._seq(), self.oi, 0xFFFF, self.my, bytes([T_AQ]) + d64))

    def _tx_request(self, fid, d64, d16, data, kind=T_DATA, done=None):
        # 0x10 傳送要求（透明模式也走這裡，fid＝0 就不回 0x8B）
        res = {}

        def fin(st, n):
            if fid:
                self._put(self._api(w.xb_tx_status(fid, res.get('s16', 0xFFFE) if st == 0 else 0xFFFE, n, st, res.get('disc', 0))))
            if done:
                done(st)

        def go(s16, disc):
            res['disc'] = disc
            if s16 is None:
                fin(0x24, 0)
                return
            res['s16'] = 0xFFFE if s16 == 0xFFFF else s16
            self._app_send(s16, bytes([kind]) + data, fin, disc)
        if self.state != 'joined':
            fin(0x22, 0)
            return
        if self.asleep:
            self.held.append((fid, d64, d16, data, kind, done))
            return
        self.t_act = now_ms()
        self._resolve(d64, d16, go)

    def _sleepy_child(self, d64):
        for s in self.children:
            if self.children[s]['sleepy'] and self.children[s]['ext'] == d64:
                return s
        return None

    def _dest64(self):
        return (self.c['DH'] << 32) | self.c['DL']

    def _send_io(self):
        dm, am, ds, an = self._sample()
        if not dm and not am:
            return
        body = bytes([T_IO, 1]) + _ib(dm, 2) + bytes([am]) + (_ib(ds, 2) if dm else b'')
        for v in an:
            body += _ib(v, 2)
        self._tx_request(0, _ib(self._dest64(), 8), 0xFFFE, body[1:], T_IO)

    # ================= I/O 腳位 =================
    def _apply_pins(self):
        if not machine:
            self.pins = [_NoPin() for _ in range(5)]
            return
        P = machine.Pin
        for i in range(5):
            m = self.c['D%d' % i]
            n = PINS[i]
            if m == 2 and i <= 2:
                self.pins[i] = machine.ADC(P(n))
            elif m == 3:
                self.pins[i] = P(n, P.IN, P.PULL_UP)
            elif m in (4, 5):
                self.pins[i] = P(n, P.OUT)
                self.pins[i].value(1 if m == 5 else 0)
            else:
                self.pins[i] = P(n, P.IN)

    def _sample(self):
        dm = am = ds = 0
        an = []
        for i in range(5):
            m = self.c['D%d' % i]
            if m in (3, 4, 5):
                dm |= 1 << i
                if self.pins[i].value():
                    ds |= 1 << i
            elif m == 2 and i <= 2:
                am |= 1 << i
                an.append(self.pins[i].read_u16() >> 4)        # Pico 的 ADC：12 位元（0～4095）
        return dm, am, ds, an

    # ================= 節點探索 ND／DN =================
    def _nd_start(self, fid, api, name=None):
        self.nd = {'t': now_ms(), 'fid': fid, 'api': api, 'name': name, 'seen': []}
        self._send(w.mac_data(self._seq(), self.oi, 0xFFFF, self.my, bytes([T_RAT, 0x01, 0x02]) + b'ND'))

    def _nd_record(self):
        rec = _ib(self.my, 2) + self.ext + self.c['NI'].encode() + b'\x00'
        return rec + _ib(self.parent if self.parent is not None else 0xFFFE, 2) + bytes([self.role()])

    def _nd_answer(self, s16, fid):
        if self.state == 'joined':
            self._app_send(s16, bytes([T_RATR, fid]) + b'ND' + bytes([0]) + self._nd_record(), None)

    def _nd_got(self, v):
        nd = self.nd
        if not nd or len(v) < 14:
            return
        my, sh, sl = _bi(v[0:2]), _bi(v[2:6]), _bi(v[6:10])
        k = v.find(b'\x00', 10)
        ni = v[10:k].decode()
        par, typ = _bi(v[k + 1:k + 3]), v[k + 3]
        self.ext_of[my] = bytes(v[2:10])
        self.short_of[bytes(v[2:10])] = my
        if nd['name'] is not None:
            if ni == nd['name']:
                self.c['DH'], self.c['DL'] = sh, sl
                self.nd = None
                if nd['api']:
                    self._put(self._api(w.xb_at_resp(nd['fid'], 'DN', 0, v[2:10])))
                else:
                    self._put(b'OK\r')
                    self.cmd = False                     # DN 找到之後直接離開命令模式，馬上可以聊天
            return
        if nd['api']:
            self._put(self._api(w.xb_at_resp(nd['fid'], 'ND', 0, v)))
        else:
            self._put(('%X\r%X\r%X\r%s\r%X\r%d\r\r' % (my, sh, sl, ni, par, typ)).encode())

    # ================= AT 指令 =================
    def _get(self, k):
        if k in self.c:
            return self.c[k]
        if k == 'OI':
            return self.oi
        if k == 'OP':
            return self.op
        if k == 'CH':
            return self.ch or 0
        if k == 'MY':
            return self.my
        if k == 'SH':
            return _bi(self.ext[:4])
        if k == 'SL':
            return _bi(self.ext[4:])
        if k == 'AI':
            return self.ai
        if k == 'NC':
            return CAPACITY - len(self.children) if self.role() != 2 else 0
        if k == 'VR':
            return ((0x20, 0x22, 0x28)[self.role()] + (1 if self.c['AP'] else 0)) << 8 | 0x70
        if k in ('NP', 'MP'):
            return MAXDATA if k == 'NP' else (self.parent if self.parent is not None else 0xFFFE)
        return 0

    def _at(self, cmd, prm, api):
        # 執行一個 AT 指令。prm：API＝位元組、AT 模式＝文字。回傳 (狀態, 回傳值)；狀態 0 OK、1 ERROR、2 指令無效、3 參數無效
        cmd = cmd.upper()
        if cmd in ('WR', 'RE', 'AC', 'NR', 'CN', 'IS', 'ND', 'DN') or cmd == '':
            return self._exec(cmd, prm, api)
        if cmd not in PARAM:
            return 2, b''
        size, lo, hi, net = PARAM[cmd]
        if not prm:
            v = self._get(cmd)
            if size == 0:
                return 0, v.encode()
            return 0, _ib(v, size) if api else ('%X' % v).encode()
        if lo is None:
            return 3, b''
        if size == 0:
            s = prm.decode() if api else prm
            if len(s) > hi:
                return 3, b''
            self.c[cmd] = s
            return 0, b''
        try:
            v = _bi(prm) if api else int(prm.strip(), 16)
        except ValueError:
            return 3, b''
        pin = cmd in ('D0', 'D1', 'D2', 'D3', 'D4')
        if v < lo or v > hi or (cmd == 'SM' and v not in (0, 4)) or (pin and (v == 1 or (v == 2 and cmd > 'D2'))):
            return 3, b''
        if cmd == 'IR' and 0 < v < 0x32:
            return 3, b''
        old = self.c[cmd]
        self.c[cmd] = v
        if pin:
            self._apply_pins()
            if cmd == 'D4' and old != v:
                self._event('DIO4（GP15）改成 %d：LED %s' % (v, '亮' if v == 5 else ('熄' if v == 4 else '關')))
        if net and old != v:
            self._dirty = True
        return 0, b''

    def _exec(self, cmd, prm, api):
        if cmd == '':
            return 0, b''
        if cmd == 'WR':
            self._save()
        elif cmd == 'RE':
            self.c = dict(DEFAULTS)
            self._apply_pins()
            self._dirty = True
        elif cmd == 'AC':
            self._apply()
        elif cmd == 'NR':
            self._dirty = True
            self._apply()
        elif cmd == 'IS':
            dm, am, ds, an = self._sample()
            if not dm and not am:
                return 1, b''
            body = bytes([1]) + _ib(dm, 2) + bytes([am]) + (_ib(ds, 2) if dm else b'')
            for v in an:
                body += _ib(v, 2)
            if api:
                return 0, body
            lines = ['01', '%04X' % dm, '%02X' % am] + (['%04X' % ds] if dm else []) + ['%04X' % v for v in an]
            return 0, '\r'.join(lines).encode()
        elif cmd in ('ND', 'DN'):
            if self.state != 'joined':
                return 1, b''
            name = (prm.decode() if api else prm.strip()) if cmd == 'DN' else None
            if cmd == 'DN' and not name:
                return 3, b''
            self._nd_start(self._api_fid if api else 0, api, name)
            return 0, None                                      # 結果之後才陸續送出來
        return 0, b''

    def _apply(self):
        self.ap = self.c['AP']
        self._apply_pins()
        if self._dirty:
            self._dirty = False
            self._restart_net()

    def _at_line(self, line):
        # 命令模式收到一行：ATID 1001、ATID 1001,WR,CN 這種
        s = line.strip()
        if s[:2].upper() != 'AT':
            self._put(b'ERROR\r')
            return
        parts = s[2:].split(',')
        for i, part in enumerate(parts):
            part = part.strip() if i else part
            cmd, prm = part[:2].upper(), part[2:]
            if cmd not in ('NI', 'DN'):
                prm = prm.strip()
            elif prm[:1] == ' ':
                prm = prm[1:]
            if cmd == 'CN':
                self._put(b'OK\r')
                self.cmd = False
                self._apply()
                return
            st, val = self._at(cmd, prm, False)
            if val is None:
                if cmd == 'DN':
                    return
                continue
            if st:
                self._put(b'ERROR\r')
                return
            self._put((val or b'OK') + b'\r')

    # ================= 序列線輸入 =================
    def _feed(self, t, data):
        if self.ap:
            self.apibuf += data
            fs, self.apibuf = w.xb_split(self.apibuf, self.ap == 2)
            for f in fs:
                self._api_in(f)
            return
        for i in range(len(data)):
            b = data[i:i + 1]
            if self.cmd:
                self.t_cmd = t
                if b == b'\r':
                    ln, self.line = self.line, ''
                    self._at_line(ln)
                elif b != b'\n':
                    self.line += chr(b[0])
                continue
            if b == b'+' and (self.plus or since_t(self.t_in, t) >= self.c['GT']) and len(self.plus) < 3:
                self.plus += b                         # 可能是 +++：先留著，等保護時間過了再說
                self.t_plus = t
            else:
                if self.plus:
                    self.tx_buf += self.plus           # 不是 +++：剛剛的 + 號當成資料送出去
                    self.plus = b''
                self.tx_buf += b
            self.t_in = t

    def _api_in(self, f):
        d = w.parse_xbee(f)
        if not w.ok(d):
            return                                     # 檢查碼不對：整個訊框丟掉，不回應
        t = d['api']
        if t in (0x08, 0x09):
            cmd = d['cmd'].decode()
            self._api_fid = d['fid']
            st, val = self._at(cmd, d['param'], True)
            if val is None:
                return
            if cmd == 'CN':
                st = 0
            if d['fid']:
                self._put(self._api(w.xb_at_resp(d['fid'], cmd, st, val or b'')))
            if t == 0x08 and st == 0 and cmd not in ('AC', 'NR'):
                self._apply()
        elif t == 0x10:
            self._tx_request(d['fid'], bytes(d['dst64']), d['dst16'], d['data'])
        elif t == 0x17:
            fid = d['fid']
            body = bytes([d['opts']]) + d['cmd'] + d['param']
            d64 = bytes(d['dst64'])

            def go(s16, disc):
                if s16 is None or s16 == 0xFFFF:
                    if fid:
                        self._put(self._api(w.xb_remote_resp(fid, d64, 0xFFFE, d['cmd'], 4)))
                    return
                if fid:
                    self.rats.append({'fid': fid, 's16': s16, 'd64': d64, 'cmd': d['cmd'], 't': now_ms(),
                                      'lim': 3000 + int(HOLD * self.c['SP'] * 10)})

                def sent(st, n):
                    if st and fid:
                        for r in self.rats:
                            if r['fid'] == fid and r['s16'] == s16:
                                self.rats.remove(r)
                                break
                        self._put(self._api(w.xb_remote_resp(fid, d64, s16, d['cmd'], 4)))
                self._app_send(s16, bytes([T_RAT, fid]) + body, sent)
            self._resolve(d64, d['dst16'], go)

    # ================= 主迴圈 =================
    def poll(self):
        # 模組跑一輪：序列線輸入、空中收訊、各種計時器
        if self._busy:
            return
        self._busy = True
        try:
            while self._inq:
                t, data = self._inq.pop(0)
                self._feed(t, data)
            for _ in range(10):
                f = self.air.recv()
                if f is None:
                    break
                self._rx(f)
            self._timers()
            if self._out and self.on_out:
                self.on_out(self.read())
        except Exception as e:
            msg = repr(e)
            if msg != self._err[0] or since(self._err[1]) > 5000:
                print('PicoBee 錯誤：', msg)
                self._err = (msg, now_ms())
        self._busy = False

    def _timers(self):
        n = now_ms()
        # +++ 的保護時間
        if self.plus and since(self.t_plus) >= self.c['GT'] and since_t(self.t_in, n) >= self.c['GT']:
            if self.plus == b'+++':
                self.cmd = True
                self.t_cmd = n
                self.line = ''
                self._put(b'OK\r')
            else:
                self.tx_buf += self.plus
            self.plus = b''
        if self.cmd and since(self.t_cmd) >= self.c['CT'] * 100:
            self.cmd = False                           # 命令模式逾時：自動回到透明模式
            self._apply()
        # 透明模式：打進來的字停一下就送出去
        if self.tx_buf and not self.asleep and (since_t(self.t_in, n) >= 4 or len(self.tx_buf) >= MAXDATA):
            data, self.tx_buf = self.tx_buf[:MAXDATA], self.tx_buf[MAXDATA:]
            if self.state == 'joined':
                self.t_act = n
                self._tx_request(0, _ib(self._dest64(), 8), 0xFFFE, data)
        # 等 ACK、重送
        for t in self.txs[:]:
            if since(t['t']) >= ACK_MS:
                if t['n'] <= RETRIES:
                    t['n'] += 1
                    t['t'] = n
                    self._send(t['f'])
                else:
                    self.txs.remove(t)
                    if t['cb']:
                        t['cb'](False, RETRIES, 0)
        # 父節點信箱逾時
        lim = int(HOLD * self.c['SP'] * 10)
        for k in list(self.indq.keys()):
            q = self.indq[k]
            if since(q['t']) >= lim:
                del self.indq[k]
                q['cb'](0x75, 0)
        # 找位址逾時
        if self.finds and since(self.t_find) >= FIND_MS:
            fs, self.finds = self.finds, {}
            for k in fs:
                for fn in fs[k]:
                    fn(None)
        # 遠端 AT 逾時
        for r in self.rats[:]:
            if since(r['t']) >= r['lim']:
                self.rats.remove(r)
                self._put(self._api(w.xb_remote_resp(r['fid'], r['d64'], r['s16'], r['cmd'], 4)))
        # ND／DN 逾時
        if self.nd and since(self.nd['t']) >= self.c['NT'] * 100:
            nd, self.nd = self.nd, None
            if nd['name'] is not None:
                if nd['api']:
                    self._put(self._api(w.xb_at_resp(nd['fid'], 'DN', 1)))
                else:
                    self._put(b'ERROR\r')
            elif not nd['api']:
                self._put(b'\r')
        # 入網、睡眠、I/O 取樣
        if self.state == 'scan':
            self._scan_step()
        elif self.state == 'assoc' and since(self.t_assoc) >= 1500:
            self._fail(0x27, '父節點沒有回應入網請求')
        elif self.state == 'idle' and self.t_retry is not None and since(self.t_retry) >= 5000:
            self.t_retry = None
            self._restart_net()
        elif self.state == 'joined':
            if self.role() == 2:
                self._sleep_cycle(n)
            elif self.c['IR'] and since(self.t_io) >= self.c['IR']:
                self.t_io = n
                self._send_io()
        self._led(n)

    def _sleep_cycle(self, n):
        # 終端裝置：睡 SP×10 毫秒 → 醒來問父節點有沒有信、送一次 I/O 取樣 → 沒事做 ST 毫秒後再睡
        if self.asleep:
            if since(self.t_sleep) >= self.c['SP'] * 10:
                self.asleep = False
                self.t_act = n
                self.t_poll = n - POLL_MS
                self._event('醒來（睡了 %.2f 秒），問父節點有沒有我的信' % (self.c['SP'] / 100))
                if self.c['IR']:
                    self._send_io()
                held, self.held = self.held, []
                for h in held:
                    self._tx_request(*h)
            return
        if since(self.t_poll) >= POLL_MS and not self.poll_wait:
            self.t_poll = n
            self.poll_wait = True
            f = w.mac_cmd(self._seq(), self.oi, self.parent, self.my, 4)

            def got(good, k, pend):
                self.poll_wait = False
                self.poll_fail = 0 if good else self.poll_fail + 1
                if good and pend:
                    self.t_act = now_ms()               # 父節點說「我這裡有你的信」：先別睡
                if self.poll_fail >= 3:
                    self._event('連續 3 次問不到父節點：重新掃描入網')
                    self._restart_net()
            self._send_tx(f, got)
        if since(self.t_act) >= self.c['ST'] and not self.txs and not self.poll_wait and not self.cmd:   # 命令模式時不睡
            self.asleep = True
            self.t_sleep = n
            self._event('睡著（SP＝0x%X，%.2f 秒後醒來）' % (self.c['SP'], self.c['SP'] / 100))

    def _led(self, n):
        # 板載 LED 當 ASSOC 燈：還沒入網恆亮、入網後閃（協調器 0.5 秒、其他 0.25 秒）、睡著熄滅
        if self.state != 'joined':
            self.led.value(1)
        elif self.asleep:
            self.led.value(0)
        elif since(self.t_led) >= (500 if self.role() == 0 else 250):
            self.t_led = n
            self.led.value(0 if self.led.value() else 1)

    # ================= 給人看的 =================
    def whoami(self):
        return '板子 %s｜%s｜%s｜CH %s｜PAN 0x%04X｜MY 0x%04X｜AI 0x%02X' % (
            self.board, ROLE[self.role()], {'joined': '已入網', 'scan': '掃描中', 'assoc': '入網中'}.get(self.state, '未入網'),
            self.ch or '-', self.oi, self.my, self.ai)

    def term(self, sniff=None, tree=True):
        # PicoBee 終端機：AT 模式打字（+++ 單獨一行不補 Enter）；API 模式打十六進位。以 . 開頭的是終端機自己的指令
        if sniff is not None:
            self.sniff = sniff
        self._tree = tree
        self._hex = False
        self._tbuf = b''
        self.on_out = self._t_out
        self.on_event = lambda t: print('（PicoBee）' + t)
        print('==== PicoBee 終端機 ====  ' + self.whoami())
        print('打 +++ 按 Enter 進命令模式；AT 指令或文字按 Enter 送出；.help 看終端機選單')
        while True:
            try:
                line = input()
            except (KeyboardInterrupt, EOFError):
                break
            if line[:1] == '.':
                if self._meta(line.split()):
                    break
                continue
            if self.ap or self._hex:
                try:
                    data = w.unhex(line)
                except ValueError:
                    print('（看不懂的十六進位）')
                    continue
                print('→ 送進模組 ' + w.hexs(data).upper())
            elif line and line.strip('+') == '':
                data = line.encode()                    # 只有 + 號：照打的送，不補 Enter（真的終端機打完 +++ 不能按 Enter）
            else:
                data = line.encode() + b'\r'
            self.write(data)
            if not self._timer:
                self.wait(1300 if data[-1:] == b'+' else 500)
        self.on_out = None
        self.on_event = None
        self.stop()
        print('PicoBee 已停止')

    def _t_out(self, b):
        if self.ap:
            self._tbuf += b
            fs, self._tbuf = w.xb_split(self._tbuf, self.ap == 2)
            for f in fs:
                print('← 模組送出 ' + w.hexs(f).upper())
                if self._tree:
                    w.tree(w.decode_any(f))
            return
        try:
            s = b.decode()
        except UnicodeError:
            s = ''.join(chr(c) if 32 <= c < 127 or c in (10, 13) else '.' for c in b)
        print(s.replace('\r\n', '\n').replace('\r', '\n'), end='')

    def _meta(self, a):
        k = a[0].lower()
        v = a[1] if len(a) > 1 else ''
        if k == '.quit':
            return True
        if k == '.sniff':
            self.sniff = int(v or 1)
        elif k == '.hex':
            self._hex = v != 'off'
        elif k == '.tree':
            self._tree = v != 'off'
        elif k == '.wait':
            self.wait(int(float(v or 1) * 1000))
        elif k == '.last':
            if self.last_rx:
                print(w.hexdump(self.last_rx))
                w.tree(w.decode(self.last_rx))
            else:
                print('（還沒收到給我的資料訊框）')
        elif k == '.status':
            print(self.whoami())
            if self.ed_table:
                print('能量掃描（dBm）：' + '  '.join('%d:%d' % x for x in self.ed_table))
            if self.children:
                print('子節點：' + '、'.join('0x%04X%s' % (s, '（睡）' if c['sleepy'] else '') for s, c in self.children.items()))
        else:
            print('.sniff 0|1|2 印空中訊框　.hex on|off 十六進位輸入　.tree on|off　.last 最後收到的訊框　'
                  '.status 狀態　.wait 秒數　.quit 離開')
        return False


def since_t(t0, t):
    # t0 到 t 過了幾毫秒（t0 是 None 表示很久以前）
    if t0 is None:
        return 1 << 30
    return w.ms_since(t0, t)


# ---------------- 主控端小工具 ----------------
def frames(bee, ms=1000, n=1, want=None):
    # 收模組送出來的 API 訊框：最多等 ms 毫秒，收到 n 個（符合 want 的）就停；回傳訊框清單
    buf = b''
    got = []
    t0 = now_ms()
    while since(t0) < ms and len(got) < n:
        bee.wait(20)
        buf += bee.read()
        fs, buf = w.xb_split(buf, bee.ap == 2)
        for f in fs:
            if want is None or want(w.parse_xbee(f)):
                got.append(f)
    return got


def api_on(bee, mode=1):
    # 從 AT 模式切到 API 模式（+++、ATAP 1、ATCN），回傳模組回的字
    bee.wait(1100)
    bee.write(b'+++')
    bee.wait(1200)
    bee.write(('ATAP %d\r' % mode).encode())
    bee.wait(300)
    bee.write(b'ATCN\r')
    bee.wait(300)
    return bee.read()
