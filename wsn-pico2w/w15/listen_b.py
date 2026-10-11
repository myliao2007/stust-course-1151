import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（組號…）
# listen_b.py（B 板，任務三）：被動掃描 ROUND_MS，只收自己組 A 的廣播，拆出欄位、用 seq 點名
import bluetooth, time
import packet
roll = packet.Loss()               # 點名簿
pk, rssi = [0], []                 # 收到幾個封包（含重複）、每次的 RSSI


def irq(event, data):
    if event == 5:                 # 5＝掃到一筆廣播
        addr_type, addr, adv_type, r, adv = data
        d = packet.unpack(adv, cfg.MFG_ID, cfg.GROUP)
        if d is None:
            return                 # 別組或手機的廣播：略過
        pk[0] += 1
        rssi.append(r)
        if roll.add(d["seq"]):     # 新的一號才印一行
            print("seq %5d  %s 度  %s %%  %s lux  %s  RSSI %d" % (
                d["seq"], d["t"], d["h"], d["lx"], d["st"], r))


ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq)
ble.gap_scan(cfg.ROUND_MS, 30000, 30000)    # 被動掃描：掃描窗＝間隔，一直聽
time.sleep_ms(cfg.ROUND_MS + 500)           # 等掃描結束
print("封包 %d 個、不同的 seq %d 個；應收 %d，遺失率 %.1f %%" % (
    pk[0], roll.got, roll.exp, roll.rate()))
if rssi:
    print("平均 RSSI %.1f dBm；每個 seq 平均收到 %.1f 次" % (
        sum(rssi) / len(rssi), pk[0] / roll.got))
