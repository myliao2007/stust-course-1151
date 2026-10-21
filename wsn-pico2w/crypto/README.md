# Pico 2 W 加密與解密（MicroPython）

無線感測網路協定與應用（Pico 2W 版）上課版「加密與解密」的程式。在 Thonny 打開，接上 Pico 2 W（MicroPython 1.29.0）直接執行。

每支程式的第一行都是 `import myid`，執行後 Shell 第一行會印出身份指紋（組長學號｜板子序號｜Wi-Fi MAC）。板子裡要先存好 `myid.py`，並把第 4 行改成組長的學號。

| 練習 | 程式 | 做什麼 | 配分 |
|---|---|---|---|
| 一 | ex1_aes_speed.py | AES-128（CBC）速度比賽：內建 cryptolib vs 純 Python | 10 |
| 二 | ex2_aes_key.py | AES 金鑰與加解密：換金鑰、用錯金鑰會怎樣（ECB，教學用） | 20 |
| 三 | ex3_sha256_speed.py | SHA-256 速度比賽：內建 hashlib vs 純 Python | 10 |
| 四 | ex4_sha256_hash.py | SHA-256 雜湊特性：hello 和 hello1 | 10 |
| 五 | ex4_sha256_hash.py | 和線上工具 https://emn178.github.io/online-tools/sha256.html 互相驗證 | 15 |
| 六 | ex6_random.py | 硬體亂數 os.urandom vs 固定種子的 random | 10 |
| 七 | ex7_base64.py | Base64 解碼與編碼 | 10 |
| 八 | （寫在 Word） | 設計你的專題情境 | 15 |

## 練習七要解的兩個字串

```
eyJpZCI6MSwidGVtcCI6MjV9
aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ==
```

## 說明

- RP2350 沒有 AES 硬體加速器；MicroPython 1.29.0 的 rp2 版 hashlib 用 mbedtls 軟體計算 SHA-256，沒有用到晶片的 SHA-256 加速器，所以練習一、三比的是「內建 C 模組」和「純 Python」。
- `os.urandom()` 在 RP2350 上會混入晶片的硬體真亂數產生器（TRNG）。
- 純 Python 的 AES、SHA-256 照 FIPS 197、FIPS 180-4 撰寫，結果已和 OpenSSL 比對一致。
