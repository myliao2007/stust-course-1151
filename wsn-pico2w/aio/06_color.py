# 06_color.py：挑戰。調色盤（Color Picker）選 LED 顏色；溫度太高自動變紅燈
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, PWM
import dht, time, aio_cfg

INTERVAL = 10
T_HIGH = 30                      # 溫度到這裡就變紅燈；測試時可以改成比室溫低一點

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
i2c.writeto(0x23, b"\x01")
i2c.writeto(0x23, b"\x10")
d = dht.DHT11(Pin(15))
leds = [PWM(Pin(p)) for p in (6, 7, 8)]
for led in leds:
    led.freq(1000)

state = {"on": False, "rgb": (255, 255, 255), "hot": False}


def color(r, g, b):
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)


def show():                      # 照目前的狀態決定燈的顏色
    if state["hot"]:
        color(255, 0, 0)         # 太熱：一律紅燈
    elif state["on"]:
        color(*state["rgb"])     # 開著：調色盤選的顏色
    else:
        color(0, 0, 0)


def read_all():
    try:
        d.measure()
    except OSError:
        return None              # DHT11 偶爾讀失敗，這一輪跳過
    b = i2c.readfrom(0x23, 2)
    lux = round((b[0] << 8 | b[1]) / 1.2)
    return d.temperature(), d.humidity(), lux


def on_msg(topic, msg):
    topic, msg = topic.decode(), msg.decode()
    print("收到", topic, "=", msg)
    if topic.endswith("/led"):
        state["on"] = msg.upper() in ("ON", "1")
    elif topic.endswith("/color"):
        hx = msg.lstrip("#")     # "#FF8800" → "FF8800"
        try:
            state["rgb"] = (int(hx[0:2], 16),
                            int(hx[2:4], 16),
                            int(hx[4:6], 16))
        except ValueError:
            print("看不懂的顏色：", msg)
    elif topic.endswith("/throttle"):
        print("注意：送太快了！", msg)
    show()


def upload(c):                   # 讀感測器，上傳三個 feed
    v = read_all()
    if v:
        aio_cfg.send(c, "temperature", v[0])
        aio_cfg.send(c, "humidity", v[1])
        aio_cfg.send(c, "light", v[2])
        print("上傳：%d °C　%d %%　%d lux" % v)
    return v


def check_hot(t):                # 溫度跨過門檻的那一刻才換燈
    hot = t >= T_HIGH
    if hot != state["hot"]:
        print("太熱了，紅燈！" if hot else "溫度回來了")
        state["hot"] = hot
        show()


def start():
    aio_cfg.connect_wifi()
    c = aio_cfg.connect_aio(on_msg)
    for f in ("led", "color"):   # 訂閱開關和調色盤，再要一次現在的值
        c.subscribe(aio_cfg.topic(f))
        c.publish(aio_cfg.topic(f) + "/get", "")
    c.subscribe(aio_cfg.AIO_USER + "/throttle")
    print("等儀表板的開關和調色盤…")
    return c


c = start()
last = time.time() - INTERVAL
while True:
    try:
        c.check_msg()
        if time.time() - last >= INTERVAL:
            last = time.time()
            v = upload(c)
            if v:
                check_hot(v[0])
    except OSError:
        print("連線斷了，重新連線…")
        time.sleep(2)
        c = start()
    time.sleep_ms(100)
