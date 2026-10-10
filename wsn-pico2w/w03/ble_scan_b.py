import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import bluetooth, time
TARGET = b"wsn-g%02d-A" % cfg.GROUP   # 自己組 A 板的廣播名稱
rssi = []

def adv_name(adv):                 # 從廣播資料找出 0x09 完整名稱
    i = 0
    while i + 1 < len(adv):
        n, t = adv[i], adv[i + 1]  # 每一段：長度、型別、內容
        if t == 0x09:
            return bytes(adv[i + 2:i + 1 + n])
        i += 1 + n
def irq(event, data):              # 5＝掃到一筆；data[3]＝RSSI
    if event == 5 and adv_name(data[4]) == TARGET:
        rssi.append(data[3])
ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq)
ble.gap_scan(10000, 30000, 30000)  # 被動掃描 10 秒
time.sleep(11)
avg = sum(rssi) / max(len(rssi), 1)
print(TARGET.decode(), "收到", len(rssi), "次，平均 RSSI %.1f dBm" % avg)
