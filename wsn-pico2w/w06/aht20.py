# aht20.py：讀 AHT20 溫溼度（I2C0：SDA＝GP4 第 6 腳、SCL＝GP5 第 7 腳，位址 0x38）
from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
i2c.writeto(0x38, b"\xbe\x08\x00")       # 初始化（校正）
time.sleep_ms(10)

def convert(d):                          # 7 個位元組 → (溫度 °C, 濕度 %)
    raw_h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    raw_t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    return raw_t / 1048576 * 200 - 50, raw_h / 1048576 * 100

def read():
    i2c.writeto(0x38, b"\xac\x33\x00")   # 叫它量一次
    time.sleep_ms(80)                    # 等 80 毫秒量完
    return convert(i2c.readfrom(0x38, 7))
