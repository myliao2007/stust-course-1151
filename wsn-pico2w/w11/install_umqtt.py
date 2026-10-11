import myid                       # 身份指紋（第一行；A、B 兩片都跑這支）
import cfg                        # 本組參數（Wi-Fi、broker、client id）
import mip
from wifi import connect

print('IP =', connect(cfg.WIFI_SSID, cfg.WIFI_PASS)[0])
mip.install('umqtt.simple')

# 安裝完成後確認可以匯入
from umqtt.simple import MQTTClient
print('umqtt.simple 已就緒')

c = MQTTClient(cfg.CID, cfg.BROKER, cfg.PORT)   # 試連一次 broker
c.connect(timeout=5)
print('已連上 broker', cfg.BROKER, '| client id =', cfg.CID)
c.disconnect()
