# wifi.py：連上可以上網的 Wi-Fi（任務三用；主題 11 用過同名的 connect）
import network, time

def connect(ssid, pwd, timeout=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, pwd)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout * 1000:
                raise OSError("Wi-Fi 連不上，status=%d" % wlan.status())
            time.sleep(0.5)
    print("Wi-Fi 已連上", ssid, "IP", wlan.ifconfig()[0])
    return wlan
