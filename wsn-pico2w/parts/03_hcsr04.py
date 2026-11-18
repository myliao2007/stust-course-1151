# 03 HC-SR04 超音波：Trig 接 GP12，Echo 接 GP13
from machine import Pin, time_pulse_us
import time

trig = Pin(12, Pin.OUT, value=0)
echo = Pin(13, Pin.IN)         # Echo 是 5 V，不可接 GP26～28

def distance_cm():
    trig.value(1)
    time.sleep_us(10)          # 送出 10 µs 的觸發脈波
    trig.value(0)
    t = time_pulse_us(echo, 1, 30000)  # Echo 高電位多久
    if t < 0:
        return None            # 逾時：沒收到回音
    return t * 0.0343 / 2      # 聲速 343 m/s，來回要除 2

while True:
    d = distance_cm()
    print("沒有回音" if d is None else "%.1f cm" % d)
    time.sleep(0.5)
