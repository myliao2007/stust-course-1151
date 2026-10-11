# alarm.py：告警與資料新鮮度的判斷（B 板用；電腦上的 Python 也能跑，方便驗算）

class Alarm:
    """跨越門檻才告警：沒超標→超標回傳 "HOT"；降到 high－band 以下回傳 "OK"；其他時候回傳 None。"""

    def __init__(self, high, band=0.5):
        self.high, self.band, self.on = high, band, False

    def update(self, v):
        if v is None:                        # 缺值：不改變狀態
            return None
        if not self.on and v > self.high:
            self.on = True
            return "HOT"
        if self.on and v < self.high - self.band:
            self.on = False
            return "OK"
        return None

def state(age_s, stale_s, a_status, hot):
    """OLED 最下面那一行和 LED：回傳 (文字, LED 模式)；LED 模式 0＝滅、1＝亮、2＝閃。"""
    if a_status == "offline":                # broker 代發的遺囑：A 斷線了
        return "A OFFLINE", 2
    if age_s is None:
        return "WAIT DATA", 0
    if age_s > stale_s:                      # 太久沒新資料：數字是舊的
        return "STALE %ds" % age_s, 2
    if hot:
        return "HOT! %ds" % age_s, 1
    return "OK %ds" % age_s, 0
