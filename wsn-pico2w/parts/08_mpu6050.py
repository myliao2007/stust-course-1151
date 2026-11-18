# 08 MPU-6050 六軸（I2C 位址 0x68）
from machine import I2C, Pin
import struct, time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
ADDR = 0x68
i2c.writeto_mem(ADDR, 0x6B, b"\x00")   # 叫醒

while True:
    d = i2c.readfrom_mem(ADDR, 0x3B, 14)
    ax, ay, az, tr, gx, gy, gz = struct.unpack(">7h", d)
    print("az %.2f g" % (az / 16384))   # 1 g = 16384
    print("gx %.1f °/s" % (gx / 131))   # 1 °/s = 131
    time.sleep(0.5)
