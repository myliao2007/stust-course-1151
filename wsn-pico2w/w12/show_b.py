import myid                                  # 身份指紋（第一行）
import cfg                                   # 本組參數
# show_b.py（B 板＝節點端顯示＋告警）：訂閱 A 的資料，OLED 顯示最新值與資料新鮮度；
# 超過門檻 GP15 的 LED 亮、太久沒更新或 A 斷線 LED 閃。OLED 接 I2C0（GP4、GP5），位址 0x3C
from wifi import connect
from umqtt.simple import MQTTClient
from machine import Pin, I2C
from alarm import Alarm, state
import ssd1306, time, json

oled = ssd1306.SSD1306_I2C(128, 64, I2C(0, sda=Pin(4), scl=Pin(5), freq=400000))
led = Pin(15, Pin.OUT)                        # 告警 LED：GP15（第 20 腳）→ 220Ω → LED → GND
al = Alarm(cfg.T_HIGH)                        # 門檻可以從儀表板改
last, got_ms, a_st = None, None, "?"          # 最後一筆資料、B 收到它的時間、A 的狀態

def on_msg(topic, msg):
    global last, got_ms, a_st
    topic = topic.decode()
    if topic == cfg.DATA_A:
        try:
            last = json.loads(msg)
        except ValueError:                   # 壞掉的 JSON：不要用
            return
        got_ms = time.ticks_ms()             # 新鮮度用 B 自己的時鐘算
        if al.update(last.get("t")):
            print("告警狀態改變：", "超標" if al.on else "解除", last.get("t"))
    elif topic == cfg.ST_A:
        a_st = msg.decode()
        print("A 的狀態：", a_st)
    elif topic == cfg.TH_B:
        al.high = float(msg)
        print("門檻改成", al.high)

def start():
    connect(cfg.SSID, cfg.PASSWORD)
    m = MQTTClient(cfg.CID_B, cfg.BROKER, keepalive=cfg.KEEPALIVE)
    m.set_callback(on_msg)
    m.set_last_will(cfg.ST_B, "offline", retain=True)
    m.connect()
    m.publish(cfg.ST_B, "online", retain=True)
    for tp in (cfg.DATA_A, cfg.ST_A, cfg.TH_B):
        m.subscribe(tp)
    return m

def f1(v):                                   # 缺值顯示 --，不要顯示 0
    return "--" if v is None else "%.1f" % v

def draw(txt):
    oled.fill(0)
    if last is None:
        oled.text("wait " + cfg.NODE_A, 0, 0)
    else:
        oled.text("%s #%d" % (last.get("id"), last.get("seq", 0)), 0, 0)
        oled.text("T %s  th %.1f" % (f1(last.get("t")), al.high), 0, 12)
        oled.text("H %s %%" % f1(last.get("h")), 0, 22)
        oled.text("P %s hPa" % f1(last.get("p")), 0, 32)
        oled.text("L %s lx" % f1(last.get("lux")), 0, 42)
    oled.text(txt, 0, 56)                    # 最下面一行：狀態
    oled.show()

c = start()
ping_ms, k, shown = time.ticks_ms(), 0, ""
while True:
    try:
        while c.check_msg() is not None:     # 一次把等著的訊息都處理完
            pass
        if time.ticks_diff(time.ticks_ms(), ping_ms) > cfg.KEEPALIVE * 500:
            c.ping()                         # B 只收不送：每 30 秒 ping 一次，broker 才不會踢掉
            ping_ms = time.ticks_ms()
    except OSError as e:
        print("斷線，重連中：", e)
        time.sleep(2)
        try:
            c = start()
        except OSError:
            pass
    age = None if got_ms is None else time.ticks_diff(time.ticks_ms(), got_ms) // 1000
    txt, mode = state(age, cfg.STALE_S, a_st, al.on)
    led.value(1 if mode == 1 else (k % 2 if mode == 2 else 0))   # 2＝閃
    draw(txt)
    if txt.split()[0] != shown:              # 狀態換了才印，Shell 不會洗版
        shown = txt.split()[0]
        print("OLED：", txt)
    k += 1
    time.sleep_ms(500)
