import myid                        # 身份指紋（第一行）
# airtime.py：LoRa 空中時間計算器（Semtech 公式；任務一）
# 預設 BW 125 kHz、CR 4/5、前導碼 8、explicit header、CRC 開


def toa_ms(sf, n, bw=125000, cr=1, pre=8, crc=1, ih=0, de=None):
    ts = (1 << sf) / bw * 1000              # 符元時間（ms）
    if de is None:                          # 符元超過 16 ms 要開 LDRO
        de = 1 if ts > 16 else 0
    num = 8 * n - 4 * sf + 28 + 16 * crc - 20 * ih
    k = max(-(-num // (4 * (sf - 2 * de))), 0)   # 無條件進位
    return (pre + 4.25 + 8 + k * (cr + 4)) * ts


def off_s(toa, duty=0.01):                 # 1%：送完要安靜幾秒
    return toa / 1000 * (1 / duty - 1)


def per_day(toa, duty=0.01):               # 一天最多送幾包
    return int(86400 * duty / (toa / 1000))


if __name__ == "__main__":
    print("SF  符元ms  20B 空中ms  安靜 s  一天幾包")
    for sf in range(7, 13):
        t = toa_ms(sf, 20)
        ts = (1 << sf) / 125           # 符元時間（ms）
        print("%2d %7.3f %10.1f %8.1f %8d" % (sf, ts, t, off_s(t), per_day(t)))
    print("SF12、CR 4/8：%.1f ms" % toa_ms(12, 20, cr=4))
    print("SF7、BW 250 kHz：%.1f ms" % toa_ms(7, 20, bw=250000))
