# 05 I2C 掃描：SDA 接 GP4，SCL 接 GP5
from machine import I2C, Pin

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
found = i2c.scan()
print(found)                      # 十進位
print([hex(a) for a in found])    # 十六進位
