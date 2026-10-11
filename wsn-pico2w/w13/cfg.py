# cfg.py：主題 13 的組別參數與接線（由 myid 的組號算出來；A、B 兩片都要存）
import myid
GROUP = myid.GROUP
SSID = "wsn-g%02d" % GROUP                  # B 板開的 AP（A 連它送資料）
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]       # 各組錯開 1、6、11
UDP_PORT = 5013                             # A 送到 B 的埠號
BLE_NAME = "wsn-g%02d-%s" % (GROUP, myid.BOARD)
SDA, SCL = 4, 5                             # B：INA219 的 I2C（第 6、7 腳）
MARK_PIN = 16                               # 標記線 A→B（GP16，第 21 腳）
GO_PIN = 17                                 # 開始線 B→A（GP17，第 22 腳）
ZERO_MA = 0.0                               # 任務一量到的零點（mA）
SEG_MS = 8000                               # 任務二、三：每一段 8 秒
SLEEP_MS = 30000                            # 任務四：每次 deepsleep 30 秒
FP = "學號 %s | 第 %d 組 | 板子 %s | 序號 %s | MAC %s" % (
    myid.STUDENT_ID, GROUP, myid.BOARD, myid.SN, myid.MAC)   # A 的指紋
