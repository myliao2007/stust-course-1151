# 練習六：亂數產生器（硬體真亂數 vs 固定種子的假亂數）
import myid                      # 第一行：印出身份指紋
import os, random, time

random.seed(2026)                # 假亂數：種子固定，每次執行都會得到同一串
print("=== RP2350 亂數產生器 ===")
print("os.urandom 的亂數混入了晶片裡的硬體真亂數產生器（TRNG）")
for n in range(1, 6):
    raw = int.from_bytes(os.urandom(4), "big")     # 32 位元的硬體亂數
    key = os.urandom(16)                           # 128 位元金鑰（給 AES 用）
    print("---- 第", n, "次 ----")
    print("[真亂數 原始值] {}（0x{:08X}）".format(raw, raw))
    print("[擲骰子 0～99]", raw % 100)
    print("[產生 128 位元金鑰]", " ".join("{:02X}".format(b) for b in key))
    print("[假亂數 random，種子 2026]", random.randint(0, 99))
    time.sleep(2)
print(">>> 再按一次綠色執行：真亂數每次都不同，假亂數每次都一樣")
