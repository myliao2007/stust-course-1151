import myid                       # 身份指紋（第一行；B 板）
import cfg                        # 本組參數（client id、A 的主題）
import time
from umqtt.simple import MQTTClient
from wifi import connect

got = []
def on_msg(topic, msg):           # A 回報的 LED 狀態
    got.append(msg)

connect()
c = MQTTClient(cfg.CID, cfg.BROKER, cfg.PORT)   # keepalive＝0：等人打字，不檢查閒置
c.set_callback(on_msg)
c.connect()
c.subscribe(cfg.LED, qos=1)
while True:
    s = input('輸入 on 或 off：').strip()
    got.clear()
    t0 = time.ticks_ms()
    c.publish(cfg.CMD, s.encode(), qos=1)
    while not got and time.ticks_diff(time.ticks_ms(), t0) < 2000:
        c.check_msg()
        time.sleep_ms(5)
    if got:
        ms = time.ticks_diff(time.ticks_ms(), t0)
        print('A 回報 LED =', got[0].decode(), '| 來回 %d ms' % ms)
    else:
        print('2 秒內沒收到 A 的回報：A 有在跑 a_cmd.py 嗎？')
