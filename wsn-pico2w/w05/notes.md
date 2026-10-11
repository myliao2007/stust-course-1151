# 主題 5 ZigBee 協定與應用：上機程式（Pico 2 W ×2，PicoBee）

這學期沒有 XBee 模組。老師提供 **PicoBee**（`picobee.py`）：讓 Pico 2 W 的行為像一顆 ZigBee 模組，
有 +++ 命令模式、AT 指令、三種角色、PAN ID、64／16 位元位址、API 訊框與檢查碼、會睡覺的終端裝置。

- A 板開 AP（`wsn-gNN`），B 板連上去。兩片之間的「空氣」是 Wi-Fi UDP，裡面裝的是**真的 IEEE 802.15.4 MAC 訊框**（含 FCS）。
- 頻道 CH（11～26）是**模擬欄位**：CH 對到 UDP 埠 5400＋CH。電波實際走的是 A 的 Wi-Fi 頻道（cfg.CHANNEL：1、6、11 輪流）。
- 主控 MCU 和模組之間的序列線用函式模擬：`bee.write(位元組)` 是送進模組（DIN），`bee.read()` 是模組送出來（DOUT）。
- `bee.term()` 是互動的 **PicoBee 終端機**（在 Thonny 的 Shell 打字）。

## 先做這三件事
1. 兩片板子都存：`myid.py`、`cfg.py`、`wsnproto.py`、`wsntree.py`、`picobee.py`。
   `myid.py` 只改前三行：`STUDENT_ID`（組長學號）、`GROUP`（組號）、`BOARD`（A 或 B）。`cfg.py` 不用改。
2. 每支上機程式第一行都是 `import myid`，截圖要看得到它印的那一行（學號｜第幾組｜板子｜序號｜MAC｜時間）和右下角的日期時間。
   Thonny 第二次執行沒印出這一行時，先按 Stop 再執行。
3. 兩人兩台電腦，一人顧一片板子（同一台電腦開兩個 Thonny 也可以：工具 → 選項 → 一般，取消「只允許一個 Thonny」）。
   **A 板先跑**，B 板再跑（B 要連 A 的 AP）。

## PicoBee 終端機怎麼打
| 你打的 | 送進模組的 | 說明 |
|---|---|---|
| `+++` 按 Enter | `+++`（**不補** Enter） | 前後各靜默 1 秒，1 秒後模組回 `OK`；真的終端機打完 +++ 不能按 Enter |
| `ATID 1007` 按 Enter | `ATID 1007` 加 Enter（CR） | 命令模式：設定；`ATID` 不加數字是查詢 |
| `ATID 1007,WR,CN` | 一次下三個指令 | 逗號後面省略 AT |
| 其他文字按 Enter | 文字加 CR | 透明模式：送到 DH／DL 指定的對象（DH＝0、DL＝0 是協調器） |
| API 模式（ATAP 1）時打十六進位 | 對應的位元組 | 例如 `7E 00 04 08 52 4E 4A 0D` |
| `.sniff 1`／`.sniff 2` | （終端機自己的指令） | 印每個空中訊框的十六進位（2 再加欄位樹） |
| `.status`、`.last`、`.hex on`、`.wait 3`、`.quit` | （終端機自己的指令） | `.help` 看全部 |

常用 AT 指令：`ATCE 1`（當協調器）、`ATSM 4`（會睡覺的終端裝置）、`ATID`（延伸 PAN ID）、`ATOI`（16 位元 PAN ID）、`ATCH`（頻道）、
`ATSC`（掃哪些頻道）、`ATMY`（16 位元位址）、`ATSH`／`ATSL`（64 位元位址＝myid 印的序號）、`ATDH`／`ATDL`（送給誰）、
`ATAI`（入網狀態，0＝成功）、`ATNJ`（開放加入）、`ATNC`（還能收幾個子節點）、`ATNI`／`ATND`／`ATDN`（名字、節點探索）、
`ATSP`／`ATST`（睡多久、醒多久）、`ATD0`～`ATD4`、`ATIR`、`ATIS`（I/O）、`ATAP`（API 模式）、`ATWR`（存檔）、`ATRE`（回預設）、`ATNR`（重新入網）、`ATCN`（離開）。

## 誰跑哪支程式
| Lab | A 板 | B 板 | 配分 |
|---|---|---|---|
| 1 AT 與角色 | `lab1_a.py`（終端機，手動設成協調器） | `lab1_b.py`（程式下 AT，再進終端機）；1-3 改跑 `lab1_b_temp.py` | 30% |
| 2 API 與檢查碼 | `lab2_a.py`（照提示一步一步按 Enter） | `lab2_b.py`（印空中訊框的十六進位與欄位樹） | 35% |
| 3 直接 I/O 與會睡覺的終端裝置 | `lab3_a.py`（選單 1、2、3） | `lab3_b.py`（終端機，自己下 ATD0、ATSM…） | 35% |
| 4 跨組網狀與節點探索（延伸，不計分） | `lab4.py` | `lab4.py` | － |

- **兩層驗證**：B 印出來的十六進位（`.sniff 1` 或 `lab2_b.py`），整行複製，貼到電腦上 Thonny 打開的 `wsn_decode.py`（按執行，貼上，再按一次 Enter），兩邊的欄位樹要一樣。
- `uart_loopback.py`：延伸練習，以後接真的 XBee 之前先測 UART（一條杜邦線短接 GP0、GP1）。

## Lab 3 接線（B 板）
- 光敏電阻：一腳接 3V3(OUT)（第 36 腳），另一腳接 GP26（第 31 腳）；10 kΩ 電阻從 GP26 接到 GND（第 38 腳）。
- LED：GP15（第 20 腳）→ 220 Ω → LED 長腳；LED 短腳 → GND（第 18 腳）。
- Lab 1-3 的溫度：AHT20 模組 SDA → GP4（第 6 腳）、SCL → GP5（第 7 腳）、VIN → 3V3(OUT)、GND → GND。

## 分組參數（cfg.py 自動算）
- AP：`wsn-gNN`，密碼 `pico`＋（組號×1234 取後四位），Wi-Fi 頻道 1、6、11 輪流（和主題 3 一樣）。
- PAN：`ATID` 設 1000＋組號（十六進位）：第 7 組 `1007`、第 10 組 `100A`、第 12 組 `100C`。
- 模擬頻道：協調器開網時自己做「能量掃描」挑最安靜的（常見是 CH 15＝0xF）；`ATSC 4210` 只掃 15、20、25。

## 記憶體不夠時
匯入時出現 `MemoryError`：把 `mpy/` 資料夾裡的 `wsnproto.mpy`、`wsntree.mpy`、`picobee.mpy` 存到板子上，並把同名的 `.py` 刪掉。

`test_w05.py`、`test_w05_sim.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
