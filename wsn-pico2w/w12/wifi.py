# wifi.py：連上教室 Wi-Fi（A、B 兩片都要存）；回傳 (IP, 遮罩, 閘道, DNS)
import network, rp2, time


def connect(ssid, password, timeout_s=15):
    rp2.country("TW")                        # 台灣的無線電規範，要在打開無線晶片之前設定
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
                raise OSError("Wi-Fi 連不上，status = %d" % wlan.status())
            time.sleep_ms(200)
    return wlan.ifconfig()
