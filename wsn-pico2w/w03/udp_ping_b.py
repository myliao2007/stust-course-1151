import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
from connect_b import wlan, A_IP   # 先連上 A 板的 AP
import socket, time
N, GAP_MS = 100, 50                # 送 100 包，每包間隔 50 毫秒
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(0.3)                  # 每次最多等回覆 300 毫秒
rtts, rssi = [], []
for seq in range(1, N + 1):
    t0 = time.ticks_ms()
    s.sendto(b"%d,%d" % (seq, t0), (A_IP, cfg.ECHO_PORT))
    try:
        while True:                # 遲到的舊回覆丟掉，繼續等
            f = s.recvfrom(128)[0].split(b",")   # b"ACK,序號,送出時間"
            if int(f[1]) == seq:
                rtts.append(time.ticks_diff(time.ticks_ms(), int(f[2])))
                break
    except OSError:
        pass                       # 逾時：這一包算遺失
    rssi.append(wlan.status("rssi"))
    time.sleep_ms(GAP_MS)
print("送出 %d 包，收到 %d 包，遺失率 %.1f%%" % (N, len(rtts), 100 * (N - len(rtts)) / N))
print("往返 %.1f ms，RSSI %.1f dBm" % (sum(rtts) / max(len(rtts), 1), sum(rssi) / N))
