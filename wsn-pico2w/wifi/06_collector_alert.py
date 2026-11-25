# 06_collector_alert.py：超過門檻就亮紅燈、嗶兩聲；太久沒收到資料亮黃燈
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
from machine import Pin, I2C, PWM
import socket, time, json, ssd1306, cfg

T_HIGH = 30          # 溫度超過幾度要警示
SOIL_LOW = 30        # 土壤低於幾 % 要警示
STALE = 6            # 幾秒沒收到資料，就算節點斷線

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
leds = [PWM(Pin(p)) for p in (6, 7, 8)]
for led in leds:
    led.freq(1000)
buzzer = Pin(11, Pin.OUT, value=0)
COLORS = {"OK": (0, 255, 0), "ALERT": (255, 0, 0), "NO DATA": (255, 160, 0)}


def color(r, g, b):
    for led, v in zip(leds, (r, g, b)):
        led.duty_u16(v * 257)


def beep(times=2):
    for i in range(times):
        buzzer.value(1)
        time.sleep_ms(120)
        buzzer.value(0)
        time.sleep_ms(120)


def show(title, lines):
    oled.fill(0)
    oled.text(title, 0, 4)
    for i, t in enumerate(lines):
        oled.text(t, 0, 20 + i * 11)
    oled.show()


ap = cfg.start_ap()                 # 開 Wi-Fi：和練習 3 一樣，寫在 cfg.py 裡

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.PORT))
s.settimeout(1)                     # 最多等 1 秒，等不到就去檢查有沒有斷線
last = time.time()
state = ""
while True:
    try:
        data, addr = s.recvfrom(256)
        r = json.loads(data.decode())
        last = time.time()
        hot = r["t"] is not None and r["t"] > T_HIGH
        dry = r["soil"] < SOIL_LOW
        new = "ALERT" if (hot or dry) else "OK"
        why = "HOT " if hot else ""
        why += "DRY" if dry else ""
        print("收到 #%d：%s" % (r["n"], r), new, why)
        show("G%02d #%d %s" % (r["g"], r["n"], new), [
            "T %sC  H %s%%" % (r["t"], r["h"]),
            "Lux  %d" % r["lux"],
            "Soil %d%%" % r["soil"],
            why if why else "all normal",
        ])
    except OSError:                 # 這 1 秒沒收到東西
        if time.time() - last <= STALE:
            continue
        new = "NO DATA"
        gap = time.time() - last
        show("G%02d NO DATA" % cfg.GROUP,
             ["%d s no packet" % gap, "check node"])
    if new != state:                # 狀態改變才換燈、才嗶
        color(*COLORS[new])
        if new == "ALERT":
            beep(2)
        state = new
