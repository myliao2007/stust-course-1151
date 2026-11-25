# 07_collector_pdr.py：用序號算封包送達率（PDR），搭配距離實驗
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, PWM
import socket, time, json, ssd1306, cfg

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
leds = [PWM(Pin(p)) for p in (6, 7, 8)]
for led in leds:
    led.freq(1000)


def color(r, g, b):
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)


def show(title, lines):
    oled.fill(0)
    oled.text(title, 0, 4)
    for i, t in enumerate(lines):
        oled.text(t, 0, 20 + i * 11)
    oled.show()


ap = cfg.start_ap()                 # 開 Wi-Fi：和練習 3 一樣，寫在 cfg.py 裡

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.PORT))
first, got, last_n = None, 0, 0
while True:
    data, addr = s.recvfrom(256)
    r = json.loads(data.decode())
    n = r["n"]
    if first is None or n < last_n:     # 第一次收到，或節點重開機（序號變小）：重新算
        first, got = n, 0
    if n == last_n:                     # 同一筆收到兩次，不重複算
        continue
    got += 1
    last_n = n
    expect = n - first + 1              # 照序號，應該要收到幾筆
    pdr = got * 100 / expect
    print("#%d 收到 %d/%d 送達率 %.1f %% RSSI %d"
          % (n, got, expect, pdr, r["rssi"]))
    show("PDR %.1f%%" % pdr, [
        "got %d/%d" % (got, expect),
        "lost %d" % (expect - got),
        "RSSI %d dBm" % r["rssi"],
        "T%s H%s S%d" % (r["t"], r["h"], r["soil"]),
    ])
    color(*((0, 255, 0) if pdr >= 95 else (255, 160, 0) if pdr >= 80 else (255, 0, 0)))
