# a_robust.py：任務四、五、六（A 板）穩定版發布端
# 遺囑＋retain 上下線、Wi-Fi 與 MQTT 都會自動重連、
# QoS 1 等不到 PUBACK 不會卡死、沒送成的那筆重連後補送
import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（client id、主題、keepalive）
import time, network
from umqtt.simple import MQTTClient
import wifi, sensor

QOS = 1            # 任務五：改成 0 再跑一次
PERIOD = 1         # 每幾秒發一筆
TIMEOUT = 5        # 等 broker 回應最多幾秒

class SafeClient(MQTTClient):
    def wait_msg(self):            # umqtt.simple 讀完一個封包就把逾時拿掉，這裡補回去
        try:
            return super().wait_msg()
        finally:
            if self.sock:
                self.sock.settimeout(TIMEOUT)

drop = False
def on_msg(topic, msg):
    global drop
    if msg == b"drop":             # 任務四：B 送 drop，A 自己斷網 DROP_S 秒
        drop = True

def up():
    wifi.connect()                 # Wi-Fi 斷了就先重連 Wi-Fi（逾時丟 OSError）
    c = SafeClient(cfg.CID, cfg.BROKER, cfg.PORT, keepalive=cfg.KEEPALIVE)
    c.set_callback(on_msg)
    c.set_last_will(cfg.STATUS, b"offline", retain=True, qos=1)   # connect 之前
    c.connect(timeout=TIMEOUT)
    c.publish(cfg.STATUS, b"online", retain=True, qos=1)
    c.subscribe(cfg.CMD, qos=1)    # clean session：每次重連都要重新訂閱
    return c

c = None
seq = 0
pending = None                     # QoS 1 送出、還沒等到 PUBACK 的那一筆
fails = 0
t_next = time.ticks_ms()
while True:
    try:
        if c is None:
            c = up()
            print("連上 broker（重連過 %d 次）" % fails)
        if pending:                # 上次沒等到 PUBACK：同一筆原封不動再送
            c.publish(cfg.DATA, pending, qos=1)
            print("補送", pending.decode())
            pending = None
        if time.ticks_diff(time.ticks_ms(), t_next) >= 0:
            t_next = time.ticks_add(time.ticks_ms(), int(PERIOD * 1000))
            seq += 1
            msg = sensor.payload(seq)
            if QOS == 1:
                pending = msg
            c.publish(cfg.DATA, msg, qos=QOS)   # QoS 1 最多等 TIMEOUT 秒
            pending = None
            print(msg.decode())
        c.check_msg()              # 看一眼有沒有 cmd（不會送封包出去）
        if drop:                   # 先斷 Wi-Fi，broker 只能靠 keepalive 發現
            drop = False
            network.WLAN(network.STA_IF).disconnect()
            print("斷網 %d 秒；broker 要 %d 秒才發現"
                  % (cfg.DROP_S, cfg.KEEPALIVE * 3 // 2))
            time.sleep(cfg.DROP_S)
            raise OSError("斷網結束")
        time.sleep_ms(20)
    except Exception as e:         # 任何錯誤都當成斷線處理
        print("斷線：", e)
        try:
            c.sock.close()         # 丟掉舊連線，不送 DISCONNECT（遺囑才會發）
        except Exception:
            pass
        c = None
        fails += 1
        time.sleep(3)              # 等 3 秒再重連，不要一直猛撞 broker
