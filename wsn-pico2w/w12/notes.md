# 主題 12 感測資料視覺化與儀表板：上機程式（Pico 2 W ×2＋教室電腦的 Node-RED）

**A 板＝感測節點**：AHT20＋BMP280、BH1750，每 5 秒送一筆多欄位 JSON（溫度、濕度、氣壓、照度、seq、時間），有遺囑與 online。
**B 板＝節點端顯示＋告警**：OLED 顯示 A 的最新值與「資料新鮮度」，超過門檻 LED 亮、太久沒更新或 A 斷線 LED 閃。
**電腦＝Node-RED 儀表板**：折線圖、量表、狀態燈、告警通知、門檻設定、A 板 LED 開關。

## 先做這三件事
1. 兩片板子都存一份 `myid.py`（全課共用），只改前三行：`STUDENT_ID`（組長學號）、`GROUP`（組號）、`BOARD`（"A" 或 "B"）。
2. `cfg.py`、`wifi.py` 原封不動存到兩片板子。cfg 會用組號算出本組的主題、client id（第 7 組：`stust/ee/e501/g07a/data`、`wsn-g07a`）。
3. 兩片都跑一次 `install.py`（裝 umqtt.simple；B 另外裝 ssd1306）。**mip 要從網路下載，Pico 要能上網**；
   下載失敗就用 Thonny 把本資料夾的 `ssd1306.py`（備用檔，MIT 授權）存到 B 板。

每支程式第一行都是 `import myid`，會印出「學號｜第幾組｜板子｜序號｜MAC｜日期時間」。
**截圖一律整個螢幕**：Thonny 和瀏覽器左右並排，同一張看得到指紋那一行、儀表板上自己組的名字（E501 g07、g07a）和右下角日期時間；看不到指紋的那一題不計分。

## 接線
| 板子 | 元件 | 接到 Pico 2 W（實體腳位） |
|---|---|---|
| A | AHT20＋BMP280 模組、BH1750 的 VCC／VIN | 3V3(OUT)（第 36 腳），不可接 VBUS（第 40 腳） |
| A | 兩片模組的 GND | GND（第 38 腳） |
| A | 兩片模組的 SDA／SCL | GP4（第 6 腳）／GP5（第 7 腳） |
| A | BH1750 的 ADDR | GND（第 13 腳），位址 0x23 |
| B | OLED 的 VCC／GND | 3V3(OUT)（第 36 腳）／GND（第 38 腳）；OLED 腳位順序各家不同，看板子上的字 |
| B | OLED 的 SDA／SCL | GP4（第 6 腳）／GP5（第 7 腳），位址 0x3C |
| B | 告警 LED | GP15（第 20 腳）→ 220Ω → LED 長腳；短腳 → GND（第 18 腳） |

A 板 I2C 掃描要看到 0x23、0x38、0x77；B 板要看到 0x3C（`oled_test.py` 會印）。

## 誰跑哪支程式
| 任務 | A 板 | B 板 | 電腦 | 配分 |
|---|---|---|---|---|
| 一 Node-RED 跑起來 | － | － | 安裝 Node-RED 與 node-red-dashboard，匯入 `flow.json`（先把 gNN 全部取代成自己組的 g07），按「部署」 | 10% |
| 二 多欄位 JSON | `pub_multi.py`（會 import `sensors.py`、`wifi.py`） | － | debug 側欄看物件 | 20% |
| 三 畫圖 | `pub_multi.py` | － | /ui：溫度兩條線、濕度量表、氣壓與照度各一張圖 | 20% |
| 四 告警與控制 | `pub_multi.py` | － | 跨越門檻通知、調門檻、A 板 LED 開關、匯出 flows.json | 20% |
| 五 B 板顯示與新鮮度 | `pub_multi.py`（之後拔掉 USB） | `oled_test.py` → `show_b.py`（會 import `alarm.py`） | 看 A、B 狀態燈 | 30% |
| 延伸（不計分） | `pub_multi.py` | － | `save_csv.py`（paho-mqtt 2.x）寫 sensor.csv | － |

## 本組參數（cfg.py 自動算，第 NN 組）
- 節點名：A＝`gNNa`、B＝`gNNb`；client id：`wsn-gNNa`、`wsn-gNNb`、Node-RED `wsn-gNNnr`、save_csv `wsn-gNNcsv`。
- 主題：`stust/ee/e501/gNNa/data`、`…/gNNa/status`、`…/gNNb/status`、`…/gNNa/cmd`（LED 開關）、`…/gNNb/th`（告警門檻）。
- broker：教室電腦 `192.168.1.10:1883`；Wi-Fi 照主題 11（`STUST-IoT`，密碼上課公布）。
- 每 5 秒一筆；超過 15 秒沒更新算過期；keepalive 60 秒，A 斷電約 90 秒後 broker 代發 offline。
- 告警門檻預設 30 °C：教室冷、捏感測器到不了 30 度，就在儀表板把門檻調成「現在溫度＋1」（B 板會跟著改）。

## 繳交
檔名：`無線感測_W12_學號_姓名.zip`，交到 FlipClass 作業區。內含每個任務的截圖、OLED 照片、匯出的 flows.json、
兩片板子的程式，以及一段 100 字說明：儀表板版面為什麼這樣排（誰在看、要做什麼決定）。

`test_w12.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
