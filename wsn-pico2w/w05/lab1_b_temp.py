import myid                        # 身份指紋（第一行）
import cfg, picobee, time
from machine import Pin, I2C
bee = picobee.PicoBee()            # B 板：PAN 已在 Lab 1-2 存好
bee.start()
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
AHT = 0x38
i2c.writeto(AHT, b"\xbe\x08\x00")
time.sleep_ms(10)
NODE = "N1"
while not bee.joined():            # 等入網（板載燈開始閃）
    bee.wait(200)

while True:
    i2c.writeto(AHT, b"\xac\x33\x00")
    time.sleep_ms(80)
    d = i2c.readfrom(AHT, 7)
    raw = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    t = raw / 1048576 * 200 - 50
    bee.write("{},{:.2f}\r\n".format(NODE, t).encode())   # 透明模式
    print("送出", NODE, "%.2f" % t)
    bee.wait(5000)
