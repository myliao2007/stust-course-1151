GROUP = 5                               # ← 第 1 行：改成你們的組號
SSID = "你的手機熱點名稱"                # ← 第 2 行：手機熱點的名稱，照手機上顯示的抄（練習 2 用）
PASSWORD = "你的熱點密碼"                # ← 第 3 行：手機熱點的密碼（練習 2 用）

# ---- cfg.py 是全組共用的設定，兩片板子都存一份（組號要一樣）。下面自動算出來，不用改 ----
AP_SSID = "PicoAP-G%02d" % GROUP        # 收集端自己開的 Wi-Fi 名稱
AP_PASS = "wsnpico%02d" % GROUP         # 收集端 Wi-Fi 密碼（第 5 組是 wsnpico05）
COLLECTOR_IP = "192.168.4.1"            # 收集端開 AP 時，自己的 IP 固定是這個
PORT = 5000 + GROUP                     # UDP 埠號（第 5 組是 5005）


def start_ap():
    """收集端開自己的 Wi-Fi（練習 5～7 共用，內容和練習 3 一樣）。"""
    import network, time
    network.WLAN(network.STA_IF).active(False)      # 收集端不用連別人，關掉
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=AP_SSID, password=AP_PASS)
    ap.active(True)
    while not ap.active():
        time.sleep(0.1)
    print("收集端 Wi-Fi：", AP_SSID, "　IP：", ap.ifconfig()[0], "　埠號：", PORT)
    return ap
