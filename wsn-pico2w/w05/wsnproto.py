# wsnproto.py：無線感測網路的協定位元組函式庫（主題 5 PicoBee、主題 8 6LoWPAN、主題 10 RPL 共用）
#
# Pico 2 W 的 MicroPython 和電腦端 Python 3 都能跑，只用 binascii、time 兩個模組（位元組都用 bytes([...]) 自己排，方便對照位元圖）。
# 欄位與數字依據：IEEE 802.15.4-2006（MAC 訊框、FCS）、Digi XBee 3 Zigbee 使用手冊（API 訊框）、
# RFC 4944（6LoWPAN 分派、分片）、RFC 6282（IPHC、NHC-UDP）、RFC 8200（IPv6）、RFC 768／4443（UDP、ICMPv6）、
# RFC 6550（RPL）、RFC 6552（OF0）、RFC 6719（MRHOF）。
#
# 目錄
#   1. 小工具：十六進位、時間、位址
#   2. IEEE 802.15.4 MAC：FCS、組訊框、拆訊框
#   3. XBee API 訊框（PicoBee 用）
#   4. IPv6 位址、IPv6／UDP／ICMPv6 與 checksum
#   5. 6LoWPAN：IPHC 壓縮與解壓縮、NHC-UDP、Mesh 標頭、分片與重組
#   6. RPL：DIS、DIO、DAO、DAO-ACK 與選項，Rank 計算
#   7. 一路解到底：decode()、decode_any()、欄位樹 tree()、自我測試 selftest()
#
# 位址的寫法（全部函式都一樣）：
#   16 位元短位址 → 整數，例如 0x0001；廣播 0xFFFF
#   64 位元長位址 → 8 個位元組，用「人看的順序」，例如 unhex('28cdc1fffe010203')
#   6 位元組的 Wi-Fi MAC（或 '28:cd:c1:01:02:03' 文字）會自動插入 FF FE 變成 EUI-64
#   放進 802.15.4 訊框時，函式庫會自動把位址倒過來（小端序），不用自己倒。

import binascii
import time

VERSION = '2026-10-10'


# ============================================================
# 1. 小工具
# ============================================================

def hexs(b, sep=' '):
    # 位元組 → 「41 88 02」這種十六進位文字（小寫；sep 是分隔字元，給 '' 就不分隔）
    if not b:
        return ''
    if sep:
        return binascii.hexlify(bytes(b), sep).decode()
    return binascii.hexlify(bytes(b)).decode()


def unhex(text):
    # 十六進位文字 → 位元組；可以夾空白、換行、冒號、逗號、減號，也可以有 0x 前綴
    if isinstance(text, (bytes, bytearray)):
        return bytes(text)
    s = text
    for ch in ',:-;\t\r\n':
        s = s.replace(ch, ' ')
    out = []
    for tok in s.split():
        if tok[:2] in ('0x', '0X'):
            tok = tok[2:]
        if len(tok) % 2:
            raise ValueError('十六進位的位數要是偶數：' + tok)
        out.append(binascii.unhexlify(tok))
    return b''.join(out)


def hexdump(b, width=16):
    # 印成傾印格式（每行開頭是位移 0000、0010…）；wsn_decode.py 和 Wireshark 的「從十六進位傾印匯入」都看得懂
    lines = []
    for i in range(0, len(b), width):
        lines.append('{:04x}  {}'.format(i, hexs(b[i:i + width])))
    return '\n'.join(lines)


def _txt(b):
    # 位元組裡看得懂的英數字照印，其他換成「.」
    return ''.join(chr(c) if 32 <= c < 127 else '.' for c in b)


def _printable(b):
    # 這串位元組是不是大部分（八成以上）都是看得懂的文字
    if not b:
        return False
    n = 0
    for c in b:
        if 32 <= c < 127 or c in (9, 10, 13):
            n += 1
    return n * 5 >= len(b) * 4


if hasattr(time, 'ticks_ms'):
    def now_ms():
        # 現在的毫秒數（Pico：time.ticks_ms）
        return time.ticks_ms()

    def ms_since(t0, now=None):
        # 從 t0 到現在（或到 now）過了幾毫秒；會處理 ticks 繞回
        return time.ticks_diff(time.ticks_ms() if now is None else now, t0)
else:
    def now_ms():
        # 現在的毫秒數（電腦：time.monotonic）
        return int(time.monotonic() * 1000)

    def ms_since(t0, now=None):
        # 從 t0 到現在（或到 now）過了幾毫秒
        return (now_ms() if now is None else now) - t0


def _addr(a):
    # 把位址整理成標準樣子：None、整數（短位址）或 8 位元組（長位址，人看的順序）
    if a is None or isinstance(a, int):
        return a
    if isinstance(a, str):
        a = unhex(a)
    a = bytes(a)
    if len(a) == 6:
        return eui64(a)
    if len(a) != 8:
        raise ValueError('位址要是整數（16 位元短位址），或 6／8 位元組（長位址）')
    return a


def addr_str(a):
    # 位址 → 文字：短位址印成 0x0002，長位址印成 28:cd:c1:ff:fe:01:02:03
    if a is None:
        return '（沒有）'
    if isinstance(a, int):
        return '0x{:04x}'.format(a) + ('（廣播）' if a == 0xFFFF else '')
    return hexs(a, ':')


class _R:
    # 依序從位元組裡拿欄位的小幫手：拿不夠就報錯；log 給清單時順便記下「拿了什麼」
    def __init__(self, b, p=0):
        # b 是要讀的位元組、p 是目前讀到的位置
        self.b = b
        self.p = p

    def take(self, n, name='欄位', log=None):
        # 拿 n 個位元組
        if self.p + n > len(self.b):
            raise ValueError('資料不夠：{}需要 {} 位元組，只剩 {}'.format(name, n, len(self.b) - self.p))
        v = bytes(self.b[self.p:self.p + n])
        self.p += n
        if log is not None and n:
            log.append((name, v))
        return v


def _need(b, n, what):
    # 長度不夠 n 就報錯
    if len(b) < n:
        raise ValueError('{}至少要 {} 位元組，只有 {}'.format(what, n, len(b)))


def _new(proto, n):
    # 每一層解碼結果的空白 dict：err 是錯誤、note 是說明、chk 是（名稱, 對不對, 正確值）
    return {'proto': proto, 'len': n, 'err': [], 'note': [], 'chk': []}


# ============================================================
# 2. IEEE 802.15.4 MAC
# ============================================================

FT_BEACON = 0
FT_DATA = 1
FT_ACK = 2
FT_CMD = 3
BROADCAST = 0xFFFF
MAX_FRAME = 127          # 802.15.4 一個訊框最多 127 位元組（含 2 位元組 FCS）


def crc16(data):
    # 802.15.4 的 FCS：CRC-16/KERMIT（ITU-T 多項式 x^16+x^12+x^5+1、位元反射 0x8408、初值 0）
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc


def add_fcs(frame):
    # 在訊框最後補上 2 位元組 FCS（小端序：低位元組先放）
    frame = bytes(frame)
    c = crc16(frame)
    return frame + bytes([c & 0xFF, c >> 8])


def fcs_ok(frame):
    # 最後 2 個位元組是不是正確的 FCS
    if len(frame) < 5:
        return False
    return crc16(frame[:-2]) == (frame[-2] | (frame[-1] << 8))


def _ab(a):
    # 位址放進訊框時要倒過來（小端序）：0x0002 → 02 00；28:cd:…:03 → 03 … cd 28
    if isinstance(a, int):
        return bytes([a & 0xFF, a >> 8])
    return bytes(reversed(a))


def _am(a):
    # 看位址的型態決定位址模式：None → 0、短位址 → 2、長位址 → 3
    if a is None:
        return 0
    return 2 if isinstance(a, int) else 3


def mac_frame(ftype, seq, pan=None, dst=None, src=None, payload=b'', ar=False,
              pending=False, src_pan=None, panc=None, version=0, fcs=True):
    # 組 802.15.4 MAC 訊框（版本 0／1 規則）：兩個位址都有、又在同一個 PAN 時自動 PAN ID 壓縮
    dst = _addr(dst)
    src = _addr(src)
    dm, sm = _am(dst), _am(src)
    if (dm or sm) and pan is None:
        raise ValueError('有位址就要給 PAN ID')
    if src_pan is None:
        src_pan = pan
    if panc is None:
        panc = dm != 0 and sm != 0 and src_pan == pan
    fcf = (ftype | (int(bool(pending)) << 4) | (int(bool(ar)) << 5) | (int(bool(panc)) << 6)
           | (dm << 10) | (version << 12) | (sm << 14))
    h = bytes([fcf & 0xFF, fcf >> 8, seq & 0xFF])
    if dm:
        h += _ab(pan) + _ab(dst)
    if sm:
        if not (panc and dm):
            h += _ab(src_pan)
        h += _ab(src)
    f = h + bytes(payload)
    if len(f) + 2 > MAX_FRAME:
        raise ValueError('訊框 {} 位元組（含 FCS）超過 127'.format(len(f) + 2))
    return add_fcs(f) if fcs else f


def mac_data(seq, pan, dst, src, payload, ar=False, pending=False, fcs=True):
    # 組資料訊框（Data）：最常用的一種
    return mac_frame(FT_DATA, seq, pan, dst, src, payload, ar, pending, fcs=fcs)


def mac_ack(seq, pending=False, fcs=True):
    # 組確認訊框（Ack）：02 00＋序號＋FCS 共 5 位元組；pending＝True 表示「我這裡還有你的信」
    f = bytes([FT_ACK | (int(bool(pending)) << 4), 0, seq & 0xFF])
    return add_fcs(f) if fcs else f


def mac_cmd(seq, pan, dst, src, cmd, data=b'', ar=True, fcs=True):
    # 組 MAC 命令訊框，例如 cmd＝4 資料請求（睡醒的終端裝置向父節點「問信」）
    return mac_frame(FT_CMD, seq, pan, dst, src, bytes([cmd]) + bytes(data), ar, fcs=fcs)


def _pan_2015(dm, sm, panc):
    # IEEE 802.15.4-2015 表 7-2：版本 2 的訊框哪些 PAN ID 會出現（回傳 目的 PAN 有沒有, 來源 PAN 有沒有）
    if dm == 0 and sm == 0:
        return panc == 1, False
    if dm and not sm:
        return not panc, False
    if sm and not dm:
        return False, not panc
    if dm == 3 and sm == 3:
        return not panc, False
    return True, not panc


