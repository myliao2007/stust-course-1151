# 05_collector_oled.py：收集端把收到的資料顯示在 OLED 上
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C
import socket, time, json, ssd1306, cfg

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)


def show(title, lines):
    oled.fill(0)
    oled.text(title, 0, 4)                  # 最上面一行放標題
    for i, t in enumerate(lines):
        oled.text(t, 0, 20 + i * 11)        # 下面四行放資料，每行隔 11 像素
    oled.show()


ap = cfg.start_ap()                 # 開 Wi-Fi：和練習 3 一樣，寫在 cfg.py 裡
show("G%02d waiting" % cfg.GROUP,
     [cfg.AP_SSID, ap.ifconfig()[0]])

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.PORT))
while True:
    data, addr = s.recvfrom(256)
    r = json.loads(data.decode())
    print("收到", addr[0], "：", r)
    show("G%02d  #%d" % (r["g"], r["n"]), [
        "T %sC  H %s%%" % (r["t"], r["h"]),
        "Lux  %d" % r["lux"],
        "Soil %d%%" % r["soil"],
        "RSSI %d dBm" % r["rssi"],
    ])
