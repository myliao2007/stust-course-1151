import myid                        # 身份指紋（第一行）
import sta_b, time
DELAYS = (950, 1000, 1040, 1500, 2000, 2100, 3000)   # 第 1～7 次上行後幾 ms 回下行

s, a = sta_b.hello()               # 連上 A、報到
while True:
    d = s.recvfrom(64)[0]
    t0 = time.ticks_ms()           # 上行到了：從這裡開始數
    if not d.startswith(b"UP"):
        continue
    fcnt = int(d.split(b",")[1])
    w = DELAYS[(fcnt - 1) % len(DELAYS)]
    print("收到上行 FCnt %d，%d ms 後回下行" % (fcnt, w))
    while time.ticks_diff(time.ticks_ms(), t0) < w:
        pass                       # 忙等，時間比 sleep 準
    s.sendto(b"DN,%d,%d" % (fcnt, w), a)
