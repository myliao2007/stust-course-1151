# 04 電容式土壤溼度：AO 接 GP26（ADC0）
from machine import ADC
import time

soil = ADC(26)
DRY, WET = 50000, 20000        # 自己量：放空氣中、插進水裡

while True:
    raw = soil.read_u16()      # 0～65535
    volt = raw * 3.3 / 65535
    pct = (DRY - raw) * 100 / (DRY - WET)
    pct = max(0, min(100, pct))
    print(raw, "%.2f V" % volt, "%.0f %%" % pct)
    time.sleep(1)
