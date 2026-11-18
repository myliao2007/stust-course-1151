# 07 OLED 顯示（I2C 位址 0x3C）
# 第一次用：板子連上 Wi-Fi 後在 Shell 打
#   import mip; mip.install("ssd1306")
from machine import I2C, Pin
import ssd1306

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)                   # 整個畫面清成黑色
oled.text("WSN Node 1", 0, 0)  # 上面 16 列是黃色
oled.text("T=25C", 0, 24)      # 下面是藍色
oled.text("H=60%", 0, 40)
oled.show()                    # 送到螢幕才會亮
