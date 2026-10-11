# 主題 17 綜合實作（三）：節能與安全強化（Pico 2 W ×2＋INA219）

以主題 11、12 的 MQTT 感測節點為底，強化三件事，每件都要量得到：
**可靠度**（遺失率、往返延遲、mem_free、斷網斷電恢復）、**安全**（Encrypt-then-MAC＋計數器防重放）、**節能**（INA219 量強化前後的平均電流與續航）。

- **A 板＝感測節點**：AHT20＋BMP280 讀溫溼度 → 加密＋訊息驗證碼 → MQTT 發布到教室 broker；B 回 ack，A 量往返時間。
- **B 板＝統計站兼量測儀器**：驗 A 的封包、算遺失率與缺號分布、重放一次證明被擋、用 INA219 量 A 的電流。
- 教室 broker：`192.168.1.10:1883`（主題 11、12 同一台），Wi-Fi `STUST-IoT`（密碼上課公布）。

## 個人繳交：輪流做
每組一樣是 2 片 Pico 2 W、同一盒器材，但**每個人都要自己做一輪、自己截圖、自己交**。
輪到你的時候：
1. 兩片板子的 `myid.py` 第一行 `STUDENT_ID` 都改成**你自己的學號**（`GROUP` 填組號、`BOARD` 一片 "A"、一片 "B"），存回板子。
2. 照下面的順序做完任務一～五，截圖都截**整個螢幕**，要看得到 `import myid` 印出的那一行（你的學號）和右下角的日期時間。
3. 做完換下一位組員。組員的截圖、記錄表不能共用；看不到你的學號的那一題不計分。

一台電腦可以同時開兩個 Thonny（工具 → 選項 → 一般，取消勾選「只允許一個 Thonny」；英文介面是 Allow only single Thonny instance），
A、B 左右並排，一張截圖就看得到兩片的輸出；或兩台電腦各截一張。

## 先做這三件事
1. 兩片板子都存一份 `myid.py`（全課共用），只改前三行。
2. 兩片板子都存一份 `mysecret.py`，填老師上課給的**種子**和 Wi-Fi 密碼。**填好的 mysecret.py 不要上傳、不要放進作業 zip。**
3. `umqtt.simple`：主題 11、12 裝過；沒有的話連上網路後 `import mip; mip.install("umqtt.simple")`。

## 每片板子存哪些檔案
| 檔案 | A 板 | B 板 | 說明 |
|---|---|---|---|
| myid.py、mysecret.py、cfg.py | ✔ | ✔ | 身份、秘密、本組參數（cfg.py 不用改） |
| mac.py、seal.py | ✔ | ✔ | 主題 14 原封不動：HMAC、Encrypt-then-MAC |
| util.py、netlink.py | ✔ | ✔ | 修正版：校時的 log、會餵狗的等待、退避重試；有 keepalive 與逾時的 MQTT |
| counter.py、sensors.py | ✔ | | 主題 14 的計數器存檔；主題 12 的感測器 |
| a_node.py | ✔（任務三起另存成 main.py） | | A 的主程式 |
| seqstat.py、ina219.py | | ✔ | 遺失率與缺號分段；主題 13 的 INA219 驅動 |
| b_rel.py、b_secure.py、b_power.py | | ✔ | 任務一三、任務二、任務四 |

## 誰跑哪支程式
| 任務 | A 板 | B 板 | 接線 | 配分 |
|---|---|---|---|---|
| 一 可靠度：T2 遺失率、T3 往返延遲、T6 mem_free | `a_node.py`（插 USB，Thonny 執行） | `b_rel.py`（`DROP = False`，收 100 格約 5 分鐘） | A、B 都插 USB | 25% |
| 二 安全：B 驗證、重放一次被擋 | `a_node.py` 繼續跑 | `b_secure.py` | 同上 | 20% |
| 三 斷網與斷電恢復：T4、T5 | `a_node.py` 另存成 `main.py`，拔 USB、改由 B 供電 | `b_rel.py`（`DROP = True`，收 50 格） | 主題 13 的 INA219 接線 | 15% |
| 四 節能：base、pm、eco 三種模式的平均電流與續航（T7） | `main.py` 繼續跑 | `b_power.py` | 同上 | 25% |
| 五 測試計畫表 T1～T7＋問題紀錄 3 筆以上＋A 的 error.log | 插回 USB 打開 `error.log` | — | 拆掉 VSYS 那條線再插 A 的 USB | 15% |

延伸挑戰與課堂練習不計分。

## 任務三、四的接線（和主題 13 一樣，先拔線再接線）
| 從 | 到 | 說明 |
|---|---|---|
| B 的 VBUS（第 40 腳） | INA219 的 VIN+ | B 插著電腦 USB，VBUS 就是 5 V |
| INA219 的 VIN− | A 的 VSYS（第 39 腳） | A 的電全部經過 0.1 Ω 分流電阻 |
| A 的 GND（第 38 腳） | B 的 GND（第 38 腳） | 一定要共地 |
| INA219 的 VCC、GND | B 的 3V3(OUT)（第 36 腳）、GND | |
| INA219 的 SDA、SCL | B 的 GP4（第 6 腳）、GP5（第 7 腳） | I2C 位址 0x40 |

- **A 的 USB 線一定要拔掉**，A 的 VBUS（第 40 腳）不接任何東西。
- 要改 A 的程式：先拔 B 的 USB（A 跟著斷電），拆掉接 A 的 VSYS 那條線，才插 A 的 USB。
- `cfg.py` 的 `ZERO_MA` 填主題 13 任務一量到的零點；接好先給助教看，再插 B 的 USB。

## 看門狗
`a_node.py` 會開看門狗（8 秒）。在 Thonny 按 Stop 之後，板子大約 8 秒後會自己重開，這是正常的。
要一行一行除錯時，把 `cfg.py` 的 `WDT_ON` 改成 `False`，除錯完再改回 `True`。

## 要交什麼（檔名 `無線感測_W17_學號_姓名.zip`，交到 FlipClass 作業區）
- 任務一：B 的結算截圖（遺失率、缺號、往返、mem_free）＋ `w17_rel.csv`
- 任務二：B 的重放截圖（收下 5 包 → 擋下：重放 → 對照）
- 任務三：B 的恢復截圖（drop 之後幾秒收到、A 的 online 與開機秒數）
- 任務四：B 的三種模式表格截圖＋ `w17_power.csv`
- 任務五：填好的 `w17_testplan.csv`、`w17_issues.csv`、A 的 `error.log` 截圖
- 不要放 `mysecret.py`。

`test_w17.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
