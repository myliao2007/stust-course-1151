# wifi.py — 之後每一週都會 import 這支，先寫好存進板子
import network, time

def connect(ssid, pwd, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, pwd)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            dt = time.ticks_diff(time.ticks_ms(), t0)
            if dt > timeout * 1000:
                raise RuntimeError('Wi-Fi 連線逾時')
            time.sleep(0.5)
    return wlan.ifconfig()   # (IP, 遮罩, 閘道, DNS)
