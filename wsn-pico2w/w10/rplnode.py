# rplnode.py：一個 RPL 節點的邏輯（A 板的 root、B 板的 N1～N4 都用這個類別）
# 封包都是真正的 802.15.4＋6LoWPAN＋IPv6 位元組（wsnproto 組／拆），只有「無線電」換成 Wi-Fi UDP
import time, random
import wsnproto as w
import cfg
from trickle import Trickle

INF = w.INFINITE_RANK                    # 0xFFFF：Rank 無限大＝「不要選我」
MAX_ETX = 512 / 128                      # MRHOF 的 MAX_LINK_METRIC 512＝ETX 4，超過不列入候選
SWITCH = 192                             # MRHOF 的 PARENT_SWITCH_THRESHOLD：好 192 以上才換
PROBE_PORT, DATA_PORT = 0xF0B0, 0xF0B1   # 61616 探測、61617 資料（埠號能壓成 4 位元）
PRE = w.ip6(cfg.PREFIX)[:8]
T0 = time.ticks_ms()


def now():
    return time.ticks_ms()


def age(t):                              # 從 t 到現在過了幾毫秒（會處理 ticks 繞回）
    return time.ticks_diff(now(), t)


def gaddr(a):                            # 全域位址：2001:db8:1::/64＋短位址推出的 IID
    return PRE + w.iid(a)


def name(a):
    return "R" if a == cfg.ROOT else cfg.NODES.get(a, "%04x" % a)


def kind(d):                             # 這個訊框是哪一種（印十六進位、統計用）
    r, u = w.layer(d, "rpl"), w.layer(d, "udp")
    if r:
        return ("DIS", "DIO", "DAO", "DAO-ACK", "RPL")[min(r["code"], 4)]
    if u:
        return "ETX" if u["dport"] == PROBE_PORT else "DATA"
    return "?"


