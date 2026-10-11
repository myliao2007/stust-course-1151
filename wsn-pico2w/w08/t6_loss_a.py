import myid                        # 身份指紋（第一行）
import cfg, ap_a, time, wsnproto as w
# 任務六（A 板）：n＝1～6 片各送 COUNT 包（資料 100×n 位元組）
COUNT = 100
GAP_MS = 15                        # 每片停一下，B 才來得及解

s, b, mac_b = ap_a.up()
src, dst = w.link_local(cfg.SHORT_A), w.link_local(cfg.SHORT_B)
seq = 0
for n in range(1, 7):
    s.sendto(b"#ROUND,%d" % n, b)              # 告訴 B：這輪 n 片
    pkt = w.ipv6_udp(src, dst, 0xF0B1, 0xF0B2, bytes(100 * n))
    for k in range(COUNT):
        fs = w.frames_ipv6(seq, cfg.PAN, cfg.SHORT_A, cfg.SHORT_B,
                           pkt, tag=n * 1000 + k)
        seq += len(fs)
        for f in fs:
            s.sendto(f, b)
            time.sleep_ms(GAP_MS)
    print("n＝%d：送了 %d 包、%d 片" % (n, COUNT, COUNT * len(fs)))
s.sendto(b"#END,%d" % COUNT, b)
