# cfg.py：綜合實作（三）的組別參數、主題與金鑰（由 myid 的組號算出來；A、B 兩片都要存，內容不用改）
import myid, mysecret
from mac import hmac_sha256
GROUP = myid.GROUP
G = "g%02d" % GROUP                       # 組代號，例：第 7 組＝g07
BROKER, PORT = "192.168.1.10", 1883       # 教室電腦上的 Mosquitto（主題 11、12 同一台）
ROOM = "stust/ee/e501/%sa/" % G           # A 板的主題前綴（主題 12 的 gNNa）
T_SEC = (ROOM + "sec").encode()           # A 發布：計數器＋IV＋密文＋MAC
T_ACK = (ROOM + "ack").encode()           # B 回送計數器，A 用它量往返時間
T_CMD = (ROOM + "cmd").encode()           # B 對 A 下指令：drop、base、pm、eco
T_ST = (ROOM + "status").encode()         # A 的上線、模式、遺囑 offline
CID_A, CID_B = "wsn17-%sa" % G, "wsn17-%sb" % G
KEEPALIVE = 60          # 秒；A 失聯 90 秒後 broker 代發 offline
TIMEOUT = 5             # 每次等 broker 最多 5 秒（比看門狗的 8 秒短）
WDT_MS = 8000           # 看門狗；rp2 上限 8388 ms。除錯時把 WDT_ON 改成 False
WDT_ON = True
PERIOD_S = 3            # 每 3 秒量一筆：100 筆＝300 秒＝5 分鐘
N_TEST = 100            # T2 一次 100 筆
DROP_S = 60             # T4 模擬斷網 60 秒
ECO_DT, ECO_MAX_S = 0.3, 30   # eco：溫度變 0.3 度以上才送，最久 30 秒報一次平安
NTP_HOST = "pool.ntp.org"     # 校時用；教室連不到外網時 log 會寫「未校時」
SDA, SCL = 4, 5         # B：INA219 的 I2C（第 6、7 腳）；A：感測器也接這兩支
ZERO_MA = 0.0           # 主題 13 任務一量到的 INA219 零點（mA）
_g = G.encode()
ENC_KEY = hmac_sha256(mysecret.SEED.encode(), b"enc|" + _g)[:16]   # AES-128：16 B
MAC_KEY = hmac_sha256(mysecret.SEED.encode(), b"mac|" + _g)        # HMAC：32 B