def parse_mac(f, fcs=True):
    # 拆解 802.15.4 MAC 訊框 → dict（短位址是整數、長位址是 8 位元組人看的順序）；fcs＝True 表示最後 2 位元組是 FCS
    f = bytes(f)
    d = _new('mac', len(f))
    d['has_fcs'] = fcs
    body = f
    if fcs:
        if len(f) < 5:
            d['err'].append('訊框太短，放不下 FCS')
            return d
        body = f[:-2]
        d['fcs'] = f[-2] | (f[-1] << 8)
        d['fcs_calc'] = crc16(body)
        d['fcs_ok'] = d['fcs'] == d['fcs_calc']
        d['chk'].append(('FCS（CRC-16）', d['fcs_ok'], '0x{:04x}'.format(d['fcs_calc'])))
    if len(body) < 2:
        d['err'].append('訊框太短，連訊框控制都放不下')
        return d
    fcf = body[0] | (body[1] << 8)
    ver = (fcf >> 12) & 3
    d['fcf'] = fcf
    d['ftype'] = fcf & 7
    d['sec'] = (fcf >> 3) & 1
    d['pending'] = (fcf >> 4) & 1
    d['ar'] = (fcf >> 5) & 1
    d['panc'] = (fcf >> 6) & 1
    d['seqsup'] = (fcf >> 8) & 1
    d['ie'] = (fcf >> 9) & 1
    d['dmode'] = (fcf >> 10) & 3
    d['ver'] = ver
    d['smode'] = (fcf >> 14) & 3
    dm, sm, panc = d['dmode'], d['smode'], d['panc']
    p = 2
    if d['seqsup'] and ver == 2:
        d['seq'] = None
    else:
        if len(body) < 3:
            d['err'].append('訊框太短，放不下序號')
            return d
        d['seq'] = body[2]
        p = 3
    if dm == 1 or sm == 1:
        d['err'].append('位址模式 1 是保留值')
        return d
    if ver < 2:
        has_dp = dm != 0
        has_sp = sm != 0 and not (panc and dm != 0)
    else:
        has_dp, has_sp = _pan_2015(dm, sm, panc)
    alen = (0, 0, 2, 8)
    need = p + (2 if has_dp else 0) + alen[dm] + (2 if has_sp else 0) + alen[sm]
    if len(body) < need:
        d['err'].append('MAC 標頭應該有 {} 位元組，訊框只有 {}'.format(need, len(body)))
        return d
    if has_dp:
        d['dpan'] = body[p] | (body[p + 1] << 8)
        p += 2
    d['dst'] = None
    if dm == 2:
        d['dst'] = body[p] | (body[p + 1] << 8)
        p += 2
    elif dm == 3:
        d['dst'] = bytes(reversed(body[p:p + 8]))
        p += 8
    if has_sp:
        d['span'] = body[p] | (body[p + 1] << 8)
        p += 2
    d['src'] = None
    if sm == 2:
        d['src'] = body[p] | (body[p + 1] << 8)
        p += 2
    elif sm == 3:
        d['src'] = bytes(reversed(body[p:p + 8]))
        p += 8
    d['hdr_len'] = p
    d['payload'] = body[p:]
    if d['sec']:
        d['note'].append('有開安全位元：後面是輔助安全標頭與密文，本工具不解密')
    if d['ie']:
        d['note'].append('有 IE（Information Element，資訊元素）：本工具不解，酬載起點可能不準')
    if d['ftype'] == FT_CMD and d['payload']:
        d['cmd'] = d['payload'][0]
    if d['dst'] == BROADCAST and d['ar']:
        d['err'].append('廣播訊框不能要求確認（AR 要是 0）')
    return d


# ============================================================
# 3. XBee API 訊框（給 PicoBee）
# ============================================================

_XB_ESC = (0x7E, 0x7D, 0x11, 0x13)


def xb_checksum(data):
    # XBee 檢查碼＝0xFF 減掉「訊框資料」（從訊框類型到最後一個資料位元組）加總的最低 8 位元
    return 0xFF - (sum(data) & 0xFF)


def xb_frame(data):
    # 把訊框資料包成 API 訊框：7E＋長度（2 位元組、大端序）＋訊框資料＋檢查碼
    data = bytes(data)
    return b'\x7e' + bytes([len(data) >> 8, len(data) & 0xFF]) + data + bytes([xb_checksum(data)])


def xb_escape(frame):
    # API 模式 2（ATAP2）：起始字元以外的 7E 7D 11 13 都改成「7D＋（原值 XOR 0x20）」
    out = bytearray(frame[:1])
    for b in frame[1:]:
        if b in _XB_ESC:
            out.append(0x7D)
            out.append(b ^ 0x20)
        else:
            out.append(b)
    return bytes(out)


def xb_unescape(raw):
    # 把 API 模式 2 跳脫過的訊框還原
    out = bytearray()
    esc = False
    for b in raw:
        if esc:
            out.append(b ^ 0x20)
            esc = False
        elif b == 0x7D:
            esc = True
        else:
            out.append(b)
    return bytes(out)


def xb_split(buf, escaped=False):
    # 從序列埠收到的一串位元組切出完整的 API 訊框；回傳（訊框清單, 還沒收完的剩餘位元組）
    buf = bytes(buf)
    frames = []
    i = 0
    while True:
        j = buf.find(b'\x7e', i)
        if j < 0:
            return frames, b''
        if escaped:
            k = buf.find(b'\x7e', j + 1)
            one = xb_unescape(buf[j:] if k < 0 else buf[j:k])
            if len(one) < 3 or len(one) < ((one[1] << 8) | one[2]) + 4:
                if k < 0:
                    return frames, buf[j:]
                i = k
                continue
            frames.append(one[:((one[1] << 8) | one[2]) + 4])
            if k < 0:
                return frames, b''
            i = k
            continue
        if len(buf) - j < 3:
            return frames, buf[j:]
        n = (buf[j + 1] << 8) | buf[j + 2]
        if len(buf) - j < n + 4:
            return frames, buf[j:]
        frames.append(buf[j:j + n + 4])
        i = j + n + 4


def _b64(a):
    # XBee 的 64 位元位址（大端序 8 位元組）：可以給整數、8 位元組或 '0013A200…' 文字
    if isinstance(a, int):
        return bytes([(a >> (8 * (7 - i))) & 0xFF for i in range(8)])
    if isinstance(a, str):
        a = unhex(a)
    if len(a) != 8:
        raise ValueError('64 位元位址要 8 個位元組')
    return bytes(a)


def _cmd2(c):
    # AT 指令名稱 → 2 個 ASCII 位元組，例如 'NJ' → 4e 4a
    if isinstance(c, str):
        c = c.encode()
    if len(c) != 2:
        raise ValueError('AT 指令要剛好 2 個字元')
    return bytes(c)


def _u16(x):
    # 16 位元整數 → 2 位元組（大端序）
    return bytes([(x >> 8) & 0xFF, x & 0xFF])


def xb_at(fid, cmd, param=b''):
    # 0x08 AT 指令：訊框編號＋2 字元指令＋參數（不給參數就是「查詢」）
    return xb_frame(bytes([0x08, fid]) + _cmd2(cmd) + bytes(param))


def xb_at_resp(fid, cmd, status=0, data=b''):
    # 0x88 AT 指令回應：訊框編號＋指令＋狀態（0 成功）＋查到的值
    return xb_frame(bytes([0x88, fid]) + _cmd2(cmd) + bytes([status]) + bytes(data))


def xb_tx(fid, dst64, data, dst16=0xFFFE, radius=0, opts=0):
    # 0x10 傳送要求：64 位元目的位址＋16 位元目的位址（不知道就填 0xFFFE）＋廣播半徑＋選項＋資料
    return xb_frame(bytes([0x10, fid]) + _b64(dst64) + _u16(dst16) + bytes([radius, opts]) + bytes(data))


def xb_tx_status(fid, dst16, retries=0, delivery=0, discovery=0):
    # 0x8B 傳送狀態：16 位元目的位址＋重試次數＋遞送狀態（0 成功）＋探索狀態
    return xb_frame(bytes([0x8B, fid]) + _u16(dst16) + bytes([retries, delivery, discovery]))


def xb_rx(src64, src16, data, opts=0x01):
    # 0x90 收到封包：64 位元來源位址＋16 位元來源位址＋接收選項＋資料
    return xb_frame(bytes([0x90]) + _b64(src64) + _u16(src16) + bytes([opts]) + bytes(data))


def xb_io(src64, src16, dmask, amask, dsamples=0, analog=(), opts=0x01):
    # 0x92 I/O 取樣：數位遮罩 2 位元組、類比遮罩 1 位元組；有數位腳才帶數位樣本；每個類比腳帶 2 位元組樣本
    n = bin(amask).count('1')
    if len(analog) != n:
        raise ValueError('類比遮罩有 {} 個腳，樣本卻給了 {} 個'.format(n, len(analog)))
    d = bytes([0x92]) + _b64(src64) + _u16(src16) + bytes([opts, 1]) + _u16(dmask) + bytes([amask])
    if dmask:
        d += _u16(dsamples)
    for v in analog:
        d += _u16(v)
    return xb_frame(d)


def xb_remote_at(fid, dst64, cmd, param=b'', dst16=0xFFFE, opts=0x02):
    # 0x17 遠端 AT 指令：目的位址＋選項（0x02＝馬上套用）＋指令＋參數
    return xb_frame(bytes([0x17, fid]) + _b64(dst64) + _u16(dst16) + bytes([opts]) + _cmd2(cmd) + bytes(param))


def xb_remote_resp(fid, src64, src16, cmd, status=0, data=b''):
    # 0x97 遠端 AT 回應：來源位址＋指令＋狀態＋值
    return xb_frame(bytes([0x97, fid]) + _b64(src64) + _u16(src16) + _cmd2(cmd) + bytes([status]) + bytes(data))


def xb_modem(status):
    # 0x8A 模組狀態：例如 0x06 協調器已啟動、0x02 已入網
    return xb_frame(bytes([0x8A, status]))


_XB_MIN = {0x08: 3, 0x09: 3, 0x88: 4, 0x10: 13, 0x8B: 6, 0x90: 11, 0x92: 15, 0x17: 14, 0x97: 14, 0x8A: 1}


