# 掃描 Wi-Fi SSID：範例程式

無線感測網路協定與應用（Pico 2W 版）｜搭配投影片「掃描 Wi-Fi SSID」

Pico 2 W 每 5 秒掃描一次附近的 Wi-Fi，列出每個基地台的名稱（SSID）、訊號強度（RSSI）、頻道（CH）和加密方式。原本 ESP32-S3 版用 Arduino IDE 寫 C，這份改成 MicroPython，用 Thonny 執行。

## 開始之前

1. `myid.py`：第 4 行改成組長學號，存到板子上（加密與解密、Wi-Fi 兩板對傳存過的板子沿用即可）。
2. `scan_wifi.py`：**第 5 行的 `Group-99` 改成你們的組別**，第 1 組就是 `Group-01`。沒有改先扣 20 分。
3. 第 6、7 行是練習 2 才要改的（手機熱點的名稱和密碼），練習 1 先不動。這時每一輪最後會印 `My phone: my-phone | not found`，是正常的。
4. 存到板子的方法：Thonny 開啟檔案 → 檔案 → 另存新檔 → Raspberry Pi Pico → 檔名照原本的名字。

不用接任何線，USB 插上就能做。Pico 2 W 只收得到 **2.4 GHz** 的 Wi-Fi。

## 檔案

| 檔案 | 內容 | 練習 |
|---|---|---|
| `myid.py` | 身份指紋：組長學號｜板子序號｜Wi-Fi MAC | — |
| `scan_wifi.py` | 每 5 秒掃描一次，照 RSSI 由強到弱列出 Nr、SSID、RSSI、CH、Encryption；練習 2 再連上自己的熱點 | 1、2 |

## 練習 1：掃描成功

按 F5 執行，整個螢幕截圖一張：要看得到第一行的身份指紋、`Scan start: Group-你們的組別`、第一輪完整的結果表（到 `My phone` 那一行），還有日期時間。

輸出長這樣（老師實機跑的片段）：

```
學號 4A1G0037 | 序號 7B05725CD29F242B | MAC 2C:CF:67:BE:BF:F5
Setup done
Scan start: Group-05
2C:CF:67:BE:BF:F5
Scan done
19 networks found
Nr | SSID                     | RSSI | CH | Encryption
 1 | aaron                    |  -31 |  6 | WPA2
 2 | Zyxel_5G                 |  -49 |  4 | WPA2
 3 | (hidden)                 |  -51 |  4 | WPA2
...
My phone: my-phone | not found
```

`(hidden)` 是不公開名稱的基地台；同一個名字出現好幾次，是好幾台不同的基地台。

## 練習 2：連上自己的手機熱點

1. 手機開熱點，頻段選 **2.4 GHz**（iPhone 打開「最大化相容性」），名稱不用改。
2. `scan_wifi.py` 第 6 行 `PHONE` 填熱點名稱、第 7 行 `PASSWORD` 填熱點密碼，大小寫和空格都要一模一樣，按 F5。
3. 手機放在 Pico 旁邊（約 30 公分），等兩輪，截圖；再拿到教室另一頭，等兩輪，再截一張。
4. 最後一行出現 IP，就表示 Pico 連上你的熱點了：

```
My phone: aaron | RSSI -29 | IP 172.20.10.2     ← 手機在旁邊
My phone: aaron | RSSI -50 | IP 172.20.10.2     ← 手機在 5 公尺外
```

- `not found`：名稱打錯、開成 5 GHz，或 iPhone 熱點休眠了（拿手機的人停在「個人熱點」畫面）。
- `not connected`：掃到了但連不上，多半是第 7 行密碼打錯。
- 截圖前把編輯區捲一下，**不要拍到第 7 行的密碼**。交上 GitHub 或分享程式時，也記得把密碼改回 `12345678`。

## 加密編號

`wlan.scan()` 每一筆的第 5 個欄位是加密編號，Pico 2 W 的無線晶片用三個位元表示：1＝有加密、2＝WPA、4＝WPA2，有幾種就加起來。常見的是 0（open）、5（WPA2）、7（WPA+WPA2）。WPA3 的基地台也會歸在 WPA2。老師在 Mac 上實機掃了好幾輪（每輪 16～22 台），全部都是 5（WPA2）。

第 6 個欄位是這次掃描收到這台幾次，程式沒有用到。

授課教師：廖明沂（南臺科技大學 電子工程系）
