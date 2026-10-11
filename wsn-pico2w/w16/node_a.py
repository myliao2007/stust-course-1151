import myid                      # 身份指紋（第一行；A 板，任務四起另存成 main.py）
import cfg, mysecret
import time, gc, socket, machine
import util, packet
import wsnproto as w
from wifi import connect
# node_a.py（A 板＝感測節點）：每 5 秒讀一次 → 13 位元組 → 6LoWPAN 訊框 → Wi-Fi UDP 交給 B
FAKE = False                     # 任務二第一步改 True：先用假資料把流程走通
if FAKE:
    read_all = packet.fake
else:
    import sensors
    read_all = sensors.read_all
led = machine.Pin("LED", machine.Pin.OUT)
FP = "%s|%s|A|%s|%s" % (myid.STUDENT_ID, cfg.G, myid.SN, myid.MAC)


def find_b(s):                   # 找邊界路由器：送 DIS（有 DODAG 嗎？），等 B 回 DIO
    dis = w.ipv6_icmp(packet.A_IP, w.ALL_RPL_NODES, 155, w.RPL_DIS, w.rpl_dis(), hlim=255)
    f = w.frames_ipv6(0, cfg.PAN, cfg.SHORT_A, w.BROADCAST, dis)[0]
    for k in range(3):
        s.sendto(f, (cfg.BCAST, cfg.PORT_B))
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < 1000:
            try:
                g, src = s.recvfrom(256)
            except OSError:
                continue
            r = w.layer(w.decode(g), "rpl")
            if r and r["code"] == w.RPL_DIO:
                rank = w.of0_rank(r["rank"])     # OF0：根 256 → 一跳 1024
                print("找到 B（%s），B 的 Rank %d，我的 Rank %d" % (src[0], r["rank"], rank))
                return src[0]
    if cfg.GW_IP:                # 網段擋了廣播：用 cfg 填的位址
        return cfg.GW_IP
    raise OSError("找不到 B：先跑 B 的 br_b.py，或把 B 的 IP 填進 cfg.GW_IP")


def up():                        # 連 Wi-Fi → 開 socket → 找 B → 報到
    connect(mysecret.WIFI_SSID, mysecret.WIFI_PASS)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", cfg.PORT_A))
    s.settimeout(0.2)
    try:
        gw = (find_b(s), cfg.PORT_B)
    except OSError:
        s.close()
        raise
    for f in packet.frame(0, FP.encode(), packet.HPORT):
        s.sendto(f, gw)          # 報到：B 會印出 A 的指紋
    return s, gw


s, seq, first = None, 0, True
nxt = t_led = time.ticks_ms()
while True:
    if s is None:
        s, gw = util.retry(up)   # 斷線：退避重試 1、2、4…秒
    now = time.ticks_ms()
    if time.ticks_diff(now, nxt) >= 0:            # 時間到才做：每 5 秒一筆
        nxt = time.ticks_add(nxt, cfg.PERIOD_MS)
        if time.ticks_diff(now, nxt) > 0:         # 落後一整格（剛重連）：從現在起算
            nxt = time.ticks_add(now, cfg.PERIOD_MS)
        d = read_all()
        seq = (seq + 1) & 0xFFFF
        b = packet.pack(seq, d)                   # 13 位元組（資料格式表）
        f = packet.frame(seq, b)[0]               # 加上 6LoWPAN、MAC 標頭與 FCS
        try:
            s.sendto(f, gw)
            print("#%d 送出 %d 位元組：%s" % (seq, len(f), packet.show(packet.unpack(b))))
            if first:
                print(w.hexdump(f))               # 第一筆印出位元組，和 B 對照
                first = False
        except OSError as e:
            util.log("送不出去：%s" % e)
            s.close()
            s = None
        gc.collect()
    if time.ticks_diff(now, t_led) >= 500:        # 每 0.5 秒閃一次：活著
        t_led = now
        led.toggle()
    time.sleep_ms(10)
