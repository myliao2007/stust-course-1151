import myid                        # 身份指紋（第一行）
import cfg, ap_a, wsnproto as w
# 任務四（A 板）：訊框尾巴加 FCS，再故意翻一個位元
FLIP = 20                          # 從 0 數第 20 個＝"25.3" 的 3

print("CRC-16 自我檢查：", hex(w.crc16(b"123456789")), "（要是 0x2189）")
s, b, mac_b = ap_a.up()
src, dst = w.link_local(cfg.SHORT_A), w.link_local(cfg.SHORT_B)
pkt = w.ipv6_udp(src, dst, 0xF0B1, 0xF0B2, b"T=25.3C RH")
good = w.frames_ipv6(2, cfg.PAN, cfg.SHORT_A, cfg.SHORT_B, pkt)[0]
bad = bytearray(good)
bad[FLIP] ^= 0x01                  # 3 變 2，FCS 不重算
for name, f in (("好的", good), ("翻一個位元", bytes(bad))):
    s.sendto(f, b)
    print("%s：%d 位元組，FCS 欄位 %s，重算是 %04x"
          % (name, len(f), w.hexs(f[-2:]), w.crc16(f[:-2])))
