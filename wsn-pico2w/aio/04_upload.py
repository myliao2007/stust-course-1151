# 04_upload.py：每 10 秒把溫度、濕度、光照送上 Adafruit IO（3 個 feed）
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C
import dht, time, aio_cfg

INTERVAL = 10                    # 幾秒送一次：3 筆 × 每分鐘 6 次 = 18 筆，免費版上限 30

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
i2c.writeto(0x23, b"\x01")
i2c.writeto(0x23, b"\x10")
d = dht.DHT11(Pin(15))


def read_all():
    d.measure()
    b = i2c.readfrom(0x23, 2)
    lux = round((b[0] << 8 | b[1]) / 1.2)
    return d.temperature(), d.humidity(), lux


aio_cfg.connect_wifi()
c = aio_cfg.connect_aio()
n = 0
while True:
    try:
        t, h, lux = read_all()
    except OSError:
        print("DHT11 這次沒讀到，2 秒後再試")
        time.sleep(2)
        continue
    try:
        c.publish(aio_cfg.topic("temperature"), str(t))
        c.publish(aio_cfg.topic("humidity"), str(h))
        c.publish(aio_cfg.topic("light"), str(lux))
    except OSError:
        print("連線斷了，重新連線…")
        aio_cfg.connect_wifi()
        c = aio_cfg.connect_aio()
        continue
    n += 1
    print("第 %d 次：溫度 %d °C　濕度 %d %%　光照 %d lux"
          % (n, t, h, lux))
    time.sleep(INTERVAL)
