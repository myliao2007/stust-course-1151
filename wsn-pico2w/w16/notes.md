# 主題 16 綜合實作（二）：網路層與上雲（Pico 2 W ×2＋INA219）

把主題 7～12 串成一條路，整合的方法照原本的「系統整合」：一次只改一件事、由下往上一層一層驗。

- **A 板＝感測節點**：AHT20＋BMP280、BH1750 讀值 → 13 位元組 → **真的 6LoWPAN／IPv6／UDP 訊框**（主題 8 的 `wsnproto`，IPHC＋NHC 壓縮、附 FCS，30 位元組）→ 用 Wi-Fi UDP 當無線電送給 B。
  開機先送 RPL 的 **DIS**（主題 10）找邊界路由器，收到 B 的 **DIO** 就知道 B 在哪、自己的 Rank。
- **B 板＝邊界路由器**：驗 FCS、解壓縮、印欄位樹 → 拆成欄位 → 一行 JSON → **MQTT** 發布（主題 11）→ 電腦上的 **Node-RED 儀表板**（主題 12 的 `flow.json`，原封不動）。
  B 的主迴圈是非阻塞的：收訊框、上行、狀態、閃燈各照自己的節奏；上行斷線時先把資料存在待送箱，連回來再補送。
- **B 也是量測儀器**：任務五用 INA219 量 A 的電流與 VSYS（主題 13 的接法），填電流預算表、算壓降。

## 個人繳交：輪流做
每組一樣是 2 片 Pico 2 W、同一盒器材，但**每個人都要自己做一輪、自己截圖、自己交**。
1. 兩片板子的 `myid.py` 第 2 行 `STUDENT_ID` 都改成**你自己的學號**（`GROUP` 填組號、`BOARD` 一片 "A"、一片 "B"），存回板子，按 Stop 再執行。
   myid.py 裡的註解寫「組長學號」，綜合實作一律填自己的學號。
2. 一台電腦開兩個 Thonny（工具 → 選項 → 一般，取消勾選「只允許一個 Thonny」；英文介面是 Allow only single Thonny instance），
   左邊連 A、右邊連 B（右下角各選不同的 COM 埠），一張截圖同時看得到兩片的指紋。做不到就兩台電腦各截一張。
3. **截圖一律整個螢幕**，要看得到 myid 印出的那一行（學號｜第幾組｜板子｜序號｜MAC｜時間）和右下角的日期時間；看不到你的學號的那一題不計分。
4. 三個 csv（用 Excel 開）每人一份，最上面寫自己的學號和板子序號後 4 碼。

## 先做這三件事
1. 兩片板子都存 `myid.py`（全課共用，只改前三行）、`mysecret.py`（填老師上課給的 Wi-Fi 密碼）、`cfg.py`（不用改）。
   **填好的 mysecret.py 不要上傳、不要放進作業 zip。**
2. 兩片板子都存協定函式庫 `wsnproto.py`、`wsntree.py`（主題 8、10 同一份，不要改）和 `packet.py`、`util.py`。
   匯入時出現 `MemoryError`：改存 `mpy/wsnproto.mpy`、`mpy/wsntree.mpy`，並把板子上同名的 `.py` 刪掉。
3. B 要有 `umqtt.simple`（主題 11、12 裝過；沒有就連上網路後 `import mip; mip.install("umqtt.simple")`）。

