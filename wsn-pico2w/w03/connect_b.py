import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import network, time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)   # 關閉 Wi-Fi 省電，降低回應延遲
wlan.connect(cfg.SSID, cfg.PASSWORD)   # 連自己組 A 板的 AP

t0 = time.ticks_ms()
while not wlan.isconnected():
    if time.ticks_diff(time.ticks_ms(), t0) > 15000:
        raise RuntimeError("逾時 status=%d" % wlan.status())
    print("status =", wlan.status())
    time.sleep(1)

print("IP 設定：", wlan.ifconfig())
print("RSSI =", wlan.status("rssi"), "dBm")
A_IP = wlan.ifconfig()[2]          # 閘道就是 A 板的 IP
print("status =", wlan.status(), "| A 的 IP：", A_IP)

if __name__ == "__main__":         # 直接執行時：再連讀 10 次 RSSI
    vals = []
    for i in range(10):
        vals.append(wlan.status("rssi"))
        time.sleep(0.5)
    print("10 次平均 RSSI = %.1f dBm" % (sum(vals) / len(vals)))
