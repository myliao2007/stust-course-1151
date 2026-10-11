import myid                        # 身份指紋（第一行）
import cfg, ap_a, wsnproto as w
# 任務一（A 板）：127 位元組預算＋由 MAC 推出 IPv6 位址

s1 = len(w.mac_data(0, cfg.PAN, cfg.SHORT_B, cfg.SHORT_A, b"", fcs=False))
s2 = len(w.mac_data(0, cfg.PAN, myid.MAC, myid.MAC, b"", fcs=False))
for name, h in (("短位址", s1), ("長位址", s2)):
    room = 127 - h - 2             # 再扣 2 位元組 FCS
    print("%s：MAC 標頭 %d，可用 %d；不壓縮剩 %d，IPHC 剩 %d"
          % (name, h, room, room - 48, room - 6))
print("A 的 MAC", myid.MAC)
print("→ EUI-64", w.hexs(w.eui64(myid.MAC), ":"))
print("→ IID   ", w.hexs(w.iid(myid.MAC), ":"))
print("→ A 的 link-local", w.ip6str(w.link_local(myid.MAC)))

s, b, mac_b = ap_a.up()            # 開 AP、等 B 報到（拿到 B 的 MAC）
print("A 替 B 算的 link-local", w.ip6str(w.link_local(mac_b)))
src, dst = w.link_local(myid.MAC), w.link_local(mac_b)
pkt = w.ipv6_udp(src, dst, 0xF0B1, 0xF0B2, b"T=25.3C RH")
f = w.frames_ipv6(1, cfg.PAN, myid.MAC, mac_b, pkt, fcs=False)[0]
s.sendto(f, b)
print("用兩個長位址送出 %d 位元組" % len(f))
