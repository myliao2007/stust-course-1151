# 03_collector_ap.py：收集端自己開 Wi-Fi（AP），用 UDP 收節點送來的資料
import myid                      # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
import network, socket, time, cfg

network.WLAN(network.STA_IF).active(False)   # 收集端不用連別人，先關掉
ap = network.WLAN(network.AP_IF)
ap.config(essid=cfg.AP_SSID, password=cfg.AP_PASS)
ap.active(True)
while not ap.active():
    time.sleep(0.1)
print("收集端的 Wi-Fi 開好了：", cfg.AP_SSID)
print("收集端的 IP：", ap.ifconfig()[0])

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.PORT))
print("在埠號", cfg.PORT, "等節點的資料…")
while True:
    data, addr = s.recvfrom(256)
    print("收到", addr[0], "：", data.decode())
