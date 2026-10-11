# cfg.py：本主題的組別參數＋模擬通道參數（由 myid 的組號算出來；A、B 兩片都要存）
import myid
GROUP = myid.GROUP                      # 延伸（兩組合併）時，節點板改成 Hub 那組的組號
SSID = "wsn-g%02d" % GROUP              # A 板（Hub）開的 AP 名稱
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]   # 各組錯開 Wi-Fi 頻道 1、6、11
HUB_PORT = 5000 + GROUP                 # Hub 收資料的埠（原分組表：第 N 組 500N）
SYNC_PORT = 6000 + GROUP                # B 板收 SYNC 的埠
PAN_ID = 0x1000 + GROUP                 # 原分組表的 PAN ID（標頭範例用）
NODE_IDS = (1, 2, 3)                    # B 板上的虛擬節點（由程式指定）
PERIOD_MS = 3000                        # 一輪 3 秒，每個節點每輪送一筆
SLOT_MS = PERIOD_MS // 3                # TDMA 每個時槽 1000 毫秒
MODES = ("不排程", "隨機退避", "TDMA")  # 三種做法（Hub 用 SYNC 告訴 B）
FMT = "<BHfI"                           # 編號 1＋序號 2＋溫度 4＋時戳 4＝11 位元組
RATE = 250000                           # 模擬通道：802.15.4（2.4 GHz）250 kbps
OVERHEAD = 6 + 9 + 2                    # 空中多出來的：PHY 6＋MAC 標頭 9＋FCS 2


def airtime_us(n):                      # n 位元組資料在模擬通道上飛多久（微秒）
    return (n + OVERHEAD) * 8 * 1000000 // RATE
