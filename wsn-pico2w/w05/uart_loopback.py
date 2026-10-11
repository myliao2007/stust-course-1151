from machine import UART, Pin
import time

# UART0：TX = GP0（第 1 腳），RX = GP1（第 2 腳）
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1),
            bits=8, parity=None, stop=1)

# 測試方法：用一條杜邦線把 GP0 與 GP1 直接短接
uart.write(b"HELLO XBEE\r")
time.sleep_ms(200)
print("收到：", uart.read())
