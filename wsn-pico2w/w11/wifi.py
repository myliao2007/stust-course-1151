# wifi.py：連教室 Wi-Fi 的小工具（給本主題各支程式匯入；兩片板子都要存）
import network, time, rp2
import cfg
wlan = network.WLAN(network.STA_IF)


def connect(ssid=cfg.WIFI_SSID, pw=cfg.WIFI_PASS, timeout=20):
    """已經連上就直接回傳；沒連上就連，逾時丟 OSError（讓呼叫的程式接住再試）。
    回傳 ifconfig()：(IP, 遮罩, 閘道, DNS)。"""
    rp2.country("TW")
    wlan.active(True)
    wlan.config(pm=0xa11140)          # 關掉 Wi-Fi 省電，指令延遲比較短（耗電主題 13 再談）
    if not wlan.isconnected():
        wlan.connect(ssid, pw)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout * 1000:
                raise OSError("Wi-Fi 連不上，status=%d" % wlan.status())
            time.sleep(0.5)
    return wlan.ifconfig()
