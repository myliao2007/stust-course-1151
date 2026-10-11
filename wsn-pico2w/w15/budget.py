import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（週期、廣播間隔…）
# budget.py（任務五，A 或 B 都可以跑）：用 cfg 的參數把三本帳算一次
# I_ON、I_SLP 換成主題 13 自己量到的值（下面是示範值）
import packet, os
I_ON, I_SLP, CAP = 55.0, 1.8, 2000.0     # 醒著 mA、睡著 mA、電池 mAh
AWAKE, SLEEP = 1000, 4000                # 改架構後：醒 1 秒、睡 4 秒（ms）
d = {"seq": 611, "t": 26.35, "h": 55.2, "lx": 312, "st": "ok"}
roll = packet.Loss()
roll.got, roll.exp = 591, 600            # 示範：10 分鐘應收 600、實收 591

L = len(packet.pack(cfg.MFG_ID, cfg.GROUP, 0, d, cfg.BLE_NAME))
air = (1 + 4 + 2 + 6 + L + 3) * 8        # LE 1M：每位元 1 微秒
ev = 1000 / cfg.ADV_MS                   # 每秒廣播幾次（每次 3 個頻道）
print("【頻寬帳】廣播 %d 位元組，空中 %d 微秒；每秒 %.0f 次 × 3 頻道，佔 %.2f %%" % (
    L, air, ev, air * 3 * ev / 1e4))
print("  每個 seq 大約有 %.0f 次被聽到的機會" % (cfg.PERIOD_MS / cfg.ADV_MS))
R = len(packet.report(cfg.GROUP, 60, d, -48, roll))
sec = cfg.ROUND_MS / 1000
print("  UDP 回報 %d 位元組，加 UDP 8、IP 20：每 %.0f 秒一次 = %.0f bps" % (
    R, sec, (R + 28) * 8 / sec))
day = 86400 / sec
print("【資料量帳】一天 %.0f 筆回報 × %d 位元組 = %.0f KB" % (day, R, day * R / 1000))
st = os.statvfs("/")
free = st[0] * st[3]                     # 區塊大小 × 剩下的區塊數
print("  這片板子還剩 %d KB，全部存下來可以存 %.1f 天" % (free // 1000, free / (day * R)))
print("【電量帳】A 一直醒著：%.0f × 0.7 ÷ %.1f = %.1f 小時" % (CAP, I_ON, CAP * 0.7 / I_ON))
avg = (I_ON * AWAKE + I_SLP * SLEEP) / (AWAKE + SLEEP)
print("  醒 %d 秒、睡 %d 秒：平均 %.2f mA，%.1f 小時" % (
    AWAKE // 1000, SLEEP // 1000, avg, CAP * 0.7 / avg))
