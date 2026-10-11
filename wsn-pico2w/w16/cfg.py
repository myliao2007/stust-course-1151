# cfg.py：綜合實作（二）的組別參數（由 myid 的組號算出來；A、B 兩片都要存，內容不用改）
import myid
GROUP = myid.GROUP
G = "g%02d" % GROUP                     # 組代號，例：第 7 組＝g07
# ---- A → B：真的 6LoWPAN 訊框，用 Wi-Fi UDP 當無線電（主題 8、10）
PAN = 0x1000 + GROUP                    # PAN ID：第 7 組＝0x1007（同主題 10）
SHORT_A, SHORT_B = 0x0002, 0x0001       # 短位址：A＝感測節點、B＝邊界路由器
PORT_B = 5000 + GROUP                   # B 收訊框的 UDP 埠（分組表）
PORT_A = 5100 + GROUP                   # A 收 B 回的 DIO
BCAST = "255.255.255.255"               # A 找 B：DIS 送給整個網段
GW_IP = None                            # 找不到 B 時，填 B 印出的 IP，例："192.168.1.37"
PERIOD_MS = 5000                        # A 每 5 秒送一筆
# ---- B → 上雲：和主題 12 同一台 broker、同一組主題（儀表板不用改）
BROKER, PORT = "192.168.1.10", 1883     # 教室電腦上的 Mosquitto
ROOM = "stust/ee/e501/"
DATA_A = ROOM + G + "a/data"            # B 代 A 發布感測資料（JSON）
ST_A = ROOM + G + "a/status"            # A 的 online／offline（B 看新鮮度代發）
ST_B = ROOM + G + "b/status"            # B 自己的 online／offline（遺囑）
CID_B = "wsn16-%sb" % G
KEEPALIVE = 60          # 秒；B 失聯 90 秒後 broker 代發 offline
TIMEOUT = 5             # 每次等 broker 最多 5 秒（比看門狗的 8 秒短）
STALE_S = 15            # A 超過 15 秒沒訊框＝offline（連 3 筆沒來）
BOX = 60                # 上行斷線時最多先存 60 筆（5 分鐘）
# ---- 穩定度（任務四）
WDT_MS = 8000           # 看門狗；rp2 上限 8388 ms。除錯時把 WDT_ON 改成 False
WDT_ON = True
DROP_S = 60             # 按 B 的按鈕：模擬上行斷網 60 秒
BTN = 14                # B：按鈕接 GP14（第 19 腳）和 GND（第 18 腳）
NTP_HOST = "pool.ntp.org"     # 校時用；教室連不到外網時 log 會寫「未校時」
# ---- 量測（任務五，B 量 A）
SDA, SCL = 4, 5         # B：INA219 的 I2C（第 6、7 腳）
ZERO_MA = 0.0           # 主題 13 任務一量到的 INA219 零點（mA）
MEAS_S = 60             # 量 60 秒，每 10 ms 一筆
