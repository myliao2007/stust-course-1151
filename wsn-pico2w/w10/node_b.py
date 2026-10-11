import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、PAN ID、拓樸矩陣…）
import socket, time, random, machine
import wsnproto as w
from wifi import connect
from rplnode import Node, kind, name
# node_b.py（B 板）：跑 N1～N4 四個虛擬節點；拓樸矩陣決定誰聽得到誰，旋鈕決定 root－N2 那道牆
# 接線：可變電阻兩端接 3V3(OUT)（第 36 腳）、GND（第 38 腳），中間腳接 GP26／ADC0（第 31 腳）
#       按鈕一腳接 GP14（第 19 腳）、另一腳接 GND（第 18 腳）：按一下 N2 斷電，再按一下復活
ip = connect(cfg.SSID, cfg.PASSWORD)   # 原本的 wifi.py：連上自己組 A 板的 AP
A = (ip[2], cfg.PORT)                  # 閘道就是 A 板（root）
print("B 的 IP：", ip[0], "→ A", A, "｜PAN 0x%04x" % cfg.PAN_ID)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", cfg.PORT))
sock.settimeout(0)                     # 不等：沒有封包就馬上回來做別的事
knob = machine.ADC(26)
btn = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
adc = machine.ADC(4)       # ADC4 = RP2350 內建溫度感測器
def read_temp():
    v = adc.read_u16() * 3.3 / 65535
    return round(27 - (v - 0.706) / 0.001721, 2)


def pdr(a, b):                         # 拓樸矩陣：a 送給 b 的送達率（沒列＝聽不到＝0）
    for x in (a, b):
        if x in nodes and not nodes[x].on:
            return 0                   # 斷電的節點：收不到也回不了
    p = cfg.TOPO.get((a, b), cfg.TOPO.get((b, a), 0))
    return wall if p is None else p


def lucky(p):                          # 以機率 p 成功
    return random.getrandbits(16) < p * 65536


def unicast(src, dst):                 # 802.15.4 單播：收到要回 ACK，沒等到 ACK 最多重傳 3 次
    got = False
    for n in range(1, 5):
        if lucky(pdr(src, dst)):
            got = True                 # 訊框到了（重傳的重複訊框，對方看序號丟掉）
            if lucky(pdr(dst, src)):
                return got, n          # ACK 也回來了：這一包一共送了 n 次
    return got, 4


def radio(src, f):                     # 「無線電」：照拓樸矩陣決定這個訊框誰收得到
    d = w.decode(f)
    dst = w.layer(d, "mac")["dst"]
    show(src, f, d)
    if dst == w.BROADCAST:             # 廣播：沒有 ACK，每個鄰居各自收不收得到
        who = [a for a in [cfg.ROOT] + list(cfg.NODES) if a != src and lucky(pdr(src, a))]
    else:
        got, n = unicast(src, dst)
        if src in tries and kind(d) == "DATA":
            tries[src] += n            # 統計資料一共送了幾次（含重傳）
        who = [dst] if got else []
    for a in who:
        if a == cfg.ROOT:
            sock.sendto(f, A)          # root 在 A 板：真的經 Wi-Fi 送過去
        elif nodes[a].on:
            inbox.append((a, d))       # B 板上的節點：排隊，等一下交給它


def show(src, f, d):                   # 印十六進位（＋欄位樹），貼到電腦的 wsn_decode.py 對照
    global n2rank
    k = kind(d)
    if src == cfg.ROOT and k in cfg.SHOW_B and k not in shown:
        shown.append(k)
        print("==== 收到 root 的第一則 %s（%d 位元組）====" % (k, len(f)))
        print(w.hexdump(f))
        w.tree(d)
    if name(src) == "N2" and k == "DIO" and w.layer(d, "rpl")["rank"] != n2rank:
        n2rank = w.layer(d, "rpl")["rank"]
        print("[N2 送出的 DIO，Rank %d] %s" % (n2rank, w.hexs(f)))


def dodag():                           # 用 N1～N4 的父節點畫出 DODAG 文字樹
    kids = {}
    for a, n in nodes.items():
        if n.on and n.parent is not None:
            kids.setdefault(n.parent, []).append(a)
    n0 = nodes[min(nodes)]
    out = ["DODAG（版本 %d，%s）" % (n0.ver, "MRHOF" if n0.ocp else "OF0"), "R  Rank 256"]
    def walk(p, pre):
        ks = sorted(kids.get(p, []))
        for i, a in enumerate(ks):
            end = i == len(ks) - 1
            out.append(pre + ("└─ " if end else "├─ ") + "%s Rank %d（成本 %d）" % (name(a), nodes[a].rank, nodes[a].cost))
            if len(pre) < 12:
                walk(a, pre + ("   " if end else "│  "))
    walk(cfg.ROOT, "")
    off = [name(a) for a, n in sorted(nodes.items()) if n.parent is None]
    return "\n".join(out + (["還沒加入：" + "、".join(off)] if off else []))


nodes = {}
for a in sorted(cfg.NODES):
    nodes[a] = Node(a, radio, sense=read_temp)
inbox, shown, n2rank = [], [], None
tries = {a: 0 for a in cfg.NODES}      # 每個節點的資料傳送次數（含重傳、含幫別人轉送）
wall, last_tree, t_stat, t_btn, was = 1.0, None, time.ticks_ms(), 0, 1
while True:
    try:
        f, _ = sock.recvfrom(256)
        radio(cfg.ROOT, f)             # A 板送來的：root 的訊框
    except OSError:
        pass
    p = min(20, knob.read_u16() * 21 // 65536) / 20      # 旋鈕 → 0%～100%，每格 5%
    if p != wall:
        wall = p
        e = "聽不到" if p == 0 else "%.2f" % (1 / (p * p))
        print("旋鈕：root－N2 每個方向送達率 %d%%（理論 ETX＝1/(p×p)＝%s）" % (p * 100, e))
    if btn.value() == 0 and was == 1 and time.ticks_diff(time.ticks_ms(), t_btn) > 300:
        t_btn = time.ticks_ms()
        n2 = [a for a in nodes if name(a) == "N2"][0]
        if nodes[n2].on:
            nodes[n2].on = False
            print("按鈕：N2 斷電（其他節點要自己發現）")
        else:
            nodes[n2] = Node(n2, radio, sense=read_temp)
            print("按鈕：N2 重新開機")
    was = btn.value()
    for n in list(nodes.values()):
        n.tick()
    while inbox:
        a, d = inbox.pop(0)
        nodes[a].rx(d)
    k = [(a, n.parent, n.on) for a, n in sorted(nodes.items())]
    if k != last_tree:                 # 有人換父節點（或斷電、加入）：重畫一次樹
        last_tree = k
        print(dodag())
    if time.ticks_diff(time.ticks_ms(), t_stat) >= cfg.STATUS_MS:
        t_stat = time.ticks_ms()
        print("[狀態] 旋鈕 %d%%（每 %d 秒一次；冒號後面是到那個鄰居的 ETX）" % (wall * 100, cfg.STATUS_MS // 1000))
        for a, n in sorted(nodes.items()):
            print("  " + (n.status() + " 資料送了 %d 次" % tries[a] if n.on else name(a) + " 斷電中"))
    time.sleep_ms(5)
