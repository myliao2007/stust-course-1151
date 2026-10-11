import myid                        # 身份指紋（第一行）
import sta_b, time
from airtime import toa_ms, off_s

s, a = sta_b.hello()               # 連上 A、報到
last = None                        # 上一包：(送完的時間, 空中時間 ms)
while True:
    f = s.recvfrom(64)[0].split(b",")          # b"T1,序號,SF,位元組"
    now = time.ticks_ms()
    seq, sf, n = int(f[1]), int(f[2]), int(f[3])
    t = toa_ms(sf, n)              # B 自己用公式重算空中時間
    msg = "第 %d 包 SF%d %d B：空中 %.1f ms" % (seq, sf, n, t)
    if last:
        quiet = (time.ticks_diff(now, last[0]) - t) / 1000   # 這包開始前安靜幾秒
        need = off_s(last[1])                               # 1%：上一包的 99 倍
        use = last[1] / (last[1] + quiet * 1000) * 100      # 上一包佔用的比例
        ok = "符合 1%" if quiet + 0.05 >= need else "違反 1%"   # 容許 Wi-Fi 晚 50 ms
        msg += "｜前面安靜 %.1f s（至少 %.1f s），佔用 %.2f%% %s" % (quiet, need, use, ok)
    print(msg)
    last = (now, t)
