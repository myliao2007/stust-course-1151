import myid                                  # 身份指紋（第一行）
import cfg                                   # 本組參數
# oled_test.py（B 板）：確認 OLED 接好、ssd1306 驅動裝好
# 先跑 install.py；不能上網就把備用的 ssd1306.py 存到板子上
from machine import Pin, I2C
import ssd1306

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
found = i2c.scan()
print("I2C 找到：", ["0x%02X" % a for a in found])   # 要看到 0x3C
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)
oled.text("WSN topic 12", 0, 0)
oled.text("node " + cfg.NODE_B, 0, 16)
oled.text("SN " + myid.SN[-8:], 0, 32)       # 序號後 8 碼，和 Shell 的指紋對得上
oled.rect(0, 48, 128, 16, 1)
oled.show()
print("OLED 應該顯示：", cfg.NODE_B, myid.SN[-8:])
