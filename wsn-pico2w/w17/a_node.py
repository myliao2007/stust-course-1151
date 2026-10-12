import myid                      # 身份指紋（第一行；A 板，任務三起另存成 main.py）
import cfg                       # 本組參數、主題、金鑰
import time, json, gc, machine
import netlink, sensors, seal, counter, util
# a_node.py（A 板＝感測節點）：每 3 秒量一次 → 加密＋MAC → MQTT 送出 → B 回 ack 量往返
# B 的指令：drop（模擬斷網 60 秒）、base／pm／eco（任務四的三種耗電模式）

led = machine.Pin("LED", machine.Pin.OUT)
mode, cmd, pend, rtt = "base", None, None, -1
FP = "學號 %s | 第 %d 組 | 板子 A | 序號 %s | MAC %s" % (
    myid.STUDENT_ID, myid.GROUP, myid.SN, myid.MAC)
P = int(cfg.PERIOD_S * 1000)     # 一格幾毫秒（每 3 秒一格）
def on_msg(topic, msg):          # B 回的 ack、B 下的指令
    global cmd, pend, rtt
    if topic == cfg.T_ACK and pend and msg == b"%d" % pend[0]:
        rtt = time.ticks_diff(time.ticks_ms(), pend[1])
        pend = None
    elif topic == cfg.T_CMD:
        cmd = msg.decode()

def up():                        # 連 Wi-Fi、連 broker、報到
    c = netlink.mqtt_up(cfg.CID_A, cfg.T_ST, on_msg, (cfg.T_ACK, cfg.T_CMD))
    up_s = time.ticks_ms() / 1000
    msg = "online %s | %s | 開機 %.1f 秒" % (FP, util.ts(), up_s)
    c.publish(cfg.T_ST, msg.encode(), True)   # retain：B 晚到也收得到
    return c

def set_mode(m):                 # base：Wi-Fi 不省電；pm、eco：省電模式
    global mode
    mode = m
    w = netlink.wlan
    w.config(pm=w.PM_NONE if m == "base" else w.PM_POWERSAVE)
    led.value(m != "eco")        # eco 連 LED 也關

util.retry(netlink.wifi_up)      # 先連上網路
util.sync_time(cfg.NTP_HOST)     # 校時之後 error.log 的時間才對
if cfg.WDT_ON:                   # 看門狗：8 秒沒餵就重開
    util.use_wdt(machine.WDT(timeout=cfg.WDT_MS))
ctr = counter.start()            # 計數器：重開機也不倒退（主題 14）
util.log("開機，計數器從 %d 起跳" % (ctr + 1))
c, nxt, slot, last_t, last_tx = None, time.ticks_ms(), 0, None, 0
while True:
    if c is None:
        c = util.retry(up)       # 斷線：退避重試，十次都失敗才重開機
        set_mode(mode)
    try:
        k = time.ticks_diff(time.ticks_ms(), nxt) // P   # 到下一格了沒（不怕繞回）
        if k >= 0:               # 新的一格（每 3 秒）：seq＝第幾格
            slot, nxt = slot + k + 1, time.ticks_add(nxt, (k + 1) * P)
            d = sensors.read_all()
            gc.collect()
            quiet = time.ticks_diff(time.ticks_ms(), last_tx) < cfg.ECO_MAX_S * 1000
            same = d["t"] is not None and last_t is not None and abs(d["t"] - last_t) < cfg.ECO_DT
            if not (mode == "eco" and quiet and same):    # eco：沒變化又不久就不送
                body = '{"seq":%d,"t":%s,"h":%s,"t2":%s,"mem":%d,"rtt":%d,"md":"%s"}' % (
                    slot, json.dumps(d["t"]), json.dumps(d["h"]), json.dumps(d["t2"]),
                    gc.mem_free(), rtt, mode)
                ctr = counter.next_(ctr)
                pend, rtt = (ctr, time.ticks_ms()), -1
                c.publish(cfg.T_SEC, seal.seal(cfg.ENC_KEY, cfg.MAC_KEY, ctr, body.encode()))
                last_t, last_tx = d["t"], time.ticks_ms()
                print("#%d" % ctr, body)
        c.check_msg()            # 收 ack 與指令（沒有就馬上回來）
        if cmd == "drop":
            cmd = None
            util.log("收到 drop：模擬斷網 %d 秒" % cfg.DROP_S)
            util.drop(cfg.DROP_S)
            netlink.wlan.disconnect()
            raise OSError("斷網")
        if cmd in ("base", "pm", "eco"):
            set_mode(cmd)
            c.publish(cfg.T_ST, b"mode " + cmd.encode())
            cmd = None
    except Exception as e:       # 網路出錯一律當斷線：記下來，下一圈重連
        util.log("斷線：%s" % e)
        try:
            c.sock.close()       # 不送 DISCONNECT，broker 才會發遺囑
        except Exception:
            pass
        c = None
    util.nap(50)                 # 每圈休息 50 ms（順便餵狗）
