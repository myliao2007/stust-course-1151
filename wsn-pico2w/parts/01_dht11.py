# 01 DHT11 溫濕度：DATA 接 GP15
import dht, time
from machine import Pin

d = dht.DHT11(Pin(15))

while True:
    d.measure()                # 叫感測器量一次
    t = d.temperature()        # 溫度（°C，整數）
    h = d.humidity()           # 相對濕度（%）
    print("溫度", t, "°C  濕度", h, "%")
    time.sleep(2)              # 至少隔 1 秒再量
