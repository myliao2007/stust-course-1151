import myid                      # 身份指紋（第一行）
import cfg, mysecret             # 本組參數、金鑰、老師給的帳密
import ssl, ntptime, gc, time
from umqtt.simple import MQTTClient
from wifi import connect
import seal
# mqtts_b.py（B 板）：用 8883 訂閱自己組的主題，照樣先驗再收

connect(mysecret.WIFI_SSID, mysecret.WIFI_PASS)
ntptime.settime()                # 沒校時，憑證的有效期限一定判斷錯
gc.collect()
with open("ca.der", "rb") as f:
    ca = f.read()
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.load_verify_locations(cadata=ca)

last = 0
rec = []

def on_msg(topic, pkt):
    global last
    r, ctr, body = seal.unseal(cfg.ENC_KEY, cfg.MAC_KEY, pkt, last)
    if r == "ok":
        last = ctr
    print("收到 %d B → %s" % (len(pkt), r), ctr, body or "")
    rec.append(pkt)
    if len(rec) == 3:                # 第 3 包原封不動重發一次到自己組的主題
        c.publish(cfg.TOPIC, pkt)

# keepalive 用預設的 0：B 只收不發，broker 不檢查閒置（主題 11）
c = MQTTClient(cfg.NODE_ID, mysecret.MQTTS_HOST, port=8883, ssl=ctx,
               user=mysecret.MQTTS_USER, password=mysecret.MQTTS_PASS)
t0 = time.ticks_ms()
c.connect()
print("8883 TLS 連線 %d ms" % time.ticks_diff(time.ticks_ms(), t0))
c.set_callback(on_msg)
c.subscribe(cfg.TOPIC)
while True:
    c.wait_msg()                     # 等到訊息就交給 on_msg
