import myid                      # 身份指紋（第一行；A 板）
import cfg                       # 本組參數（client id、主題）
from umqtt.simple import MQTTClient
from machine import Pin
from wifi import connect
import time
led = Pin('LED', Pin.OUT)   # 板載 LED 掛在 CYW43439 上
def on_msg(topic, msg):
    print('收到', topic, msg)
    led.value(1 if msg == b'on' else 0)
    c.publish(cfg.LED, b'%d' % led.value())   # 回報給 B 量來回時間
connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
c = MQTTClient(cfg.CID, cfg.BROKER, cfg.PORT, keepalive=cfg.KEEPALIVE)
c.set_callback(on_msg)
c.connect()
c.subscribe(cfg.CMD, qos=1)  # 也可訂閱 stust/ee/+/g07a/cmd
t_ping = time.ticks_ms()
while True:
    c.check_msg()           # 非阻塞；wait_msg() 會一直等
    if time.ticks_diff(time.ticks_ms(), t_ping) > 10000:
        c.ping()            # 只收不發，要自己送 PINGREQ
        t_ping = time.ticks_ms()
    time.sleep(0.1)
