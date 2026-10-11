# cfg.py：本主題的組別參數（由 myid 的組號算出來；A、B 兩片都要存，內容不用改）
import myid
GROUP = myid.GROUP
SSID, PASSWORD = "STUST-IoT", "password"     # 教室 Wi-Fi（照主題 11，密碼老師上課公布）
BROKER = "192.168.1.10"                      # 教室電腦上的 Mosquitto（1883 埠）
G = "g%02d" % GROUP                          # 組代號，例如第 7 組＝g07
NODE_A, NODE_B = G + "a", G + "b"            # 節點名：g07a（感測）、g07b（顯示）
ROOM = "stust/ee/e501/"
DATA_A = ROOM + NODE_A + "/data"             # A 發布感測資料（每 5 秒一筆）
ST_A = ROOM + NODE_A + "/status"             # A 的 online／offline（遺囑）
ST_B = ROOM + NODE_B + "/status"             # B 的 online／offline（遺囑）
CMD_A = ROOM + NODE_A + "/cmd"               # 儀表板開關 → A 的板載 LED
TH_B = ROOM + NODE_B + "/th"                 # 儀表板的門檻 → B 的告警門檻
CID_A, CID_B = "wsn-" + NODE_A, "wsn-" + NODE_B   # client id 全班不重複
KEEPALIVE = 60                               # 秒；斷線 1.5 倍（90 秒）後發遺囑
PERIOD_MS = 5000                             # A 每 5 秒送一筆
T_HIGH = 30.0                                # 告警門檻（教室冷就調低，例如現在溫度＋1）
STALE_S = 15                                 # 超過 15 秒沒新資料＝過期（3 筆沒來）