## 每片板子存哪些檔案
| 檔案 | A 板 | B 板 | 說明 |
|---|---|---|---|
| myid.py、mysecret.py、cfg.py | ✔ | ✔ | 身份、Wi-Fi 帳密、本組參數 |
| wsnproto.py、wsntree.py | ✔ | ✔ | 協定函式庫（主題 8、10；`common/` 逐字複製） |
| packet.py、util.py | ✔ | ✔ | 資料格式表的程式版；校時的 log、會餵狗的等待、退避重試（主題 17 修正版） |
| i2c_scan.py | ✔ | ✔ | 任務一：兩條匯流排一起掃（原頁的程式，第一行加 `import myid`） |
| sensors.py、wifi.py、node_a.py | ✔ | | 主題 12 的感測器、Wi-Fi；A 的主程式（任務四起另存成 `main.py`） |
| plan.py、airtime.py | ✔（或 B） | | 任務六的計算器；airtime.py 是主題 7 的空中時間計算器 |
| netlink.py、border.py、br_b.py | | ✔ | 主題 17 修正版的 Wi-Fi／MQTT；邊界路由器收訊框；B 的主程式 |
| ina219.py、power_b.py | | ✔ | 主題 13 的 INA219 驅動；任務五量 A 的電流 |

電腦上：`wsn_decode.py`（Thonny 打開按執行，貼十六進位）、`flow.json`（主題 12 同一份）、三個 csv。

## 接線
| 板子 | 元件 | 接到 Pico 2 W（實體腳位） |
|---|---|---|
| A | AHT20＋BMP280 模組、BH1750 的 VCC／VIN | 3V3(OUT)（第 36 腳），不可接 VBUS（第 40 腳） |
| A | 兩片模組的 GND | GND（第 38 腳） |
| A | 兩片模組的 SDA／SCL | GP4（第 6 腳）／GP5（第 7 腳） |
| A | BH1750 的 ADDR | GND（第 13 腳），位址 0x23 |
| B | INA219 的 VCC／GND | 3V3(OUT)（第 36 腳）／GND（第 38 腳） |
| B | INA219 的 SDA／SCL | GP4（第 6 腳）／GP5（第 7 腳），位址 0x40 |
| B | 按鈕 | 一腳接 GP14（第 19 腳）、另一腳接 GND（第 18 腳） |

任務五才接電源線（和主題 13、17 一樣，**先拔線再接線**）：

| 從 | 到 | 說明 |
|---|---|---|
| B 的 VBUS（第 40 腳） | INA219 的 VIN+ | B 插著電腦 USB，VBUS 就是 5 V |
| INA219 的 VIN− | A 的 VSYS（第 39 腳） | A 的電全部經過 0.1 Ω 分流電阻 |
| A 的 GND（第 38 腳） | B 的 GND（第 38 腳） | 一定要共地 |

- **A 的 USB 線一定要拔掉**，A 的 VBUS（第 40 腳）不接任何東西。
- 要改 A 的程式：先拔 B 的 USB（A 跟著斷電），拆掉接 A 的 VSYS 那條線，才插 A 的 USB。
- `cfg.py` 的 `ZERO_MA` 填主題 13 任務一量到的零點；接好先給助教看，再插 B 的 USB。

## 誰跑哪支程式
| 任務 | A 板 | B 板 | 配分 |
|---|---|---|---|
| 一 硬體層：I2C 掃描＋整合檢查表第 2、3 列 | `i2c_scan.py` | `i2c_scan.py` | 15% |
| 二 假資料先接流程，再換真資料（程式層＋傳輸層） | `node_a.py`（先 `FAKE = True`，再改回 `False`） | `br_b.py`（`UPLINK = False`）；電腦 `wsn_decode.py` | 20% |
| 三 上雲：MQTT＋Node-RED 儀表板（平台層＋應用層） | `node_a.py` | `br_b.py`（`UPLINK = True`）；電腦匯入 `flow.json` | 20% |
| 四 穩定度：連續 10 分鐘、按鈕斷網補送、A 重開機恢復 | `node_a.py` 另存成 `main.py` | `br_b.py` 繼續跑 | 20% |
| 五 電流預算與壓降（INA219，B 量 A） | `main.py`（拔 USB，B 供電） | `power_b.py` | 15% |
| 六 規劃題：LoRa 空中時間、RPL Rank、邊緣減量 | `plan.py`（A 或 B 跑都可以） | | 10% |

