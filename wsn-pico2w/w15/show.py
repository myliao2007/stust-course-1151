# show.py（B 板，選做）：OLED 顯示最新讀值與遺失率
# OLED 接 I2C0：SDA＝GP4（第 6 腳）、SCL＝GP5（第 7 腳），位址 0x3C
# ssd1306.py（備用檔，MIT 授權）也要存到 B 板；沒接 OLED 時 gw_b.py 自動略過
from machine import Pin, I2C
import ssd1306, cfg

oled = ssd1306.SSD1306_I2C(128, 64, I2C(0, sda=Pin(4), scl=Pin(5), freq=400000))

def f(v, fmt):                     # 缺值顯示 --，不要顯示 0
    return "--" if v is None else fmt % v

def draw(n, d, roll, warn):
    d = d or {}
    oled.fill(0)
    oled.text("g%02d round %d" % (cfg.GROUP, n), 0, 0)
    oled.text("T %s C" % f(d.get("t"), "%.2f"), 0, 14)
    oled.text("H %s %%" % f(d.get("h"), "%.1f"), 0, 24)
    oled.text("L %s lx" % f(d.get("lx"), "%d"), 0, 34)
    oled.text("loss %.1f%% %d/%d" % (roll.rate(), roll.got, roll.exp), 0, 48)
    if roll.rate() > warn:
        oled.rect(0, 46, 128, 12, 1)                 # 超過門檻：最下面那行加框
    oled.show()
