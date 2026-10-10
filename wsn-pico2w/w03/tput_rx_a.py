import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import socket, time, struct, ap_a
ap = ap_a.up()                     # 先開好 AP，等 B 送資料過來
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.TPUT_PORT))
s.settimeout(3)                    # 3 秒沒資料就結算這一輪
while True:
    total = pkts = top = 0; t1 = None
    while True:
        try:
            data, addr = s.recvfrom(1500)
        except OSError:
            break                  # 逾時：這一輪結束
        t2 = time.ticks_ms()
        if t1 is None: t1 = t2     # 第一包到的時間
        total += len(data); pkts += 1
        top = max(top, struct.unpack("!I", data[:4])[0])   # 最大序號
    if pkts:
        r = total * 8 / max(1, time.ticks_diff(t2, t1)) / 1000   # Mbps
        print("收到 %d 包、%d 位元組，%.2f Mbps" % (pkts, total, r))
        print("占 65 Mbps 的 %.1f%%" % (r / 65 * 100))
        print("B 送了 %d 包，少了 %d 包" % (top + 1, top + 1 - pkts))
