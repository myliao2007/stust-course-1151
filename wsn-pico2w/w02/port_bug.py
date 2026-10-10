# port_bug.py：抓錯練習（有 3 個錯，不要直接拿來用）
from machine import ADC, Pin
adc = ADC(Pin(26))           # 光敏電阻分壓中點
raw = adc.read_u16()
volt = raw * 5.0 / 1024
if raw > 700:
    print("照度", volt, "lux")
