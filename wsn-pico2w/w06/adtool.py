# adtool.py：AD 結構的打包與拆解（A、B 都要存）
def ad(t, data):        # 打包一段：長度、型別、資料
    return bytes((len(data) + 1, t)) + data

def split_ad(adv):      # 拆成 [(型別, 資料)…]
    out, i = [], 0
    while i + 1 < len(adv):
        n = adv[i]      # 長度＝型別 1＋資料 N
        if n == 0:      # 長度 0：後面沒資料了
            break
        body = bytes(adv[i + 2:i + 1 + n])
        out.append((adv[i + 1], body))
        i += 1 + n
    return out

def find(ads, t):       # 找某個型別，沒有回 None
    for tt, d in ads:
        if tt == t:
            return d
    return None

def mine(ads, group):   # 製造商資料＝FF FF＋組號？
    d = find(ads, 0xFF)
    me = bytes((0xFF, 0xFF, group))
    return d is not None and d[:3] == me

TYPE = {0x01: "Flags", 0x03: "UUID16 清單",
        0x09: "完整名稱", 0x16: "服務資料",
        0xFF: "製造商資料"}
PDU = {0: "ADV_IND", 1: "ADV_DIRECT_IND",
       2: "ADV_SCAN_IND", 3: "ADV_NONCONN_IND",
       4: "SCAN_RSP"}
