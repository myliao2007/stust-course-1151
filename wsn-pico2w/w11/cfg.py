# cfg.py：本主題的組別參數（由 myid 的組號算出來；兩片板子都要存，內容不用改）
import myid
GROUP = myid.GROUP
WIFI_SSID = "STUST-IoT"           # 教室路由器（或老師的熱點），上課時老師公布
WIFI_PASS = "password"            # 同上
BROKER = "192.168.1.10"           # 老師筆電上的 Mosquitto（IP 上課時公布）
PORT = 1883
G = "g%02d" % GROUP               # 組別代號，例如 g07
CID = "wsn-%s-%s" % (G, myid.BOARD)   # 這片的 client id：wsn-g07-A／wsn-g07-B
CID_A = "wsn-%s-A" % G            # A 板的 client id（任務六故意撞名用）
A_TOPIC = "stust/ee/e501/%sa/" % G    # A 板的主題前綴：場域/系所/教室/節點/
DATA = (A_TOPIC + "data").encode()    # A 發布溫溼度 JSON
STATUS = (A_TOPIC + "status").encode()  # A 的上下線（retain＋遺囑）
CMD = (A_TOPIC + "cmd").encode()      # A 訂閱的指令：on、off、drop
LED = (A_TOPIC + "led").encode()      # A 回報 LED 狀態（B 量來回時間）
HELLO = ("stust/ee/e501/%sb/hello" % G).encode()   # B 自己的主題（任務六）
KEEPALIVE = 30                    # 秒；broker 判定掉線＝30×1.5＝45 秒
DROP_S = 60                       # 任務四：A 斷網 60 秒（比 45 秒長）
