# 01_check_collector.py：收集端自我檢查（I2C 掃描＋RGB LED＋蜂鳴器）
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, PWM
import time, cfg

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
print("I2C 掃描：", [hex(a) for a in i2c.scan()])   # 要看到 0x3c（OLED）

leds = [PWM(Pin(p)) for p in (6, 7, 8)]   # R、G、B 接 GP6、GP7、GP8
for led in leds:
    led.freq(1000)


def color(r, g, b):
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)


buzzer = Pin(11, Pin.OUT, value=0)        # 蜂鳴器 I/O 接 GP11
for name, c in (("紅", (255, 0, 0)), ("綠", (0, 255, 0)), ("藍", (0, 0, 255))):
    print("RGB LED 亮：", name)
    color(*c)
    time.sleep(1)
color(0, 0, 0)
print("蜂鳴器嗶兩聲")
for i in range(2):
    buzzer.value(1)
    time.sleep_ms(150)
    buzzer.value(0)
    time.sleep_ms(150)
print("OLED 要等練習 2 裝好驅動才會亮")
