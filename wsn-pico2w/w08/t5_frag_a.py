import myid                        # 身份指紋（第一行）
import cfg, ap_a, time, wsnproto as w
# 任務五（A 板）：150 位元組資料放不下 → FRAG1＋FRAGN，亂序送
TAG = 1                            # datagram_tag（延伸：改學號後四位）
ORDER = (1, 1, 0)                  # FRAGN、再一次 FRAGN、最後 FRAG1

s, b, mac_b = ap_a.up()
src, dst = w.link_local(cfg.SHORT_A), w.link_local(cfg.SHORT_B)
pkt = w.ipv6_udp(src, dst, 0xF0B1, 0xF0B2, bytes(range(150)))
fs = w.frames_ipv6(3, cfg.PAN, cfg.SHORT_A, cfg.SHORT_B, pkt,
                   tag=TAG, fcs=False)
print("IPv6 %d 位元組 → %d 片：%s" % (len(pkt), len(fs), [len(f) for f in fs]))
for i in ORDER:
    s.sendto(fs[i], b)
    print("送出第 %d 片：%s …" % (i + 1, w.hexs(fs[i][9:14])))
    time.sleep_ms(300)
