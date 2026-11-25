# 01_check_node.py：感測節點自我檢查（I2C 掃描＋三個感測器各讀 5 次）
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, ADC
import dht, time, cfg

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
print("I2C 掃描：", [hex(a) for a in i2c.scan()])   # 要看到 0x23（BH1750）

d = dht.DHT11(Pin(15))          # DHT11 DATA 接 GP15
soil = ADC(26)                  # 土壤 AOUT 接 GP26
i2c.writeto(0x23, b"\x01")      # BH1750 開機
i2c.writeto(0x23, b"\x10")      # 連續高解析度模式
time.sleep_ms(180)

for k in range(5):
    d.measure()
    b = i2c.readfrom(0x23, 2)
    lux = (b[0] << 8 | b[1]) / 1.2
    raw = soil.read_u16()
    print("第%d次：溫度 %d °C　濕度 %d %%　光照 %.0f lux　土壤讀值 %d"
          % (k + 1, d.temperature(), d.humidity(), lux, raw))
    time.sleep(2)
print("記下土壤讀值：放在空氣中＝DRY，插進水裡＝WET")
