# sensors.py（A 板）：AHT20＋BMP280＋BH1750 都掛在 I2C0（SDA＝GP4 第 6 腳、SCL＝GP5 第 7 腳）
# 讀不到的感測器回傳 None（JSON 裡變成 null），不要用 0 代替
from machine import Pin, I2C
import time, struct

AHT, BMP, BH = 0x38, 0x77, 0x23
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
_cal = None                                  # BMP280 出廠校正值（12 個）

def _aht_init():
    time.sleep_ms(100)                       # 上電穩定時間
    i2c.writeto(AHT, b"\xbe\x08\x00")        # AHT20 初始化校正
    time.sleep_ms(10)

def _bmp_init():
    global _cal
    _cal = struct.unpack("<HhhHhhhhhhhh", i2c.readfrom_mem(BMP, 0x88, 24))

def _bh_init():
    i2c.writeto(BH, b"\x01")                 # BH1750 Power On
    i2c.writeto(BH, b"\x10")                 # 連續高解析度模式（一次約 120～180 ms）
    time.sleep_ms(180)

def read_aht20():
    i2c.writeto(AHT, b"\xac\x33\x00")        # 觸發一次量測，約 80 ms
    time.sleep_ms(80)
    d = i2c.readfrom(AHT, 7)
    if d[0] & 0x80:                          # 忙碌位元還是 1：這次沒量完
        return None, None
    h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    return t / 1048576 * 200 - 50, h / 1048576 * 100

def bmp280_compensate(adc_t, adc_p, cal):
    """Bosch BMP280 資料手冊的浮點數補償公式；回傳 (溫度 °C, 氣壓 hPa)。"""
    T1, T2, T3, P1, P2, P3, P4, P5, P6, P7, P8, P9 = cal
    v1 = (adc_t / 16384 - T1 / 1024) * T2
    v2 = (adc_t / 131072 - T1 / 8192) ** 2 * T3
    tf = v1 + v2                             # t_fine：氣壓補償也要用
    v1 = tf / 2 - 64000
    v2 = v1 * v1 * P6 / 32768 + v1 * P5 * 2
    v2 = v2 / 4 + P4 * 65536
    v1 = (1 + (P3 * v1 * v1 / 524288 + P2 * v1) / 524288 / 32768) * P1
    if v1 == 0:                              # 避免除以 0
        return tf / 5120, None
    p = (1048576 - adc_p - v2 / 4096) * 6250 / v1
    p += (P9 * p * p / 2147483648 + p * P8 / 32768 + P7) / 16
    return tf / 5120, p / 100                # Pa ÷ 100 ＝ hPa

def read_bmp280():
    i2c.writeto_mem(BMP, 0xF4, b"\x2d")      # 溫度 ×1、氣壓 ×4、強制模式量一次
    time.sleep_ms(20)                        # 資料手冊：這個設定最長 13.3 ms
    d = i2c.readfrom_mem(BMP, 0xF7, 6)
    adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
    adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
    return bmp280_compensate(adc_t, adc_p, _cal)

def read_lux():
    raw = i2c.readfrom(BH, 2)
    return ((raw[0] << 8) | raw[1]) / 1.2

def read_all():
    """一次讀三顆：t、h（AHT20）、t2、p（BMP280）、lux（BH1750）；讀不到的是 None。"""
    t = h = t2 = p = lux = None
    try:
        t, h = read_aht20()
    except OSError:
        pass
    try:
        t2, p = read_bmp280()
    except (OSError, TypeError):             # 開機沒讀到校正值
        pass
    try:
        lux = read_lux()
    except OSError:
        pass
    r = lambda v, n: None if v is None else round(v, n)
    return {"t": r(t, 2), "h": r(h, 1), "p": r(p, 1),
            "lux": r(lux, 1), "t2": r(t2, 2)}

for _f in (_aht_init, _bmp_init, _bh_init):
    try:
        _f()
    except OSError:
        print("找不到感測器：", _f.__name__)   # 先用主題 2 的 i2c_scan.py 查接線