- **B 先跑**（`br_b.py` 會印「B 的 IP」），**A 再跑**：A 送 DIS 找 B，Shell 印「找到 B（IP），B 的 Rank 256，我的 Rank 1024」。
- A 一直找不到 B（教室的網路擋廣播）：把 B 印的 IP 填進 A 的 `cfg.py` 的 `GW_IP`，例如 `GW_IP = "192.168.1.37"`。
- 任務二：B 會印前 3 個訊框的十六進位＋欄位樹（DIS、報到、第一筆資料）。把「指紋」那一行和第一筆資料的十六進位（0000、0010 開頭的兩行）
  一起複製，電腦端 Thonny 右下角切到「本機 Python 3」→ 打開 `wsn_decode.py` → 執行 → 在 Shell 貼上 → 再按一次 Enter；兩邊的欄位樹要一樣。
- 任務三：Node-RED 匯入 `flow.json`，先把裡面的 `gNN` 全部取代成自己組的（例如 `g07`），按「部署」，打開 /ui。
- 任務四：`br_b.py` 從任務三起一直跑，每 60 秒印一行「[運作 … 秒]」；跑滿 600 秒截圖。按 B 的按鈕一下 → 模擬上行斷網 60 秒（Wi-Fi 還在，A 的訊框照收、放進待送箱），
  約 63 秒後 B 自己連回 broker、補送。A 的 `node_a.py` 另存成 `main.py`，在 A 的 Thonny **不要按 Stop**，直接拔掉 A 的 USB 再插回：B 印出第二次「A 報到」、「A 重開機 1 次」。
- 看門狗：`br_b.py` 會開看門狗（8 秒）。按 Stop 之後 B 大約 8 秒後會自己重開，這是正常的；要一行一行除錯時把 `cfg.py` 的 `WDT_ON` 改成 `False`。

## 要交什麼（檔名 `無線感測_W16_學號_姓名.zip`，交到 FlipClass 作業區）
- 任務一：截圖 ×1（A、B 並排的掃描結果）＋ `w16_checklist.csv` 第 2、3 列
- 任務二：截圖 ×3（假資料的 B 欄位樹、`wsn_decode.py` 對照、真資料的 A、B 並排）＋檢查表第 4 列
- 任務三：截圖 ×2（B 的 Shell 和儀表板並排；Node-RED 的 debug 看到 JSON）
- 任務四：截圖 ×3（運作 600 秒那一行、按鈕斷網到補送、A 重開機）＋ B 的 `error.log` ＋檢查表第 5～7 列
- 任務五：截圖 ×1（power_b.py 的結果）＋ `w16_power.csv` ＋ `w16_budget.csv` ＋檢查表第 1 列
- 任務六：截圖 ×1（plan.py）＋ `w16_plan.csv`
- **不要放 `mysecret.py`。**

## 延伸挑戰（不計分）
- 待送箱只存在記憶體裡，B 重開機就沒了：改成斷線時寫進檔案、連回來再補送（課堂練習第 6 題）。
- Node-RED 加一個文字元件，顯示 JSON 裡邊界路由器補的欄位：`n`（訊框位元組）、`loss`（遺失率）。
- 相鄰兩組合併：隔壁組的 A 改用你們的 PAN 與埠號，B 的欄位樹裡看得出是誰送的嗎？（兩組的 A 短位址都是 0x0002，要先改一個。）

`test_w16.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
本資料夾的 `wsnproto.py`、`wsntree.py`、`wsn_decode.py`、`mpy/` 逐字取自 `code/common/`；`util.py`、`netlink.py` 逐字取自主題 17；
`sensors.py`、`wifi.py`、`flow.json` 逐字取自主題 12；`ina219.py` 逐字取自主題 13；`airtime.py` 逐字取自主題 7；
`packet.py` 的 `Loss` 類別逐字取自主題 15 的 `packet.py`。
