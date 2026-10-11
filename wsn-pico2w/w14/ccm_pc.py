# ccm_pc.py：延伸挑戰 B（電腦端 Thonny 執行，不是板子）
# 板子的 cryptolib 只有 ECB、CBC；電腦端用 cryptography 套件的 AESCCM
# 先安裝：Thonny「工具 → 管理套件」搜尋 cryptography → 安裝
import os
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

key = os.urandom(16)                  # AES-128
body = b'{"id":"g07A","t":28.5}'      # 和 A 板同一種資料（22 B）
ccm = AESCCM(key, tag_length=8)       # 標籤 8 B（像 802.15.4 的 MIC-64）
nonce = os.urandom(13)                # 13 B；同一把金鑰下不能重複
ctr = (1).to_bytes(4, "big")          # 計數器：只驗證、不加密
ct = ccm.encrypt(nonce, body, ctr)    # 加密＋標籤一次完成
n = len(ctr) + len(nonce) + len(ct)
print("CCM 封包", n, "B（計數器 4＋nonce 13＋密文 22＋標籤 8）")
print("上機的 CBC＋HMAC", 4 + 16 + (len(body) // 16 + 1) * 16 + 32, "B")
print("解回來：", ccm.decrypt(nonce, ct, ctr))
bad = bytearray(ct)
bad[0] ^= 1                           # 改 1 個位元
try:
    ccm.decrypt(nonce, bytes(bad), ctr)
except Exception as e:
    print("改 1 個位元：", type(e).__name__)   # InvalidTag：被擋下
