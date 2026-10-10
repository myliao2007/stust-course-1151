import myid
# cal_b.py（B 板）：任務四第 1、2 步。連讀 8 次看突波，再把旋鈕轉到底做兩點校正
from machine import Pin, ADC
from filter_cal import mean, median, TwoPoint

photo = ADC(Pin(26))
knob = ADC(Pin(27))

# 第 1 步：同一時刻連讀 8 次，比較平均和中位數
xs = [photo.read_u16() for _ in range(8)]
print("8 次讀值", xs)
span = max(xs) - min(xs)
print("最大－最小 {}  平均 {:.1f}  中位數 {}".format(span, mean(xs), median(xs)))

# 第 2 步：兩點校正。旋鈕轉到底就是 0 V，轉到另一頭就是 3.3 V
input("把旋鈕轉到 GND 那一頭，按 Enter ")
lo = median([knob.read_u16() for _ in range(15)])
input("把旋鈕轉到 3V3 那一頭，按 Enter ")
hi = median([knob.read_u16() for _ in range(15)])
cal = TwoPoint(lo, 0.0, hi, 3.3)
print("RAW_LO, RAW_HI = {}, {}".format(lo, hi))
print("a = {:.4e} V/格   b = {:.4f} V".format(cal.a, cal.b))
before = hi * 3.3 / 65535
print("讀到 {} → 校正前 {:.3f} V，校正後 {:.3f} V".format(hi, before, cal.y(hi)))