def parse_xbee(f):
    # 拆解 XBee API 訊框（API 模式 1；模式 2 跳脫過的先用 xb_unescape 還原）→ dict
    f = bytes(f)
    d = _new('xbee', len(f))
    if len(f) < 5 or f[0] != 0x7E:
        d['err'].append('XBee API 訊框要用 0x7E 開頭，至少 5 個位元組')
        return d
    n = (f[1] << 8) | f[2]
    d['length'] = n
    if len(f) != n + 4:
        d['err'].append('長度欄位寫 {} 位元組，實際的訊框資料有 {} 位元組'.format(n, len(f) - 4))
        if len(f) < n + 4:
            return d
    data = f[3:3 + n]
    d['fdata'] = data
    d['cksum'] = f[3 + n]
    d['sum'] = sum(data)
    d['cksum_calc'] = xb_checksum(data)
    d['chk'].append(('XBee 檢查碼', d['cksum'] == d['cksum_calc'], '0x{:02x}'.format(d['cksum_calc'])))
    if n == 0:
        d['err'].append('訊框資料是空的')
        return d
    t = data[0]
    p = data[1:]
    d['api'] = t
    if t in _XB_MIN and len(p) < _XB_MIN[t]:
        d['err'].append('這種訊框的資料至少要 {} 位元組，只有 {}'.format(_XB_MIN[t] + 1, n))
        return d
    if t in (0x08, 0x09):
        d['fid'] = p[0]
        d['cmd'] = p[1:3]
        d['param'] = p[3:]
    elif t == 0x88:
        d['fid'] = p[0]
        d['cmd'] = p[1:3]
        d['status'] = p[3]
        d['value'] = p[4:]
    elif t == 0x10:
        d['fid'] = p[0]
        d['dst64'] = p[1:9]
        d['dst16'] = (p[9] << 8) | p[10]
        d['radius'] = p[11]
        d['opts'] = p[12]
        d['data'] = p[13:]
    elif t == 0x8B:
        d['fid'] = p[0]
        d['dst16'] = (p[1] << 8) | p[2]
        d['retries'] = p[3]
        d['delivery'] = p[4]
        d['discovery'] = p[5]
    elif t == 0x90:
        d['src64'] = p[0:8]
        d['src16'] = (p[8] << 8) | p[9]
        d['opts'] = p[10]
        d['data'] = p[11:]
    elif t == 0x92:
        d['src64'] = p[0:8]
        d['src16'] = (p[8] << 8) | p[9]
        d['opts'] = p[10]
        d['nsamp'] = p[11]
        d['dmask'] = (p[12] << 8) | p[13]
        d['amask'] = p[14]
        q = 15
        if d['dmask']:
            if len(p) < q + 2:
                d['err'].append('少了數位樣本')
                return d
            d['dsamples'] = (p[q] << 8) | p[q + 1]
            q += 2
        d['analog'] = []
        for bit in range(8):
            if d['amask'] & (1 << bit):
                if len(p) < q + 2:
                    d['err'].append('少了類比樣本 AD{}'.format(bit))
                    return d
                d['analog'].append((bit, (p[q] << 8) | p[q + 1]))
                q += 2
        if len(p) > q:
            d['note'].append('後面還有 {} 位元組沒用到'.format(len(p) - q))
    elif t == 0x17:
        d['fid'] = p[0]
        d['dst64'] = p[1:9]
        d['dst16'] = (p[9] << 8) | p[10]
        d['opts'] = p[11]
        d['cmd'] = p[12:14]
        d['param'] = p[14:]
    elif t == 0x97:
        d['fid'] = p[0]
        d['src64'] = p[1:9]
        d['src16'] = (p[9] << 8) | p[10]
        d['cmd'] = p[11:13]
        d['status'] = p[13]
        d['value'] = p[14:]
    elif t == 0x8A:
        d['status'] = p[0]
    else:
        d['note'].append('這種訊框類型本工具只印原始位元組')
        d['raw'] = p
    return d


# ============================================================
# 4. IPv6、UDP、ICMPv6 與 checksum
# ============================================================

NH_HOPOPT = 0
NH_UDP = 17
NH_ICMPV6 = 58
LL_PREFIX = b'\xfe\x80\x00\x00\x00\x00\x00\x00'        # fe80::/64
IID_SHORT = b'\x00\x00\x00\xff\xfe\x00'                # 短位址的 IID 前 6 位元組 0000:00ff:fe00（RFC 6282）


def ip6(s):
    # IPv6 位址文字（例如 'fe80::1'）→ 16 位元組；本來就是 16 位元組就原樣回傳
    if isinstance(s, (bytes, bytearray)):
        if len(s) != 16:
            raise ValueError('IPv6 位址要 16 位元組')
        return bytes(s)
    s = s.strip().lower()
    if '/' in s:
        s = s.split('/')[0]
    if '::' in s:
        a, b = s.split('::', 1)
        ha = a.split(':') if a else []
        hb = b.split(':') if b else []
        n = 8 - len(ha) - len(hb)
        if n < 1:
            raise ValueError('IPv6 位址寫錯：' + s)
        groups = ha + ['0'] * n + hb
    else:
        groups = s.split(':')
    if len(groups) != 8:
        raise ValueError('IPv6 位址要有 8 段：' + s)
    out = bytearray()
    for g in groups:
        if not 1 <= len(g) <= 4:
            raise ValueError('IPv6 位址每段 1～4 個十六進位字：' + s)
        v = int(g, 16)
        out.append(v >> 8)
        out.append(v & 0xFF)
    return bytes(out)


def ip6str(b):
    # 16 位元組 → IPv6 位址文字（RFC 5952：小寫、最長的一串 0 縮成 ::、只有一段 0 不縮）
    b = bytes(b)
    g = [(b[2 * i] << 8) | b[2 * i + 1] for i in range(8)]
    best, bl = -1, 0
    i = 0
    while i < 8:
        if g[i] == 0:
            j = i
            while j < 8 and g[j] == 0:
                j += 1
            if j - i > bl:
                best, bl = i, j - i
            i = j
        else:
            i += 1
    if bl < 2:
        return ':'.join('{:x}'.format(x) for x in g)
    left = ':'.join('{:x}'.format(x) for x in g[:best])
    right = ':'.join('{:x}'.format(x) for x in g[best + bl:])
    return left + '::' + right


def eui64(mac):
    # 48 位元 MAC（Wi-Fi）→ 64 位元 EUI-64：中間插入 FF FE；本來就是 8 位元組就原樣回傳
    if isinstance(mac, str):
        mac = unhex(mac)
    mac = bytes(mac)
    if len(mac) == 8:
        return mac
    if len(mac) != 6:
        raise ValueError('MAC 位址要 6 或 8 個位元組')
    return mac[:3] + b'\xff\xfe' + mac[3:]


def iid(addr):
    # 802.15.4 位址 → IPv6 介面識別碼 IID（8 位元組）：長位址翻轉 U/L 位元（第一個位元組 XOR 0x02）；短位址 0000:00ff:fe00:XXXX
    addr = _addr(addr)
    if isinstance(addr, int):
        return IID_SHORT + _u16(addr)
    return bytes([addr[0] ^ 0x02]) + addr[1:]


def link_local(addr):
    # 802.15.4 位址（或 Wi-Fi MAC）→ link-local 位址 fe80::IID（16 位元組；要文字就用 ip6str）
    return LL_PREFIX + iid(addr)


def ipv6(src, dst, nh, payload, hlim=64, tc=0, flow=0):
    # 組 IPv6 封包：40 位元組標頭（版本 6、流量類別、流標籤、酬載長度、下一個標頭、跳數上限、來源、目的）＋酬載
    payload = bytes(payload)
    n = len(payload)
    h = bytes([0x60 | (tc >> 4), ((tc & 0x0F) << 4) | ((flow >> 16) & 0x0F), (flow >> 8) & 0xFF, flow & 0xFF,
               n >> 8, n & 0xFF, nh, hlim])
    return h + ip6(src) + ip6(dst) + payload


def _sum16(data, s=0):
    # 每 2 個位元組當成一個 16 位元數字加起來（奇數長度最後補 0）
    n = len(data)
    for i in range(0, n - 1, 2):
        s += (data[i] << 8) | data[i + 1]
    if n & 1:
        s += data[n - 1] << 8
    return s


def cksum6(src, dst, nh, upper):
    # UDP／ICMPv6 checksum：IPv6 偽標頭（來源、目的、上層長度、下一個標頭）＋上層資料，1 的補數加總後取補數
    s = _sum16(ip6(src))
    s = _sum16(ip6(dst), s)
    n = len(upper)
    s += (n >> 16) + (n & 0xFFFF) + nh
    s = _sum16(upper, s)
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF


def udp(src, dst, sport, dport, data):
    # 組 UDP 區段：8 位元組標頭（來源埠、目的埠、長度、checksum）＋資料；checksum 用 IPv6 偽標頭算好填進去
    data = bytes(data)
    n = 8 + len(data)
    seg = _u16(sport) + _u16(dport) + _u16(n) + b'\x00\x00' + data
    c = cksum6(src, dst, NH_UDP, seg)
    if c == 0:
        c = 0xFFFF
    return seg[:6] + _u16(c) + seg[8:]


def icmpv6(src, dst, typ, code, body):
    # 組 ICMPv6 訊息：類型＋代碼＋checksum＋內容（checksum 一樣要用 IPv6 偽標頭算）
    msg = bytes([typ, code, 0, 0]) + bytes(body)
    c = cksum6(src, dst, NH_ICMPV6, msg)
    return msg[:2] + _u16(c) + msg[4:]


def ipv6_udp(src, dst, sport, dport, data, hlim=64, tc=0, flow=0):
    # 一次組好「IPv6＋UDP＋資料」整個封包
    return ipv6(src, dst, NH_UDP, udp(src, dst, sport, dport, data), hlim, tc, flow)


def ipv6_icmp(src, dst, typ, code, body, hlim=64, tc=0, flow=0):
    # 一次組好「IPv6＋ICMPv6」整個封包（RPL 訊息就是 typ＝155）
    return ipv6(src, dst, NH_ICMPV6, icmpv6(src, dst, typ, code, body), hlim, tc, flow)


def _fill_udp_cksum(pkt):
    # 6LoWPAN 省略了 UDP checksum 時，接收端自己把它算回來填進去
    seg = pkt[40:48 - 2] + b'\x00\x00' + pkt[48:]
    c = cksum6(pkt[8:24], pkt[24:40], NH_UDP, seg)
    if c == 0:
        c = 0xFFFF
    return pkt[:46] + _u16(c) + pkt[48:]


