import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（組號…）
import bluetooth, time
from adtool import split_ad, find, mine, PDU
cnt = {}                # PDU 型態 → 次數
a_addr = None           # 自己組 A 的位址
name = None

def irq(event, data):
    global a_addr, name
    if event == 5:      # 5＝掃到一筆
        addr_type, addr, adv_type, rssi, adv = data
        ads = split_ad(adv)
        if mine(ads, cfg.GROUP):    # 主廣播：認出 A
            a_addr = bytes(addr)
        elif adv_type != 4 or bytes(addr) != a_addr:
            return                  # 別人的，不算
        cnt[adv_type] = cnt.get(adv_type, 0) + 1
        if find(ads, 0x09):
            name = find(ads, 0x09).decode()

ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq)
for active in (False, True):        # 先被動、再主動
    cnt.clear()
    name = None
    ble.gap_scan(10000, 30000, 30000, active)
    time.sleep(11)
    ks = sorted(cnt)
    s = ["%s %d 次" % (PDU[k], cnt[k]) for k in ks]
    kind = "主動" if active else "被動"
    print(kind + "掃描：", ", ".join(s))
    print("  名稱：", name or "看不到")
