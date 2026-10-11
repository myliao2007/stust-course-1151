# lwcrypto.py：LoRaWAN 1.0.x 用到的 AES 小工具（任務三、四；A、B 兩片都要存）
# 多位元組欄位在空中一律小端序（低位元組先送）；EUI 寫的時候是大端序，要反過來
import cryptolib


def aes(key, block):               # AES-128 加密一個 16 位元組區塊（ECB）
    return cryptolib.aes(key, 1).encrypt(block)


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def dbl(b):                        # 子金鑰：整塊左移 1 位元，溢出就 XOR 0x87
    out, c = bytearray(16), 0
    for i in range(15, -1, -1):
        out[i] = ((b[i] << 1) | c) & 0xFF
        c = b[i] >> 7
    out[15] ^= 0x87 if c else 0
    return bytes(out)


def cmac(key, msg):                # AES-CMAC（RFC 4493）；MIC 取前 4 個位元組
    k1 = dbl(aes(key, bytes(16)))  # 兩把子金鑰
    k2 = dbl(k1)
    n = max(1, (len(msg) + 15) // 16)
    last = msg[16 * (n - 1):]
    if len(last) == 16:            # 最後一塊剛好滿：XOR K1
        last = xor(last, k1)
    else:                          # 不滿：補 0x80 和 0，XOR K2
        last = xor(last + b"\x80" + bytes(15 - len(last)), k2)
    x = bytes(16)
    for i in range(n - 1):         # 一塊一塊 XOR 再加密（像 CBC 串起來）
        x = aes(key, xor(x, msg[16 * i:16 * i + 16]))
    return aes(key, xor(x, last))


def le(v, n):                      # 整數 → n 個位元組（小端序）
    return v.to_bytes(n, "little")


def u(b):                          # 位元組（小端序）→ 整數
    return int.from_bytes(b, "little")


def rev(b):                        # EUI 反過來（大端序 ↔ 小端序）
    return bytes(reversed(b))


def join_request(app_key, join_eui, dev_eui, dev_nonce):    # 23 位元組
    m = b"\x00" + rev(join_eui) + rev(dev_eui) + le(dev_nonce, 2)
    return m + cmac(app_key, m)[:4]


def join_accept(app_key, app_nonce, net_id, dev_addr):      # 17 位元組
    # 最後兩個位元組：0x02＝RX2 用 DR2（SF10）、0x01＝RX1 延遲 1 秒
    m = b"\x20" + le(app_nonce, 3) + le(net_id, 3) + le(dev_addr, 4) + b"\x02\x01"
    m += cmac(app_key, m)[:4]      # 加上 MIC
    return m[:1] + cryptolib.aes(app_key, 1).decrypt(m[1:])  # 伺服器用「解密」來加密


def open_accept(app_key, f):       # 裝置：還原 Join Accept，檢查 MIC
    m = f[:1] + aes(app_key, f[1:17])
    ok = cmac(app_key, m[:13])[:4] == m[13:17]
    return ok, u(m[1:4]), u(m[4:7]), u(m[7:11])   # 對不對、AppNonce、NetID、DevAddr


def skeys(app_key, app_nonce, net_id, dev_nonce):  # → (NwkSKey, AppSKey)
    t = le(app_nonce, 3) + le(net_id, 3) + le(dev_nonce, 2) + bytes(7)
    return aes(app_key, b"\x01" + t), aes(app_key, b"\x02" + t)


def blk(b0, dev_addr, fcnt, up, last):      # 資料訊框的 B0／Ai 區塊
    return bytes((b0, 0, 0, 0, 0, 0 if up else 1)) + le(dev_addr, 4) + le(fcnt, 4) + bytes((0, last))


def crypt(app_skey, dev_addr, fcnt, data, up=True):   # FRMPayload 加密＝解密
    out = b""
    for k in range(0, len(data), 16):
        out += xor(data[k:k + 16], aes(app_skey, blk(1, dev_addr, fcnt, up, k // 16 + 1)))
    return out


def mic(nwk_skey, dev_addr, fcnt, m, up=True):        # 資料訊框的 MIC（4 位元組）
    return cmac(nwk_skey, blk(0x49, dev_addr, fcnt, up, len(m)) + m)[:4]


def uplink(nwk_skey, app_skey, dev_addr, fcnt, port, data):   # 不需確認的上行
    m = b"\x40" + le(dev_addr, 4) + b"\x00" + le(fcnt & 0xFFFF, 2) + bytes((port,))
    m += crypt(app_skey, dev_addr, fcnt, data)
    return m + mic(nwk_skey, dev_addr, fcnt, m)