def parse_ipv6(pkt, src_how=None, dst_how=None, partial=False, udp_elided=False):
    # 拆解 IPv6 封包 → dict，再接著拆 UDP／ICMPv6（會驗 checksum）；partial＝True 表示只有前半段（分片還沒到齊）
    pkt = bytes(pkt)
    d = _new('ipv6', len(pkt))
    if len(pkt) < 40:
        d['err'].append('IPv6 標頭要 40 位元組，只有 {}'.format(len(pkt)))
        return d
    d['ver'] = pkt[0] >> 4
    d['tc'] = ((pkt[0] & 0x0F) << 4) | (pkt[1] >> 4)
    d['flow'] = ((pkt[1] & 0x0F) << 16) | (pkt[2] << 8) | pkt[3]
    d['plen'] = (pkt[4] << 8) | pkt[5]
    d['nh'] = pkt[6]
    d['hlim'] = pkt[7]
    d['src'] = pkt[8:24]
    d['dst'] = pkt[24:40]
    d['src_how'] = src_how
    d['dst_how'] = dst_how
    if d['ver'] != 6:
        d['err'].append('版本欄位是 {}，IPv6 要是 6'.format(d['ver']))
        return d
    pay = pkt[40:]
    d['partial'] = partial
    if partial:
        d['note'].append('這只是第一片：IPv6 標頭已經還原，要等其他片段到齊才能驗長度與 checksum')
        return d
    if d['plen'] != len(pay):
        d['err'].append('酬載長度欄位寫 {}，實際有 {} 位元組'.format(d['plen'], len(pay)))
        pay = pay[:d['plen']]
    if d['nh'] == NH_UDP:
        d['next'] = parse_udp(d['src'], d['dst'], pay, udp_elided)
    elif d['nh'] == NH_ICMPV6:
        d['next'] = parse_icmpv6(d['src'], d['dst'], pay)
    else:
        d['note'].append('下一個標頭 {}：本工具不再往上解'.format(d['nh']))
    return d


def parse_udp(src, dst, seg, elided=False):
    # 拆解 UDP 區段並驗 checksum（用 IPv6 偽標頭）
    seg = bytes(seg)
    d = _new('udp', len(seg))
    if len(seg) < 8:
        d['err'].append('UDP 標頭要 8 位元組，只有 {}'.format(len(seg)))
        return d
    d['sport'] = (seg[0] << 8) | seg[1]
    d['dport'] = (seg[2] << 8) | seg[3]
    d['ulen'] = (seg[4] << 8) | seg[5]
    d['cksum'] = (seg[6] << 8) | seg[7]
    d['data'] = seg[8:]
    if d['ulen'] != len(seg):
        d['err'].append('UDP 長度欄位寫 {}，實際有 {} 位元組'.format(d['ulen'], len(seg)))
    c = cksum6(src, dst, NH_UDP, seg[:6] + b'\x00\x00' + seg[8:])
    if c == 0:
        c = 0xFFFF
    d['cksum_calc'] = c
    if elided:
        d['note'].append('6LoWPAN 把 UDP checksum 省略了（NHC 的 C＝1），這個值是接收端自己算回來的')
    elif d['cksum'] == 0:
        d['err'].append('IPv6 上的 UDP checksum 不能是 0（RFC 8200）')
    else:
        d['chk'].append(('UDP checksum', d['cksum'] == c, '0x{:04x}'.format(c)))
    return d


def parse_icmpv6(src, dst, msg):
    # 拆解 ICMPv6 訊息並驗 checksum；類型 155 再交給 parse_rpl
    msg = bytes(msg)
    d = _new('icmpv6', len(msg))
    if len(msg) < 4:
        d['err'].append('ICMPv6 至少要 4 位元組')
        return d
    d['type'] = msg[0]
    d['code'] = msg[1]
    d['cksum'] = (msg[2] << 8) | msg[3]
    d['cksum_calc'] = cksum6(src, dst, NH_ICMPV6, msg[:2] + b'\x00\x00' + msg[4:])
    d['chk'].append(('ICMPv6 checksum', d['cksum'] == d['cksum_calc'], '0x{:04x}'.format(d['cksum_calc'])))
    d['body'] = msg[4:]
    if d['type'] == 155:
        d['next'] = parse_rpl(d['code'], d['body'])
    return d


# ============================================================
# 5. 6LoWPAN（RFC 4944、RFC 6282）
# ============================================================

def _ctx(ctx):
    # 把 context 表整理成 {編號: 8 位元組前綴}；可以寫 {0: '2001:db8:1::/64'}（本函式庫只用 /64）
    if not ctx:
        return {}
    out = {}
    for k in ctx:
        v = ctx[k]
        if isinstance(v, str):
            v = ip6(v)
        out[k] = bytes(v)[:8]
    return out


def _comp_addr(a, mac, ctx, is_src):
    # 單播位址怎麼壓（RFC 6282 3.1.1）：回傳 (AC, AM, 要帶著的位元組, context 編號)
    if a == bytes(16):
        if is_src:
            return 1, 0, b'', 0              # SAC＝1、SAM＝00：未指定位址 ::
        return 0, 0, a, 0
    if a[:8] == LL_PREFIX:
        ac, ci = 0, 0
    else:
        ci = None
        for k in sorted(ctx):
            if ctx[k] == a[:8]:
                ci = k
                break
        if ci is None:
            return 0, 0, a, 0                # 沒有對應的 context：128 位元全部帶著
        ac = 1
    i = a[8:]
    if mac is not None and i == iid(mac):
        return ac, 3, b'', ci                # IID 可以由 MAC 位址推得：完全省略
    if i[:6] == IID_SHORT:
        return ac, 2, i[6:], ci              # 0000:00ff:fe00:XXXX：只帶 16 位元
    return ac, 1, i, ci                      # 帶整個 64 位元 IID


def _comp_mcast(a):
    # 群播位址怎麼壓（M＝1、DAC＝0）：回傳 (DAM, 要帶著的位元組)
    if a[1] == 0x02 and a[2:15] == bytes(13):
        return 3, a[15:]                     # ff02::00XX → 帶 8 位元
    if a[2:13] == bytes(11):
        return 2, a[1:2] + a[13:]            # ffXX::00XX:XXXX → 帶 32 位元
    if a[2:11] == bytes(9):
        return 1, a[1:2] + a[11:]            # ffXX::00XX:XXXX:XXXX → 帶 48 位元
    return 0, a


def _nhc_udp(h, elide=False):
    # NHC-UDP（RFC 6282 4.3.3）：11110CPP；長度一定省略，埠號落在 0xF0Bx／0xF0xx 就能縮短
    sp = (h[0] << 8) | h[1]
    dp = (h[2] << 8) | h[3]
    if (sp & 0xFFF0) == 0xF0B0 and (dp & 0xFFF0) == 0xF0B0:
        p, ports = 3, bytes([((sp & 15) << 4) | (dp & 15)])
    elif (dp & 0xFF00) == 0xF000:
        p, ports = 1, _u16(sp) + bytes([dp & 0xFF])
    elif (sp & 0xFF00) == 0xF000:
        p, ports = 2, bytes([sp & 0xFF]) + _u16(dp)
    else:
        p, ports = 0, _u16(sp) + _u16(dp)
    c = 1 if elide else 0
    return bytes([0xF0 | (c << 2) | p]) + ports + (b'' if c else bytes(h[6:8]))


def _iphc(pkt, ms, md, ctx=None, nhc=True, elide=False):
    # IPHC 壓縮的核心（RFC 6282）：回傳（壓縮後的標頭, 它代表的未壓縮長度 40 或 48）
    ctx = _ctx(ctx)
    tc = ((pkt[0] & 0x0F) << 4) | (pkt[1] >> 4)
    fl = ((pkt[1] & 0x0F) << 16) | (pkt[2] << 8) | pkt[3]
    nh, hl = pkt[6], pkt[7]
    src, dst = pkt[8:24], pkt[24:40]
    inl = bytearray()
    ecn, dscp = tc & 3, tc >> 2
    if tc == 0 and fl == 0:                  # TF＝11：流量類別、流標籤都省略
        tf = 3
    elif fl == 0:                            # TF＝10：只帶 ECN＋DSCP（1 位元組）
        tf = 2
        inl.append((ecn << 6) | dscp)
    elif dscp == 0:                          # TF＝01：帶 ECN＋流標籤（3 位元組）
        tf = 1
        inl.extend(bytes([(ecn << 6) | (fl >> 16), (fl >> 8) & 0xFF, fl & 0xFF]))
    else:                                    # TF＝00：全部帶著（4 位元組）
        tf = 0
        inl.extend(bytes([(ecn << 6) | dscp, fl >> 16, (fl >> 8) & 0xFF, fl & 0xFF]))
    use_nhc = (nhc and nh == NH_UDP and len(pkt) >= 48
               and ((pkt[44] << 8) | pkt[45]) == len(pkt) - 40)
    if not use_nhc:
        inl.append(nh)                       # NH＝0：下一個標頭直接帶著
    hcode = {1: 1, 64: 2, 255: 3}.get(hl, 0)
    if hcode == 0:
        inl.append(hl)                       # HLIM＝00：跳數上限直接帶著
    sac, sam, sinl, sci = _comp_addr(src, ms, ctx, True)
    if dst[0] == 0xFF:
        m, dac, dci = 1, 0, 0
        dam, dinl = _comp_mcast(dst)
        if dam == 0 and dst[2] == 0 and dst[3] == 64:      # 以單播前綴為基礎的群播（RFC 3306）：前綴在 context 裡就壓成 48 位元
            for k in sorted(ctx):
                if ctx[k] == dst[4:12]:
                    dac, dci, dinl = 1, k, dst[1:3] + dst[12:16]
                    break
    else:
        m = 0
        dac, dam, dinl, dci = _comp_addr(dst, md, ctx, False)
    inl.extend(sinl)
    inl.extend(dinl)
    cid = 1 if (sci or dci) else 0
    b0 = 0x60 | (tf << 3) | (int(use_nhc) << 2) | hcode
    b1 = (cid << 7) | (sac << 6) | (sam << 4) | (m << 3) | (dac << 2) | dam
    out = bytes([b0, b1]) + (bytes([(sci << 4) | dci]) if cid else b'') + bytes(inl)
    if use_nhc:
        return out + _nhc_udp(pkt[40:48], elide), 48
    return out, 40


def _unc_addr(r, ac, am, mac, ctx, ci, log, warn, is_src):
    # 還原單播位址（SAC/SAM 或 DAC/DAM）：回傳 (16 位元組, 「這個位址怎麼來的」說明)
    who = '來源' if is_src else '目的'
    if ac == 0:
        if am == 0:
            return r.take(16, who + '位址（128 位元）', log), '128 位元整個直接帶著'
        pre, how = LL_PREFIX, '前綴 fe80::/64（link-local）'
    else:
        if am == 0:
            if is_src:
                return bytes(16), 'SAC＝1、SAM＝00：未指定位址 ::'
            raise ValueError('DAC＝1、DAM＝00 是保留值')
        if ci in ctx:
            pre, how = ctx[ci], '前綴來自 context {}'.format(ci)
        else:
            pre, how = bytes(8), 'context {} 沒設定，前綴先當成 0'.format(ci)
            warn.append('context {} 沒設定：請在 ctx 填前綴，例如 {{{}: \'2001:db8:1::/64\'}}'.format(ci, ci))
    if am == 1:
        i = r.take(8, who + '位址的 IID（64 位元）', log)
        how += '＋IID 直接帶著（64 位元）'
    elif am == 2:
        s = r.take(2, who + '位址（16 位元）', log)
        i = IID_SHORT + s
        how += '＋IID 0000:00ff:fe00:{}（帶 16 位元）'.format(hexs(s, ''))
    else:
        if mac is None:
            raise ValueError(who + '位址完全省略，但沒有 802.15.4 位址可以推')
        i = iid(mac)
        how += '＋IID 由 802.15.4 {}位址 {} 推得'.format(who, addr_str(mac))
    return pre + i, how


