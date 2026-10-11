import myid                       # 身份指紋（第一行；A 板）
import cfg                        # 本組參數（client id、主題）
from umqtt.simple import MQTTClient
from wifi import connect
import time, sensor               # sensor.py：AHT20 溫溼度＋晶片溫度

connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
c = MQTTClient(cfg.CID, cfg.BROKER, port=cfg.PORT, keepalive=60)
c.connect()
print('發布到', cfg.DATA.decode())

seq = 0
while True:
    seq += 1                      # 每筆編號，B 才算得出遺失和重複
    msg = sensor.payload(seq)
    c.publish(cfg.DATA, msg)      # 沒寫 qos，就是 QoS 0
    print(len(msg), '位元組', msg.decode())
    time.sleep(10)
