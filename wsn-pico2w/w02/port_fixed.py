# port_fixed.py：port_bug.py 改好的版本
from machine import ADC, Pin
adc = ADC(Pin(26))           # 光敏電阻分壓中點
raw = adc.read_u16()         # 0～65535
volt = raw * 3.3 / 65535     # ① 3.3 V、滿刻度 65535
if raw > 44843:              # ② 700÷1023 換到新尺度
    print("分壓", volt, "V")  # ③ 分壓只有電壓
