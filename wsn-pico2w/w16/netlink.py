# netlink.py：Wi-Fi 與 MQTT 的事收在一個模組（A、B 兩片都要存）
# 修正原版：① CONNECT 帶 keepalive，broker 才發現得到節點掉線、代發遺囑
#           ② socket 一律有逾時，網路斷了會丟 OSError，不會卡死到看門狗重開
import network, rp2, time
from umqtt.simple import MQTTClient
import cfg, mysecret, util
wlan = network.WLAN(network.STA_IF)

class SafeClient(MQTTClient):
    def wait_msg(self):        # umqtt.simple 讀完一個封包會把逾時拿掉，這裡補回去
        try:
            return super().wait_msg()
        finally:
            if self.sock:
                self.sock.settimeout(cfg.TIMEOUT)

def wifi_up(timeout_s=10):
    if util.down():
        raise OSError("模擬斷網中")
    rp2.country("TW")
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(mysecret.WIFI_SSID, mysecret.WIFI_PASS)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
                raise OSError("Wi-Fi 連不上，status=%d" % wlan.status())
            util.nap(200)      # 等的時候也餵狗
    return wlan.ifconfig()[0]

def mqtt_up(cid, will, cb, subs):
    wifi_up()
    c = SafeClient(cid, cfg.BROKER, cfg.PORT, keepalive=cfg.KEEPALIVE)
    c.set_callback(cb)
    if will:                   # 遺囑要在 connect 之前交代
        c.set_last_will(will, b"offline", retain=True)
    c.connect(timeout=cfg.TIMEOUT)
    for t in subs:             # clean session：每次重連都要重新訂閱
        util.feed()            # 每一步最多等 5 秒，之間先餵狗
        c.subscribe(t)
    return c
