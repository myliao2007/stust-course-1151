import myid                       # 身份指紋（第一行；B 板）
import cfg                        # 本組參數（client id）
import time
from umqtt.simple import MQTTClient
from wifi import connect

FIX = False        # 改成 True：換回自己的 client id 再跑一次
CID = cfg.CID if FIX else cfg.CID_A    # False 時故意用 A 的 id
connect()
kicked = 0
c = None
t_end = time.ticks_add(time.ticks_ms(), 30000)      # 跑 30 秒
while time.ticks_diff(t_end, time.ticks_ms()) > 0:
    try:
        if c is None:
            c = MQTTClient(CID, cfg.BROKER, cfg.PORT)
            c.connect(timeout=5)
            print('用', CID, '連上')
        c.sock.settimeout(5)
        c.publish(cfg.HELLO, b'hello', qos=1)   # QoS 1 才發現得了被踢
        time.sleep(1)
    except Exception as e:
        kicked += 1
        print('被踢下線（第 %d 次）：' % kicked, e)
        c = None
        time.sleep(1)
print('30 秒內被踢 %d 次（FIX=%s，client id=%s）' % (kicked, FIX, CID))
