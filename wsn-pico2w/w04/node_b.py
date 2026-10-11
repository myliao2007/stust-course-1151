import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號、模擬通道）
import network, socket, struct, time, random, machine
# node_b.py（B 板）：一片板子跑好幾個虛擬節點，照 SYNC 決定何時發射
UNIT_US, CCA_US, TURN_US = 320, 128, 192   # 20、8、12 個符元
MIN_BE, MAX_BE, MAX_BACKOFFS = 3, 5, 4     # 802.15.4 的預設值
led = machine.Pin(15, machine.Pin.OUT)     # GP15 接 LED：每送一包閃一下


def csma(ready, air):              # 802.15.4 非時槽 CSMA-CA（簡化版）
    st = {}                        # 節點 → [下次 CCA 時間, NB, BE]
    for n, t in ready.items():
        st[n] = [t + random.getrandbits(MIN_BE) * UNIT_US, 0, MIN_BE]
    out = []                       # 已決定的發射：(起點, 編號)
    while st:
        n = min(st, key=lambda k: st[k][0])   # 最早的節點先做 CCA
        t, nb, be = st[n]
        if any(a < t + CCA_US and t < a + air for a, k in out):
            nb, be = nb + 1, min(be + 1, MAX_BE)   # 通道忙
            if nb > MAX_BACKOFFS:
                del st[n]          # 通道存取失敗，這一輪放棄
            else:
                w = random.getrandbits(be) * UNIT_US
                st[n] = [t + CCA_US + w, nb, be]
        else:                      # 通道空：聽完、切換完才發射
            out.append((t + CCA_US + TURN_US, n))
            del st[n]
    return out


def plan(mode, slot_ms, ids, air):  # 每個節點的發射起點（微秒）
    if mode == 2:                   # TDMA：節點 n 用第 n 個時槽
        return [((n - 1) * slot_ms * 1000, n) for n in ids]
    ready = {}                      # 處理時間差 0～4095 微秒
    for n in ids:
        ready[n] = random.getrandbits(12)
    if mode == 0:                   # 不排程：資料好了就送
        return [(ready[n], n) for n in ids]
    return csma(ready, air)         # 隨機退避（簡化 CSMA）


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)            # 關閉 Wi-Fi 省電，SYNC 才收得快
wlan.connect(cfg.SSID, cfg.PASSWORD)
while not wlan.isconnected():
    time.sleep(0.5)
HUB = (wlan.ifconfig()[2], cfg.HUB_PORT)   # 閘道就是 Hub（A 板）
print("節點 IP：", wlan.ifconfig()[0], "→ Hub", HUB)
ctl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ctl.bind(("0.0.0.0", cfg.SYNC_PORT))       # 收 SYNC 用
ctl.settimeout(2 * cfg.PERIOD_MS / 1000)   # 等兩輪
socks = {}                          # 每個虛擬節點一個 socket
for n in cfg.NODE_IDS:
    socks[n] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
adc = machine.ADC(4)
air = cfg.airtime_us(11)            # 11 位元組要飛 896 微秒
ctl.sendto(b"JOIN", HUB)
while True:
    try:
        data, addr = ctl.recvfrom(16)
    except OSError:                 # 兩輪沒等到 SYNC：重新 JOIN
        print("等不到 SYNC，重新 JOIN")
        ctl.sendto(b"JOIN", HUB)
        continue
    t0 = time.ticks_us()            # 收到 SYNC＝這一輪的 0
    if data[:1] != b"S":
        continue
    rnd, mode, slot, okbits = struct.unpack("<HBHB", data[1:])
    v = adc.read_u16() * 3.3 / 65535
    t = 27 - (v - 0.706) / 0.001721
    sent = sorted(plan(mode, slot, cfg.NODE_IDS, air))
    for start, n in sent:           # 照起點先後，等到了才送
        now = time.ticks_diff(time.ticks_us(), t0)
        time.sleep_us(max(0, start - now))
        pkt = struct.pack(cfg.FMT, n, rnd, t, start)
        socks[n].sendto(pkt, HUB)
        led.toggle()
    got = [n for n in cfg.NODE_IDS if okbits >> (n - 1) & 1]
    pts = " ".join("%d@%.3fms" % (n, a / 1000) for a, n in sent)
    print("R%d %s 送出：%s｜上一輪 Hub 收到：%s" % (
        rnd, cfg.MODES[mode], pts, got))
