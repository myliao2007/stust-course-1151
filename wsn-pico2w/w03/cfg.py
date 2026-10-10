# cfg.py：本主題的組別參數（由 myid 的組號算出來；兩片板子都要存）
import myid
GROUP = myid.GROUP
SSID = "wsn-g%02d" % GROUP                  # A 板開的 AP 名稱
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]       # 各組錯開 1、6、11
BLE_NAME = "wsn-g%02d-%s" % (GROUP, myid.BOARD)   # BLE 廣播名稱
ECHO_PORT = 5005                            # 任務三：UDP 回聲
TPUT_PORT = 5006                            # 任務五：吞吐量
