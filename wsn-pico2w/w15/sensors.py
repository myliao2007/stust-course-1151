# sensors.py（A 板）：對外只有 init() 和 read_all() 兩個函式，主程式不用管裡面怎麼讀
# AHT20（0x38，溫溼度）＋BH1750（0x23，照度）都掛在 I2C0：SDA＝GP4（第 6 腳）、SCL＝GP5（第 7 腳）
# 找不到 AHT20 時，溫度改用晶片內部溫度 ADC(4) 當替身（狀態 "sub"），鏈路照樣能先通
from machine import Pin, I2C, ADC
import time
AHT, BH = 0x38, 0x23
_i2c = None
_adc = ADC(4)                        # 替身：晶片內部溫度
_has = []                            # 找得到的感測器位址


def init():
    global _i2c
    _i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100_000)
    found = _i2c.scan()
    print("I2C 掃描結果：", ["0x%02X" % a for a in found])
    if AHT in found:
        time.sleep_ms(100)                   # 上電穩定時間
        _i2c.writeto(AHT, b"\xbe\x08\x00")   # AHT20 初始化校正
        _has.append(AHT)
    if BH in found:
        _i2c.writeto(BH, b"\x01")            # BH1750 Power On
        _i2c.writeto(BH, b"\x10")            # 連續高解析度模式（一次約 120～180 ms）
        _has.append(BH)
    time.sleep_ms(180)                       # 等第一筆量完
    return found


def _aht():
    _i2c.writeto(AHT, b"\xac\x33\x00")       # 觸發一次量測，約 80 ms
    time.sleep_ms(80)
    d = _i2c.readfrom(AHT, 7)
    if d[0] & 0x80:                          # 忙碌位元還是 1：這次沒量完
        raise OSError("AHT20 busy")
    h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    t = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    return t / 1048576 * 200 - 50, h / 1048576 * 100


def _lux():
    raw = _i2c.readfrom(BH, 2)
    return ((raw[0] << 8) | raw[1]) / 1.2


def _sub():                                  # 替身溫度：主題 15 原版 sensors.py 的算法
    v = _adc.read_u16() * 3.3 / 65535
    return 27 - (v - 0.706) / 0.001721


def read_all():
    """回傳 {'t': 度, 'h': %, 'lx': lux, 'st': 'ok'／'sub'／'err'}；讀不到的值是 None，不用 0 代替。"""
    t = h = lx = None
    st = "ok"
    if AHT in _has:
        try:
            t, h = _aht()
        except OSError:
            st = "err"
    else:
        t, st = _sub(), "sub"
    if BH in _has:
        try:
            lx = _lux()
        except OSError:
            st = "err"
    elif st == "ok":
        st = "err"                           # 少了照度也要讓 B 知道
    r = lambda v, n: None if v is None else round(v, n)
    return {"t": r(t, 2), "h": r(h, 2), "lx": r(lx, 1), "st": st}
