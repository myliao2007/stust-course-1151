import myid
# baud_probe.py（B 板，延伸挑戰 D）：量 A 送來的 0x55 最短低電位脈波，反推鮑率
from machine import Pin, time_pulse_us

rx = Pin(1, Pin.IN, Pin.PULL_UP)        # 接 A 的 TX（線不用改）
widths = []
for _ in range(60):
    w = time_pulse_us(rx, 0, 200000)    # 低電位幾微秒，逾時回負數
    if w > 0:
        widths.append(w)
bit = min(widths)
print("最短低脈波 {} µs → 鮑率約 {:.0f}".format(bit, 1000000 / bit))
for std in (9600, 19200, 38400, 57600, 115200):
    if abs(1000000 / bit - std) < std * 0.05:
        print("最接近的標準鮑率：", std)
