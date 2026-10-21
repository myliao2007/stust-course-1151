# 練習一：AES-128 加密速度比賽（內建 cryptolib 對上純 Python）
import myid                      # 第一行：印出身份指紋
import cryptolib, time

KEY = bytes(range(16))           # 128 位元金鑰：00 01 02 … 0F
IV = bytes(range(0xA1, 0xB1))    # CBC 模式的初始向量：A1 A2 … B0
SIZE = 2048                      # 每次加密 2 KB（必須是 16 的倍數）
ROUNDS_C = 50                    # 內建模組很快，跑 50 次
ROUNDS_PY = 2                    # 純 Python 很慢，跑 2 次就好
DATA = bytes(i & 0xFF for i in range(SIZE))

# ---------- 純 Python 寫的 AES-128（照 FIPS 197 標準一步一步算） ----------
SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76"
    "ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d83115"
    "04c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f84"
    "53d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa8"
    "51a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d1973"
    "60814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479"
    "e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a"
    "703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df"
    "8ca1890dbfe6426841992d0fb054bb16"
)
RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)

def xtime(a):                    # 在 GF(2^8) 裡乘以 2
    a <<= 1
    return (a ^ 0x1B) & 0xFF if a & 0x100 else a

def expand_key(key):             # 16 位元組金鑰 → 11 把回合金鑰（共 176 位元組）
    w = bytearray(key)
    for i in range(4, 44):
        t = w[(i - 1) * 4:i * 4]
        if i % 4 == 0:
            t = bytearray((SBOX[t[1]] ^ RCON[i // 4 - 1], SBOX[t[2]], SBOX[t[3]], SBOX[t[0]]))
        for j in range(4):
            w.append(w[(i - 4) * 4 + j] ^ t[j])
    return w

def encrypt_block(blk, w):       # 加密一個 16 位元組的區塊
    s = bytearray(blk[i] ^ w[i] for i in range(16))
    for r in range(1, 11):
        s = bytearray(SBOX[s[(i + 4 * (i % 4)) % 16]] for i in range(16))  # SubBytes＋ShiftRows
        if r < 10:                                                            # MixColumns
            t = bytearray(16)
            for c in range(0, 16, 4):
                a0, a1, a2, a3 = s[c], s[c + 1], s[c + 2], s[c + 3]
                x = a0 ^ a1 ^ a2 ^ a3
                t[c] = a0 ^ x ^ xtime(a0 ^ a1)
                t[c + 1] = a1 ^ x ^ xtime(a1 ^ a2)
                t[c + 2] = a2 ^ x ^ xtime(a2 ^ a3)
                t[c + 3] = a3 ^ x ^ xtime(a3 ^ a0)
            s = t
        k = r * 16
        for i in range(16):                                                   # AddRoundKey
            s[i] ^= w[k + i]
    return s

def cbc_py(data, key, iv):       # CBC：每一塊先和上一塊的密文 XOR，再加密
    w = expand_key(key)
    out = bytearray()
    prev = iv
    for p in range(0, len(data), 16):
        blk = bytearray(data[p + i] ^ prev[i] for i in range(16))
        prev = encrypt_block(blk, w)
        out += prev
    return bytes(out)

# ---------- 開始比賽 ----------
print("===== AES-128 加密速度比賽（CBC 模式）=====")
print("每次加密", SIZE // 1024, "KB；RP2350 沒有 AES 硬體，這題比的是兩種軟體寫法")

t0 = time.ticks_us()
for _ in range(ROUNDS_C):
    ct_c = cryptolib.aes(KEY, 2, IV).encrypt(DATA)     # 2 = CBC 模式
t_c = time.ticks_diff(time.ticks_us(), t0) / 1_000_000

t0 = time.ticks_us()
for _ in range(ROUNDS_PY):
    ct_py = cbc_py(DATA, KEY, IV)
t_py = time.ticks_diff(time.ticks_us(), t0) / 1_000_000

kb_c = SIZE * ROUNDS_C / 1024
kb_py = SIZE * ROUNDS_PY / 1024
print("[內建 cryptolib（C 語言）] 加密 {:.0f} KB，耗時 {:.3f} 秒，吞吐量 {:.1f} KB/s".format(kb_c, t_c, kb_c / t_c))
print("[純 Python 自己寫的]      加密 {:.0f} KB，耗時 {:.3f} 秒，吞吐量 {:.2f} KB/s".format(kb_py, t_py, kb_py / t_py))
print("兩邊算出的密文一樣嗎？", ct_c == ct_py)
print("密文前 16 個位元組：", ct_c[:16].hex())
print("內建模組比純 Python 快 {:.0f} 倍".format((kb_c / t_c) / (kb_py / t_py)))
