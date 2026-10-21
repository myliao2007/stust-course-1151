# 練習七：Base64 編碼與解碼
import myid                      # 第一行：印出身份指紋
import binascii

print("=== Base64 → 文字 解碼器 ===")
print("例如輸入 SGVsbG8gV29ybGQ=")
while True:
    s = input("\n輸入 Base64 字串 > ").strip()
    if not s:
        continue
    try:
        raw = binascii.a2b_base64(s)                 # Base64 → 位元組
        if not raw:
            raise ValueError("沒有解出任何資料")
        print("原始編碼：", s)
        print("解碼結果：", raw.decode())
        print("長度變化：", len(s), "個字 →", len(raw), "個位元組")
        print("再編碼回去：", binascii.b2a_base64(raw).decode().strip())   # 位元組 → Base64
    except Exception as e:
        print("解碼失敗（格式錯誤）：", e)
