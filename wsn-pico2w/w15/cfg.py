# cfg.py：主題 15 綜合實作（一）的組別參數（由 myid 的組號算出來；A、B 兩片都要存）
# 這個檔沒有任何真的密碼：AP 密碼由組號算出來，只是避免連錯組。
# 老師網路或自己家裡的 Wi-Fi 密碼，不要寫進任何要上傳、要交的檔案。
import myid
GROUP = myid.GROUP
SSID = "wsn-g%02d" % GROUP                  # A 板開的 AP（B 連它回報）
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]       # 各組錯開 1、6、11
BLE_NAME = "wsn-g%02d-A" % GROUP            # A 的廣播名稱（含組號）
MFG_ID = 0xFFFF                             # 製造商代碼：0xFFFF 保留給測試用
PORT = 5015                                 # B → A 的 UDP 回報埠
PERIOD_MS = 1000                            # A 每 1 秒讀一次、seq 加 1
ADV_MS = 200                                # A 的廣播間隔（任務五：A 改成 1000 再跑一次）
ROUND_MS = 10000                            # B 每輪掃描 10 秒，掃完回報一次
LOSS_WARN = 5.0                             # 遺失率超過 5 % 就警告
