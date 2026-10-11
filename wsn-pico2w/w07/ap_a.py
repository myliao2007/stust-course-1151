import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import network, socket, time


def up():                          # A 板：開本組的 AP、等 B 報到，回傳 (socket, B 的位址)
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
    ap.active(True)
    while not ap.active():
        time.sleep_ms(100)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", cfg.PORT_A))
    print("AP 已開：", cfg.SSID, "，等 B 報到…")
    while True:                    # 真的 LoRa 是廣播；Wi-Fi UDP 要先知道 B 在哪
        data, b = s.recvfrom(64)
        if data == b"HELLO":
            s.sendto(b"HI", b)
            print("B 報到了：", b[0])
            return s, b
