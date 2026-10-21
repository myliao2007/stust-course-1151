# 練習四、五：SHA-256 雜湊計算機
import myid                      # 第一行：印出身份指紋
import hashlib, time

def bits_diff(a, b):             # 兩個雜湊值有幾個位元不一樣
    n = 0
    for x, y in zip(a, b):
        v = x ^ y
        while v:
            n += v & 1
            v >>= 1
    return n

print("=== SHA-256 雜湊計算機 ===")
last = None
while True:
    text = input("\n輸入任意文字（例如 hello）> ")
    data = text.encode()                     # 文字 → 位元組（UTF-8）
    t0 = time.ticks_us()
    d = hashlib.sha256(data).digest()
    us = time.ticks_diff(time.ticks_us(), t0)
    print("輸入字串：", text)
    print("資料長度：", len(data), "位元組；運算耗時：", us, "微秒")
    print("SHA-256 ：", d.hex())
    if last is not None:
        print("和上一個比：256 個位元裡有", bits_diff(d, last), "個不一樣")
    last = d
