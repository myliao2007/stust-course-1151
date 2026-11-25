# 05_led.py：儀表板的開關（Toggle）控制 RGB LED，同時每 10 秒上傳感測值
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, PWM
import dht, time, aio_cfg

INTERVAL = 10

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
i2c.writeto(0x23, b"\x01")
i2c.writeto(0x23, b"\x10")
d = dht.DHT11(Pin(15))
leds = [PWM(Pin(p)) for p in (6, 7, 8)]
for led in leds:
    led.freq(1000)


def color(r, g, b):
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)


def read_all():
    try:
        d.measure()
    except OSError:
        return None              # DHT11 偶爾讀失敗，這一輪跳過
    b = i2c.readfrom(0x23, 2)
    lux = round((b[0] << 8 | b[1]) / 1.2)
    return d.temperature(), d.humidity(), lux


def on_msg(topic, msg):          # 收到訂閱的訊息，就會自動呼叫這個函式
    topic, msg = topic.decode(), msg.decode()
    print("收到", topic, "=", msg)
    if topic.endswith("/led"):
        if msg.upper() in ("ON", "1"):
            color(255, 255, 255)     # 開：三色全亮，白光
        else:
            color(0, 0, 0)           # 關：熄滅
    elif topic.endswith("/throttle"):
        print("注意：送太快了！", msg)


def upload(c):                   # 讀感測器，上傳三個 feed
    v = read_all()
    if v:
        aio_cfg.send(c, "temperature", v[0])
        aio_cfg.send(c, "humidity", v[1])
        aio_cfg.send(c, "light", v[2])
        print("上傳：%d °C　%d %%　%d lux" % v)
    return v


def start():                     # 連熱點、連 Adafruit IO、訂閱
    aio_cfg.connect_wifi()
    c = aio_cfg.connect_aio(on_msg)
    c.subscribe(aio_cfg.topic("led"))             # 訂閱 led：儀表板一按就收到
    c.subscribe(aio_cfg.AIO_USER + "/throttle")   # 訂閱 throttle：送太快會收到警告
    c.publish(aio_cfg.topic("led") + "/get", "")  # 請伺服器把 led 現在的值送過來
    print("等儀表板的開關…")
    return c


c = start()
last = time.time() - INTERVAL    # 讓第一次馬上送
while True:
    try:
        c.check_msg()            # 有新訊息就交給 on_msg；沒有就馬上往下走
        if time.time() - last >= INTERVAL:
            last = time.time()
            upload(c)
    except OSError:
        print("連線斷了，重新連線…")
        time.sleep(2)
        c = start()
    time.sleep_ms(100)
