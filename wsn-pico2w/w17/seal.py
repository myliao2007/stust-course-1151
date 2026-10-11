# seal.py：AES-CBC 加密＋Encrypt-then-MAC 封包（A 用 seal 封、B 用 unseal 拆）
# 封包＝計數器 4 B＋IV 16 B＋密文＋MAC 32 B；MAC 算在前三段上
from cryptolib import aes
import os, struct
from mac import hmac_sha256, same

def pad(b):                    # PKCS#7：補到 16 的倍數（剛好整除也補一整塊）
    n = 16 - len(b) % 16
    return b + bytes([n]) * n

def unpad(b):
    n = b[-1]
    if n < 1 or n > 16 or b[-n:] != bytes([n]) * n:
        raise ValueError("填補不對")
    return b[:-n]

def encrypt(key, body, iv=None):            # 任務一：只加密（IV＋密文）
    iv = iv or os.urandom(16)               # 每筆換新 IV；iv 參數只給測試用
    return iv + aes(key, 2, iv).encrypt(pad(body))   # mode 2 = CBC

def decrypt(key, blob):                     # 任務一：只解密，被改過也不知道
    return unpad(aes(key, 2, blob[:16]).decrypt(blob[16:]))

def seal(enc_key, mac_key, ctr, body, iv=None):
    head = struct.pack(">I", ctr)            # 計數器 4 B（大端序）
    blob = encrypt(enc_key, body, iv)        # ① 先加密：IV＋密文
    return head + blob + hmac_sha256(mac_key, head + blob)   # ② 再算 MAC

def unseal(enc_key, mac_key, pkt, last):
    """回傳 (結果, 計數器, 明文)。結果是 ok、長度不對、MAC 不符、重放 其中一個。"""
    if len(pkt) < 68 or (len(pkt) - 52) % 16:
        return "長度不對", None, None
    msg, tag = pkt[:-32], pkt[-32:]
    if not same(hmac_sha256(mac_key, msg), tag):     # ① 先驗 MAC
        return "MAC 不符", None, None
    ctr = struct.unpack(">I", msg[:4])[0]
    if ctr <= last:                                  # ② 計數器要比上次大
        return "重放", ctr, None
    return "ok", ctr, decrypt(enc_key, msg[4:])      # ③ 最後才解密
