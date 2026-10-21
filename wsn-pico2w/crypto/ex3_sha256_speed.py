# 練習三：SHA-256 雜湊速度比賽（內建 hashlib 對上純 Python）
import myid                      # 第一行：印出身份指紋
import hashlib, time

SIZE = 2048                      # 每次算 2 KB 的雜湊
ROUNDS_C = 50                    # 內建模組跑 50 次
ROUNDS_PY = 2                    # 純 Python 跑 2 次
DATA = bytes(i & 0xFF for i in range(SIZE))

# ---------- 純 Python 寫的 SHA-256（照 FIPS 180-4 標準） ----------
K = (
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
)
M32 = 0xFFFFFFFF

def rotr(x, n):                  # 32 位元向右旋轉 n 位
    return ((x >> n) | (x << (32 - n))) & M32

def sha256_py(msg):
    h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
         0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]
    n = len(msg)
    msg = msg + b"\x80" + bytes((55 - n) % 64) + (n * 8).to_bytes(8, "big")   # 補位：湊成 64 的倍數
    for off in range(0, len(msg), 64):
        w = [int.from_bytes(msg[off + 4 * i:off + 4 * i + 4], "big") for i in range(16)]
        for i in range(16, 64):
            s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w.append((w[i - 16] + s0 + w[i - 7] + s1) & M32)
        a, b, c, d, e, f, g, hh = h
        for i in range(64):     # 64 回合的壓縮
            t1 = (hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) & M32
            t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) & M32
            hh, g, f, e, d, c, b, a = g, f, e, (d + t1) & M32, c, b, a, (t1 + t2) & M32
        h = [(x + y) & M32 for x, y in zip(h, (a, b, c, d, e, f, g, hh))]
    return b"".join(x.to_bytes(4, "big") for x in h)

# ---------- 開始比賽 ----------
print("===== SHA-256 雜湊速度比賽 =====")
print("每次算", SIZE // 1024, "KB 的雜湊")

t0 = time.ticks_us()
for _ in range(ROUNDS_C):
    d_c = hashlib.sha256(DATA).digest()
t_c = time.ticks_diff(time.ticks_us(), t0) / 1_000_000

t0 = time.ticks_us()
for _ in range(ROUNDS_PY):
    d_py = sha256_py(DATA)
t_py = time.ticks_diff(time.ticks_us(), t0) / 1_000_000

kb_c = SIZE * ROUNDS_C / 1024
kb_py = SIZE * ROUNDS_PY / 1024
print("[內建 hashlib（C 語言）] 處理 {:.0f} KB，耗時 {:.3f} 秒，吞吐量 {:.1f} KB/s".format(kb_c, t_c, kb_c / t_c))
print("[純 Python 自己寫的]    處理 {:.0f} KB，耗時 {:.3f} 秒，吞吐量 {:.2f} KB/s".format(kb_py, t_py, kb_py / t_py))
print("兩邊算出的雜湊一樣嗎？", d_c == d_py)
print("雜湊值：", d_c.hex())
print("內建模組比純 Python 快 {:.0f} 倍".format((kb_c / t_c) / (kb_py / t_py)))
