# cfg.py：主題 7 的組別參數（A、B 兩片都要存，內容不用改）
import myid
GROUP = myid.GROUP
SSID = "wsn-g%02d" % GROUP                  # A 板開的 AP（沿用主題 3）
PASSWORD = "pico%04d" % (GROUP * 1234 % 10000)
CHANNEL = (1, 6, 11)[(GROUP - 1) % 3]       # 各組錯開 1、6、11
PORT_A, PORT_B = 5071, 5072                 # A 收報到與下行；B 收上行
DEV_ADDR = (GROUP << 8) | 0x01              # 前 7 位元 NwkID＝0＋25 位元位址
JOIN_EUI = bytes(7) + bytes((GROUP,))       # 任務四：JoinEUI（示範值）
APP_KEY = bytes((GROUP * 37 + i * 59) & 0xFF for i in range(16))  # 任務四
NWK_SKEY = bytes((GROUP * 11 + i * 7) & 0xFF for i in range(16))  # 任務三
APP_SKEY = bytes((GROUP * 13 + i * 5) & 0xFF for i in range(16))  # 任務三
