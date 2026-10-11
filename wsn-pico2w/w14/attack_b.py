import myid                      # 身份指紋（第一行）
import cfg                       # 本組參數與金鑰
import gw_b, seal
# attack_b.py（B 兼任攻擊者）：只打自己組，攻擊封包不從空中送出去

gw_b.ap_up()
pk = gw_b.collect(3)             # 先正常收 A 的 3 包
p = pk[-1]                       # 錄到的最新一包

def flip(b, i, x=0x01):          # 第 i 個位元組 XOR x
    t = bytearray(b)
    t[i] ^= x
    return bytes(t)

iv2 = p[4:20]                    # 假 IV：想把組號改成 99
for k in range(2):
    iv2 = flip(iv2, 8 + k, cfg.NODE_ID.encode()[1 + k] ^ ord("9"))
ctr = int.from_bytes(p[:4], "big") + 100
tests = [("① 重放：原封不動再送一次", p),
         ("② 竄改：密文翻 1 個位元", flip(p, 20)),
         ("③ 換 IV：組號改成 99", p[:4] + iv2 + p[20:]),
         ("④ 計數器 +100：假裝是新的", ctr.to_bytes(4, "big") + p[4:])]
for name, x in tests:
    print(name)
    gw_b.handle(x)
print("⑤ 對照：只加密、不驗 MAC 的閘道（任務一的 aes 模式）")
print("  ② 解出來：", seal.decrypt(cfg.ENC_KEY, flip(p[4:-32], 16)))
print("  ③ 解出來：", seal.decrypt(cfg.ENC_KEY, iv2 + p[20:-32]))
print("⑥ 攻擊結束，A 的下一包照樣收下：")
gw_b.collect(1)
