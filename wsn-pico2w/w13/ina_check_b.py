import myid                      # 身份指紋（B 板：任務一，確認 INA219 的讀值）
import cfg
import time
from machine import Pin, I2C
import ina219

i2c = I2C(0, sda=Pin(cfg.SDA), scl=Pin(cfg.SCL), freq=400_000)
print("I2C 掃描：", [hex(a) for a in i2c.scan()])         # 要看到 0x40
ina = ina219.INA219(i2c, cfg.ZERO_MA)
print("設定暫存器 = 0x%04X" % ina.read(0x00))              # 要讀回 0x01E7
for k in range(10):                      # 每秒一筆，共 10 筆
    raw = ina.shunt_raw()
    v, ma = ina.bus_v(), ina.ma(raw)
    print("%2d %.3f V 原始 %5d %6.1f mA %6.1f mW" % (k + 1, v, raw, ma, v * ma))
    time.sleep(1)
print("接 220 Ω 假負載時，應該是 %.1f mA 左右" % (v / 220 * 1000))
