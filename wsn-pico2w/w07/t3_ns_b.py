import myid                        # 身份指紋（第一行）
import cfg, sta_b, math, random, lwcrypto as lw
GW = (("GW1", 500, 500), ("GW2", 2500, 500), ("GW3", 1500, 2100))   # 公尺
SF, N = 9, 3.5                     # 上行 SF9；路徑損耗指數 n（主題 3 的模型）
random.seed(cfg.GROUP)             # 每組的遮蔽亂數不同；同一組重跑結果一樣


def hear(x, y):                    # 每台閘道算 RSSI、SNR；SNR 低於門檻就收不到
    out = []
    for g, gx, gy in GW:
        d = max(1, math.sqrt((x - gx) ** 2 + (y - gy) ** 2))
        rssi = 14 - 31.7 - 10 * N * math.log10(d) + random.uniform(-3, 3)
        snr = rssi + 117           # 雜訊底：−174＋51＋6＝−117 dBm
        if snr >= -7.5 - 2.5 * (SF - 7):
            out.append((snr, rssi, g))
    return out


s, a = sta_b.hello()               # 連上 A、報到
seen = {}                          # 網路伺服器：(DevAddr, FCnt) → 收到的副本
while True:
    x, y, f = s.recvfrom(128)[0].split(b",", 2)
    copies = hear(int(x), int(y))  # 閘道：收到就轉送，不解密、不去重複
    for snr, rssi, g in copies:
        print("  %s 收到：RSSI %.1f dBm、SNR %.1f dB → 轉給網路伺服器" % (g, rssi, snr))
    dev, fcnt = int.from_bytes(f[1:5], "little"), int.from_bytes(f[6:8], "little")
    if not copies or lw.mic(cfg.NWK_SKEY, dev, fcnt, f[:-4]) != f[-4:]:
        print("  三台閘道都收不到（或 MIC 不對）")
        continue
    if (dev, fcnt) in seen:        # 同一個上行又來一次（重送）
        print("網路伺服器：(%08X, %d) 處理過了，%d 份全部丟掉" % (dev, fcnt, len(copies)))
        continue
    seen[(dev, fcnt)] = copies
    best = max(copies)             # SNR 最好的那台閘道負責回下行
    t = int.from_bytes(lw.crypt(cfg.APP_SKEY, dev, fcnt, f[9:-4]), "little")   # 解密
    print("網路伺服器：(%08X, %d) %d 份留 1 份" % (dev, fcnt, len(copies)))
    print("應用伺服器：溫度 %.2f｜下行走 %s" % (t / 100, best[2]))
    s.sendto(("DN,%d,%s,SNR %.1f dB" % (fcnt, best[2], best[0])).encode(), a)
