# sensor.py：A 板的感測與訊息格式（給 a_pub.py、a_robust.py 匯入，不用單獨執行）
# 接線（A 板）：AHT20＋BMP280 模組 VIN→3V3(OUT) 第 36 腳、GND→GND 第 38 腳、
#               SDA→GP4 第 6 腳、SCL→GP5 第 7 腳（I2C 位址 0x38、0x77）
from machine import Pin, I2C, ADC
import time
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
AHT = 0x38
adc = ADC(4)                        # ADC4 = 晶片內建溫度感測器（對照用）
time.sleep_ms(100)                  # 上電穩定時間
i2c.writeto(AHT, b"\xbe\x08\x00")   # 初始化校正

def aht20():
    i2c.writeto(AHT, b"\xac\x33\x00")   # 觸發一次量測
    time.sleep_ms(80)
    d = i2c.readfrom(AHT, 7)            # 狀態＋濕度＋溫度共 7 位元組
    h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    return t / 1048576 * 200 - 50, h / 1048576 * 100

def chip():
    v = adc.read_u16() * 3.3 / 65535
    return 27 - (v - 0.706) / 0.001721

def payload(seq):
    """固定欄位順序、不留空白的 JSON，長度好算：b'{"seq":1,"t":26.55,"rh":61.2,"chip":27.6}'"""
    t, rh = aht20()
    return b'{"seq":%d,"t":%.2f,"rh":%.1f,"chip":%.1f}' % (seq, t, rh, chip())
