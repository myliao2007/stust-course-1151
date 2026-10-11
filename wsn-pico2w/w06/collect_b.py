import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（組號…）
import bluetooth, struct, time
from adtool import split_ad, find
SECONDS = 40            # 收集幾秒
nodes = {}              # 組號 → [序號集合, 封包, RSSI, 溫, 濕]

def lost(seqs):         # 序號應該連續，少幾個＝掉幾筆
    s = sorted(seqs)
    if s[-1] - s[0] > 128:          # 跨過 255→0
        s = sorted(x + 256 if x < 128 else x for x in s)
    return s[-1] - s[0] + 1 - len(s)

def irq(event, data):
    if event == 5:      # 5＝掃到一筆
        addr_type, addr, adv_type, rssi, adv = data
        d = find(split_ad(adv), 0xFF) or b""
        if len(d) != 8 or d[:2] != b"\xff\xff":
            return      # 其他廣播：略過
        _, g, seq, t, h = struct.unpack("<HBBhH", d)
        n = nodes.setdefault(g, [set(), 0, 0, 0, 0])
        n[0].add(seq)
        n[1] += 1
        n[2], n[3], n[4] = rssi, t / 100, h / 100

ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq)
ble.gap_scan(SECONDS * 1000, 30000, 30000)   # 只掃不連
time.sleep(SECONDS + 1)
print("組  封包  序號  遺失   溫度   濕度  RSSI")
for g in sorted(nodes):
    s, cnt, rssi, t, h = nodes[g]
    row = (g, cnt, len(s), lost(s), t, h, rssi)
    me = " ← 自己組" if g == cfg.GROUP else ""
    print("%02d %5d %5d %5d %6.2f %6.2f %5d" % row + me)
