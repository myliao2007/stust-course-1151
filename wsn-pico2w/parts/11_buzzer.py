# 11 有源蜂鳴器：I/O 接 GP11，高電位會響
from machine import Pin
import time

buzzer = Pin(11, Pin.OUT, value=0)

def beep(ms=200):
    buzzer.value(1)               # 高電位：響
    time.sleep_ms(ms)
    buzzer.value(0)               # 低電位：停

for i in range(3):                # 嗶三聲
    beep()
    time.sleep_ms(200)
