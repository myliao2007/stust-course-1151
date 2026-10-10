import myid
from machine import Pin, I2C

# I2C0：SDA 接 GP4（第 6 腳），SCL 接 GP5（第 7 腳）
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

found = i2c.scan()
print("共找到", len(found), "個 I2C 裝置")
for a in found:
    print("位址 0x{:02X}".format(a))

# 正常應該看到 0x23（BH1750）、0x38（AHT20）與 0x77（BMP280）

# 再確認 0x77 是哪一顆：讀它的暫存器 0xD0（chip ID）
CHIP = {0x58: "BMP280", 0x60: "BME280", 0x55: "BMP180"}
if 0x77 in found:
    cid = i2c.readfrom_mem(0x77, 0xD0, 1)[0]
    name = CHIP.get(cid, "不認識的晶片")
    print("0x77 的 chip ID = 0x{:02X} → {}".format(cid, name))
