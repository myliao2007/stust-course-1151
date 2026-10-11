# border.py：邊界路由器「收訊框」的那一半（B 板；br_b.py、power_b.py 都用它）
# 驗 FCS → 解壓縮 → 認出是 DIS、報到還是資料；DIS 就回 DIO，資料就拆成欄位
import socket, time
import wsnproto as w
import cfg, packet
RANK = 256                       # RPL：根（B）的 Rank＝MinHopRankIncrease（主題 10）
DODAG = w.ip6("2001:db8:1::ff:fe00:1")       # DODAG 的名字：B 的全域位址


class Border:
    def __init__(self, show=3):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(("0.0.0.0", cfg.PORT_B))
        self.s.setblocking(False)            # 沒有訊框就馬上回來，不卡住主迴圈
        self.r = w.Reassembler(timeout_ms=5000)
        self.loss = packet.Loss()            # 用 A 的 seq 點名（主題 15）
        self.n = self.ok = self.bad = 0      # 收到幾個訊框、全對、丟掉
        self.show = show                     # 前幾個訊框印十六進位＋欄位樹
        self.last = None                     # 最後一次收到 A 的時間（算新鮮度）
        self.dsn = 0                         # B 自己的 802.15.4 序號

    def poll(self):
        """收一個訊框；是 A 的資料就回傳拆好的 dict，其他（或沒收到）回傳 None。"""
        try:
            f, src = self.s.recvfrom(256)
        except OSError:
            return None
        self.n += 1
        d = w.decode(f, fcs=True, reasm=self.r)
        if self.show > 0:
            self.show -= 1
            print("==== 第 %d 個訊框（%d 位元組，來自 %s）====" % (self.n, len(f), src[0]))
            print(w.hexdump(f))
            w.tree(d)
        if not w.ok(d):                      # FCS 或 checksum 不對：整個丟掉
            self.bad += 1
            print("丟掉第 %d 個訊框：%s" % (self.n, w.errors(d)))
            return None
        self.ok += 1
        self.last = time.ticks_ms()
        r, u = w.layer(d, "rpl"), w.layer(d, "udp")
        if r and r["code"] == w.RPL_DIS:     # A 在問「有 DODAG 嗎？」：回一則 DIO
            self.dio(src[0])
        elif u and u["dport"] == packet.HPORT:
            print("A 報到：", u["data"].decode())
        elif u and u["dport"] == packet.DPORT and len(u["data"]) == packet.SIZE:
            x = packet.unpack(u["data"])
            x["n"] = len(f)
            self.loss.add(x["seq"])
            return x
        return None

    def dio(self, ip):               # 我是根：Rank 256、目標函數 OF0
        body = w.rpl_dio(RANK, DODAG, options=w.opt_conf(min_hop=RANK, ocp=0))
        pkt = w.ipv6_icmp(packet.B_IP, packet.A_IP, 155, w.RPL_DIO, body, hlim=255)
        for f in w.frames_ipv6(self.dsn, cfg.PAN, cfg.SHORT_B, cfg.SHORT_A, pkt):
            self.s.sendto(f, (ip, cfg.PORT_A))
        self.dsn = (self.dsn + 1) & 0xFF
        print("回 DIO 給 %s：我是根，Rank %d" % (ip, RANK))

    def line(self):                  # 一行統計
        l = self.loss
        return "訊框 %d（全對 %d、丟掉 %d）｜A 應收 %d、實收 %d、遺失 %.1f %%｜A 重開機 %d 次" % (
            self.n, self.ok, self.bad, l.exp, l.got, l.rate(), l.restart)
