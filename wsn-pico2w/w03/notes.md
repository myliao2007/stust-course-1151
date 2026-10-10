# 主題 3 無線通訊基礎：上機程式（Pico 2 W ×2）

## 先做這兩件事
1. 兩片板子都存一份 `myid.py`（全課共用），只改前三行：`STUDENT_ID`（組長學號）、`GROUP`（組號）、`BOARD`（這片是 A 還是 B）。
   `cfg.py` 原封不動也存到兩片板子，它會用 myid 的組號算出本組的 SSID、密碼、頻道、BLE 名稱和埠號。
2. 每支程式前兩行都是 `import myid`、`import cfg`，截圖要看得到 myid 印出的那一行（學號｜第幾組｜板子 A／B｜序號｜MAC｜日期時間）和右下角的時間。
   Thonny 第二次執行沒印出這一行時，先按 Stop（軟重開）再執行。

## 誰跑哪支程式
| 任務 | A 板（開 AP） | B 板（接電腦量測） | 配分 |
|---|---|---|---|
| 一 掃描 Wi-Fi | `ap_a.py` | `scan_b.py` | 15% |
| 二 連線與狀態碼 | `ap_a.py` | `connect_b.py` | 15% |
| 三 UDP 往返與遺失率（走廊） | `udp_echo_a.py`（帶出去前另存成 `main.py`） | `udp_ping_b.py` | 30% |
| 四 BLE 廣播 RSSI | `ble_adv_a.py` | `ble_scan_b.py` | 20% |
| 五 實際吞吐量 | `tput_rx_a.py` | `tput_tx_b.py`（改 `SIZE` 試 64、1024） | 20% |

`connect_b.py` 會被 B 的其他程式匯入（自動連上 A 的 AP），`ap_a.py` 會被 A 的其他程式匯入（自動開 AP）。

## 分組參數（cfg.py 自動算）
- SSID：`wsn-gNN`（NN＝兩位數組號）；密碼：`pico` 加上「組號 × 1234 取後四位」。
- AP 頻道：組號 1、2、3 依序用 1、6、11，之後輪流。
- UDP 埠：任務三 5005、任務五 5006。BLE 名稱：`wsn-gNN-A`。

## 接線（選做）
- A 板 GP15（第 20 腳）→ 220Ω → LED 長腳，LED 短腳 → GND（第 18 腳）：有 B 連上時燈亮。
- A 帶去走廊時用行動電源接 USB 孔供電，天線（板子遠離 USB 的那一端）附近不要放金屬或杜邦線。

## 記錄表
`w03_record.csv` 用 Excel 開，量完當場填。

`test_w03.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
