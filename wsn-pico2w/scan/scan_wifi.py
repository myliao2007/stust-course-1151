# scan_wifi.py：Pico 2 W 每 5 秒掃描一次附近的 Wi-Fi，列出名稱、訊號強度、頻道和加密方式
import myid                         # 第一行：印出身份指紋（組長學號｜板子序號｜MAC）
import network, binascii, time

GROUP = "Group-99"                  # ← 改成你的組別，第 1 組就是 Group-01
PHONE = "my-phone"                  # ← 練習 2：你手機熱點的名稱（SSID）
PASSWORD = "12345678"               # ← 練習 2：你手機熱點的密碼
HEAD = "Nr | %-24s | RSSI | CH | Encryption" % "SSID"     # 表頭：SSID 欄寬 24 個字

wlan = network.WLAN(network.STA_IF)     # 將 Wi-Fi 設成 Station 模式
wlan.active(True)                       # 打開 Wi-Fi 晶片
wlan.disconnect()                       # 先不連任何熱點，專心掃描
time.sleep(0.1)
print("Setup done")


def sec_name(code):
    # Pico 回報的加密編號：1＝有加密、2＝WPA、4＝WPA2，有幾種就加起來
    if code == 0:
        return "open"
    if code & 4 and code & 2:
        return "WPA+WPA2"
    if code & 4:
        return "WPA2"
    if code & 2:
        return "WPA"
    return "WEP"


def show(i, n):
    # 印出一台基地台：Nr｜SSID｜RSSI｜CH｜加密方式
    try:
        ssid = n[0].replace(b"\x00", b"").decode()   # 拿掉空字元
    except Exception:
        ssid = "?"                      # 名稱裡有看不懂的字
    if ssid == "":
        ssid = "(hidden)"               # 不公開名稱的基地台
    print("%2d | %-24s | %4d | %2d | %s"
          % (i, ssid, n[3], n[2], sec_name(n[4])))


def connect_phone():
    # 練習 2：用 PHONE 和 PASSWORD 連上手機熱點，最多等 10 秒
    wlan.connect(PHONE, PASSWORD)
    for t in range(10):
        if wlan.isconnected():
            return
        time.sleep(1)


def my_phone(nets):
    # 練習 2：找到你的熱點，印出 RSSI；連上了再印 IP
    for n in nets:
        if n[0] == PHONE.encode():      # 名稱跟 PHONE 一樣
            if not wlan.isconnected():
                connect_phone()
            if wlan.isconnected():
                state = "| IP " + wlan.ifconfig()[0]
            else:
                state = "| not connected"
            print("My phone:", PHONE, "| RSSI", n[3], state)
            return
    print("My phone:", PHONE, "| not found")


while True:
    mac = binascii.hexlify(wlan.config("mac"), ":")
    print("Scan start:", GROUP)
    print(mac.decode().upper())
    nets = wlan.scan()                  # 掃描 Wi-Fi，回傳找到的清單
    print("Scan done")
    if len(nets) == 0:
        print("no networks found")
    else:
        nets.sort(key=lambda n: n[3], reverse=True)    # 照 RSSI 由強到弱排
        print(len(nets), "networks found")
        print(HEAD)
        for i, n in enumerate(nets):    # 列印每一個 AP 的資訊
            show(i + 1, n)
        my_phone(nets)                  # 練習 2：你的熱點收到多強
    print()                             # 空行
    time.sleep(5)                       # 每 5 秒再掃一次
