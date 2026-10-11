import myid                      # 身份指紋（第一行）
import cfg                       # 本組參數與金鑰
import network, socket, time, machine
import seal, counter
# node_a.py（A 板＝感測節點）：每 2 秒送一包給自己組的 B

MODE = "seal"                    # 任務一先 "plain" 再 "aes"；任務二 "seal"

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(cfg.AP_SSID, cfg.AP_PASS)        # 連上自己組 B 開的 AP
while not sta.isconnected():
    time.sleep(0.5)
gw = (sta.ifconfig()[2], cfg.GW_PORT)        # 閘道就是 B
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
adc = machine.ADC(4)                          # 晶片內建的溫度感測器
ctr = counter.start()
print("A 送往", gw, "模式", MODE, "計數器從", ctr + 1, "開始")

while True:
    v = adc.read_u16() * 3.3 / 65535
    t = 27 - (v - 0.706) / 0.001721
    body = ('{"id":"%s","t":%.1f}' % (cfg.NODE_ID, t)).encode()
    t0 = time.ticks_us()
    if MODE == "plain":
        pkt = body                                          # 明文
    elif MODE == "aes":
        pkt = seal.encrypt(cfg.ENC_KEY, body)               # IV＋密文
    else:
        ctr = counter.next_(ctr)
        pkt = seal.seal(cfg.ENC_KEY, cfg.MAC_KEY, ctr, body)   # 計數器＋IV＋密文＋MAC
    us = time.ticks_diff(time.ticks_us(), t0)
    s.sendto(pkt, gw)
    print("送出 %d B（明文 %d B，處理 %d µs）" % (len(pkt), len(body), us), body)
    time.sleep(2)
