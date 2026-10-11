# cfg.py：本組參數與金鑰（由組號算出來；兩片都要存，不用改）
import myid, mysecret
from mac import hmac_sha256
GROUP = myid.GROUP
NODE_ID = "g%02d%s" % (GROUP, myid.BOARD)        # 例：g07A
AP_SSID = "wsn14-g%02d" % GROUP                   # B 板（閘道）開的 AP
AP_PASS = "pico%04d" % (GROUP * 4321 % 10000)
AP_CH = (1, 6, 11)[(GROUP - 1) % 3]               # 各組錯開 1、6、11
GW_PORT = 5014                                    # A → B 的 UDP 埠
# 金鑰：老師給的種子＋組號 → 本組兩把（一把加密、一把算 MAC）
_g = ("g%02d" % GROUP).encode()
ENC_KEY = hmac_sha256(mysecret.SEED.encode(), b"enc|" + _g)[:16]   # AES-128：16 B
MAC_KEY = hmac_sha256(mysecret.SEED.encode(), b"mac|" + _g)        # HMAC：32 B
# 任務三：教室 Wi-Fi、教室 Mosquitto（1883）、老師的 HiveMQ Cloud（8883）
BROKER_PLAIN = "192.168.1.10"
TOPIC = ("stust/wsn14/g%02d/sec" % GROUP).encode()
