# cfg.py：本主題的組別參數（由 myid 的組號算出來；兩片板子都要存，內容不用改）
import myid
GROUP = myid.GROUP


def ap_of(g):                               # 第 g 組 A 板開的 AP：(SSID, 密碼)
    return "wsn-g%02d" % g, "pico%04d" % (g * 1234 % 10000)


SSID, PASSWORD = ap_of(GROUP)               # 和主題 3 一樣：A 板開 AP，B 板連上去
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]       # A 的 AP 真正用的 Wi-Fi 頻道（各組錯開 1、6、11）
PAN = 0x1000 + GROUP                        # 本組的 PAN：ATID 要設的值（第 7 組 1007、第 12 組 100C）
AIR_PORT = 5400                             # 模擬的 802.15.4 頻道 CH 走 UDP 埠 5400＋CH（CH 15 → 5415）
