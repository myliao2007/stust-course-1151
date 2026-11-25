# 02_hotspot.py：連上手機熱點，印出 IP 和訊號強度，再安裝 MQTT 函式庫 umqtt.simple
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
import network, time, aio_cfg

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("附近的 Wi-Fi（訊號最強的 5 個）：")
nets = wlan.scan()
nets.sort(key=lambda x: x[3], reverse=True)   # 照 RSSI 由強到弱排
for ssid, bssid, ch, rssi, sec, hidden in nets[:5]:
    try:
        name = ssid.decode()
    except Exception:
        name = "(看不懂的名稱)"
    print("  %-18s 頻道 %2d　RSSI %d dBm"
          % (name, ch, rssi))

print("連線到", aio_cfg.SSID, "…")
wlan.connect(aio_cfg.SSID, aio_cfg.PASSWORD)
for i in range(20):
    st = wlan.status()
    if st == 3 or st < 0:
        break
    print("  等待中… status =", st)
    time.sleep(1)

MSG = {3: "連上了！", -1: "連線失敗，再試一次",
       -2: "找不到熱點：名稱打錯，或開成 5 GHz",
       -3: "密碼錯誤"}
st = wlan.status()
print("status =", st, MSG.get(st, "逾時：檢查熱點有沒有開"))
if wlan.isconnected():
    print("我的 IP 位址：", wlan.ifconfig()[0])
    print("訊號強度 RSSI：", wlan.status("rssi"), "dBm")
    import mip
    mip.install("umqtt.simple")  # 從網路下載 MQTT 函式庫，存進板子的 /lib
    print("umqtt.simple 裝好了")
