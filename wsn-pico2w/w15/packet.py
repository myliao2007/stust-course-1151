# packet.py：資料格式表的程式版（A、B 都要存；電腦上的 Python 也能跑）
# 1. BLE 廣播（A → B）：製造商資料 12 位元組，小端序
# 2. seq 點名：算應收、實收、遺失率
# 3. UDP 回報（B → A）：一行 JSON
import struct
FMT = "<HBHhHHB"    # 製造商代碼、組號、seq、溫度×100、濕度×100、照度、狀態
SIZE = 12           # struct.calcsize(FMT)
ST = ("ok", "sub", "err")                   # 狀態碼 0、1、2
NO_T, NO_H, NO_LX = -32768, 65535, 65535    # 缺值記號：讀不到就送這個，不送 0


def ad(t, data):                            # 一段 AD 結構：長度、型別、資料
    return bytes((len(data) + 1, t)) + data


def pack(mfg, group, seq, d, name):
    """d＝sensors.read_all() 的結果；回傳整個廣播封包（Flags＋名稱＋製造商資料）。"""
    t = NO_T if d["t"] is None else round(d["t"] * 100)
    h = NO_H if d["h"] is None else round(d["h"] * 100)
    lx = NO_LX if d["lx"] is None else min(65534, round(d["lx"]))
    body = struct.pack(FMT, mfg, group, seq & 0xFFFF, t, h, lx, ST.index(d["st"]))
    return ad(0x01, b"\x06") + ad(0x09, name.encode()) + ad(0xFF, body)


def unpack(adv, mfg, group):
    """從廣播封包找出自己組的製造商資料；不是自己組的回傳 None。"""
    i = 0
    while i + 1 < len(adv):
        n = adv[i]                          # 長度＝型別 1＋資料
        if n == 0:
            break
        if adv[i + 1] == 0xFF and n - 1 == SIZE:
            m, g, seq, t, h, lx, st = struct.unpack(FMT, bytes(adv[i + 2:i + 1 + n]))
            if m == mfg and g == group:
                return {"seq": seq, "t": None if t == NO_T else t / 100,
                        "h": None if h == NO_H else h / 100,
                        "lx": None if lx == NO_LX else lx, "st": ST[st]}
        i += 1 + n
    return None


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


REPORT = ('{"id":"g%02d","n":%d,"seq":%s,"t":%s,"h":%s,"lx":%s,"st":"%s",'
          '"rssi":%s,"got":%d,"exp":%d,"loss":%.1f}')


def num(v, f="%d"):                         # 缺值寫成 null（JSON 的「沒有值」），不要寫 0
    return "null" if v is None else f % v


def report(group, n, d, rssi, loss):
    """B 每一輪送給 A 的一行 JSON：d＝這一輪最後一筆讀值（可能是 None）、rssi＝這一輪平均。"""
    d = d or {}
    return REPORT % (group, n, num(d.get("seq")), num(d.get("t"), "%.2f"), num(d.get("h"), "%.2f"),
                     num(d.get("lx")), d.get("st", "none"), num(rssi), loss.got, loss.exp, loss.rate())
