# counter.py：A 板的計數器存檔，重開機也不會倒退（每 STEP 筆才寫一次 flash）
STEP = 20
FILE = "ctr.txt"

def _save(c):
    with open(FILE, "w") as f:
        f.write(str(c))

def start():
    """開機時呼叫一次：從上次存的值再跳 STEP，保證比用過的都大。"""
    try:
        with open(FILE) as f:
            c = int(f.read()) + STEP
    except OSError:
        c = 0                          # 第一次開機，還沒有檔案
    _save(c)
    return c

def next_(c):
    """每送一筆前呼叫：回傳新的計數器，遇到 STEP 的倍數就存檔。"""
    c += 1
    if c % STEP == 0:
        _save(c)
    return c
