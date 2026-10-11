import myid                                  # 身份指紋（第一行）
import cfg                                   # 本組參數：主題、client id、週期…
# pub_multi.py（A 板＝感測節點）：每 5 秒送一筆多欄位 JSON
# 有遺囑＋online；訂閱 cmd 控制板載 LED
from wifi import connect
from umqtt.simple import MQTTClient
import sensors, machine, time, json

led = machine.Pin("LED", machine.Pin.OUT)

def on_cmd(topic, msg):                      # 儀表板的開關送 on／off 過來
    led.value(1 if msg == b"on" else 0)
    print("收到指令：", msg)

def start():
    connect(cfg.SSID, cfg.PASSWORD)
    c = MQTTClient(cfg.CID_A, cfg.BROKER, keepalive=cfg.KEEPALIVE)
    c.set_callback(on_cmd)
    c.set_last_will(cfg.ST_A, "offline", retain=True)   # 遺囑：connect 之前交代
    c.connect()
    c.publish(cfg.ST_A, "online", retain=True)         # 上線就翻成 online
    c.subscribe(cfg.CMD_A)
    return c

c = start()
seq = 0
nxt = time.ticks_ms()
while True:
    d = sensors.read_all()                   # t、h、p、lux、t2（讀不到是 None）
    seq += 1
    d["id"], d["seq"] = cfg.NODE_A, seq
    d["ts"] = "%04d-%02d-%02d %02d:%02d:%02d" % time.localtime()[:6]
    s = json.dumps(d)
    try:
        c.publish(cfg.DATA_A, s)
        c.check_msg()                        # 順便看有沒有 cmd
        print(s)                             # 第 1 關：Shell 上看得到每一筆
    except OSError as e:                     # 斷線：等 2 秒，Wi-Fi 和 broker 都重連
        print("斷線，重連中：", e)
        time.sleep(2)
        try:
            c = start()
        except OSError:
            pass
    nxt = time.ticks_add(nxt, cfg.PERIOD_MS)
    wait = time.ticks_diff(nxt, time.ticks_ms())
    if wait < 0:                             # 落後太多（剛重連）：從現在重新起算
        nxt, wait = time.ticks_ms(), 0
    time.sleep_ms(wait)
