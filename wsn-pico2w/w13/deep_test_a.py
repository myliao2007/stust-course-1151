import myid                      # 身份指紋（A 板，存成 main.py）
import cfg
import machine, network, socket, time, os
from machine import Pin

mark = Pin(cfg.MARK_PIN, Pin.OUT, value=0)   # 0＝醒著，睡前拉高
rc = machine.reset_cause()
print('reset_cause =', rc)
# rp2 的 reset_cause 分不出睡醒和一般重開機，所以再看睡前留的旗標檔
woke = "deep.flg" in os.listdir() and rc != machine.PWRON_RESET
if woke:
    os.remove('deep.flg')               # 用完就刪
with open('count.txt', 'a') as f:
    f.write('%s reset_cause=%d\n' % ('深睡醒來' if woke else '一般開機', rc))

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(cfg.SSID, cfg.PASSWORD)        # 醒來連 B 的 AP，送一筆就走
t0 = time.ticks_ms()
while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), t0) < 10000:
    time.sleep_ms(50)
if wlan.isconnected():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(cfg.FP.encode(), (wlan.ifconfig()[2], cfg.UDP_PORT))
    s.close()
wlan.disconnect()
wlan.active(False)          # 睡之前一定要先關無線

time.sleep(2)               # 留 2 秒讓你來得及中斷程式
open('deep.flg', 'w').close()   # 寫旗標：下次開機才知道是睡醒
mark.on()                   # 告訴 B：開始睡了
machine.deepsleep(cfg.SLEEP_MS)
print('這一行在 rp2 上不會被執行')