def _unc_mcast(r, dac, dam, ctx, ci, log, warn):
    # 還原群播目的位址（M＝1）：回傳 (16 位元組, 說明)
    if dac == 0:
        if dam == 0:
            return r.take(16, '目的群播位址（128 位元）', log), '128 位元整個直接帶著'
        if dam == 1:
            v = r.take(6, '目的群播位址（48 位元）', log)
            return b'\xff' + v[:1] + bytes(9) + v[1:], '群播 ffXX::00XX:XXXX:XXXX（帶 48 位元）'
        if dam == 2:
            v = r.take(4, '目的群播位址（32 位元）', log)
            return b'\xff' + v[:1] + bytes(11) + v[1:], '群播 ffXX::00XX:XXXX（帶 32 位元）'
        v = r.take(1, '目的群播位址（8 位元）', log)
        return b'\xff\x02' + bytes(13) + v, '群播 ff02::00XX（帶 8 位元）'
    if dam != 0:
        raise ValueError('M＝1、DAC＝1 時 DAM 只能是 00（其他是保留值）')
    v = r.take(6, '目的群播位址（48 位元）', log)
    pre = ctx.get(ci)
    if pre is None:
        pre = bytes(8)
        warn.append('context {} 沒設定，群播前綴先當成 0'.format(ci))
    return b'\xff' + v[0:2] + bytes([64]) + pre + v[2:6], '以單播前綴為基礎的群播（前綴來自 context {}）'.format(ci)


def _iphc_unc(data, ms, md, ctx=None, size=None):
    # IPHC 解壓縮的核心：回傳 (說明 dict, 未壓縮的 IPv6〔＋UDP〕標頭, 用掉的壓縮位元組數, UDP checksum 是否省略)
    ctx = _ctx(ctx)
    data = bytes(data)
    r = _R(data)
    v = r.take(2, 'IPHC')
    b0, b1 = v[0], v[1]
    if b0 >> 5 != 3:
        raise ValueError('IPHC 的前 3 個位元要是 011')
    log = []
    warn = []
    info = {'kind': 'iphc', 'iphc': (b0 << 8) | b1, 'tf': (b0 >> 3) & 3, 'nh': (b0 >> 2) & 1,
            'hlim': b0 & 3, 'cid': b1 >> 7, 'sac': (b1 >> 6) & 1, 'sam': (b1 >> 4) & 3,
            'm': (b1 >> 3) & 1, 'dac': (b1 >> 2) & 1, 'dam': b1 & 3, 'inline': log, 'warn': warn}
    sci = dci = 0
    if info['cid']:
        c = r.take(1, 'CID（來源｜目的 context 編號）', log)[0]
        sci, dci = c >> 4, c & 15
    info['sci'] = sci
    info['dci'] = dci
    tf = info['tf']
    if tf == 0:
        v = r.take(4, 'TF（ECN＋DSCP＋流標籤）', log)
        ecn, dscp, fl = v[0] >> 6, v[0] & 0x3F, ((v[1] & 0x0F) << 16) | (v[2] << 8) | v[3]
    elif tf == 1:
        v = r.take(3, 'TF（ECN＋流標籤）', log)
        ecn, dscp, fl = v[0] >> 6, 0, ((v[0] & 0x0F) << 16) | (v[1] << 8) | v[2]
    elif tf == 2:
        v = r.take(1, 'TF（ECN＋DSCP）', log)
        ecn, dscp, fl = v[0] >> 6, v[0] & 0x3F, 0
    else:
        ecn, dscp, fl = 0, 0, 0
    tc = (dscp << 2) | ecn
    nh = None
    if not info['nh']:
        nh = r.take(1, '下一個標頭 Next Header', log)[0]
    if info['hlim'] == 0:
        hl = r.take(1, '跳數上限 Hop Limit', log)[0]
    else:
        hl = (0, 1, 64, 255)[info['hlim']]
    src, info['src_how'] = _unc_addr(r, info['sac'], info['sam'], ms, ctx, sci, log, warn, True)
    if info['m']:
        dst, info['dst_how'] = _unc_mcast(r, info['dac'], info['dam'], ctx, dci, log, warn)
    else:
        dst, info['dst_how'] = _unc_addr(r, info['dac'], info['dam'], md, ctx, dci, log, warn, False)
    info['iphc_len'] = r.p
    elided = False
    if info['nh']:
        nb = r.take(1, 'NHC')[0]
        if (nb & 0xF8) != 0xF0:
            raise ValueError('NHC 0x{:02x}：本工具只支援 NHC-UDP（11110xxx）'.format(nb))
        c, pp = (nb >> 2) & 1, nb & 3
        plog = []
        if pp == 0:
            v = r.take(4, '來源埠＋目的埠（各 16 位元）', plog)
            sp, dp = (v[0] << 8) | v[1], (v[2] << 8) | v[3]
        elif pp == 1:
            v = r.take(3, '來源埠 16 位元＋目的埠低 8 位元', plog)
            sp, dp = (v[0] << 8) | v[1], 0xF000 | v[2]
        elif pp == 2:
            v = r.take(3, '來源埠低 8 位元＋目的埠 16 位元', plog)
            sp, dp = 0xF000 | v[0], (v[1] << 8) | v[2]
        else:
            v = r.take(1, '來源埠｜目的埠（各 4 位元）', plog)
            sp, dp = 0xF0B0 | (v[0] >> 4), 0xF0B0 | (v[0] & 15)
        if c:
            ck = 0
            elided = True
        else:
            ck_b = r.take(2, 'UDP checksum', plog)
            ck = (ck_b[0] << 8) | ck_b[1]
        nh = NH_UDP
        info['nhc'] = {'byte': nb, 'c': c, 'p': pp, 'sport': sp, 'dport': dp, 'inline': plog}
    consumed = r.p
    unc = 48 if info['nh'] else 40
    if size is None:
        size = unc + len(data) - consumed
    plen = size - 40
    hdr = ipv6(src, dst, nh, b'', hl, tc, fl)
    hdr = hdr[:4] + _u16(plen) + hdr[6:]
    if info['nh']:
        hdr += _u16(sp) + _u16(dp) + _u16(plen) + _u16(ck)
    info['comp_len'] = consumed
    info['unc_len'] = unc
    return info, hdr, consumed, elided


def iphc_compress(pkt, mac_src, mac_dst, ctx=None, nhc=True, elide_cksum=False):
    # 把完整 IPv6 封包壓成 IPHC 格式（RFC 6282）：能由 MAC 位址推得的 IID 就省略；UDP 用 NHC 壓
    pkt = bytes(pkt)
    h, used = _iphc(pkt, _addr(mac_src), _addr(mac_dst), ctx, nhc, elide_cksum)
    return h + pkt[used:]


def iphc_decompress(data, mac_src, mac_dst, ctx=None):
    # 把 IPHC 壓縮過的 6LoWPAN 酬載還原成完整 IPv6 封包
    data = bytes(data)
    info, hdr, n, elided = _iphc_unc(data, _addr(mac_src), _addr(mac_dst), ctx)
    pkt = hdr + data[n:]
    return _fill_udp_cksum(pkt) if elided else pkt


def _head(data, ms, md, ctx, size):
    # 未分片或 FRAG1 的內容開頭：0x41 未壓縮 IPv6 或 IPHC；回傳 (說明, 未壓縮標頭, 用掉的位元組, checksum 省略?)
    if data and data[0] == 0x41:
        return {'kind': 'ipv6'}, b'', 1, False
    if data and (data[0] >> 5) == 3:
        return _iphc_unc(data, ms, md, ctx, size)
    raise ValueError('FRAG1 後面要接 0x41（未壓縮 IPv6）或 IPHC')


def mesh_hdr(orig, final, hops=14):
    # Mesh 標頭（RFC 4944 5.2）：10 V F 剩餘跳數(4 位元)＋原始來源＋最終目的；V／F＝1 表示該位址是 16 位元短位址
    # 剩餘跳數 15 以上：4 位元填 0xF，後面多 1 位元組 Deep Hops Left
    orig, final = _addr(orig), _addr(final)
    if not 0 <= hops <= 255:
        raise ValueError('剩餘跳數用 0～255')
    v = 1 if isinstance(orig, int) else 0
    f = 1 if isinstance(final, int) else 0

    def a(x):
        # Mesh 標頭裡的位址用大端序：短位址 2 位元組、長位址 8 位元組照原順序
        return _u16(x) if isinstance(x, int) else x
    if hops < 15:
        h = bytes([0x80 | (v << 5) | (f << 4) | hops])
    else:
        h = bytes([0x80 | (v << 5) | (f << 4) | 0x0F, hops])
    return h + a(orig) + a(final)


