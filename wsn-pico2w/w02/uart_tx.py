import myid
# uart_tx.py（B 板）：光敏、旋鈕各讀 9 次取中位數，套兩點校正，每秒用 UART 送一行給 A
# 接線：B GP0(TX, 第 1 腳) → A GP1(RX)；B GP1(RX, 第 2 腳) ← A GP0(TX)；GND 接 GND
from machine import Pin, ADC, UART
import time
from filter_cal import median, TwoPoint

BAUD = 9600
RAW_LO, RAW_HI = 320, 65200     # ← 換成 cal_b.py 的值
cal = TwoPoint(RAW_LO, 0.0, RAW_HI, 3.3)
uart = UART(0, baudrate=BAUD, bits=8, parity=None, stop=1,
            tx=Pin(0), rx=Pin(1))       # 9600 8N1
photo = ADC(Pin(26))            # 光敏電阻分壓中點（ADC0）
knob = ADC(Pin(27))             # 可變電阻中間腳（ADC1）

def read_median(adc, n=9):
    return median([adc.read_u16() for _ in range(n)])

seq = 0
nxt = time.ticks_ms()
while True:
    p, k = read_median(photo), read_median(knob)
    line = "{},{},{:.3f},{:.3f}\n".format(
        seq, p, cal.y(p), cal.y(k))  # 序號,原始值,光敏 V,旋鈕 V
    uart.write(line)
    print("送出", line.strip())
    seq += 1
    nxt = time.ticks_add(nxt, 1000)
    left = time.ticks_diff(nxt, time.ticks_ms())
    time.sleep_ms(max(0, left))
