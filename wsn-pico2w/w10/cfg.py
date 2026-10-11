# cfg.py：主題 10 的組別參數與模擬拓樸（A、B 兩片都存，不用改）
import myid
GROUP = myid.GROUP
SSID = "wsn-g%02d" % GROUP               # A 板開的 AP 名稱
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]    # 各組錯開 Wi-Fi 頻道 1、6、11
PORT = 5000 + GROUP                      # 分組表：第 N 組用 500N 埠
PAN_ID = 0x1000 + GROUP                  # 分組表：0x100N（取代 MAGIC）

# 虛擬節點（短位址）：A 板只跑 root，B 板跑 N1～N4
ROOT = 0x0001
NODES = {0x0011: "N1", 0x0012: "N2", 0x0013: "N3", 0x0014: "N4"}
PREFIX = "2001:db8:1::"                  # DIO 帶的前綴（組全域位址）
# 拓樸矩陣：誰聽得到誰、每個方向的送達率；沒列＝聽不到
TOPO = {(0x0001, 0x0011): 1.0,
        (0x0001, 0x0012): None,          # None＝B 板的旋鈕（那道牆）
        (0x0011, 0x0012): 1.0, (0x0011, 0x0013): 1.0,
        (0x0012, 0x0014): 1.0, (0x0013, 0x0014): 0.82}   # 0.82×0.82≈0.67

# RPL 參數（root 放進 DIO 的 DODAG 設定選項，B 的節點照著用）
OCP = 1                    # 目標函數：0＝OF0（RFC 6552）、1＝MRHOF（RFC 6719）
MIN_HOP = 256              # MinHopRankIncrease（RFC 6550 預設）；root 的 Rank 也是 256
MAX_RANK_INC = 1792        # DAGMaxRankIncrease：同一版本裡 Rank 最多比最低時大 7 層
DIO_IMIN = 10              # Trickle：Imin＝2^10 毫秒≈1 秒（RFC 預設 3＝8 毫秒，放慢才看得到）
DIO_DOUBLINGS = 6          # Imax＝Imin×2^6≈65.5 秒（RFC 預設 20，約 2.3 小時）
DIO_K = 10                 # 冗餘常數 k（RFC 預設 10）

# 計時（毫秒）
PROBE_MS = 500             # 每個節點每 0.5 秒送一則探測（量 ETX 用）
WINDOW = 20                # ETX 用最近 20 則探測（10 秒）算
PARENT_TIMEOUT_MS = 3000   # 連續 6 則探測都沒聽到父節點＝父節點不見了
POISON_MS = 2000           # 毒化後等 2 秒，讓子孫先離開，再重新找父節點
DIS_MS = 3000              # 還沒加入時，每 3 秒送一次 DIS
DAO_DELAY_MS = 1000        # 換父節點 1 秒後送 DAO（RFC 6550 預設 DAO 延遲 1 秒）
DATA_MS = 5000             # 每個節點每 5 秒送一筆資料給 root
STATUS_MS = 5000           # B 板每 5 秒印一次狀態表

# 要印出「十六進位＋欄位樹」的訊框（每一種只印第一次），貼到電腦的 wsn_decode.py 對照
SHOW_A = ("DIO", "DIS", "DAO", "DATA")   # A 板：自己送的第一則 DIO、收到的第一則 DIS／DAO／DATA
SHOW_B = ("DIO",)                        # B 板：收到 root 的第一則 DIO
LOG_TRICKLE = ("R", "N2")                # 誰的 Trickle 每一段都要印出來