def lowpan_frag(comp_hdr, used, pkt, tag, room):
    # 把 IPv6 封包切成 FRAG1／FRAGN（RFC 4944 5.3）。comp_hdr：壓縮後的標頭；used：它代表的未壓縮位元組數；room：每個訊框可用的空間
    pkt = bytes(pkt)
    size = len(pkt)
    rest = pkt[used:]
    if len(comp_hdr) + len(rest) <= room:
        return [comp_hdr + rest]                         # 放得下，不用切
    if size > 2047:
        raise ValueError('datagram_size 只有 11 位元，最大 2047')
    k = ((room - 4 - len(comp_hdr) + used) // 8) * 8 - used
    if k <= 0:
        raise ValueError('空間太小，第一片放不下壓縮後的標頭')
    out = [_u16(0xC000 | size) + _u16(tag) + comp_hdr + rest[:k]]
    off = used + k                                       # 未壓縮封包裡的位置，一定是 8 的倍數
    step = ((room - 5) // 8) * 8
    while off < size:
        n = min(step, size - off)
        out.append(_u16(0xE000 | size) + _u16(tag) + bytes([off // 8]) + pkt[off:off + n])
        off += n
    return out


def frames_ipv6(seq, pan, mac_src, mac_dst, pkt, compress=True, ctx=None, nhc=True, elide_cksum=False,
                tag=0, ar=False, fcs=True, mesh=None):
    # IPv6 封包 → 要送出去的 802.15.4 訊框清單：壓縮（或 0x41 不壓）→ 太大就分片 → 加 MAC 標頭（與 FCS）；序號從 seq 起每片加 1
    ms, md = _addr(mac_src), _addr(mac_dst)
    pkt = bytes(pkt)
    if mesh:
        mo, mf = _addr(mesh[0]), _addr(mesh[1])
        mh = mesh_hdr(mo, mf, mesh[2] if len(mesh) > 2 else 14)
    else:
        mo, mf, mh = ms, md, b''
    if compress:
        ch, used = _iphc(pkt, mo, mf, ctx, nhc, elide_cksum)
    else:
        ch, used = b'\x41', 0
    room = MAX_FRAME - 2 - len(mac_frame(FT_DATA, 0, pan, md, ms, b'', fcs=False)) - len(mh)
    parts = lowpan_frag(ch, used, pkt, tag, room)
    return [mac_data((seq + i) & 0xFF, pan, md, ms, mh + p, ar, fcs=fcs) for i, p in enumerate(parts)]


class Reassembler:
    # 6LoWPAN 分片重組（RFC 4944 5.3）：依（來源、目的、datagram_size、datagram_tag）開緩衝；亂序、重複、重疊、逾時都會處理
    def __init__(self, timeout_ms=60000, max_bufs=4):
        # timeout_ms：多久沒拼完就丟（RFC 4944 最長 60 秒，上課示範可以用 5000）；max_bufs：最多同時拼幾包（省記憶體）
        self.timeout = timeout_ms
        self.max = max_bufs
        self.bufs = {}
        self.note = ''
        self.elided = False
        self.info = None
        self.stats = {'done': 0, 'dup': 0, 'overlap': 0, 'timeout': 0, 'dropped': 0, 'bad': 0}

    def expire(self, now=None):
        # 丟掉逾時還沒拼完的緩衝，回傳丟了幾個
        t = now_ms() if now is None else now
        old = [k for k in self.bufs if ms_since(self.bufs[k][0], t) > self.timeout]
        for k in old:
            del self.bufs[k]
        self.stats['timeout'] += len(old)
        return len(old)

    def add(self, frag, mac_src, mac_dst, ctx=None, now=None):
        # 收一片（從 FRAG 標頭開始的位元組）：拼完回傳整個 IPv6 封包，還沒拼完回傳 None；self.note 說明發生什麼事
        t = now_ms() if now is None else now
        msg = []
        n_old = self.expire(t)
        if n_old:
            msg.append('逾時丟掉 {} 個舊緩衝'.format(n_old))
        frag = bytes(frag)
        ms, md = _addr(mac_src), _addr(mac_dst)
        _need(frag, 4, '分片標頭')
        kind = frag[0] >> 3
        size = ((frag[0] & 7) << 8) | frag[1]
        tag = (frag[2] << 8) | frag[3]
        elided = False
        info = None
        if kind == 0x18:
            start = 0
            info, hdr, n, elided = _head(frag[4:], ms, md, ctx, size)
            piece = hdr + frag[4 + n:]
        elif kind == 0x1C:
            _need(frag, 5, 'FRAGN 標頭')
            start = frag[4] * 8
            piece = frag[5:]
        else:
            raise ValueError('不是分片標頭（FRAG1 是 11000、FRAGN 是 11100）')
        end = start + len(piece)
        if end > size:
            self.stats['bad'] += 1
            msg.append('這一片超出 datagram_size（{} > {}），丟掉'.format(end, size))
            self.note = '；'.join(msg)
            return None
        key = (ms, md, size, tag)
        e = self.bufs.get(key)
        if e is None:
            if len(self.bufs) >= self.max:
                k_old = None
                for k in self.bufs:
                    if k_old is None or ms_since(self.bufs[k][0], t) > ms_since(self.bufs[k_old][0], t):
                        k_old = k
                del self.bufs[k_old]
                self.stats['dropped'] += 1
                msg.append('緩衝滿了，丟掉最舊的一包')
            e = [t, bytearray(size), [], False, None]
            self.bufs[key] = e
            msg.append('開新的重組緩衝（size {}、tag 0x{:04x}）'.format(size, tag))
        else:
            for s, x in e[2]:
                if s == start and x == end:
                    self.stats['dup'] += 1
                    msg.append('重複的片段（位置 {}～{}），不理它'.format(start, end))
                    self.note = '；'.join(msg)
                    return None
                if start < x and s < end:
                    self.stats['overlap'] += 1
                    msg.append('片段重疊但位置不同：丟掉之前收的，從這一片重新開始')
                    e = [t, bytearray(size), [], False, None]
                    self.bufs[key] = e
                    break
        e[1][start:end] = piece
        e[2].append((start, end))
        if elided:
            e[3] = True
        if info is not None:
            e[4] = info
        got = 0
        for s, x in e[2]:
            got += x - s
        if got < size:
            msg.append('放進位置 {}～{}，已收 {}／{} 位元組'.format(start, end, got, size))
            self.note = '；'.join(msg)
            return None
        del self.bufs[key]
        pkt = bytes(e[1])
        self.elided = e[3]
        self.info = e[4]
        if e[3]:
            pkt = _fill_udp_cksum(pkt)
        self.stats['done'] += 1
        msg.append('放進位置 {}～{}，重組完成：{} 位元組（{} 片）'.format(start, end, size, len(e[2])))
        self.note = '；'.join(msg)
        return pkt


def _parse_mesh(data, p):
    # 拆 Mesh 標頭：回傳 (dict, 長度)
    b = data[p]
    v, f, hops = (b >> 5) & 1, (b >> 4) & 1, b & 15
    q = p + 1
    deep = hops == 15
    if deep:
        _need(data, q + 1, 'Mesh 標頭')
        hops = data[q]
        q += 1
    addrs = []
    for short in (v, f):
        n = 2 if short else 8
        _need(data, q + n, 'Mesh 標頭')
        a = data[q:q + n]
        addrs.append((a[0] << 8) | a[1] if short else bytes(a))
        q += n
    return {'kind': 'mesh', 'v': v, 'f': f, 'hops': hops, 'deep': deep,
            'orig': addrs[0], 'final': addrs[1]}, q - p


def is_lowpan(b):
    # 第一個位元組是不是有定義的 6LoWPAN 分派值（0x41 IPv6、0x42 HC1、0x50 BC0、011xxxxx IPHC、10xxxxxx Mesh、11000xxx FRAG1、11100xxx FRAGN）
    return b in (0x41, 0x42, 0x50) or (b >> 5) == 3 or (b >> 6) == 2 or (b >> 3) in (0x18, 0x1C)


def parse_lowpan(data, mac_src, mac_dst, ctx=None, reasm=None):
    # 拆 6LoWPAN（802.15.4 的酬載）：Mesh／BC0／FRAG 標頭 → IPHC 或未壓縮 IPv6 → 再往上拆 IPv6
    data = bytes(data)
    ms, md = _addr(mac_src), _addr(mac_dst)
    d = _new('lowpan', len(data))
    d['hdrs'] = []
    try:
        p = 0
        while p < len(data):
            b = data[p]
            if (b >> 6) == 2:
                h, n = _parse_mesh(data, p)
                d['hdrs'].append(h)
                ms, md = h['orig'], h['final']   # 有 Mesh 標頭時，IID 改由原始來源／最終目的推
                p += n
            elif b == 0x50:
                _need(data, p + 2, 'BC0 標頭')
                d['hdrs'].append({'kind': 'bc0', 'seq': data[p + 1]})
                p += 2
            else:
                break
        if p >= len(data):
            raise ValueError('只有標頭，後面沒有內容')
        b = data[p]
        if (b >> 3) in (0x18, 0x1C):
            fr = data[p:]
            first = (b >> 3) == 0x18
            _need(fr, 4 if first else 5, '分片標頭')
            h = {'kind': 'frag1' if first else 'fragn', 'size': ((b & 7) << 8) | fr[1],
                 'tag': (fr[2] << 8) | fr[3]}
            if not first:
                h['offset'] = fr[4]
            h['data_len'] = len(fr) - (4 if first else 5)
            d['hdrs'].append(h)
            info = None
            if first:
                info, hdr, n, el = _head(fr[4:], ms, md, ctx, h['size'])
                d['hdrs'].append(info)
            if reasm is not None:
                pkt = reasm.add(fr, ms, md, ctx)
                d['note'].append('重組：' + reasm.note)
                if pkt is not None:
                    d['reassembled'] = len(pkt)
                    ri = reasm.info if (reasm.info and reasm.info.get('kind') == 'iphc') else {}
                    d['next'] = parse_ipv6(pkt, ri.get('src_how'), ri.get('dst_how'), udp_elided=reasm.elided)
                elif info is not None and info.get('kind') == 'iphc':
                    d['next'] = parse_ipv6(hdr + fr[4 + n:], info['src_how'], info['dst_how'], partial=True)
            else:
                d['note'].append('沒有給 Reassembler，只解這一片')
                if info is not None and info.get('kind') == 'iphc':
                    d['next'] = parse_ipv6(hdr + fr[4 + n:], info['src_how'], info['dst_how'], partial=True)
        elif b == 0x41:
            d['hdrs'].append({'kind': 'ipv6'})
            d['next'] = parse_ipv6(data[p + 1:])
        elif (b >> 5) == 3:
            info, hdr, n, el = _iphc_unc(data[p:], ms, md, ctx)
            d['hdrs'].append(info)
            pkt = hdr + data[p + n:]
            if el:
                pkt = _fill_udp_cksum(pkt)
            d['next'] = parse_ipv6(pkt, info['src_how'], info['dst_how'], udp_elided=el)
        elif (b >> 6) == 0:
            d['hdrs'].append({'kind': 'nalp'})
            d['note'].append('分派值 00xxxxxx：這不是 6LoWPAN 封包（NALP）')
        elif b == 0x42:
            raise ValueError('分派值 0x42 是 HC1（RFC 4944），已被 RFC 6282 的 IPHC 取代，本工具不解')
        else:
            raise ValueError('分派值 0x{:02x} 是保留值'.format(b))
    except ValueError as ex:
        d['err'].append(str(ex))
    for h in d['hdrs']:
        for w in h.get('warn', ()):
            d['err'].append(w)
    return d


# ============================================================
# 6. RPL（RFC 6550）
# ============================================================

RPL_DIS = 0
RPL_DIO = 1
RPL_DAO = 2
RPL_DAO_ACK = 3
ALL_RPL_NODES = 'ff02::1a'          # 所有 RPL 節點的群播位址
INFINITE_RANK = 0xFFFF


def opt_pad(n):
    # 補位選項：n＝1 用 Pad1（00），n≥2 用 PadN（01＋長度＋0）
    if n == 1:
        return b'\x00'
    return bytes([1, n - 2]) + bytes(n - 2)


def opt_conf(doublings=20, imin=3, redundancy=10, max_rank_inc=1792, min_hop=256, ocp=0,
             def_lifetime=0xFF, lifetime_unit=60, auth=0, pcs=0):
    # DODAG 設定選項（類型 4、長度 14）：Trickle 三參數與 MinHopRankIncrease 用 RFC 6550 第 17 節預設、OCP 0＝OF0；
    # MaxRankIncrease 與兩個壽命欄位 RFC 沒有規定預設，這裡用常見的 7×256＝1792、0xFF、60 秒
    return (bytes([4, 14, (auth << 3) | pcs, doublings, imin, redundancy]) + _u16(max_rank_inc)
            + _u16(min_hop) + _u16(ocp) + bytes([0, def_lifetime]) + _u16(lifetime_unit))


def _u32(x):
    # 32 位元整數 → 4 位元組（大端序）
    return bytes([(x >> 24) & 0xFF, (x >> 16) & 0xFF, (x >> 8) & 0xFF, x & 0xFF])


def opt_prefix(prefix, plen=64, l=0, a=1, r=0, valid=2592000, preferred=604800):
    # 前綴資訊選項（類型 8、長度 30）：讓節點用這個前綴自己組全域位址（A＝1）；壽命預設用 RFC 4861 的 30 天／7 天
    return (bytes([8, 30, plen, (l << 7) | (a << 6) | (r << 5)]) + _u32(valid) + _u32(preferred)
            + bytes(4) + ip6(prefix))


def opt_target(prefix, plen=128, flags=0):
    # RPL 目標選項（類型 5）：DAO 裡說「我（或我後面）有這個位址／前綴」；前綴欄位補成 8／16 位元組（RFC 允許補 0，Wireshark 只認這兩種）
    n = 0 if plen == 0 else (8 if plen <= 64 else 16)
    return bytes([5, 2 + n, flags, plen]) + ip6(prefix)[:n]


def opt_transit(lifetime=0xFF, seq=0, control=0, e=0, parent=None):
    # 轉送資訊選項（類型 6）：路徑壽命（0xFF＝無限、0＝撤銷路由）；non-storing 模式要帶父節點位址
    body = bytes([e << 7, control, seq, lifetime]) + (ip6(parent) if parent else b'')
    return bytes([6, len(body)]) + body


def opt_solicited(instance=None, dodagid=None, version=None):
    # 請求資訊選項（類型 7、長度 19）：DIS 裡指定「只想聽這個 Instance／DODAG／版本的 DIO」
    flags = ((version is not None) << 7) | ((instance is not None) << 6) | ((dodagid is not None) << 5)
    return (bytes([7, 19, instance or 0, flags]) + (ip6(dodagid) if dodagid else bytes(16))
            + bytes([version or 0]))


def opt_route(prefix, plen, lifetime=0xFFFFFFFF, prf=0):
    # 路由資訊選項（類型 3）：DIO 裡宣告「經過我可以到這個前綴」；前綴欄位補成 0／8／16 位元組（RFC 4191 的寫法，Wireshark 也只認這三種）
    n = 0 if plen == 0 else (8 if plen <= 64 else 16)
    return bytes([3, 6 + n, plen, (prf & 3) << 3]) + _u32(lifetime) + ip6(prefix)[:n]


def rpl_dis(options=b'', flags=0):
    # DIS 內容：旗標＋保留（各 1 位元組）＋選項。新節點用它請鄰居快點送 DIO
    return bytes([flags, 0]) + bytes(options)


def rpl_dio(rank, dodagid, instance=0, version=240, g=1, mop=2, prf=0, dtsn=240, options=b''):
    # DIO 內容：InstanceID、版本、Rank、G|0|MOP|Prf、DTSN、旗標、保留、DODAGID（共 24 位元組）＋選項
    return (bytes([instance, version]) + _u16(rank) + bytes([(g << 7) | (mop << 3) | prf, dtsn, 0, 0])
            + ip6(dodagid) + bytes(options))


def rpl_dao(seq, instance=0, k=1, dodagid=None, options=b''):
    # DAO 內容：InstanceID、K|D|旗標、保留、DAOSequence（D＝1 再帶 DODAGID）＋選項（Target、Transit）
    dflag = 1 if dodagid else 0
    return (bytes([instance, (k << 7) | (dflag << 6), 0, seq & 0xFF]) + (ip6(dodagid) if dodagid else b'')
            + bytes(options))


def rpl_dao_ack(seq, instance=0, status=0, dodagid=None):
    # DAO-ACK 內容：InstanceID、D|保留、DAOSequence、狀態（0 接受、1～127 接受但建議換父、128 以上拒絕）
    dflag = 1 if dodagid else 0
    return bytes([instance, dflag << 7, seq & 0xFF, status]) + (ip6(dodagid) if dodagid else b'')


def _rpl_opts(b, p):
    # 拆 RPL 選項清單
    opts = []
    while p < len(b):
        t = b[p]
        if t == 0:
            opts.append({'type': 0, 'len': 0})
            p += 1
            continue
        _need(b, p + 2, '選項標頭')
        n = b[p + 1]
        _need(b, p + 2 + n, '選項 {} 的內容'.format(t))
        v = b[p + 2:p + 2 + n]
        o = {'type': t, 'len': n}
        if t == 3:
            _need(v, 6, '路由資訊選項')
            o['plen'], o['prf'] = v[0], (v[1] >> 3) & 3
            o['lifetime'] = (v[2] << 24) | (v[3] << 16) | (v[4] << 8) | v[5]
            o['prefix'] = (v[6:] + bytes(16))[:16]
        elif t == 4:
            _need(v, 14, 'DODAG 設定選項')
            o['auth'], o['pcs'] = (v[0] >> 3) & 1, v[0] & 7
            o['doublings'], o['imin'], o['redundancy'] = v[1], v[2], v[3]
            o['max_rank_inc'] = (v[4] << 8) | v[5]
            o['min_hop'] = (v[6] << 8) | v[7]
            o['ocp'] = (v[8] << 8) | v[9]
            o['def_lifetime'] = v[11]
            o['lifetime_unit'] = (v[12] << 8) | v[13]
        elif t == 5:
            _need(v, 2, 'RPL 目標選項')
            o['flags'], o['plen'] = v[0], v[1]
            o['prefix'] = (v[2:] + bytes(16))[:16]
        elif t == 6:
            _need(v, 4, '轉送資訊選項')
            o['e'], o['control'], o['pseq'], o['lifetime'] = v[0] >> 7, v[1], v[2], v[3]
            if n >= 20:
                o['parent'] = v[4:20]
        elif t == 7:
            _need(v, 19, '請求資訊選項')
            o['instance'] = v[0]
            o['vf'], o['if'], o['df'] = v[1] >> 7, (v[1] >> 6) & 1, (v[1] >> 5) & 1
            o['dodagid'] = v[2:18]
            o['version'] = v[18]
        elif t == 8:
            _need(v, 30, '前綴資訊選項')
            o['plen'] = v[0]
            o['l'], o['a'], o['r'] = v[1] >> 7, (v[1] >> 6) & 1, (v[1] >> 5) & 1
            o['valid'] = (v[2] << 24) | (v[3] << 16) | (v[4] << 8) | v[5]
            o['preferred'] = (v[6] << 24) | (v[7] << 16) | (v[8] << 8) | v[9]
            o['prefix'] = v[14:30]
        elif t == 9:
            _need(v, 4, '目標描述選項')
            o['descriptor'] = (v[0] << 24) | (v[1] << 16) | (v[2] << 8) | v[3]
        else:
            o['raw'] = v
        opts.append(o)
        p += 2 + n
    return opts


def parse_rpl(code, body):
    # 拆 RPL 控制訊息（ICMPv6 類型 155）的內容：DIS、DIO、DAO、DAO-ACK 與選項
    b = bytes(body)
    d = _new('rpl', len(b))
    d['code'] = code
    d['opts'] = []
    try:
        if code == RPL_DIS:
            _need(b, 2, 'DIS')
            d['flags'] = b[0]
            p = 2
        elif code == RPL_DIO:
            _need(b, 24, 'DIO')
            d['instance'], d['version'] = b[0], b[1]
            d['rank'] = (b[2] << 8) | b[3]
            d['g'], d['zero'], d['mop'], d['prf'] = b[4] >> 7, (b[4] >> 6) & 1, (b[4] >> 3) & 7, b[4] & 7
            d['dtsn'], d['flags'] = b[5], b[6]
            d['dodagid'] = b[8:24]
            p = 24
        elif code == RPL_DAO:
            _need(b, 4, 'DAO')
            d['instance'] = b[0]
            d['k'], d['d'] = b[1] >> 7, (b[1] >> 6) & 1
            d['seq'] = b[3]
            p = 4
            if d['d']:
                _need(b, 20, 'DAO（D＝1 帶 DODAGID）')
                d['dodagid'] = b[4:20]
                p = 20
        elif code == RPL_DAO_ACK:
            _need(b, 4, 'DAO-ACK')
            d['instance'] = b[0]
            d['d'] = b[1] >> 7
            d['seq'], d['status'] = b[2], b[3]
            p = 4
            if d['d']:
                _need(b, 20, 'DAO-ACK（D＝1 帶 DODAGID）')
                d['dodagid'] = b[4:20]
                p = 20
        else:
            d['note'].append('代碼 0x{:02x}：本工具只解 DIS／DIO／DAO／DAO-ACK（安全版 0x80～0x83 不解）'.format(code))
            return d
        d['opts'] = _rpl_opts(b, p)
    except ValueError as ex:
        d['err'].append(str(ex))
    return d


def of0_rank(parent_rank, min_hop=256, rf=1, sp=3, sr=0):
    # OF0（RFC 6552）：R(N)＝R(P)＋(Rf×Sp＋Sr)×MinHopRankIncrease；預設每跳加 3×256＝768（根 256 → 一跳 1024）
    return min(INFINITE_RANK, parent_rank + (rf * sp + sr) * min_hop)


def mrhof_cost(parent_rank, etx):
    # MRHOF（RFC 6719，沒有度量容器時）：經過這個父節點的路徑成本＝父節點 Rank＋鏈路 ETX×128
    return parent_rank + int(etx * 128 + 0.5)


def mrhof_rank(parent_rank, etx, min_hop=256):
    # MRHOF 的 Rank（RFC 6719 3.3，只有一個父節點時）：取「路徑成本」「父 Rank＋MinHopRankIncrease」「父 Rank 進位到下一個整數級」的最大值
    r = max(mrhof_cost(parent_rank, etx), parent_rank + min_hop, min_hop * (1 + parent_rank // min_hop))
    return min(INFINITE_RANK, r)


def mrhof_switch(cur_cost, new_cost, threshold=192):
    # MRHOF 換父節點的遲滯：新路徑要比現在少至少 192（ETX 1.5）才換（PARENT_SWITCH_THRESHOLD）
    return cur_cost - new_cost >= threshold


def dag_rank(rank, min_hop=256):
    # DAGRank＝floor(Rank ÷ MinHopRankIncrease)，可以想成「樓層號」
    return rank // min_hop


def etx(df, dr):
    # ETX＝1／(Df×Dr)：Df 是對方收到的比例、Dr 是 ACK 回來的比例；有一個是 0 就回傳 None（連不上）
    if df <= 0 or dr <= 0:
        return None
    return 1 / (df * dr)


# ============================================================
# 7. 一路解到底、欄位樹、自我測試
# ============================================================

def _data_layer(pay):
    # 不是 6LoWPAN 的酬載（例如 PicoBee 的應用資料）
    d = _new('data', len(pay))
    d['data'] = bytes(pay)
    return d


def _upper(pay, src, dst, ctx, reasm):
    # MAC 酬載：00xxxxxx 不是 6LoWPAN；其他照 6LoWPAN 解，解不通而且大多是文字，就當成應用資料（PicoBee 送的文字）
    if pay[0] < 0x40:
        d = _data_layer(pay)
        d['note'].append('第一個位元組 0x{:02x} 是 00xxxxxx（NALP，RFC 4944：不是 6LoWPAN），當成應用資料'.format(pay[0]))
        return d
    if not is_lowpan(pay[0]):
        d = _data_layer(pay)
        d['note'].append('第一個位元組 0x{:02x} 是 6LoWPAN 沒有定義的分派值，當成應用資料'.format(pay[0]))
        return d
    lo = parse_lowpan(pay, src, dst, ctx, reasm)
    bad = lo['err'] or not all(c[1] for c in checks(lo))
    if bad and _printable(pay):
        d = _data_layer(pay)
        why = lo['err'][0] if lo['err'] else 'checksum 不對'
        d['note'].append('第一個位元組 0x{:02x} 落在 6LoWPAN 分派範圍，但照 6LoWPAN 解不通（{}），內容又大多是文字，所以當成應用資料'.format(pay[0], why))
        return d
    return lo


def decode(frame, fcs=True, ctx=None, reasm=None, strict=True):
    # 802.15.4 訊框一路解到最上層（MAC → 6LoWPAN → IPv6 → UDP／ICMPv6 → RPL）；每一層 dict 的 'next' 是上一層
    d = parse_mac(frame, fcs)
    if d['err']:
        return d
    if fcs and not d['fcs_ok']:
        if strict:
            d['note'].append('FCS 錯誤：接收端應該整個訊框丟掉，所以不往上解')
            return d
        d['note'].append('FCS 錯誤：接收端應該整個訊框丟掉；下面照樣往上解，只是給你對照')
    if d['ftype'] == FT_DATA and not d['sec'] and d['payload']:
        d['next'] = _upper(d['payload'], d['src'], d['dst'], ctx, reasm)
    return d


def _xbee_mode(raw):
    # 這串位元組是 XBee API 訊框嗎？0＝不是、1＝API 模式 1、2＝API 模式 2（有跳脫）
    if len(raw) < 5 or raw[0] != 0x7E:
        return 0
    if ((raw[1] << 8) | raw[2]) + 4 == len(raw):
        return 1
    if raw.find(b'\x7d') >= 0:
        u = xb_unescape(raw)
        if len(u) >= 5 and ((u[1] << 8) | u[2]) + 4 == len(u):
            return 2
    return 0


def _score(d):
    # 一份解碼結果有幾個問題（FCS 以外的錯誤＋沒過的檢查），用來猜「有沒有附 FCS」
    n = len(errors(d))
    for c in checks(d):
        if not c[1] and not c[0].startswith('FCS'):
            n += 1
    return n


def decode_any(raw, ctx=None, reasm=None, fcs=None):
    # 自動判斷：XBee API 訊框？802.15.4 有 FCS？沒 FCS？然後解碼。fcs 給 True／False 就照你說的，不猜
    raw = bytes(raw)
    mode = _xbee_mode(raw)
    if mode == 1:
        return parse_xbee(raw)
    if mode == 2:
        d = parse_xbee(xb_unescape(raw))
        d['guess'] = '有跳脫字元 0x7D：API 模式 2（ATAP2），已先還原再解'
        return d
    if fcs is not None:
        return decode(raw, fcs, ctx, reasm)
    if fcs_ok(raw):
        d = decode(raw, True, ctx, reasm)
        d['guess'] = '最後 2 個位元組剛好是正確的 FCS，判斷為「有附 FCS」'
        return d
    if len(raw) >= 5:
        a = decode(raw, False, ctx, None)
        b = decode(raw, True, ctx, None, strict=False)
        if _score(b) < _score(a):
            d = decode(raw, True, ctx, reasm, strict=False)
            d['guess'] = ('最後 2 個位元組不是正確的 FCS；但把它當成 FCS 時其他各層都對，'
                          '判斷為「有附 FCS，但 FCS 算錯了」（正確的是 {:02x} {:02x}）'.format(
                              d['fcs_calc'] & 0xFF, d['fcs_calc'] >> 8))
            return d
    d = decode(raw, False, ctx, reasm)
    d['guess'] = '最後 2 個位元組不是正確的 FCS，判斷為「沒附 FCS」；如果你有附 FCS，表示 FCS 算錯了'
    return d


def chain(d):
    # 把一層一層的結果排成清單：[MAC, 6LoWPAN, IPv6, UDP…]
    out = []
    while d is not None:
        out.append(d)
        d = d.get('next')
    return out


def layer(d, proto):
    # 找出某一層的結果，例如 layer(d, 'udp')['data'] 就是 UDP 資料；找不到回傳 None
    for x in chain(d):
        if x.get('proto') == proto:
            return x
    return None


def checks(d):
    # 收集每一層的檢查結果：[（名稱, 對不對, 正確值）…]
    out = []
    for x in chain(d):
        out.extend(x.get('chk', ()))
    return out


def errors(d):
    # 收集每一層的錯誤訊息
    out = []
    for x in chain(d):
        out.extend(x.get('err', ()))
    return out


def ok(d):
    # 沒有錯誤、所有檢查都通過
    return not errors(d) and all(c[1] for c in checks(d))


def tree_lines(d):
    # 把解碼結果變成一行一行的欄位樹文字（印字的程式在 wsntree.py，用到才載入，省 Pico 記憶體）
    import wsntree
    return wsntree.tree_lines(d)


def tree(d, out=None):
    # 印出欄位樹（中文欄位名＋英文縮寫）；out 可以給一個「收一行文字」的函式（例如寫檔），不給就用 print
    import wsntree
    wsntree.tree(d, out)


def summary(d):
    # 一行摘要（像 Wireshark 的 Info 欄）
    import wsntree
    return wsntree.summary(d)


def selftest(verbose=True):
    # 自我測試（上課前在 Pico 上跑一次）：CRC 檢查值、XBee 手冊範例、IPHC、分片亂序重組、RPL，順便量時間
    t0 = now_ms()
    res = []

    def t(name, cond):
        # 記錄一項測試結果
        res.append((name, bool(cond)))
    t('CRC-16 "123456789" = 0x2189', crc16(b'123456789') == 0x2189)
    t('XBee 檢查碼 7E 00 04 08 52 4E 4A → 0D', xb_at(0x52, 'NJ') == unhex('7e 00 04 08 52 4e 4a 0d'))
    a, b = 0x0001, 0x0002
    pkt = ipv6_udp(link_local(b), link_local(a), 0xF0B1, 0xF0B2, b'T=25.3C RH')
    f = frames_ipv6(2, 0xABCD, b, a, pkt, fcs=False)
    t('IPHC＋NHC-UDP 25 位元組', len(f) == 1 and f[0] == unhex(
        '41 88 02 cd ab 01 00 02 00 7e 33 f3 12 d9 52 54 3d 32 35 2e 33 43 20 52 48'))
    d = decode(f[0], fcs=False)
    t('IPHC 解回來 UDP checksum 正確', ok(d) and layer(d, 'udp')['data'] == b'T=25.3C RH')
    big = ipv6_udp(link_local(a), link_local(b), 0xF0B1, 0xF0B2, bytes(range(150)))
    fs = frames_ipv6(3, 0xABCD, a, b, big, tag=1)
    r = Reassembler(5000)
    got = None
    for fr in reversed(fs):
        dd = decode(fr, True, reasm=r)
        if dd.get('next') and dd['next'].get('reassembled'):
            got = dd
    t('分片 {} 片、亂序重組成功'.format(len(fs)), got is not None and ok(got) and layer(got, 'udp')['data'] == bytes(range(150)))
    root = link_local(a)
    dio = rpl_dio(256, '2001:db8:1::1', options=opt_conf())
    fr = frames_ipv6(6, 0xABCD, a, BROADCAST, ipv6_icmp(root, ALL_RPL_NODES, 155, RPL_DIO, dio, hlim=255))[0]
    dd = decode(fr)
    t('RPL DIO 組裝與解析', ok(dd) and layer(dd, 'rpl')['rank'] == 256)
    t('OF0 一跳 Rank 1024', of0_rank(256) == 1024)
    ms = ms_since(t0)
    n_ok = sum(1 for _, g in res if g)
    if verbose:
        for name, g in res:
            print(('通過 ' if g else '失敗 ') + name)
        print('wsnproto {}：{}／{} 項通過，共花 {} 毫秒'.format(VERSION, n_ok, len(res), ms))
        z = bytes(125)
        for name, job in (('算一個 125 位元組訊框的 FCS', lambda: crc16(z)),
                          ('解一個 DIO 訊框（不印）', lambda: decode(fr)),
                          ('把 150 位元組資料切成分片', lambda: frames_ipv6(3, 0xABCD, a, b, big, tag=1))):
            t1 = now_ms()
            n = 0
            while ms_since(t1) < 200:
                job()
                n += 1
            print('  {}：每次約 {} 微秒'.format(name, ms_since(t1) * 1000 // n))
    return n_ok == len(res)
