# 02 HC-SR501 人體紅外線：OUT 接 GP14
from machine import Pin
import time

pir = Pin(14, Pin.IN)
print("暖機中，等 60 秒…")
time.sleep(60)                 # 剛通電會亂跳

last = 0
while True:
    now = pir.value()          # 1 = 有人在動
    if now != last:            # 狀態變了才印
        print("有人！" if now else "沒人了")
        last = now
    time.sleep(0.1)
