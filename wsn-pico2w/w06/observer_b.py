import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（組號…）
import bluetooth, time
from adtool import split_ad, mine, TYPE, PDU
got = []                # 自己組 A 的封包

def irq(event, data):
    if event == 5:      # 5＝掃到一筆廣播
        addr_type, addr, adv_type, rssi, adv = data
        if mine(split_ad(adv), cfg.GROUP):
            got.append((adv_type, rssi, bytes(adv)))

ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq)
ble.gap_scan(10000, 30000, 30000)   # 被動掃描 10 秒
time.sleep(11)                      # 掃描窗＝間隔：一直聽
if not got:
    print("沒收到第", cfg.GROUP, "組 A 的廣播")
else:
    adv_type, rssi, adv = got[-1]
    print(PDU[adv_type], "共", len(adv), "位元組")
    print(adv.hex(" "))
    for t, d in split_ad(adv):      # 一段一列
        head = "%02X %02X" % (len(d) + 1, t)
        print(head, TYPE.get(t), d.hex(" "))
    avg = sum(g[1] for g in got) / len(got)
    print("收到", len(got), "次，平均 RSSI %.1f dBm" % avg)
