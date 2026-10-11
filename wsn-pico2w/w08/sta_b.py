import myid                        # 身份指紋（第一行）
import cfg
import network, socket, time


def hello():                       # 連上 A 的 AP、報到；回傳 (socket, A 的 MAC)
    w = network.WLAN(network.STA_IF)
    w.active(True)
    w.connect(cfg.SSID, cfg.PASSWORD)
    for i in range(150):           # 最多等 15 秒
        if w.isconnected():
            break
        time.sleep_ms(100)
    else:
        raise RuntimeError("連不上 A：status=%d" % w.status())
    a = (w.ifconfig()[2], cfg.PORT_A)    # 閘道就是 A
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", cfg.PORT_B))
    s.settimeout(1)
    while True:                    # 每秒報到，直到 A 回 HI
        s.sendto(b"HELLO," + myid.MAC.encode(), a)
        try:
            data = s.recvfrom(64)[0]
            if data.startswith(b"HI,"):
                break
        except OSError:
            print("A 還沒準備好，1 秒後再報到")
    mac_a = data[3:].decode()
    print("已連上 A（%s），報到完成；A 的 MAC" % a[0], mac_a)
    return s, mac_a
