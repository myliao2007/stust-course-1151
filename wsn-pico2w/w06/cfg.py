# cfg.py：本主題組別參數（由 myid 組號算出，兩片都要存）
import myid
GROUP = myid.GROUP
# 這一片的廣播名稱（≤ 26 字元）
BLE_NAME = "wsn-g%02d-%s" % (GROUP, myid.BOARD)
# B 要找的：自己組 A 板
A_NAME = "wsn-g%02d-A" % GROUP
# 製造商代碼：0xFFFF 保留給測試用
MFG_ID = 0xFFFF
# 任務五：自訂 128 位元 UUID，後半段含組號
TAIL = "-f4b2-4f7c-bfaa-8a0cea5c64%02x" % GROUP
SVC_UUID = "282c0001" + TAIL   # 服務
DATA_UUID = "282c0002" + TAIL  # 資料（通知／指示）
CMD_UUID = "282c0003" + TAIL   # 指令（B 寫入 N 或 I）
