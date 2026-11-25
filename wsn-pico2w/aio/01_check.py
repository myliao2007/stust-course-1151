# 01_check.py：接線自我檢查（I2C 掃描、DHT11 和 BH1750 各讀 5 次、RGB 亮紅綠藍）
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, PWM
import dht, time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
print("I2C 掃描：", [hex(a) for a in i2c.scan()])   # 要看到 0x23（BH1750）
i2c.writeto(0x23, b"\x01")       # BH1750 開機
i2c.writeto(0x23, b"\x10")       # 連續高解析度模式
d = dht.DHT11(Pin(15))           # DHT11 DATA 接 GP15
time.sleep(1)                    # DHT11 通電後要等一下才讀得到

for k in range(5):
    try:
        d.measure()
    except OSError:
        print("第%d次：DHT11 沒讀到" % (k + 1))   # 偶爾一次沒關係
        time.sleep(2)
        continue
    b = i2c.readfrom(0x23, 2)
    lux = (b[0] << 8 | b[1]) / 1.2
    print("第%d次：溫度 %d °C　濕度 %d %%　光照 %.0f lux"
          % (k + 1, d.temperature(), d.humidity(), lux))
    time.sleep(2)

leds = [PWM(Pin(p)) for p in (6, 7, 8)]   # R、G、B 接 GP6、GP7、GP8
for led in leds:
    led.freq(1000)


def color(r, g, b):              # 每個 0～255
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)


COLORS = (("紅", (255, 0, 0)), ("綠", (0, 255, 0)),
          ("藍", (0, 0, 255)))
for name, c in COLORS:
    print("RGB LED 亮：", name)
    color(*c)
    time.sleep(1)
color(0, 0, 0)
print("檢查完成")
