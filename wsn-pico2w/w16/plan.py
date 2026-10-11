import myid                      # 身份指紋（第一行；A、B 哪一片跑都可以）
import cfg, packet, airtime
import wsnproto as w
# plan.py：任務六規劃題的計算器（主題 7 LoRa、主題 10 RPL、主題 12 邊緣減量）

# 一、同一筆 13 位元組改走 LoRaWAN：再加 13 位元組（MHDR 1＋FHDR 7＋FPort 1＋MIC 4）
n = packet.SIZE + 13
print("一、LoRa：%d 位元組（BW 125 kHz、CR 4/5），工作週期 1 %%" % n)
print("SF  空中ms  最快幾秒一筆  每 %d 秒一筆？" % (cfg.PERIOD_MS // 1000))
for sf in range(7, 13):
    t = airtime.toa_ms(sf, n)
    gap = t / 1000 + airtime.off_s(t)        # 送一次＋安靜時間
    ok = "可以" if gap <= cfg.PERIOD_MS / 1000 else "不行"
    print("%2d %7.1f %10.1f     %s" % (sf, t, gap, ok))

# 二、RPL：B 是根（Rank 256），A 一跳、隔壁組的 C 經過 A 兩跳
a0 = w.of0_rank(256)
am = [w.mrhof_rank(256, e) for e in (1.0, 1.5, 2.0, 3.0)]
print("二、RPL：A（一跳）OF0 %d；MRHOF ETX 1.0／1.5／2.0／3.0 → %d／%d／%d／%d"
      % (a0, am[0], am[1], am[2], am[3]))
c0, cm = w.of0_rank(a0), w.mrhof_rank(am[0], 1.0)
print("C 經過 A（兩跳）：OF0 %d（第 %d 層）；MRHOF（兩段 ETX 都 1.0）%d"
      % (c0, w.dag_rank(c0), cm))
print("C 送出時 Hop Limit 64，A 轉送一次減 1，到 B 剩 63")

# 三、邊緣減量：B 每筆都上傳 vs 每分鐘只上傳一則平均
d = {"seq": 120, "t": 26.35, "h": 55.2, "p": 1008.4, "lux": 313, "t2": 25.08, "st": "ok"}
j = packet.to_json(d, 30, 0.0, "2026-12-23 10:15:05")
rem = 2 + len(cfg.DATA_A) + len(j)                 # 主題長度欄＋主題＋內容
m = 1 + (1 if rem < 128 else 2) + rem              # PUBLISH：固定標頭＋剩餘長度
day = 86400 * 1000 // cfg.PERIOD_MS
print("三、上雲：一則 JSON %d 位元組 → PUBLISH %d 位元組" % (len(j), m))
print("每筆都送：一天 %d 則、%.1f KB；每分鐘一則平均：1440 則、%.1f KB（少 %d 倍）"
      % (day, day * m / 1000, 1440 * m / 1000, day // 1440))
