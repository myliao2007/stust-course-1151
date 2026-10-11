# packet.py：資料格式表的程式版（A、B 兩片都要存）
# A：讀值 → 13 位元組 → IPv6＋UDP → 6LoWPAN 訊框（IPHC＋NHC 壓縮，附 FCS）
# B：13 位元組 → 拆回欄位 → 一行 JSON（欄位和主題 12 的儀表板一樣）
import struct
import wsnproto as w
import cfg
FMT = "<HhHhHHB"        # seq、溫度×100、濕度×100、溫度2×100、氣壓×10、照度、狀態
SIZE = 13               # struct.calcsize(FMT)：2＋2＋2＋2＋2＋2＋1
KEYS = ("t", "h", "t2", "p", "lux")
K = (100, 100, 100, 10, 1)                    # 放大幾倍再存成整數
NO = (-32768, 65535, -32768, 65535, 65535)    # 讀不到時送的記號（不送 0）
ST = ("ok", "part", "fake")                   # 狀態：都讀到／有缺值／假資料
SPORT, DPORT, HPORT = 0xF0B1, 0xF0B2, 0xF0B3  # UDP 埠：A 送、B 收資料、B 收報到
A_IP, B_IP = w.link_local(cfg.SHORT_A), w.link_local(cfg.SHORT_B)


def fake():                     # 假資料（原頁的 25.0、60.0）：感測器還沒接也能先走通
    return {"t": 25.0, "h": 60.0, "t2": None, "p": None, "lux": None, "fake": True}


def pack(seq, d):
    """d＝sensors.read_all() 的結果 → 13 位元組（小端序）。"""
    v = [n if d[k] is None else min(65534, round(d[k] * m)) for k, m, n in zip(KEYS, K, NO)]
    st = 2 if d.get("fake") else (1 if None in [d[k] for k in KEYS] else 0)
    return struct.pack(FMT, seq & 0xFFFF, v[0], v[1], v[2], v[3], v[4], st)


def unpack(b):
    """13 位元組 → 欄位；讀不到的記號換回 None。"""
    x = struct.unpack(FMT, b)
    d = {"seq": x[0], "st": ST[x[6]] if x[6] < 3 else "?"}
    for k, m, n, v in zip(KEYS, K, NO, x[1:6]):
        d[k] = None if v == n else (v if m == 1 else v / m)
    return d


def frame(seq, data, dport=DPORT):
    """IPv6＋UDP → 802.15.4＋6LoWPAN 訊框（附 FCS）；放得下就只有一個訊框。"""
    pkt = w.ipv6_udp(A_IP, B_IP, SPORT, dport, data)
    return w.frames_ipv6(seq & 0xFF, cfg.PAN, cfg.SHORT_A, cfg.SHORT_B, pkt)


def num(v):                     # 缺值寫成 null（JSON 的「沒有值」），不要寫 0
    return "null" if v is None else str(v)


def show(d):                    # 一行人看的讀值（d＝unpack 的結果）
    return "t %s h %s t2 %s p %s lux %s %s" % (
        num(d["t"]), num(d["h"]), num(d["t2"]), num(d["p"]), num(d["lux"]), d["st"])


JSON = ('{"id":"%sa","seq":%d,"t":%s,"h":%s,"p":%s,"lux":%s,"t2":%s,'
        '"st":"%s","n":%d,"loss":%.1f,"ts":"%s"}')


def to_json(d, n, loss, ts):
    """B 送上 MQTT 的一行：前 7 個欄位和主題 12 一樣，後面是邊界路由器補的。"""
    return JSON % (cfg.G, d["seq"], num(d["t"]), num(d["h"]), num(d["p"]),
                   num(d["lux"]), num(d["t2"]), d["st"], n, loss, ts)


class Loss:
    """照座號點名：seq 應該一號接一號，跳過幾號就是掉了幾筆。"""
    def __init__(self):
        self.last = None
        self.got = 0                        # 實收（不同的 seq 有幾個）
        self.exp = 0                        # 應收
        self.restart = 0                    # A 重開機幾次（seq 往回跳）

    def add(self, seq):
        """新的一號回傳 True；同一號重複收到（廣播會重送）回傳 False。"""
        if self.last is None:
            self.last, self.got, self.exp = seq, 1, 1
            return True
        d = (seq - self.last) & 0xFFFF      # 跨過 65535 → 0 也算得對
        if d == 0:
            return False
        if d > 0x8000:                      # 號碼往回跳：A 重開機，從這一號重新點
            self.restart += 1
            d = 1
        self.last = seq
        self.got += 1
        self.exp += d
        return True

    def rate(self):                         # 遺失率（%）
        return 0.0 if self.exp == 0 else (self.exp - self.got) * 100 / self.exp
