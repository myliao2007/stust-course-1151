import myid                       # 身份指紋（第一行；B 板）
import cfg                        # 本組參數（client id、A 的主題）
import time, json
from umqtt.simple import MQTTClient
from wifi import connect
from seqstat import SeqStat       # 用 seq 算遺失、重複

CLEAN = True       # 任務五：True 跑一次、False 跑一次
SUB_QOS = 1        # 訂閱時要求的 QoS
OFFLINE_AT = 0     # 收到幾筆後離線 10 秒（任務二＝0 不離線；任務五＝20）
OFFLINE_S = 10
WINDOW = 40        # 任務五：統計 40 個 seq 就結束

st = SeqStat()
def on_msg(topic, msg):
    d = json.loads(msg)
    r = st.add(d['seq'])
    print('seq %3d  %5.2f °C  %4.1f %%RH  晶片 %4.1f °C  [%s]'
          % (d['seq'], d['t'], d['rh'], d['chip'], r))
    if st.got() % 10 == 0:
        print('   ', st.line())

def up(clean):
    c = MQTTClient(cfg.CID, cfg.BROKER, cfg.PORT, keepalive=cfg.KEEPALIVE)
    c.set_callback(on_msg)
    present = c.connect(clean_session=clean)
    print('connect(clean_session=%s)，broker 還留著會話：%d' % (clean, present))
    if not present:               # 會話沒留著，訂閱也沒了，要重新訂閱
        c.subscribe(cfg.DATA, qos=SUB_QOS)
    return c

connect()
c = up(True)
c.disconnect()                    # 先用 clean_session=True 連一次，把舊會話清掉
c = up(CLEAN)
t_ping = time.ticks_ms()
went_off = False
while True:
    c.check_msg()
    if OFFLINE_AT and not went_off and st.got() >= OFFLINE_AT:
        went_off = True
        c.disconnect()            # 正常說再見，B 離線
        print('B 離線 %d 秒……' % OFFLINE_S)
        time.sleep(OFFLINE_S)
        c = up(CLEAN)             # 用同一個 client id 回來
    if time.ticks_diff(time.ticks_ms(), t_ping) > 10000:
        c.ping()                  # 只收不發，要自己送 PINGREQ
        t_ping = time.ticks_ms()
    if OFFLINE_AT and st.first is not None and st.top - st.first + 1 >= WINDOW:
        break
    time.sleep_ms(20)
print('結果（B 訂閱 QoS %d，clean_session=%s）：' % (SUB_QOS, CLEAN))
print(st.line())
