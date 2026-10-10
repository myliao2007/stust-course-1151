import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import network, time
from machine import Pin
led = Pin(15, Pin.OUT)             # GP15 接 LED：有 B 連上就亮（選做）

def up():                          # 開自己組的 AP，回傳 AP 物件
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
    ap.active(True)
    while not ap.active():
        time.sleep_ms(100)
    print("AP 已開：", cfg.SSID, "頻道", ap.config("channel"))
    print("A 的 IP：", ap.ifconfig()[0])
    return ap

if __name__ == "__main__":         # 直接執行時：每 2 秒看有幾台連上
    ap = up()
    while True:
        n = len(ap.status("stations"))
        led.value(1 if n else 0)
        print("連上的裝置：", n)
        time.sleep(2)
