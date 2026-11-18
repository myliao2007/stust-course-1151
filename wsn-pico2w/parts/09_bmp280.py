# 09 BMP280 氣壓（I2C 位址 0x76），先把 bmp280.py 存到板子
from machine import I2C, Pin
import bmp280, time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
cid = i2c.readfrom_mem(0x76, 0xD0, 1)[0]
print("晶片 ID", hex(cid))        # BMP280 是 0x58
s = bmp280.BMP280(i2c, 0x76)

while True:
    t, p = s.read()               # °C、Pa
    print("%.2f °C  %.2f hPa" % (t, p / 100))
    time.sleep(1)
