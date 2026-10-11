import myid                      # 身份指紋（B 板：量 A、供電給 A）
import cfg
import network, socket, time, array
from machine import Pin, I2C
import ina219

NAMES = ("0 開機閒置", "1 Wi-Fi 連線中", "2 A 基準（LED 亮、空轉）", "3 B 關 LED",
         "4 連上閒置 PERFORMANCE", "5 連上閒置 POWERSAVE", "6 連上閒置 NONE",
         "7 UDP 傳送", "8 C 關無線（空轉）", "9 D 降頻 48 MHz", "10 BLE 100 ms",
         "11 BLE 1000 ms", "12 E lightsleep", "13 F deepsleep", "14 深睡醒來")
ap = network.WLAN(network.AP_IF)               # B 開 AP，給 A 連
ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
ap.active(True)
u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
u.bind(("0.0.0.0", cfg.UDP_PORT))
u.setblocking(False)                           # 沒封包時馬上回來，不卡住量測
i2c = I2C(0, sda=Pin(cfg.SDA), scl=Pin(cfg.SCL), freq=400_000)
ina = ina219.INA219(i2c, cfg.ZERO_MA)
go = Pin(cfg.GO_PIN, Pin.OUT, value=0)         # 開始線：先放低，A 會等
n = 0; pkts = 0                                # n＝A 送來幾個脈衝＝A 在第幾段


def poll_udp():                  # 收 A 的 UDP：指紋印出來，資料包只數數量
    global pkts
    try:
        msg = u.recv(256)
        if msg[0] == 120:                      # b"x" 開頭：一般資料包
            pkts += 1
        else:
            print("收到 A 的指紋：", msg.decode())
    except OSError:
        pass


def pulse(p):                    # 標記線每來一個脈衝（上升緣），n 加 1
    global n
    n += 1


Pin(cfg.MARK_PIN, Pin.IN, Pin.PULL_DOWN).irq(pulse, Pin.IRQ_RISING)
raw = [array.array("h") for _ in NAMES]        # 每一段的原始讀值
volt = [0.0] * len(NAMES); sec = [0.0] * len(NAMES)
cur = 0; t0 = t_ph = time.ticks_ms()
print("先量 5 秒開機閒置，再叫 A 開始")
while cur < len(NAMES):
    now = time.ticks_ms()
    if cur == 0 and time.ticks_diff(now, t0) > 5000:
        go.on()                                # 開始線拉高：A 開始跑
    if n != cur:                               # A 換段了：結算上一段的秒數
        sec[cur] = time.ticks_diff(now, t_ph) / 1000; t_ph = now
        cur = n
        if cur < len(NAMES):
            print("→", NAMES[cur])
        continue
    if time.ticks_diff(now, t_ph) > 40000:
        print("40 秒沒收到 A 的標記：檢查標記線、A 的 main.py"); break
    raw[cur].append(ina.shunt_raw()); volt[cur] += ina.bus_v()   # 記在這一段
    poll_udp(); time.sleep_ms(10)

go.off()
print("B 收到 A 的 UDP 資料包：", pkts)
print("秒數  平均mA  中位數  最大mA  電壓V  段")
f = open("w13_phases.csv", "w")
f.write("段,秒數,平均mA,中位數mA,最大mA,電壓V\n")
for k in range(len(NAMES)):
    d = sorted(raw[k]); m = len(d)
    if m == 0:
        continue
    avg, med, top = ina.ma(sum(d) / m), ina.ma(d[m // 2]), ina.ma(d[-1])
    r = (sec[k], avg, med, top, volt[k] / m)
    print("%4.1f %7.1f %7.1f %7.1f %6.2f " % r, NAMES[k])
    f.write("%s,%.1f,%.2f,%.1f,%.1f,%.3f\n" % ((NAMES[k],) + r))
f.close()
