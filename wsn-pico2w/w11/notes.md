# 主題 11 MQTT 與雲端平台整合：上機程式（Pico 2 W ×2）

**A 板**接 AHT20＋BMP280 模組，當發布端（發溫溼度、接指令、交代遺囑）；**B 板**接著電腦不動，當訂閱端兼統計員（用 seq 算遺失與重複、量遺囑時間、遙控 A）。
broker 是老師筆電上的 Mosquitto，兩片板子都連教室路由器（或老師的熱點）。Wi-Fi 名稱、密碼、broker 的 IP 上課時公布，填進 `cfg.py` 最上面三行。

## 先做這三件事
1. 兩片板子都存一份 `myid.py`（全課共用），只改前三行：`STUDENT_ID`（組長學號）、`GROUP`（組號）、`BOARD`（這片是 A 還是 B）。
2. `cfg.py`、`wifi.py` 兩片都存；A 板另外存 `sensor.py`，B 板另外存 `seqstat.py`。
   `cfg.py` 會用 myid 的組號算出本組的 client id 和主題，**不用自己取名字**，全班不會撞名。
3. 每支上機程式第一行都是 `import myid`，截圖要看得到 myid 印出的那一行（學號｜第幾組｜板子 A／B｜序號｜MAC｜日期時間）和右下角的時間。
   Thonny 第二次執行沒印出這一行時，先按 Stop 再執行。

## 誰跑哪支程式
| 任務 | A 板（AHT20＋BMP280） | B 板（接電腦） | 配分 |
|---|---|---|---|
| 一 裝 umqtt、連上 broker | `install_umqtt.py` | `install_umqtt.py` | 10% |
| 二 定時發布、B 用 seq 統計 | `a_pub.py`（每 10 秒、QoS 0） | `b_stats.py`（`OFFLINE_AT = 0`） | 20% |
| 三 B 遙控 A 的 LED | `a_cmd.py` | `b_ctl.py`（輸入 on／off） | 10% |
| 四 遺囑與斷線重連時間線 | `a_robust.py` | `b_watch.py`（先 `DROP_AFTER = 3`，拔 USB 那次改 0） | 25% |
| 五 QoS 0／1 × clean_session | `a_robust.py`（`QOS` 改 0、1） | `b_stats.py`（`OFFLINE_AT = 20`，`CLEAN` 改 True、False） | 25% |
| 六 client id 撞名 | `a_robust.py` | `b_clash.py`（先 `FIX = False`，再 `True`） | 10% |

延伸挑戰不計分。

## 分組參數（cfg.py 自動算，以第 7 組為例）
- client id：A 板 `wsn-g07-A`、B 板 `wsn-g07-B`。
- A 的主題：`stust/ee/e501/g07a/data`（溫溼度）、`…/status`（上下線，retain＋遺囑）、`…/cmd`（指令 on、off、drop）、`…/led`（A 回報 LED）。
- keepalive 30 秒：broker 超過 30×1.5＝45 秒沒收到 A 的任何封包，才代發遺囑 offline。
- 任務四 A 斷網 60 秒（比 45 秒長，broker 才看得到 A 掉線）。

## 接線（A 板）
| 模組腳位 | Pico 2 W 腳位（實體腳位） |
|---|---|
| VIN | 3V3(OUT)（第 36 腳），**不可接 VBUS（第 40 腳）** |
| GND | GND（第 38 腳） |
| SDA | GP4（第 6 腳） |
| SCL | GP5（第 7 腳） |

AHT20 位址 0x38、BMP280 位址 0x77（本主題只用 AHT20）。LED 用板載 LED，不用接線。B 板不用接線。

## 小提醒
- umqtt.simple 以 `mip.install('umqtt.simple')` 安裝的 1.6.0 版為準（`connect()` 有 `clean_session`、`timeout` 參數）。
- umqtt.simple 的 QoS 1 會等 PUBACK，可是不保存、不自動重送；`a_robust.py` 自己記住沒送成的那一筆，重連後補送。
- 只收不發的程式要自己定時 `ping()`，不然 broker 會在 keepalive×1.5 之後把它踢掉。
- 任務五每換一種組合，A、B 都要按 Stop 重跑；B 開頭會先用 clean_session=True 連一次，把上一輪留下的會話清掉。

## 記錄表
`w11_record.csv` 用 Excel 開，量完當場填。

## 繳交
檔名 `無線感測_W11_學號_姓名.zip`（照原規則），交到 FlipClass 作業區，期限：下次上課前一天 23:59。截圖一律截整個螢幕（A、B 兩片都要）。

`test_w11.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
