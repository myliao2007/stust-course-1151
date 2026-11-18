# 10 INA219 電流／電壓（I2C 位址 0x40），分流電阻 R100 = 0.1 Ω
from machine import I2C, Pin
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
ADDR = 0x40

def reg(r):                       # 讀一個 16 位元暫存器
    d = i2c.readfrom_mem(ADDR, r, 2)
    return d[0] << 8 | d[1]

while True:
    s = reg(0x01)                 # 分流電壓，有正負號
    if s & 0x8000:
        s -= 65536
    v_sh = s * 10e-6              # 1 格 = 10 µV
    v_bus = (reg(0x02) >> 3) * 0.004   # 1 格 = 4 mV
    ma = v_sh / 0.1 * 1000        # I = V ÷ R
    print("%.2f V  %.1f mA" % (v_bus, ma))
    time.sleep(0.5)
