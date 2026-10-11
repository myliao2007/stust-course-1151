import myid                       # 身份指紋（第一行）

def parse_iphc(pkt):
    b0, b1 = pkt[0], pkt[1]
    if (b0 >> 5) != 0b011:
        return None          # 不是 IPHC 壓縮標頭
    tf = (b0 >> 3) & 0b11
    nh = (b0 >> 2) & 0b1
    hlim = b0 & 0b11
    sam = (b1 >> 4) & 0b11
    dam = b1 & 0b11
    hop = {1: 1, 2: 64, 3: 255}.get(hlim, "inline")
    print("TF=%d NH=%d HopLimit=%s" % (tf, nh, hop))
    print("SAM=%d DAM=%d" % (sam, dam))
    return tf, nh, hlim, sam, dam

parse_iphc(bytes([0x7A, 0x33]))   # 驗證用的測試資料
parse_iphc(bytes([0x7E, 0x33]))   # 任務三：B 收到的那兩個位元組
