# 06 BH1750 光照度（I2C 位址 0x23）
from machine import I2C, Pin
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
ADDR = 0x23
i2c.writeto(ADDR, b"\x01")     # 開機（Power On）
i2c.writeto(ADDR, b"\x10")     # 連續高解析度模式
time.sleep_ms(180)             # 等第一次量完

while True:
    d = i2c.readfrom(ADDR, 2)  # 讀 2 個位元組
    raw = d[0] << 8 | d[1]     # 拼成 16 位元
    print("%.1f lux" % (raw / 1.2))
    time.sleep(1)
