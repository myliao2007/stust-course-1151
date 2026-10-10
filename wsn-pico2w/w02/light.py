import myid
# light.py（A 板）：讀 BH1750 照度，用 ticks_ms 排時間，剛好每 1000 ms 印一筆
from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
BH = 0x23
i2c.writeto(BH, b"\x01")   # Power On
i2c.writeto(BH, b"\x10")   # 連續高解析度模式
time.sleep_ms(180)         # 高解析度一次量測約需 120～180ms，先等第一筆量完

PERIOD = 1000              # 每 1000 ms 一筆
nxt = time.ticks_ms()
while True:
    raw = i2c.readfrom(BH, 2)
    lux = ((raw[0] << 8) | raw[1]) / 1.2
    print("照度 {:.1f} lux".format(lux))
    nxt = time.ticks_add(nxt, PERIOD)              # 下一筆該讀的時間
    left = time.ticks_diff(nxt, time.ticks_ms())   # 還剩幾 ms
    time.sleep_ms(max(0, left))                    # 只睡剩下的
