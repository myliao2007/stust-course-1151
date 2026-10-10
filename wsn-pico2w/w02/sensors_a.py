# sensors_a.py（A 板）：把任務二、三的讀值包成兩個函式，給 uart_rx.py 用
from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
AHT, BH = 0x38, 0x23
time.sleep_ms(100)                  # 上電穩定時間
i2c.writeto(AHT, b"\xbe\x08\x00")   # AHT20 初始化校正
time.sleep_ms(10)
i2c.writeto(BH, b"\x01")            # BH1750 Power On
i2c.writeto(BH, b"\x10")            # BH1750 連續高解析度模式
time.sleep_ms(180)

def read_aht20():
    i2c.writeto(AHT, b"\xac\x33\x00")   # 觸發一次量測
    time.sleep_ms(80)
    d = i2c.readfrom(AHT, 7)
    h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    return t / 1048576 * 200 - 50, h / 1048576 * 100

def read_lux():
    raw = i2c.readfrom(BH, 2)
    return ((raw[0] << 8) | raw[1]) / 1.2
