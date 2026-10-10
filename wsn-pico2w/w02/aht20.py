import myid
from machine import Pin, I2C
import time
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
AHT = 0x38
time.sleep_ms(100)                  # 上電穩定時間
i2c.writeto(AHT, b"\xbe\x08\x00")   # 初始化校正
time.sleep_ms(10)

def read_aht20():
    i2c.writeto(AHT, b"\xac\x33\x00")   # 觸發一次量測
    time.sleep_ms(80)
    d = i2c.readfrom(AHT, 7)   # 狀態+濕度+溫度共 7 位元組
    h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    return t / 1048576 * 200 - 50, h / 1048576 * 100

while True:
    tc, rh = read_aht20()
    print("溫度 {:.2f} °C   濕度 {:.2f} %RH".format(tc, rh))  # 補上
    time.sleep(1)                                             # 補上
