import myid                        # 身份指紋（第一行）
import cfg, network, socket, time


def hello():                       # B 板：連上 A 的 AP、向 A 報到
    w = network.WLAN(network.STA_IF)
    w.active(True)
    w.config(pm=0xa11140)          # 關掉 Wi-Fi 省電，時間量得比較準
    w.connect(cfg.SSID, cfg.PASSWORD)
    for i in range(150):           # 最多等 15 秒
        if w.isconnected():
            break
        time.sleep_ms(100)
    else:
        raise RuntimeError("連不上 A：status=%d" % w.status())
    a = (w.ifconfig()[2], cfg.PORT_A)    # 閘道就是 A 的 IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", cfg.PORT_B))
    s.settimeout(1)
    while True:                    # 每秒報到一次，直到 A 回 HI
        s.sendto(b"HELLO", a)
        try:
            if s.recvfrom(64)[0] == b"HI":
                break
        except OSError:
            print("A 還沒準備好，1 秒後再報到")
    s.settimeout(None)
    print("已連上 A（%s），報到完成" % a[0])
    return s, a
