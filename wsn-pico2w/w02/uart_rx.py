import myid
# uart_rx.py（A 板）：每秒印一行「A 的溫濕度、照度＋B 用 UART 送來的 ADC 讀值」
# 接線：A GP1(RX, 第 2 腳) ← B GP0(TX)；A GP0(TX, 第 1 腳) → B GP1(RX)；GND 接 GND
from machine import Pin, UART
import time
from sensors_a import read_aht20, read_lux

BAUD = 9600     # 第 4 步：故意改成 19200 看亂碼（再試 115200），截圖後改回 9600
uart = UART(0, baudrate=BAUD, bits=8, parity=None, stop=1,
            tx=Pin(0), rx=Pin(1))       # 9600 8N1

def parse_b(line):              # B 的一行：序號,光敏原始值,光敏 V,旋鈕 V
    try:
        seq, praw, pv, kv = line.decode().strip().split(",")
        return "B#{} 光敏 {} V（{}） 旋鈕 {} V".format(seq, pv, praw, kv)
    except (UnicodeError, ValueError):
        return "看不懂：{}".format(line)

last_b, buf = "（還沒收到 B）", b""
nxt = time.ticks_ms()
while True:
    n = uart.any()
    if n:
        buf += uart.read(n)
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            last_b = parse_b(line)
        if len(buf) > 40:       # 一直等不到換行，多半是鮑率不一致
            print("亂碼？", buf)
            buf = b""
    if time.ticks_diff(time.ticks_ms(), nxt) >= 0:
        nxt = time.ticks_add(nxt, 1000)
        tc, rh = read_aht20()
        lux = read_lux()
        print("A {:.2f} °C {:.2f} %RH {:.1f} lux |".format(tc, rh, lux), last_b)
    time.sleep_ms(5)
