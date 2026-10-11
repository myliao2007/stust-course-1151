# util.py：校時、記錄、會餵狗的等待、退避重試（A、B 兩片都要存）
# 修正原版：① log() 先校時 ② 等待時每秒餵一次看門狗 ③ 重試撐得過 60 秒斷網
import time, machine, random
TZ = 8 * 3600            # 台灣＝UTC＋8 小時
_off = None              # None＝還沒校時
_wdt = None              # 有開看門狗就記在這裡
_down = None             # 任務三：模擬斷網到幾點（ticks_ms）

def use_wdt(w):
    global _wdt
    _wdt = w

def sync_time(host="pool.ntp.org"):   # 連上 Wi-Fi 後呼叫一次
    global _off
    try:
        import ntptime
        ntptime.host = host
        ntptime.settime()                # 板子時鐘改成 UTC
        _off = TZ
    except Exception:                    # 連不到 NTP：Thonny 對過時就沿用
        _off = 0 if time.localtime()[0] >= 2025 else None
    return _off is not None

def ts():
    if _off is None:                     # 沒校時：寫開機後第幾秒，不寫錯的日期
        return "未校時+%ds" % (time.ticks_ms() // 1000)
    return "%04d-%02d-%02d %02d:%02d:%02d" % time.localtime(time.time() + _off)[:6]

def log(msg):                            # 寫進 error.log，隔天才查得到
    line = ts() + " " + str(msg)
    try:
        with open("error.log", "a") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line)

def feed():                             # 餵狗一次（沒開看門狗就什麼都不做）
    if _wdt:
        _wdt.feed()

def nap(ms):                             # 等 ms 毫秒，每 1 秒餵一次狗
    end = time.ticks_add(time.ticks_ms(), int(ms))
    while True:
        feed()
        left = time.ticks_diff(end, time.ticks_ms())
        if left <= 0:
            return
        time.sleep_ms(min(left, 1000))

def retry(fn, tries=10, cap=60):         # 退避 1,2,4…60 秒，再加 0～1 秒錯開
    wait = 1
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            j = random.getrandbits(10)   # 0～1023 ms：各組錯開
            log("第 %d 次失敗 %s，%d 秒後再試" % (i + 1, e, wait))
            nap(wait * 1000 + j)
            wait = min(wait * 2, cap)
    log("連續 %d 次失敗，重新開機" % tries)
    machine.reset()                      # 共等約 303 秒才重開

def drop(sec):                           # 任務三：從現在起模擬斷網 sec 秒
    global _down
    _down = time.ticks_add(time.ticks_ms(), sec * 1000)

def down():                              # 還在模擬斷網嗎？
    global _down
    if _down is not None and time.ticks_diff(_down, time.ticks_ms()) > 0:
        return True
    _down = None
    return False
