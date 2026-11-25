# Adafruit IO 雲端儀表板：範例程式

無線感測網路協定與應用（Pico 2W 版）｜搭配投影片「Adafruit IO 雲端儀表板」

一片 Pico 2 W（830 孔麵包板）接 DHT11、BH1750、RGB LED，透過手機熱點連上網，用 MQTT 每 10 秒把溫度、濕度、光照送到 Adafruit IO；在 Adafruit IO 的儀表板上看儀表和曲線，按開關（Toggle）控制 RGB LED，用調色盤（Color Picker）選燈的顏色，溫度太高自動亮紅燈。

## 開始之前

1. `myid.py`：第 4 行改成組長學號，存到板子上（上次存過的板子沿用即可）。
2. `aio_cfg.py`：練習 2 在第 1、2 行填手機熱點的名稱和密碼；練習 3 註冊好 Adafruit IO 之後，第 3 行貼 Username、第 4 行貼 Active Key。每次改完都要再存回板子。
3. 存到板子的方法：Thonny 開啟檔案 → 檔案 → 另存新檔 → Raspberry Pi Pico → 檔名照原本的名字。

每支程式第一行都是 `import myid`，Shell 第一行會印出身份指紋（組長學號｜板子序號｜Wi-Fi MAC）。截圖要看得到這一行。

**Key 等於帳號密碼**：不要截圖、不要傳到群組、不要把填好熱點密碼和 Key 的 `aio_cfg.py` 上傳到 GitHub。外流了就到 Adafruit IO 按 REGENERATE KEY，把新的 Key 貼回 `aio_cfg.py`。

## 手機熱點：不用改名，把名稱和密碼抄進 `aio_cfg.py`

| `aio_cfg.py` | 填什麼 | 去哪裡看 |
|---|---|---|
| 第 1 行 `SSID` | 手機熱點的名稱，例如 `"小明的iPhone"` | Android：設定 › 搜尋「熱點」› Wi-Fi 熱點 › 熱點名稱；iPhone：設定 › 一般 › 關於本機 › 名稱 |
| 第 2 行 `PASSWORD` | 手機熱點的密碼 | Android：同一頁的熱點密碼（點一下才顯示）；iPhone：設定 › 個人熱點 › Wi-Fi 密碼 |

- 大小寫、空格、中文都要一模一樣，引號留著。名稱有彎的撇號（例如 `Ming’s iPhone`）打不出來時，先跑一次 `02_hotspot.py`，從 Shell 印出的清單複製名稱貼上。
- 頻段一定要 2.4 GHz：Android 選 2.4 GHz（Pixel 打開「延伸相容性」）；iPhone 打開「最大化相容性」，Pico 連線時手機停在個人熱點畫面。

## Adafruit IO 要建的 5 個 feed（名稱全小寫）

| feed | 放什麼 | 誰送 → 誰收 |
|---|---|---|
| `temperature` | 溫度（°C） | Pico → 儀表板 |
| `humidity` | 濕度（%） | Pico → 儀表板 |
| `light` | 光照（lux） | Pico → 儀表板 |
| `led` | `ON` / `OFF` | 儀表板（Toggle）→ Pico |
| `color` | 色碼，例如 `#FF8800` | 儀表板（Color Picker）→ Pico |

免費帳號：每分鐘最多 30 筆、最多 10 個 feed、5 個儀表板、資料存 30 天。一次送 3 個 feed，間隔至少 6 秒（60 ÷ 間隔 × 3 ≤ 30）；程式用 10 秒，留空間給開關和調色盤。

MQTT 設定：伺服器 `io.adafruit.com`、埠號 1883（課堂用，不加密；正式作品建議 8883）、帳號是 Username、密碼是 Key、topic 是 `Username/feeds/feed名稱`。

## 接線（830 孔麵包板，Pico USB 朝左，插 c、h 列第 1～20 排）

| 模組 | 接法 |
|---|---|
| 電源軌 | 3V3（第 36 腳，b5）→ 上＋軌、GND（第 38 腳，b3）→ 上－軌，上下電源軌用兩條跳線接通 |
| BH1750 | VCC → ＋軌、GND → －軌、SCL → j7（GP5）、SDA → j6（GP4），ADDR 不接 |
| RGB LED（共陰） | R → j9（GP6）、G → j10（GP7）、B → j11（GP8）、－ → －軌 |
| DHT11 | VCC → ＋軌、DATA → j20（GP15）、GND → －軌 |

所有模組都接 3.3 V。

## 檔案

| 檔案 | 內容 | 練習 |
|---|---|---|
| `myid.py` | 身份指紋 | — |
| `aio_cfg.py` | 手機熱點名稱和密碼、Username、Key；`topic()`、`send()`、`connect_wifi()`、`connect_aio()` | — |
| `01_check.py` | I2C 掃描、DHT11 和 BH1750 讀 5 次、RGB 亮紅綠藍 | 1 |
| `02_hotspot.py` | 掃描附近 Wi-Fi、連手機熱點、`mip` 安裝 `umqtt.simple` | 2 |
| `03_first_send.py` | 連上 Adafruit IO，送一筆溫度到 `temperature` | 4 |
| `04_upload.py` | 每 10 秒送溫度、濕度、光照 | 5 |
| `05_led.py` | 訂閱 `led`：儀表板開關控制 RGB LED，同時每 10 秒上傳 | 7 |
| `06_color.py` | 訂閱 `led`、`color`：調色盤選顏色；溫度 ≥ `T_HIGH` 自動紅燈 | 8 |

練習 3（註冊、拿 Key、建 feed）和練習 6（做儀表板）在瀏覽器上操作，步驟見投影片。

## 常見問題

| Shell 看到什麼 | 怎麼辦 |
|---|---|
| `ImportError: no module named 'umqtt'` | 重跑 `02_hotspot.py`，看到「umqtt.simple 裝好了」 |
| `Adafruit IO 連不上： 5`（或 4） | Username 或 Key 打錯；重新複製貼上，存回板子 |
| `Adafruit IO 連不上： -2` | 手機沒有行動網路 |
| `RuntimeError: 連不上熱點` | 熱點沒開、開成 5 GHz，或 `aio_cfg.py` 第 1、2 行的名稱密碼打錯 |
| Shell 有「送出」，網頁沒資料 | Feeds 頁的 Key 要和程式裡的名稱一模一樣（全小寫） |
| `注意：送太快了！` | 超過每分鐘 30 筆；把間隔調長，或檢查是不是兩片板子用同一個帳號 |

授課教師：廖明沂（南臺科技大學 電子工程系）
