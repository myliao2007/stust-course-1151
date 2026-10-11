import myid                      # 身份指紋（第一行）
import cfg, mysecret             # 本組參數、金鑰、老師給的帳密
import ssl, ntptime, gc
from umqtt.simple import MQTTClient
from wifi import connect

connect(mysecret.WIFI_SSID, mysecret.WIFI_PASS)
ntptime.settime()
gc.collect()                # TLS 很吃記憶體，先清一次

with open('ca.der', 'rb') as f:
    ca = f.read()           # 事先把 CA 憑證轉成 DER 存進板子
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.load_verify_locations(cadata=ca)

# ---- 後半：量連線時間與記憶體，再用 8883 發布 ----
import time, machine, seal, counter

def link(tls):                   # 連一次 broker，回傳 (client, 毫秒)
    if tls:
        c = MQTTClient(cfg.NODE_ID, mysecret.MQTTS_HOST, port=8883,
                       user=mysecret.MQTTS_USER, password=mysecret.MQTTS_PASS,
                       keepalive=60, ssl=ctx)
    else:
        c = MQTTClient(cfg.NODE_ID, cfg.BROKER_PLAIN, port=1883, keepalive=60)
    t0 = time.ticks_ms()
    c.connect()
    return c, time.ticks_diff(time.ticks_ms(), t0)

try:
    c, ms = link(False)
    print("1883 明文連線 %d ms" % ms)
    c.disconnect()
except Exception:
    print("教室 Mosquitto 連不上，略過 1883 對照")
gc.collect()
free0 = gc.mem_free()
c, ms = link(True)
print("8883 TLS 連線 %d ms，多用掉約 %d B 記憶體" % (ms, free0 - gc.mem_free()))
adc = machine.ADC(4)
ctr = counter.start()
while True:
    t = 27 - (adc.read_u16() * 3.3 / 65535 - 0.706) / 0.001721
    body = ('{"id":"%s","t":%.1f}' % (cfg.NODE_ID, t)).encode()
    ctr = counter.next_(ctr)
    c.publish(cfg.TOPIC, seal.seal(cfg.ENC_KEY, cfg.MAC_KEY, ctr, body))
    print("已發布 #%d" % ctr, body)
    time.sleep(5)
