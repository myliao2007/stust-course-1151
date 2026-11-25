# 掃描 Wi-Fi SSID：範例程式

無線感測網路協定與應用（Pico 2W 版）｜搭配投影片「掃描 Wi-Fi SSID」

Pico 2 W 每 5 秒掃描一次附近的 Wi-Fi，列出每個基地台的名稱（SSID）、訊號強度（RSSI）、頻道（CH）和加密方式。原本 ESP32-S3 版用 Arduino IDE 寫 C，這份改成 MicroPython，用 Thonny 執行。

## 開始之前

1. `myid.py`：第 4 行改成組長學號，存到板子上（加密與解密、Wi-Fi 兩板對傳存過的板子沿用即可）。
2. `scan_wifi.py`：**第 5 行的 `Group-99` 改成你們的組別**，第 1 組就是 `Group-01`。沒有改先扣 20 分。
3. 存到板子的方法：Thonny 開啟檔案 → 檔案 → 另存新檔 → Raspberry Pi Pico → 檔名照原本的名字。

不用接任何線，USB 插上就能做。Pico 2 W 只收得到 **2.4 GHz** 的 Wi-Fi。

## 檔案

| 檔案 | 內容 | 練習 |
|---|---|---|
| `myid.py` | 身份指紋：組長學號｜板子序號｜Wi-Fi MAC | — |
| `scan_wifi.py` | 每 5 秒掃描一次，照 RSSI 由強到弱列出 Nr、SSID、RSSI、CH、Encryption | 1、2 |

## 練習 2：找到自己的手機熱點

手機開熱點，名稱 `WSN-G05`、密碼 `wsnpico05`（05 換成你們的組號，頻段選 2.4 GHz；iPhone 打開「最大化相容性」）。Pico 不用連上去，只要掃得到。手機放在 Pico 旁邊、再拿到教室另一頭，各記一次 `WSN-G05` 那一行的 RSSI。

## 加密編號

`wlan.scan()` 每一筆的第 5 個欄位是加密編號，Pico 2 W 的無線晶片用三個位元表示：1＝有加密、2＝WPA、4＝WPA2，有幾種就加起來。常見的是 0（open）、5（WPA2）、7（WPA+WPA2）。WPA3 的基地台也會歸在 WPA2。

授課教師：廖明沂（南臺科技大學 電子工程系）
