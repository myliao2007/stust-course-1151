# aio_cfg.py：Adafruit IO 練習的設定。只要改最上面三行
GROUP = 5                                    # ← 改成你們的組號
AIO_USER = "your_username"                   # ← Adafruit IO 的 Username（大小寫要一樣）
AIO_KEY = "aio_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"   # ← Adafruit IO 的 Key：等於密碼，不要給別組看

HOTSPOT_SSID = "WSN-G%02d" % GROUP           # 手機熱點名稱：第 5 組是 WSN-G05
HOTSPOT_PASS = "wsnpico%02d" % GROUP         # 手機熱點密碼：第 5 組是 wsnpico05
SERVER = "io.adafruit.com"                   # Adafruit IO 的 MQTT 伺服器
PORT = 1883                                  # 課堂用 1883（不加密）；正式作品改用 8883（加密）


def topic(feed):
    # feed 的 MQTT 主題：「使用者名稱/feeds/feed 名稱」
    return AIO_USER + "/feeds/" + feed


def send(c, feed, value):
    # 把一個數值送到某個 feed（數字先轉成文字）
    c.publish(topic(feed), str(value))


def connect_wifi():
    # 連上手機熱點；已經連上就直接用
    import network, time
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("連線到", HOTSPOT_SSID, "…")
        wlan.connect(HOTSPOT_SSID, HOTSPOT_PASS)
        for i in range(20):
            if wlan.isconnected() or wlan.status() < 0:
                break
            time.sleep(1)
    if not wlan.isconnected():
        raise RuntimeError("連不上熱點，status = %d" % wlan.status())
    print("熱點連上了，IP：", wlan.ifconfig()[0])
    return wlan


def connect_aio(callback=None):
    # 連上 Adafruit IO：帳號是 Username、密碼是 Key
    from umqtt.simple import MQTTClient
    import myid
    c = MQTTClient("pico-" + myid.SN, SERVER, port=PORT,
                   user=AIO_USER, password=AIO_KEY, keepalive=60)
    if callback:
        c.set_callback(callback)
    try:
        c.connect()
    except Exception as e:
        print("Adafruit IO 連不上：", e)
        print("4 或 5：Username 或 Key 打錯；-2：手機沒有網路")
        raise
    print("Adafruit IO 連上了，使用者：", AIO_USER)
    return c