class Nb:                                # 鄰居表的一列
    def __init__(self):
        self.rank, self.ver = INF, None  # 對方最近一則 DIO 的 Rank 與版本
        self.first = self.last = now()   # 第一次、最後一次聽到對方的時間
        self.got = []                    # 最近收到對方探測的時間（算 Dr）
        self.df, self.df_t = 0, now()    # 對方說「我收到你幾成」（Df）

    def heard(self):                     # 最近 WINDOW 則探測收到幾則、照理該收到幾則
        win = (cfg.WINDOW + 0.5) * cfg.PROBE_MS
        self.got = [t for t in self.got if age(t) < win]
        exp = max(cfg.WINDOW // 2, age(self.first) // cfg.PROBE_MS)
        exp = min(cfg.WINDOW, exp)       # 新鄰居至少當 10 則算，才不會太樂觀
        return min(len(self.got), exp), exp

    def etx(self):                       # ETX＝1／(Df×Dr)；有一邊是 0 就連不上（None）
        g, e = self.heard()
        df = self.df if age(self.df_t) < cfg.PARENT_TIMEOUT_MS else 0
        return w.etx(df, g / e)


class Node:
    def __init__(self, addr, tx, root=False, sense=None):
        self.me, self.tx, self.root, self.sense = addr, tx, root, sense
        self.nbs = {}                    # 鄰居表：短位址 → Nb
        self.routes = {}                 # 下行路由（storing）：目標短位址 → 下一跳
        self.seq = random.getrandbits(8) # 802.15.4 序號
        self.ver = 240                   # DODAG 版本（lollipop 計數器初值 240）
        self.ocp, self.min_hop = cfg.OCP, cfg.MIN_HOP
        self.trickle = Trickle(cfg.DIO_IMIN, cfg.DIO_DOUBLINGS, cfg.DIO_K)
        self.buf, self.dseq, self.stats = [], 0, {}
        self.dao_seq, self.dao_at, self.dao_try = 0, None, 0
        self.poison_t, self.on = None, True
        self.t_probe = self.t_data = self.t_choose = now()
        self.t_dis = time.ticks_add(now(), -cfg.DIS_MS)   # 開機馬上送第一則 DIS
        self.detach()
        if root:                         # ROOT_RANK＝MinHopRankIncrease＝256
            self.rank = self.low = cfg.MIN_HOP

    def log(self, msg):
        print("[%6.1fs %s] %s" % (age(T0) / 1000, name(self.me), msg))

    def detach(self):
        self.parent, self.rank, self.cost, self.low = None, INF, None, INF

    # ---------- 送：IPv6 封包 → 802.15.4 訊框 → 交給「無線電」 ----------
    def send(self, dst, pkt):
        for f in w.frames_ipv6(self.seq, cfg.PAN_ID, self.me, dst, pkt):
            self.seq = (self.seq + 1) & 0xFF
            self.tx(self.me, f)

    def rpl(self, dst, code, body):      # RPL 控制訊息＝ICMPv6 類型 155
        ip = w.ALL_RPL_NODES if dst == w.BROADCAST else w.link_local(dst)
        self.send(dst, w.ipv6_icmp(w.link_local(self.me), ip, 155, code, body, hlim=255))

    def dio(self):                       # DIO：版本、Rank、DODAG 設定（Trickle、OF）、前綴
        conf = w.opt_conf(doublings=cfg.DIO_DOUBLINGS, imin=cfg.DIO_IMIN,
                          redundancy=cfg.DIO_K, max_rank_inc=cfg.MAX_RANK_INC,
                          min_hop=self.min_hop, ocp=self.ocp)
        body = w.rpl_dio(self.rank, gaddr(cfg.ROOT), version=self.ver, dtsn=self.ver,
                         options=conf + w.opt_prefix(cfg.PREFIX))
        self.rpl(w.BROADCAST, w.RPL_DIO, body)

    def dao(self, life=0xFF, to=None, tg=None):   # DAO：往上報到；life＝0 是撤銷路由
        tg = [self.me] + list(self.routes) if tg is None else tg
        opts = b"".join(w.opt_target(gaddr(a)) for a in tg)
        self.dao_seq = (self.dao_seq + 1) & 0xFF
        body = w.rpl_dao(self.dao_seq, k=1 if life else 0,
                         options=opts + w.opt_transit(life))
        self.rpl(self.parent if to is None else to, w.RPL_DAO, body)

    def probe(self):                     # 探測：告訴鄰居「最近我收到你幾則」（量 ETX）
        s = "ETX"
        for a, n in self.nbs.items():
            s += " %s=%d/%d" % ((name(a),) + n.heard())
        pkt = w.ipv6_udp(w.link_local(self.me), w.ip6("ff02::1"),
                         PROBE_PORT, PROBE_PORT, s.encode())
        self.send(w.BROADCAST, pkt)

    # ---------- 資料：一跳一跳往 root 送 ----------
    def up(self, src, hlim, data):       # 送一筆資料（自己的，或幫子節點轉的）
        pkt = w.ipv6_udp(src, gaddr(cfg.ROOT), DATA_PORT, DATA_PORT, data, hlim=hlim)
        if self.parent is None:          # 還沒有父節點：真的存起來，最多 5 筆
            self.buf = (self.buf + [pkt])[-5:]
            self.log("還沒有父節點，先暫存（%d 筆）" % len(self.buf))
        else:
            self.send(self.parent, pkt)

    def on_data(self, ip, data):         # 收到一筆資料
        if not self.root:                # 不是給我的：Hop Limit 減 1，往父節點轉送
            if ip["hlim"] > 1:
                self.up(ip["src"], ip["hlim"] - 1, data)
            return
        a = (ip["src"][14] << 8) | ip["src"][15]       # 位址最後 2 位元組＝短位址
        relay = 64 - ip["hlim"]          # root：來源送出時是 64，每經過一台中繼減 1
        s = self.stats.setdefault(a, [0, None, 0])     # [收到幾筆, 第一個序號, 最後序號]
        q = int(data.decode().split("#")[1])
        s[0], s[1], s[2] = s[0] + 1, q if s[1] is None else s[1], q
        lost = 100 - 100 * s[0] // (s[2] - s[1] + 1)
        self.log("收到 %s：%s｜Hop Limit %d → 經過 %d 台中繼、%d 跳｜遺失 %d%%" % (
            name(a), data.decode(), ip["hlim"], relay, relay + 1, lost))

    # ---------- 收：「無線電」把解好的訊框 d 交給我 ----------
    def rx(self, d):
        mac = w.layer(d, "mac")
        if not self.on or mac["dpan"] != cfg.PAN_ID or mac["dst"] not in (self.me, w.BROADCAST):
            return                       # 關機、別組的 PAN、不是給我的：丟掉
        src = mac["src"]
        n = self.nbs.get(src)
        if n is None:
            n = self.nbs[src] = Nb()
        n.last = now()
        r, u = w.layer(d, "rpl"), w.layer(d, "udp")
        if r:
            self.on_rpl(src, n, r)
        elif u and u["dport"] == PROBE_PORT:
            n.got.append(now())          # Dr：我又收到 src 一則探測
            for tok in u["data"].decode().split()[1:]:   # 例："N2=17/20"
                k, v = tok.split("=")
                if k == name(self.me):   # Df：src 說它收到我幾則
                    g, e = v.split("/")
                    n.df, n.df_t = int(g) / int(e), now()
        elif u and u["dport"] == DATA_PORT:
            self.on_data(w.layer(d, "ipv6"), u["data"])

    def on_rpl(self, src, n, r):
        c = r["code"]
        if c == w.RPL_DIS and self.rank != INF:
            self.trickle.reset()         # 有新鄰居在問：DIO 間隔縮回 Imin
        elif c == w.RPL_DIO:
            self.on_dio(src, n, r)
        elif c == w.RPL_DAO:
            self.on_dao(src, r)
        elif c == w.RPL_DAO_ACK and r["seq"] == self.dao_seq:
            self.dao_at = None
            self.log("收到 %s 的 DAO-ACK（序號 %d，狀態 %d）" % (name(src), r["seq"], r["status"]))

    def on_dio(self, src, n, r):
        n.rank, n.ver = r["rank"], r["version"]
        if self.root:
            if n.ver == self.ver:
                self.trickle.heard()
            return
        if ((n.ver - self.ver) & 0xFF) in range(1, 128):   # 版本變新：root 做了全域修復
            self.log("版本 %d → %d：全域修復，全部重新選父節點" % (self.ver, n.ver))
            self.ver, self.routes, self.poison_t = n.ver, {}, None
            self.detach()
            for m in self.nbs.values():
                m.rank = INF if m is not n else m.rank   # 舊版本的 Rank 不算數
        for o in r["opts"]:
            if o["type"] == 4:           # DODAG 設定選項：照 root 指定的目標函數與層高
                self.ocp, self.min_hop = o["ocp"], o["min_hop"]
        before = (self.parent, self.rank)
        self.choose()
        if (self.parent, self.rank) == before and n.ver == self.ver:
            self.trickle.heard()         # 一致的 DIO（沒讓我改變任何事）：c 加 1

    def on_dao(self, src, r):            # 子節點報到（storing 模式：每一台都記下行路由）
        life, tg, gone = 0xFF, [], []
        for o in r["opts"]:
            if o["type"] == 5:           # RPL 目標：位址最後 2 位元組就是短位址
                tg.append((o["prefix"][14] << 8) | o["prefix"][15])
            elif o["type"] == 6:         # 轉送資訊：路徑壽命（0＝撤銷）
                life = o["lifetime"]
        for a in tg:
            if life:
                self.routes[a] = src
            elif self.routes.get(a) == src:
                del self.routes[a]       # No-Path DAO：撤銷經過 src 的路由
                gone.append(a)
        if r["k"]:
            self.rpl(src, w.RPL_DAO_ACK, w.rpl_dao_ack(r["seq"]))
        self.log("%s 的 DAO（%s）→ 下行路由：%s" % (name(src), "報到" if life else "撤銷",
                 "、".join("%s→%s" % (name(a), name(b)) for a, b in sorted(self.routes.items()))))
        if not self.root and self.parent is not None:
            if life:
                self.dao_at, self.dao_try = now(), 0     # 也往上報，root 才知道怎麼走下來
            elif gone:
                self.dao(0, None, gone)                  # 撤銷也要往上傳，上游才不會留舊路

    # ---------- 選父節點（OF0 或 MRHOF） ----------
    def via(self, n, e):                 # 經過鄰居 n：（路徑成本, 我會變成的 Rank）
        if self.ocp == 0:                # OF0：每跳加 3×256，不看鏈路品質
            r = w.of0_rank(n.rank, self.min_hop)
            return r, r
        return w.mrhof_cost(n.rank, e), w.mrhof_rank(n.rank, e, self.min_hop)

    def choose(self):
        if self.root or self.poison_t is not None or not self.on:
            return
        cand = {}
        for a, n in self.nbs.items():
            e = n.etx()
            if n.rank == INF or n.ver != self.ver or e is None or (self.ocp and e > MAX_ETX):
                continue                 # 還沒加入、舊版本、連不上、鏈路太爛：不考慮
            cand[a] = self.via(n, e)
        cur = cand.get(self.parent)
        lim = cur[1] if cur else self.rank           # 我現在的 Rank
        best = None
        for a, (cost, rank) in cand.items():         # 只考慮 Rank 比我小的鄰居（防迴圈）
            if a != self.parent and self.nbs[a].rank < lim:
                if best is None or cost < cand[best][0]:
                    best = a
        need = SWITCH if self.ocp == 1 else 1        # OF0 嚴格變小就換；MRHOF 要好 192
        if cur and (best is None or cur[0] - cand[best][0] < need):
            best = self.parent                       # 現在的父節點還能用，又沒有好很多的
        if best is not None:
            self.set_parent(best, cand[best])
        elif self.parent is not None or self.rank != INF:
            self.poison("父節點 %s 不能用了，又沒有 Rank 比我小的鄰居" % name(self.parent))

    def set_parent(self, a, cr):
        if self.low != INF and cr[1] > self.low + cfg.MAX_RANK_INC:
            self.poison("新 Rank %d 超過 L＋MaxRankIncrease" % cr[1])
            return
        old, oldr = self.parent, self.rank
        self.parent, (self.cost, self.rank) = a, cr
        self.low = min(self.low, self.rank)
        if a != old:
            self.log("父節點 %s → %s｜Rank %s → %d｜路徑成本 %d" % (name(old) if old else "無",
                     name(a), oldr if oldr != INF else "無限大", self.rank, self.cost))
            if old is not None and old in self.nbs:
                self.dao(0, old)                     # 跟舊父節點說：經過你的路撤銷
            self.dao_at, self.dao_try = now(), 0
            self.trickle.reset()
            for pkt in self.buf:                     # 有父節點了：把暫存的資料送出去
                self.send(a, pkt)
            self.buf = []
        elif oldr // self.min_hop != self.rank // self.min_hop:
            self.log("Rank %d → %d（換樓層，重置 Trickle）" % (oldr, self.rank))
            self.trickle.reset()

    def poison(self, why):               # 毒化：宣告 Rank 無限大，等子孫先離開再重新找
        self.log("毒化：%s → 廣播 Rank 0xFFFF，%.0f 秒後重新找" % (why, cfg.POISON_MS / 1000))
        self.parent, self.rank, self.cost = None, INF, None
        self.poison_t = now()
        self.trickle.reset()
        self.dio()

    # ---------- 計時器：主迴圈一直呼叫 ----------
    def tick(self):
        if not self.on:
            return
        if age(self.t_probe) >= cfg.PROBE_MS:
            self.t_probe = now()
            self.probe()
        p = self.nbs.get(self.parent)
        if p and age(p.last) > cfg.PARENT_TIMEOUT_MS:
            self.log("父節點 %s %.0f 秒沒聲音 → 本地修復" % (
                name(self.parent), cfg.PARENT_TIMEOUT_MS / 1000))
            self.choose()                # 太久沒聽到的鄰居 ETX 算不出來，不會被選
        if self.poison_t is not None and age(self.poison_t) >= cfg.POISON_MS:
            self.poison_t = None
            self.rpl(w.BROADCAST, w.RPL_DIS, w.rpl_dis())
        if age(self.t_choose) >= cfg.PROBE_MS:       # ETX 一直在變：每 0.5 秒重新評估
            self.t_choose = now()
            self.choose()
        go = self.trickle.poll()
        if go is not None and (self.rank != INF or self.poison_t is not None):
            if go:
                self.dio()
            if name(self.me) in cfg.LOG_TRICKLE:
                self.log("Trickle I=%.3f s t=%.2f s c=%d → %s（Rank %d）" % (
                    self.trickle.i / 1000, self.trickle.t / 1000, self.trickle.c,
                    "送出 DIO" if go else "壓下", self.rank))
        if not self.root:
            self.timers()

    def timers(self):
        if self.rank == INF and self.poison_t is None and age(self.t_dis) >= cfg.DIS_MS:
            self.t_dis = now()
            self.rpl(w.BROADCAST, w.RPL_DIS, w.rpl_dis())   # 還沒加入：問附近有沒有 DODAG
        if self.dao_at is not None and self.parent is not None:
            if age(self.dao_at) >= cfg.DAO_DELAY_MS:
                if self.dao_try < 3:     # 等 DAO-ACK；沒等到每 1 秒重送，最多 3 次
                    self.dao()
                    self.dao_at, self.dao_try = now(), self.dao_try + 1
                else:
                    self.dao_at = None
        if self.sense and age(self.t_data) >= cfg.DATA_MS:
            self.t_data = now()
            self.dseq += 1
            txt = "%s T=%.1f #%d" % (name(self.me), self.sense(), self.dseq)
            self.up(gaddr(self.me), 64, txt.encode())

    def status(self):                    # 一行狀態：父節點、Rank、路徑成本、到每個鄰居的 ETX
        s = "%s 父=%s Rank=%s 成本=%s |" % (name(self.me), name(self.parent) if self.parent
                                          else "無", self.rank if self.rank != INF else "∞", self.cost)
        for a, n in sorted(self.nbs.items()):
            e = n.etx()
            s += " %s:%s" % (name(a), "--" if e is None else "%.2f" % e)
        return s
