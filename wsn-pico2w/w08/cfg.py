# cfg.py：主題 8 的組別參數（A、B 兩片都存，不用改）
import myid
GROUP = myid.GROUP
SSID = "wsn-g%02d" % GROUP           # A 板開的 AP（同主題 3）
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]  # 各組錯開 1、6、11
PORT_A = 5080                        # A 收 B 的報到
PORT_B = 5000 + GROUP                # B 收訊框（分組參數表）
PAN = 0xABCD                         # PAN ID：和答案卷一樣
SHORT_A = 0x0002                     # A 板（感測節點）短位址
SHORT_B = 0x0001                     # B 板（收集端）短位址
CTX = {0: "2001:db8:1::/64"}         # context 0（任務三旋鈕 4）
LED_OK, LED_ACT = 15, 16             # B 板：GP15 全對、GP16 收到
KNOB_ADC = 26                        # B 板：GP26 接遺失旋鈕
