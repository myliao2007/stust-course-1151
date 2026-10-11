import myid                      # 身份指紋（B 板：任務四之一）
import cfg
import network, socket, time
from machine import Pin, I2C
import ina219

CYCLES = 3                                     # 量幾個完整週期（睡＋醒）
ap = network.WLAN(network.AP_IF)               # B 開 AP：A 每次醒來連上來送一筆
ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
ap.active(True)
u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
u.bind(("0.0.0.0", cfg.UDP_PORT))
u.setblocking(False)
i2c = I2C(0, sda=Pin(cfg.SDA), scl=Pin(cfg.SCL), freq=400_000)
ina = ina219.INA219(i2c, cfg.ZERO_MA)
mark = Pin(cfg.MARK_PIN, Pin.IN, Pin.PULL_DOWN)   # A 睡著＝1，醒著＝0
Pin(cfg.GO_PIN, Pin.OUT, value=1)              # 開始線一直拉高


def poll_udp():                  # A 醒來送的那一筆：印出 A 的指紋
    try:
        print("  A 送來：", u.recv(256).decode())
    except OSError:
        pass


ma = [0.0, 0.0]; k = [0, 0]; ms = [0, 0]       # [醒, 睡]：電流總和、筆數、毫秒
print("等 A 第一次睡著（標記線變 1）才開始算…")
while mark.value() == 0:
    poll_udp(); time.sleep_ms(10)
lv, cyc, t_lv = 1, 0, time.ticks_ms()
while cyc < CYCLES:
    v = mark.value()
    if v != lv:                                # 換狀態：把上一段的時間記下來
        now = time.ticks_ms()
        ms[lv] += time.ticks_diff(now, t_lv); t_lv = now; lv = v
        if v == 1:                             # 又睡著了＝一個週期結束
            cyc += 1; print("第 %d 個週期完成" % cyc)
        continue
    ma[lv] += ina.current_ma(); k[lv] += 1     # 依標記線分開累加
    poll_udp(); time.sleep_ms(10)

I_on, I_slp = ma[0] / k[0], ma[1] / k[1]      # 醒著、睡著各自的平均電流
t_on, t_slp = ms[0] / 1000 / CYCLES, ms[1] / 1000 / CYCLES
I_meas = (ma[0] + ma[1]) / (k[0] + k[1])       # 整段直接平均（不靠公式）
print("醒著：平均 %.1f mA，每次 %.2f 秒" % (I_on, t_on))
print("睡著：平均 %.2f mA，每次 %.2f 秒" % (I_slp, t_slp))
print("整段直接量的平均：%.3f mA" % I_meas)
with open("duty_result.txt", "w") as f:        # 給 duty.py 讀
    f.write("%.3f,%.3f,%.3f,%.3f,%.3f" % (I_on, t_on, I_slp, t_slp, I_meas))
