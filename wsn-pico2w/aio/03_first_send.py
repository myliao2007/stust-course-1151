# 03_first_send.py：連上 Adafruit IO，把現在的溫度送到 temperature 這個 feed
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin
import dht, time, aio_cfg

d = dht.DHT11(Pin(15))
time.sleep(1)
d.measure()
t = d.temperature()
print("量到的溫度：", t, "°C")

aio_cfg.connect_wifi()           # 連手機熱點
c = aio_cfg.connect_aio()        # 連 Adafruit IO
c.publish(aio_cfg.topic("temperature"), str(t))
print("送出", aio_cfg.topic("temperature"), "=", t)
time.sleep(1)
c.disconnect()
print("到 Feeds › temperature 看看有沒有這一筆")
