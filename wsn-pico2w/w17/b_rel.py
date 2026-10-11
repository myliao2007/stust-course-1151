import myid                      # 身份指紋（第一行；B 板）
import cfg                       # 本組參數、主題、金鑰
import time, json, math
import netlink, seal
from seqstat import SeqStat
# b_rel.py（B 板＝統計站）：驗 A 的封包、回 ack、算遺失率、往返延遲、mem_free 趨勢
# 任務一：DROP = False（收 100 格）；任務三：DROP = True（第 20 筆叫 A 斷網 60 秒，收 50 格）

DROP = False
DROP_AT, N = (20, 50) if DROP else (0, cfg.N_TEST)
st, rtt, mem = SeqStat(), [], []
last, f = 0, open("w17_rel.csv", "w")
t_drop = [None, False]           # [叫 A 斷網的時間, 已經恢復了嗎]
f.write("seq,ctr,t,h,t2,mem,rtt,md,b_ms\n")

def on_msg(topic, pkt):
    global last
    if topic == cfg.T_ST:
        print("A 狀態：", pkt.decode())
        return
    r, ctr, body = seal.unseal(cfg.ENC_KEY, cfg.MAC_KEY, pkt, last)
    if r != "ok":
        print("擋下：", r)
        return
    last = ctr
    c.publish(cfg.T_ACK, b"%d" % ctr)       # 把計數器送回去，A 才量得到往返時間
    d = json.loads(body)
    how = st.add(d["seq"])
    if d["rtt"] > 0:
        rtt.append(d["rtt"])
    mem.append(d["mem"])
    f.write("%d,%d,%s,%s,%s,%d,%d,%s,%d\n" % (d["seq"], ctr, d["t"], d["h"], d["t2"],
            d["mem"], d["rtt"], d["md"], time.ticks_ms()))
    print("seq %3d #%-4d %s °C %s %%RH mem %d rtt %d ms [%s]" % (
        d["seq"], ctr, d["t"], d["h"], d["mem"], d["rtt"], how))
    if t_drop[0] is not None and not t_drop[1]:    # 斷網後收到的第一筆
        s = time.ticks_diff(time.ticks_ms(), t_drop[0]) / 1000
        print("A 恢復：drop 之後 %.1f 秒收到下一筆（比 %d 秒多 %.1f 秒）" % (s, cfg.DROP_S, s - cfg.DROP_S))
        t_drop[1] = True
    if DROP_AT and t_drop[0] is None and st.got() == DROP_AT:
        c.publish(cfg.T_CMD, b"drop")
        t_drop[0] = time.ticks_ms()
        print("叫 A 模擬斷網 %d 秒……" % cfg.DROP_S)

c = netlink.mqtt_up(cfg.CID_B, None, on_msg, (cfg.T_SEC, cfg.T_ST))
print("B 訂閱 %s，收滿 %d 格就結算" % (cfg.T_SEC.decode(), N))
tp = time.ticks_ms()
while st.first is None or st.top - st.first + 1 < N:
    c.check_msg()
    if time.ticks_diff(time.ticks_ms(), tp) > 20000:
        c.ping()                 # A 斷網時 B 也沒事做：自己送 PINGREQ 免得被 broker 踢掉
        tp = time.ticks_ms()
    time.sleep_ms(20)
f.close()
c.disconnect()

n = st.top - st.first + 1                  # 應收＝最後減最前再加一
print("=== 結算（第 %d 組）===" % cfg.GROUP)
print("T2 應收 %d、收到 %d、遺失 %d，遺失率 %.1f %%" % (n, st.got(), st.lost(), st.lost() / n * 100))
g = st.gaps()
print("缺號：", "、".join("%d" % a if a == b else "%d～%d" % (a, b) for a, b in g) or "無")
big = [x for x in g if x[1] - x[0] >= 2]
print("集中（連 3 筆以上）%d 段，零星 %d 段" % (len(big), len(g) - len(big)))
if rtt:
    rtt.sort()
    k = len(rtt)
    avg = sum(rtt) / k
    sd = math.sqrt(sum((x - avg) ** 2 for x in rtt) / k)
    med = (rtt[(k - 1) // 2] + rtt[k // 2]) / 2
    print("T3 往返 %d 筆：平均 %.0f、中位數 %.0f、最大 %d、標準差 %.0f ms；單向最大約 %d ms" % (
        k, avg, med, rtt[-1], sd, rtt[-1] // 2))
if len(mem) >= 20:
    a, b = sum(mem[:10]) / 10, sum(mem[-10:]) / 10
    mins = (len(mem) - 10) * cfg.PERIOD_S / 60   # 前後兩段中點相隔幾分鐘
    print("T6 mem_free 前 10 筆平均 %.0f、後 10 筆平均 %.0f，每分鐘少 %.0f B" % (a, b, (a - b) / mins))
