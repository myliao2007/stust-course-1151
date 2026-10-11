import myid                        # 身份指紋（第一行）
import cfg, ap_a, wsnproto as w
# 任務三（A 板）：IPHC＋NHC；KNOB 一次只轉一顆旋鈕
KNOB = 0    # 0 原本 1 UDP 不壓 2 跳數 30 3 埠 5683 4 全域＋ctx

s, b, mac_b = ap_a.up()
src, dst = w.link_local(cfg.SHORT_A), w.link_local(cfg.SHORT_B)
hlim, sport, nhc, ctx = 64, 0xF0B1, True, None
if KNOB == 1:
    nhc = False                    # UDP 不用 NHC 壓（NH＝0）
elif KNOB == 2:
    hlim = 30                      # 跳數上限不是 1／64／255
elif KNOB == 3:
    sport = 5683                   # 來源埠不在 0xF0Bx
elif KNOB == 4:
    src, dst = "2001:db8:1::ff:fe00:2", "2001:db8:1::ff:fe00:1"
    ctx = cfg.CTX                  # 全域前綴查 context 0
pkt = w.ipv6_udp(src, dst, sport, 0xF0B2, b"T=25.3C RH", hlim=hlim)
f = w.frames_ipv6(2, cfg.PAN, cfg.SHORT_A, cfg.SHORT_B, pkt,
                  ctx=ctx, nhc=nhc, fcs=False)[0]
s.sendto(f, b)
k = len(f) - 9 - 10                # 扣掉 MAC 9、資料 10
print("旋鈕 %d：標頭 48 → %d 位元組" % (KNOB, k))
print("壓縮後：", w.hexs(f[9:9 + k]))
print("整個訊框 %d 位元組" % len(f))
