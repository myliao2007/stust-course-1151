# 12 RGB LED：R、G、B 接 GP6、GP7、GP8，用 PWM 調亮度
from machine import Pin, PWM
import time

leds = [PWM(Pin(p)) for p in (6, 7, 8)]
for led in leds:
    led.freq(1000)                # 1 kHz，眼睛看不出閃

def color(r, g, b):               # 每個 0～255
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)     # 255 × 257 = 65535

color(255, 0, 0); time.sleep(1)   # 紅
color(0, 255, 0); time.sleep(1)   # 綠
color(255, 160, 0); time.sleep(1) # 橘黃
color(0, 0, 0)                    # 熄滅
