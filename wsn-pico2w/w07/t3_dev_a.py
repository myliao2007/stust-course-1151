import myid                        # 身份指紋（第一行）
import cfg, ap_a, time, lwcrypto as lw
PATH = ((200, 200), (1500, 1000), (3100, 200), (2400, 1600), (1500, 4500))   # 公尺

s, b = ap_a.up()                   # 開 AP、等 B 報到
s.settimeout(2)
for fcnt, (x, y) in enumerate(PATH, 1):
    temp = 2630 + fcnt             # 溫度 ×100（示範值；延伸挑戰換成 AHT20）
    f = lw.uplink(cfg.NWK_SKEY, cfg.APP_SKEY, cfg.DEV_ADDR, fcnt, 1, lw.le(temp, 2))
    for k in (1, 2):               # 同一個 FCnt 送兩次（NbTrans＝2）
        s.sendto(b"%d,%d," % (x, y) + f, b)    # 位置只給模擬器算 RSSI
        print("FCnt %d 第 %d 次 @(%d, %d)：%s" % (fcnt, k, x, y, f.hex()))
        try:
            print("  下行：", s.recvfrom(64)[0].decode())
        except OSError:
            print("  沒有下行")
        time.sleep(1)
