import myid                        # 身份指紋（第一行）
import cfg
import network, socket, time


def up():                          # 開 AP、等 B 報到；回傳 (socket, B, B 的 MAC)
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
    ap.active(True)
    while not ap.active():
        time.sleep_ms(100)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", cfg.PORT_A))
    print("AP 已開：", cfg.SSID, "，等 B 報到…")
    while True:                    # UDP 要先知道 B 在哪
        data, b = s.recvfrom(64)
        if data.startswith(b"HELLO,"):   # B 順便說出 MAC
            s.sendto(b"HI," + myid.MAC.encode(), b)
            mac_b = data[6:].decode()
            print("B 報到了：", b[0], "，B 的 MAC", mac_b)
            return s, b, mac_b
