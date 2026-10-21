# 練習二：AES 金鑰與加解密（ECB 模式，只用來教學觀察）
import myid                      # 第一行：印出身份指紋
import cryptolib

def to_key(text):                # 文字 → 16 位元組金鑰（不足補 0，太長只取前 16）
    k = text.encode()
    if len(k) != 16:
        print("提醒：金鑰是", len(k), "個位元組，已自動補 0 或截斷成 16 個")
    k = k[:16]
    return k + bytes(16 - len(k))

def show(label, data):           # 每 16 個位元組一行，用十六進位印出
    print(label)
    for i in range(0, len(data), 16):
        print("   ", " ".join("{:02X}".format(b) for b in data[i:i + 16]))

print("=== AES-128 加解密實驗室 ===")
last = None                      # 上一回合的密文，用來比較
while True:
    k1 = to_key(input("\n步驟 1：輸入「加密金鑰」（16 個字）> "))
    show("加密金鑰（十六進位）：", k1)
    msg = input("步驟 2：輸入要加密的訊息 > ").encode()
    plain = msg + bytes((-len(msg)) % 16) if msg else bytes(16)       # 補 0 湊成 16 的倍數
    cipher = cryptolib.aes(k1, 1).encrypt(plain)                        # 1 = ECB 模式
    show("密文（十六進位）：", cipher)
    if last is not None:
        same = sum(1 for a, b in zip(cipher, last) if a == b)
        print("和上一回合的密文比：", "完全相同" if cipher == last else "不同（{} 個位元組裡只有 {} 個相同）".format(len(cipher), same))
    last = cipher

    k2 = to_key(input("步驟 3：輸入「解密金鑰」> "))
    back = cryptolib.aes(k2, 1).decrypt(cipher)
    print("[系統偵測]", "金鑰正確！" if k2 == k1 else "金鑰不對，預期會看到亂碼…")
    show("解密結果（十六進位）：", back)
    try:
        print("解密結果（文字）：[" + back.rstrip(b"\x00").decode() + "]")
    except Exception:
        print("解密結果（文字）：[看不懂的亂碼，無法轉成文字]")
    print(">>> 再來一回合；要結束請按紅色 STOP")
