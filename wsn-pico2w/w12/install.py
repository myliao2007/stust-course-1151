import myid                                  # 身份指紋（第一行）
import cfg                                   # 本組參數
# install.py：安裝 MQTT 與 OLED 函式庫（每片做一次）
# mip 要從網路下載，Pico 要能上網
from wifi import connect
import mip

print("IP =", connect(cfg.SSID, cfg.PASSWORD)[0])
mip.install("umqtt.simple")                  # A、B 都要（主題 11 裝過就會直接覆蓋）
if myid.BOARD == "B":
    mip.install("ssd1306")                   # 只有 B 接 OLED
from umqtt.simple import MQTTClient
print("umqtt.simple 已就緒")
if myid.BOARD == "B":
    import ssd1306
    print("ssd1306 已就緒")
