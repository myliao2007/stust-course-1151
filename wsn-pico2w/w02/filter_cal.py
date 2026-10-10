# filter_cal.py：任務四的小工具（純 Python，存到 B 板）
# mean 平均、median 中位數、MovingAvg 滑動平均、TwoPoint 兩點校正

def mean(xs):
    return sum(xs) / len(xs)

def median(xs):
    s = sorted(xs)
    n = len(s)
    m = n // 2
    if n % 2:                        # 奇數筆：正中間那一筆
        return s[m]
    return (s[m - 1] + s[m]) / 2     # 偶數筆：中間兩筆的平均

class MovingAvg:
    """滑動平均：只留最近 n 筆，每來一筆就重算一次平均。"""
    def __init__(self, n):
        self.n = n
        self.buf = []
    def add(self, x):
        self.buf.append(x)
        if len(self.buf) > self.n:
            self.buf.pop(0)
        return mean(self.buf)

class TwoPoint:
    """兩點校正：真值 = a × 讀值 + b"""
    def __init__(self, x1, y1, x2, y2):
        self.a = (y2 - y1) / (x2 - x1)
        self.b = y1 - self.a * x1
    def y(self, x):
        return self.a * x + self.b
