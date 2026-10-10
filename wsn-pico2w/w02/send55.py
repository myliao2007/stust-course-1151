import myid
# send55.py（A 板，延伸挑戰 D）：用一個 B 不知道的鮑率，一直送 0x55
# 0x55 在線上是 0、1 交錯，每一段低電位剛好一個位元寬
from machine import Pin, UART
import time

BAUD = 9600     # 老師或 A 自己挑一個，先不要告訴 B
uart = UART(0, baudrate=BAUD, tx=Pin(0), rx=Pin(1))
while True:
    uart.write(b"\x55" * 20)
    time.sleep_ms(50)
