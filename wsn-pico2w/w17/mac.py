# mac.py：用內建 hashlib 寫 HMAC-SHA256（RFC 2104），不用上網安裝
# 算出來的是訊息驗證碼（MAC），不是數位簽章
import hashlib

def hmac_sha256(key, msg):
    if len(key) > 64:                       # 金鑰比區塊長：先雜湊成 32 B
        key = hashlib.sha256(key).digest()
    key = key + bytes(64 - len(key))        # 補 0 到 64 B（SHA-256 一個區塊）
    ipad = bytes(k ^ 0x36 for k in key)     # 內層用的金鑰
    opad = bytes(k ^ 0x5C for k in key)     # 外層用的金鑰
    inner = hashlib.sha256(ipad + msg).digest()
    return hashlib.sha256(opad + inner).digest()   # 32 B

def same(a, b):                             # 比對 MAC：每個位元組都看完才回答
    if len(a) != len(b):
        return False
    d = 0
    for x, y in zip(a, b):
        d |= x ^ y
    return d == 0
