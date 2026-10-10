import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
from connect_b import wlan, A_IP   # 先連上 A 板的 AP
import socket, time, struct

SIZE = 1024                        # 每包酬載：試 64、512、1024、1460
SECONDS = 10                       # 連續送幾秒
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
pad = bytes(SIZE - 4)              # 前 4 位元組放序號，後面補 0
seq = full = 0
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < SECONDS * 1000:
    try:
        s.sendto(struct.pack("!I", seq) + pad, (A_IP, cfg.TPUT_PORT))
        seq += 1
    except OSError:                # 送出緩衝區滿了：等 1 毫秒再送
        full += 1
        time.sleep_ms(1)
ms = time.ticks_diff(time.ticks_ms(), t0)
print("送出 %d 包 × %d 位元組，%.1f 秒" % (seq, SIZE, ms / 1000))
print("送出端 %.2f Mbps；緩衝區滿 %d 次" % (seq * SIZE * 8 / ms / 1000, full))
print("RSSI =", wlan.status("rssi"), "dBm")
