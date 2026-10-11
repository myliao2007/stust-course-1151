import myid                      # 身份指紋（A 板，存成 main.py）
import cfg
import machine, network, socket, bluetooth, time, os
from machine import Pin

mark = Pin(cfg.MARK_PIN, Pin.OUT, value=0)     # 標記線：A 的 GP16 → B 的 GP16
go = Pin(cfg.GO_PIN, Pin.IN, Pin.PULL_DOWN)    # 開始線：B 的 GP17 → A 的 GP17
log = open("a_log.txt", "a")                   # A 沒有 Shell 可看，寫進檔案


def phase(n, what):              # 進入第 n 段：送一個 20 ms 脈衝給 B，並記進檔案
    mark.on(); time.sleep_ms(20); mark.off()
    log.write("%d %s\n" % (n, what)); log.flush()


def busy(ms):                    # CPU 全速空轉 ms 毫秒（不睡）
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < ms:
        pass


rc = machine.reset_cause()
if "deep.flg" in os.listdir() and rc != machine.PWRON_RESET:
    os.remove("deep.flg")        # 有旗標檔、又不是剛上電＝剛從 deepsleep 醒來
    phase(14, "深睡醒來 reset_cause=%d" % rc)
    time.sleep_ms(cfg.SEG_MS)
    phase(15, "結束")
    log.close()
    raise SystemExit

log.write(cfg.FP + "\n")
while go.value() == 0:           # 第 0 段：開機閒置，等 B 拉高開始線
    time.sleep_ms(50)

wlan = network.WLAN(network.STA_IF)
phase(1, "Wi-Fi 連線中")
wlan.active(True)
wlan.connect(cfg.SSID, cfg.PASSWORD)           # 連 B 開的 AP
t0 = time.ticks_ms()
while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), t0) < 15000:
    time.sleep_ms(50)
led = Pin("LED", Pin.OUT)
phase(2, "A 基準：Wi-Fi 連著、LED 亮、CPU 空轉"); led.on(); busy(cfg.SEG_MS)
phase(3, "B 關 LED"); led.off(); busy(cfg.SEG_MS)

for n, pm, what in ((4, wlan.PM_PERFORMANCE, "PERFORMANCE（預設）"),
                    (5, wlan.PM_POWERSAVE, "POWERSAVE"),
                    (6, wlan.PM_NONE, "NONE")):
    wlan.config(pm=pm)           # Wi-Fi 省電模式：CPU 用 sleep_ms 等，不空轉
    phase(n, "連上後閒置 pm=" + what); time.sleep_ms(cfg.SEG_MS)
wlan.config(pm=wlan.PM_PERFORMANCE)

phase(7, "UDP 每 50 ms 送 200 B")
if wlan.isconnected():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    b_ip = wlan.ifconfig()[2]                      # B 開的 AP：閘道就是 B
    s.sendto(cfg.FP.encode(), (b_ip, cfg.UDP_PORT))   # 第一包是 A 的指紋
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < cfg.SEG_MS:
        s.sendto(b"x" * 200, (b_ip, cfg.UDP_PORT))
        time.sleep_ms(50)
    s.close()
else:
    log.write("沒連上 B 的 AP，第 7 段只等待\n"); time.sleep_ms(cfg.SEG_MS)

phase(8, "C 關無線（CPU 空轉）")
wlan.disconnect(); wlan.active(False); busy(cfg.SEG_MS)
phase(9, "D 降頻 48 MHz（CPU 空轉）")
machine.freq(48_000_000); busy(cfg.SEG_MS)
machine.freq(150_000_000)        # 換回預設時脈再開藍牙

ble = bluetooth.BLE()
ble.active(True)
adv = bytes((2, 1, 6, len(cfg.BLE_NAME) + 1, 9)) + cfg.BLE_NAME.encode()
for n, ms in ((10, 100), (11, 1000)):
    ble.gap_advertise(ms * 1000, adv)             # 廣播間隔單位是微秒
    phase(n, "BLE 每 %d ms 廣播" % ms); time.sleep_ms(cfg.SEG_MS)
ble.gap_advertise(None)
ble.active(False)

phase(12, "E lightsleep"); machine.lightsleep(cfg.SEG_MS)
open("deep.flg", "w").close()    # 寫旗標：醒來（重開機）時才知道剛剛是 deepsleep
phase(13, "F deepsleep")
log.close()
machine.deepsleep(cfg.SEG_MS)    # rp2：醒來等同重開機，main.py 從第一行重跑
