import myid                 # 身份指紋（第一行）
# MicroPython 內建 cryptolib，不必額外安裝
from cryptolib import aes
import os, json, binascii

KEY = b'0123456789abcdef'   # 16 位元組 = AES-128

def pad(b):                 # PKCS#7：補到 16 的倍數
    n = 16 - len(b) % 16
    return b + bytes([n]) * n

def encrypt(msg):
    iv = os.urandom(16)     # 每次加密都要換一組新的 IV
    c = aes(KEY, 2, iv)     # mode 1 = ECB，mode 2 = CBC
    return iv + c.encrypt(pad(msg))

body = json.dumps({'id': 'n01', 't': 28.5}).encode()
print(binascii.hexlify(encrypt(body)))

def decrypt(blob):
    iv, ct = blob[:16], blob[16:]   # 前 16 位元組是 IV
    c = aes(KEY, 2, iv)             # 每次都要建新物件
    pt = c.decrypt(ct)
    return pt[:-pt[-1]]             # 去掉 PKCS#7 填補

blob = encrypt(b'{"id":"n01","t":28.5}')
print(decrypt(blob))

# 注意：cryptolib 只提供 ECB 與 CBC，沒有 GCM
# 也就是說「完整性」必須另外用 HMAC 補上
# 同一個 aes 物件不能重複使用，狀態會被帶著走
