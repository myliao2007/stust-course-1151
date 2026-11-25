# 04_node_send.py：感測節點連上收集端的 Wi-Fi，每隔幾秒用 UDP 送一筆資料
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, ADC
import network, socket, time, json, dht, cfg

DRY, WET = 50000, 20000      # 改成練習 1 量到的乾、濕讀值
INTERVAL = 2                 # 幾秒送一筆（練習 7 可以改成 1）

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
i2c.writeto(0x23, b"\x01")
i2c.writeto(0x23, b"\x10")
d = dht.DHT11(Pin(15))
soil = ADC(26)


def read_all():
    try:
        d.measure()
        t, h = d.temperature(), d.humidity()
    except OSError:
        t, h = None, None            # DHT11 偶爾讀失敗，這筆送 null
    b = i2c.readfrom(0x23, 2)
    lux = round((b[0] << 8 | b[1]) / 1.2)
    raw = soil.read_u16()
    pct = (DRY - raw) * 100 // (DRY - WET)
    return t, h, lux, max(0, min(100, pct))


wlan = network.WLAN(network.STA_IF)
wlan.active(True)


def join():
    wlan.connect(cfg.AP_SSID, cfg.AP_PASS)
    while not wlan.isconnected():
        print("連線中… status =", wlan.status())
        time.sleep(1)
    print("連上收集端了，我的 IP：", wlan.ifconfig()[0])


join()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = (cfg.COLLECTOR_IP, cfg.PORT)          # 收件地址：192.168.4.1、5005
n = 0
while True:
    if not wlan.isconnected():       # 走太遠斷線了：回來之後自動重連
        join()
    n += 1
    t, h, lux, sp = read_all()
    data = {"g": cfg.GROUP, "n": n, "t": t, "h": h,
            "lux": lux, "soil": sp,
            "rssi": wlan.status("rssi")}
    msg = json.dumps(data)           # 變成一行 JSON 文字
    try:
        s.sendto(msg.encode(), addr)
        print("送出第", n, "筆：", msg)
    except OSError as e:
        print("第", n, "筆送不出去：", e)
    time.sleep(INTERVAL)
