# 主題 6 BLE 藍牙低功耗：上機程式（Pico 2 W ×2＋手機 nRF Connect）

## 先做這三件事
1. 兩片板子都存 `myid.py`（全課共用），只改前三行：`STUDENT_ID`（組長學號）、`GROUP`（組號）、`BOARD`（這片是 A 還是 B）。
   `cfg.py`、`adtool.py` 原封不動存到兩片板子；A 板另外存 `aht20.py`。
   cfg.py 會用組號算出本組的 BLE 名稱：A 板是 `wsn-gNN-A`、B 板是 `wsn-gNN-B`（NN＝兩位數組號），全班不會撞名。
2. 在 Thonny 的 Shell 打 `import aioble`：沒有錯誤就好（MicroPython 1.26.1 的 Pico 2 W 韌體已內建）。
   出現 ImportError 才需要先連 Wi-Fi，再 `import mip`、`mip.install("aioble")`。
3. 手機裝好 nRF Connect（Nordic 出的免費 App），打開藍牙；Android 還要開「定位」權限才掃得到。

每支程式前兩行都是 `import myid`、`import cfg`。截圖一律整個螢幕，要看得到 myid 印出的那一行（學號｜第幾組｜板子 A／B｜序號｜MAC｜日期時間）和右下角時間；
Thonny 第二次執行沒印出這一行時，先按 Stop 再執行。手機截圖要看得到自己組的名稱 `wsn-gNN-A`。

## 誰跑哪支程式
| 任務 | A 板（接 AHT20） | B 板（接電腦） | 手機 | 配分 |
|---|---|---|---|---|
| 一 廣播封包解剖 | `adv_a.py` | `observer_b.py` | 看 Raw data 逐位元組對照 | 15% |
| 二 被動 vs 主動掃描 | `scanrsp_a.py` | `scan2_b.py` | 看得到名稱（手機是主動掃描） | 15% |
| 三 GATT 服務＋手動寫 CCCD | `ble_peripheral.py` | `ble_central.py`、`cccd_b.py` | 連上、開通知看溫溼度 | 30% |
| 四 無連線感測網 | `beacon_a.py`（`ADV_MS` 試 1000、200） | `collect_b.py` | 可看到全班的廣播 | 20% |
| 五 通知 vs 指示吞吐量 | `tput_a.py` | `tput_b.py` | 不用 | 20% |

- 任務三：先讓手機連 A 驗證，**手機斷線後** B 才連得上（Pico 的 BTstack 一次只接受一條連線）。
- `ble_central.py` 會被 `cccd_b.py`、`tput_b.py` 匯入（共用「掃描找自己組 A」那一段），三個檔都要存在 B 板上。

## 接線（只有 A 板要接）
| 訊號 | AHT20＋BMP280 模組 | Pico 2 W |
|---|---|---|
| 電源 | VIN | 3V3(OUT)（第 36 腳） |
| 接地 | GND | GND（第 38 腳） |
| I2C 資料 | SDA | GP4（第 6 腳） |
| I2C 時脈 | SCL | GP5（第 7 腳） |
| 連線指示（選做） | LED 長腳串 220Ω | GP15（第 20 腳）；短腳接 GND（第 18 腳） |

天線在板子遠離 USB 的那一端，附近 5 mm 不要壓金屬或整排杜邦線。

## 分組參數（cfg.py 自動算）
- BLE 名稱：`wsn-gNN-A`／`wsn-gNN-B`；製造商資料：`FF FF`（測試用公司代碼 0xFFFF）＋組號 1 位元組。
- 任務五自訂服務 UUID：`282c0001-f4b2-4f7c-bfaa-8a0cea5c64NN`（最後兩位是組號的十六進位），資料特徵 282c0002-…、指令特徵 282c0003-…。

## 記錄表
`w06_record.csv` 用 Excel 開，量完當場填。

## 延伸挑戰（不計分）
連線參數 ping-pong、MTU 協商、Battery Service、Heart Rate Service 給 nRF Toolbox 畫圖、多節點掃描地圖：做法見投影片「延伸挑戰」頁。

`test_w06.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
