import myid                       # 身份指紋（第一行；B 板）
import cfg                        # 本組參數（client id、A 的主題）
import time
from umqtt.simple import MQTTClient
from wifi import connect

DROP_AFTER = 3     # 收到 3 筆 data 後請 A 斷網（拔 USB 那一次改成 0）
t0 = time.ticks_ms()
def now():                        # 從程式開始算起的秒數
    return time.ticks_diff(time.ticks_ms(), t0) / 1000

n = 0
t_last = None                     # A 最後一次有動靜的時間
t_sub = 0
def on_msg(topic, msg):
    global n, t_last
    t = now()
    if topic == cfg.STATUS:
        note = ''
        if t - t_sub < 1:
            note = '（一訂閱就收到：broker 保留的那一筆）'
        elif msg == b'offline' and t_last is not None:
            note = '（距離 A 最後一次有動靜 %.1f 秒）' % (t - t_last)
        print('%6.1f s  status → %s%s' % (t, msg.decode(), note))
    else:
        n += 1
        t_last = t
        print('%6.1f s  data #%d %s' % (t, n, msg.decode()))

connect()
c = MQTTClient(cfg.CID, cfg.BROKER, cfg.PORT, keepalive=cfg.KEEPALIVE)
c.set_callback(on_msg)
c.connect()
t_sub = now()
c.subscribe(cfg.STATUS, qos=1)
c.subscribe(cfg.DATA, qos=1)
sent = False
t_ping = now()
while True:
    c.check_msg()
    if DROP_AFTER and n >= DROP_AFTER and not sent:
        sent = True
        c.publish(cfg.CMD, b'drop', qos=1)
        t_last = now()            # A 收到 drop 回 PUBACK，之後就沒聲音了
        print('%6.1f s  請 A 斷網 %d 秒；broker 應在 %d×1.5＝%.0f 秒後代發 offline'
              % (t_last, cfg.DROP_S, cfg.KEEPALIVE, cfg.KEEPALIVE * 1.5))
    if now() - t_ping > 10:
        c.ping()                  # 只收不發，要自己送 PINGREQ
        t_ping = now()
    time.sleep_ms(20)
