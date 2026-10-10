import myid
# adc_b.py（B 板）：每 1000 ms 讀一次光敏電阻（GP26）與可變電阻（GP27）
from machine import Pin, ADC
import time

photo = ADC(Pin(26))       # 光敏電阻分壓中點（ADC0，第 31 腳）
knob = ADC(Pin(27))        # 可變電阻中間腳（ADC1，第 32 腳）

PERIOD = 1000
nxt = time.ticks_ms()
while True:
    p = photo.read_u16()
    k = knob.read_u16()
    print("光敏 {:5d}（{:.3f} V）  旋鈕 {:5d}（{:.3f} V）".format(
        p, p * 3.3 / 65535, k, k * 3.3 / 65535))
    nxt = time.ticks_add(nxt, PERIOD)
    left = time.ticks_diff(nxt, time.ticks_ms())
    time.sleep_ms(max(0, left))
