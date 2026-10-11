# save_csv.py（電腦端，用 Thonny 執行）：訂閱 A 的資料，一筆一列寫進 sensor.csv（含 seq）
# 需要 paho-mqtt 2.x：Thonny「工具 → 管理套件」搜尋 paho-mqtt 安裝
import csv, json, os, time
import paho.mqtt.client as mqtt

GROUP = 1                                    # ← 改成自己的組號
G = "g%02d" % GROUP
TOPIC = "stust/ee/e501/%sa/data" % G
COLS = ["rx_time", "topic", "id", "seq", "t", "h", "p", "lux", "t2", "ts"]

new = not os.path.exists("sensor.csv")
f = open("sensor.csv", "a", newline="", encoding="utf-8")
w = csv.writer(f)
if new:
    w.writerow(COLS)                         # 新檔先寫表頭

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(TOPIC)                  # 斷線重連後會再訂一次
    print("已連上 broker，訂閱", TOPIC)

def on_message(client, userdata, msg):
    try:
        d = json.loads(msg.payload)
    except ValueError:
        print("不是 JSON，略過：", msg.payload[:40])
        return
    row = [time.strftime("%Y-%m-%d %H:%M:%S"), msg.topic] + [d.get(k) for k in COLS[2:]]
    w.writerow(row)
    f.flush()                                # 每寫一列就存，程式被關掉也不會掉資料
    print(row)

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="wsn-%scsv" % G)
c.on_connect, c.on_message = on_connect, on_message
c.connect("192.168.1.10", 1883, 60)
c.loop_forever()                             # 一直收，按 Stop 才結束
