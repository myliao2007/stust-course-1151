import myid                      # 身份指紋（第一行）
import cfg                       # 本組參數與金鑰
import network, socket, time, binascii
import seal
# gw_b.py（B 板＝閘道）：開 AP 收 A 的封包，先驗再收

MODE = "seal"                    # 跟 A 一樣："plain"、"aes" 或 "seal"
last = 0                         # 收過最大的計數器（只要記一個數字）
sock = None

def ap_up():                     # 開本組的 AP，綁好 UDP 埠
    global sock
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=cfg.AP_SSID, key=cfg.AP_PASS, channel=cfg.AP_CH)
    ap.active(True)
    while not ap.active():
        time.sleep_ms(100)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", cfg.GW_PORT))
    print("閘道 AP：", cfg.AP_SSID, "IP", ap.ifconfig()[0], "埠", cfg.GW_PORT)

def handle(pkt):                 # 收件口：A 的封包、攻擊測試的封包都從這裡進來
    global last
    print("收到 %d B：" % len(pkt), binascii.hexlify(pkt[:20]).decode(), "…")
    if MODE == "plain":
        print("  明文：", pkt)
        return "ok"
    if MODE == "aes":
        print("  解密：", seal.decrypt(cfg.ENC_KEY, pkt))
        return "ok"
    r, ctr, body = seal.unseal(cfg.ENC_KEY, cfg.MAC_KEY, pkt, last)
    if r == "ok":
        last = ctr
        print("  收下 #%d" % ctr, body)
    else:
        print("  擋下：%s（目前收過最大 #%d）" % (r, last))
    return r

def collect(n):                  # 正常收 n 包，回傳收到的原始封包
    got = []
    while len(got) < n:
        pkt = sock.recvfrom(256)[0]
        handle(pkt)
        got.append(pkt)
    return got

if __name__ == "__main__":       # 直接執行：一直收下去
    ap_up()
    while True:
        collect(1)
