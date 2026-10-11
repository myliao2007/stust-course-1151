import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號、週期…）
# node_a.py（A 板＝感測節點）：開 AP 給 B 連；每 PERIOD_MS 讀一次、換一次廣播；隨時收 B 的回報
import network, socket, bluetooth, time, json
import sensors, packet

ap = network.WLAN(network.AP_IF)             # 1. 開自己組的 AP（主題 3）
ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
ap.active(True)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.PORT))                # 2. 收 B 的 UDP 回報
s.setblocking(False)                         #    沒有回報時不要卡住
ble = bluetooth.BLE()                        # 3. BLE 廣播（主題 6）
ble.active(True)
sensors.init()                               # 4. 感測器（主題 2）
print("A 的 IP", ap.ifconfig()[0], "| 廣播", cfg.BLE_NAME, "每", cfg.ADV_MS, "ms")

seq, nxt = 0, time.ticks_ms()
while True:
    if time.ticks_diff(time.ticks_ms(), nxt) >= 0:    # 到點了才讀值、換廣播
        d = sensors.read_all()
        p = packet.pack(cfg.MFG_ID, cfg.GROUP, seq, d, cfg.BLE_NAME)
        ble.gap_advertise(cfg.ADV_MS * 1000, adv_data=p, connectable=False)
        if seq % 10 == 0:
            print("seq %d 已送出" % seq, d)
        seq += 1
        nxt = time.ticks_add(nxt, cfg.PERIOD_MS)      # 從「上一次該到的時間」往後排
    try:
        msg, addr = s.recvfrom(256)                   # 沒有回報會丟 OSError
        r = json.loads(msg)
        print("B 回報 #%d：實收 %d／應收 %d，遺失率 %.1f %%，RSSI %s" % (
            r["n"], r["got"], r["exp"], r["loss"], r["rssi"]))
    except (OSError, ValueError, KeyError):
        pass
    time.sleep_ms(5)                         # 只是讓出 CPU 一下，週期由 ticks 決定
