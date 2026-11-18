# 零件認識與模組接線：範例程式

無線感測網路協定與應用（Pico 2W 版）｜搭配投影片「零件認識與模組接線」

每支程式都可以直接在 Thonny 開啟、存到 Pico 2 W 上執行。檔案裡有中文註解，比投影片上寫得更細。

## 接線總表（全部模組同時接上也不會衝突）

| 模組 | VCC | 訊號腳 | GND |
|---|---|---|---|
| DHT11 溫濕度 | 3V3(OUT) 第 36 腳 | DATA → GP15（第 20 腳） | 第 38 腳 |
| HC-SR501 人體紅外線 | VBUS 第 40 腳（5 V） | OUT → GP14（第 19 腳） | 第 38 腳 |
| HC-SR04 超音波 | VBUS 第 40 腳（5 V） | Trig → GP12（第 16 腳）、Echo → GP13（第 17 腳） | 第 38 腳 |
| 電容式土壤溼度 | 3V3(OUT) 第 36 腳 | AOUT → GP26／ADC0（第 31 腳） | 第 33 腳 |
| I2C 模組（BH1750、OLED、MPU-6050、BMP280、INA219） | 3V3(OUT) 第 36 腳 | SDA → GP4（第 6 腳）、SCL → GP5（第 7 腳） | 第 38 腳 |
| 有源蜂鳴器 | 3V3(OUT) 第 36 腳 | I/O → GP11（第 15 腳） | 第 38 腳 |
| RGB LED | （共陰） | R → GP6（第 9 腳）、G → GP7（第 10 腳）、B → GP8（第 11 腳） | − → 第 8 腳 |
| nRF24L01+ | 3V3(OUT) 第 36 腳（**不可接 5 V**） | SCK → GP18、MOSI → GP19、MISO → GP16、CSN → GP17、CE → GP20 | 第 38 腳 |
| 3 號電池 × 3 | ＋ → VSYS 第 39 腳 | — | − → 第 38 腳 |

注意：

- HC-SR04 的 Echo 是 5 V，只能接一般 GP，**不可以接 GP26～GP28**。
- 改用電池時先拔掉 USB；VBUS 沒有 5 V 了，超音波、人體紅外線要改接 VSYS。程式要存成板子上的 `main.py` 才會開機自動執行。

## I2C 位址

| 模組 | 位址 |
|---|---|
| BH1750（GY-302） | 0x23 |
| 0.96 吋 OLED | 0x3C |
| INA219 | 0x40 |
| MPU-6050（GY-521） | 0x68 |
| BMP280 | 0x76 |

## 檔案

| 檔案 | 內容 |
|---|---|
| `01_dht11.py` | DHT11 讀溫度、濕度 |
| `02_pir.py` | HC-SR501 有人／沒人（狀態變了才印） |
| `03_hcsr04.py` | HC-SR04 量距離（公分） |
| `04_soil.py` | 土壤溼度：讀值 → 電壓 → 百分比（DRY、WET 要自己校正） |
| `05_i2c_scan.py` | I2C 掃描：誰在線上 |
| `06_bh1750.py` | BH1750 光照度（lux） |
| `07_oled.py` | OLED 顯示文字（先 `mip.install("ssd1306")`） |
| `08_mpu6050.py` | MPU-6050 加速度、角速度 |
| `bmp280.py` | BMP280 小驅動（先存到板子上） |
| `09_bmp280.py` | BMP280 溫度、氣壓 |
| `10_ina219.py` | INA219 電壓、電流 |
| `11_buzzer.py` | 有源蜂鳴器嗶三聲 |
| `12_rgb.py` | RGB LED 用 PWM 混顏色 |
| `13_nrf_tx.py` | nRF24L01 感測節點：每 2 秒送一筆（先 `mip.install("nrf24l01")`） |
| `14_nrf_rx.py` | nRF24L01 收集端：收到就拆開印出 |

## 安裝驅動

板子先連上 Wi-Fi，在 Thonny 的 Shell 打：

```python
import mip
mip.install("ssd1306")
mip.install("nrf24l01")
```
