import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號、每輪幾秒…）
# gw_b.py（B 板＝閘道）：一個無線電輪流做兩件事——掃 BLE 收 A 的廣播 ROUND_MS，掃完用 Wi-Fi UDP 回報給 A
import network, socket, bluetooth, time
import packet
try:
    import show                    # 選做：OLED（show.py、ssd1306.py 都存到 B 板，接好 OLED 才會用）
except (ImportError, OSError):
    show = None

wlan = network.WLAN(network.STA_IF)


def wifi_up():                     # 連自己組 A 的 AP（主題 3）；回傳 A 的 IP
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(cfg.SSID, cfg.PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > 15000:
                raise OSError("連不上 %s，status=%d" % (cfg.SSID, wlan.status()))
            time.sleep_ms(200)
    return wlan.ifconfig()[2]      # 閘道就是 A


A_IP = wifi_up()
print("已連上", cfg.SSID, "| A 的 IP", A_IP)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
roll = packet.Loss()               # 從頭到現在的點名簿
rnd = {"pk": 0, "rs": 0, "last": None, "done": False}   # 這一輪的統計


def irq(event, data):
    if event == 5:                 # 5＝掃到一筆
        d = packet.unpack(data[4], cfg.MFG_ID, cfg.GROUP)
        if d:
            rnd["pk"] += 1
            rnd["rs"] += data[3]
            if roll.add(d["seq"]):
                rnd["last"] = d
    elif event == 6:               # 6＝這一輪掃描結束
        rnd["done"] = True


ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq)
n = 0
while True:
    n += 1
    rnd["pk"], rnd["rs"], rnd["done"] = 0, 0, False
    t1 = time.ticks_ms()
    ble.gap_scan(cfg.ROUND_MS, 30000, 30000)   # 時槽一：只聽 BLE
    while not rnd["done"] and time.ticks_diff(time.ticks_ms(), t1) < cfg.ROUND_MS + 2000:
        time.sleep_ms(20)                      # B 插 USB 當閘道，等掃描結束
    t2 = time.ticks_ms()
    rssi = round(rnd["rs"] / rnd["pk"]) if rnd["pk"] else None
    msg = packet.report(cfg.GROUP, n, rnd["last"], rssi, roll)
    try:                                       # 時槽二：Wi-Fi 回報
        A_IP = wifi_up()
        s.sendto(msg.encode(), (A_IP, cfg.PORT))
    except OSError as e:
        print("回報失敗：", e)
    t3 = time.ticks_ms()
    print(msg)
    print("  第 %d 輪：掃描 %d ms、回報 %d ms、%d 位元組、封包 %d 個" % (
        n, time.ticks_diff(t2, t1), time.ticks_diff(t3, t2), len(msg), rnd["pk"]))
    if roll.rate() > cfg.LOSS_WARN:
        print("  ⚠ 遺失率超過 %.0f %%" % cfg.LOSS_WARN)
    if show:
        show.draw(n, rnd["last"], roll, cfg.LOSS_WARN)
