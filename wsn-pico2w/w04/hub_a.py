import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號、模擬通道）
import network, socket, struct, time
# hub_a.py（A 板＝Hub）：開 AP、每輪送 SYNC、收 B 的封包、判斷碰撞、算 PDR 與延遲
PLAN = ((0, 60), (1, 60), (2, 60))  # (做法, 輪數)：0 不排程、1 隨機退避、2 TDMA
SLOT_MS = cfg.SLOT_MS               # TDMA 時槽；想試 10 毫秒就改這裡

ap = network.WLAN(network.AP_IF)
ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
ap.active(True)
while not ap.active():
    time.sleep(0.2)
print("Hub 已啟動：", cfg.SSID, ap.ifconfig()[0], "埠", cfg.HUB_PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", cfg.HUB_PORT))
s.settimeout(0.05)
nodes = []                          # 加入的 B 板位址（SYNC 要送給誰）
known = set()                       # 出現過的節點編號


def collide(pk):                    # pk＝[(編號, 起點, 終點, 溫度)]，單位微秒
    hit = set()
    for i in range(len(pk)):
        for j in range(i + 1, len(pk)):
            if pk[i][1] < pk[j][2] and pk[j][1] < pk[i][2]:   # 時間重疊
                hit.add(pk[i][0])
                hit.add(pk[j][0])
    return hit


def take(rnd, pk):                  # 收一筆：JOIN 記位址，11 位元組是資料
    try:
        data, addr = s.recvfrom(64)
    except OSError:
        return                      # 50 毫秒內沒有東西
    if data == b"JOIN" and addr not in nodes:
        nodes.append(addr)
        print("B 板加入：", addr)
    elif len(data) == 11:
        n, seq, temp, ts = struct.unpack(cfg.FMT, data)
        if seq == rnd:              # 這一輪的才算，遲到的丟掉
            pk.append((n, ts, ts + cfg.airtime_us(len(data)), temp))


def one_round(rnd, mode, okbits):   # 送 SYNC，收一整輪，回傳這輪的封包
    t0 = time.ticks_us()
    sync = b"S" + struct.pack("<HBHB", rnd, mode, SLOT_MS, okbits)
    for a in nodes:
        s.sendto(sync, a)
    pk = []
    while time.ticks_diff(time.ticks_us(), t0) < cfg.PERIOD_MS * 1000:
        take(rnd, pk)
    return pk


def report(mode, st):               # st[編號]＝[應送, 成功, 撞到, 延遲總和]
    print("==", cfg.MODES[mode], "== 節點 應送 成功 撞到 沒收到 PDR 平均延遲")
    tot = [0, 0, 0, 0]
    for n in sorted(st):
        e, ok, hit, dsum = st[n]
        tot = [a + b for a, b in zip(tot, st[n])]
        print("節點%d %4d %4d %4d %4d %6.1f%% %9.3f ms" % (
            n, e, ok, hit, e - ok - hit, 100 * ok / e, dsum / max(ok, 1) / 1000))
    pdr = 100 * tot[1] / max(tot[0], 1)
    dly = tot[3] / max(tot[1], 1) / 1000
    print("合計 應送 %d 成功 %d 撞到 %d｜PDR %.1f%%｜平均延遲 %.3f ms" % (
        tot[0], tot[1], tot[2], pdr, dly))
    return pdr, dly


print("等 B 板 JOIN…")
while not nodes:
    take(0, [])
rnd, okbits, summary = 0, 0, []
for mode, rounds in PLAN:
    st = {}                         # st[編號]＝[應送, 成功, 撞到, 延遲總和]
    for k in range(rounds):
        rnd += 1
        pk = one_round(rnd, mode, okbits)
        hit, okbits = collide(pk), 0
        known.update(p[0] for p in pk)
        for n in known:             # 出現過的節點，每輪都應該送一包
            st.setdefault(n, [0, 0, 0, 0])[0] += 1
        for n, a, b, temp in pk:
            ok = n not in hit
            st[n][1 if ok else 2] += 1
            if ok:
                st[n][3] += b       # 延遲＝SYNC 到發射結束
                okbits |= 1 << (n - 1)
            print("R%d %s 節點%d %.2f°C %8.3f~%8.3f ms %s" % (rnd, cfg.MODES[mode],
                  n, temp, a / 1000, b / 1000, "成功" if ok else "撞到"))
    summary.append((mode,) + report(mode, st))
print("== 三種做法比較 ==")
for mode, pdr, dly in summary:
    print("%s PDR %.1f%% 平均延遲 %.3f ms" % (cfg.MODES[mode], pdr, dly))
