import myid                        # 身份指紋（第一行）
import cfg, ap_a, wsnproto as w
# 任務二（A 板）：不壓縮：分派 41＋IPv6 40＋UDP 8＋資料

s, b, mac_b = ap_a.up()
src = w.link_local(cfg.SHORT_A)    # fe80::ff:fe00:2
dst = w.link_local(cfg.SHORT_B)    # fe80::ff:fe00:1
pkt = w.ipv6_udp(src, dst, 0xF0B1, 0xF0B2, b"T=25.3C RH")
f = w.frames_ipv6(1, cfg.PAN, cfg.SHORT_A, cfg.SHORT_B, pkt,
                  compress=False, fcs=False)[0]
s.sendto(f, b)
print("未壓縮：%d 位元組（9＋1＋40＋8＋10）" % len(f))
print(w.hexdump(f))
