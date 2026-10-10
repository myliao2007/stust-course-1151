import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import network, rp2, time

rp2.country("TW")        # 設定法規區域，影響可用通道
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
time.sleep(1)

for ap in wlan.scan():
    ssid, bssid, ch, rssi, sec, hidden = ap
    name = ssid.decode() or "(隱藏 SSID)"
    print("{:<20} ch={:<3} RSSI={} dBm".format(name, ch, rssi))

# 第二段：只看自己組 A 板的 AP，掃 10 次取平均
vals = []
for i in range(10):
    for ap in wlan.scan():
        if ap[0].decode() == cfg.SSID:
            vals.append(ap[3])
    time.sleep(1)
if vals:
    avg = sum(vals) / len(vals)
    print(cfg.SSID, "掃到", len(vals), "次，平均 RSSI = %.1f dBm" % avg)
else:
    print("掃不到", cfg.SSID, "：A 板的 ap_a.py 有在跑嗎？")
