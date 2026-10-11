import myid                      # 身份指紋（第一行；B 板：供電給 A、量 A 的電流）
import cfg                       # 本組參數、主題、金鑰
import time, json
from machine import Pin, I2C
import netlink, seal, ina219
# b_power.py（任務四）：叫 A 依序換 base、pm、eco，每種模式量 60 秒平均電流
# 接線（主題 13）：B 的 VBUS（40）→ INA219 VIN+，VIN− → A 的 VSYS（39），A、B 共地，A 拔掉 USB

MODES, SETTLE_S, MEAS_S, CAP = ("base", "pm", "eco"), 10, 60, 2000   # CAP：假設電池 2000 mAh
ina = ina219.INA219(I2C(0, sda=Pin(cfg.SDA), scl=Pin(cfg.SCL), freq=400_000), cfg.ZERO_MA)
st = {"mode": None, "pk": 0, "rtt": [], "last": 0}

def on_msg(topic, pkt):
    if topic == cfg.T_ST:
        s = pkt.decode()
        print("A 狀態：", s)
        if s.startswith("mode "):
            st["mode"] = s[5:]
        return
    r, ctr, body = seal.unseal(cfg.ENC_KEY, cfg.MAC_KEY, pkt, st["last"])
    if r == "ok":
        st["last"] = ctr
        c.publish(cfg.T_ACK, b"%d" % ctr)
        st["pk"] += 1                          # 這一段 A 送了幾包
        d = json.loads(body)
        if d["rtt"] > 0:
            st["rtt"].append(d["rtt"])

def run(sec, meas):              # 跑 sec 秒；meas＝True 時每 10 ms 讀一次 INA219
    s = v = n = 0
    t0 = tp = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < sec * 1000:
        if meas:
            s += ina.current_ma()
            v += ina.bus_v()
            n += 1
        c.check_msg()
        if time.ticks_diff(time.ticks_ms(), tp) > 20000:
            c.ping()             # B 只收不發的時候，自己送 PINGREQ
            tp = time.ticks_ms()
        time.sleep_ms(10)
    return (s / n, v / n, n) if n else None

def ask(m):                      # 叫 A 換模式：每 3 秒講一次，直到 A 回報「mode m」
    for _ in range(20):
        c.publish(cfg.T_CMD, m.encode())
        for _ in range(15):
            run(0.2, False)
            if st["mode"] == m:
                return
    raise OSError("A 沒回應：A 有沒有在跑 main.py？")

c = netlink.mqtt_up(cfg.CID_B, None, on_msg, (cfg.T_ST, cfg.T_SEC))
res = []
for m in MODES:
    ask(m)
    run(SETTLE_S, False)         # 先等 10 秒讓 A 穩定
    st["pk"], st["rtt"] = 0, []
    i, v, n = run(MEAS_S, True)
    r = sum(st["rtt"]) / len(st["rtt"]) if st["rtt"] else -1
    res.append((m, i, st["pk"], r))
    print("%-4s 平均 %.1f mA（%d 筆），VSYS %.2f V，A 送 %d 包，往返平均 %.0f ms" % (m, i, n, v, st["pk"], r))
c.publish(cfg.T_CMD, b"base")
f = open("w17_power.csv", "w")
f.write("模式,平均mA,包數,往返ms,理論h,保守h\n")
print("模式   平均mA  包數  往返ms  理論h  保守h（×0.7）")
for m, i, pk, r in res:
    print("%-5s %7.1f %5d %7.0f %6.1f %6.1f" % (m, i, pk, r, CAP / i, CAP / i * 0.7))
    f.write("%s,%.2f,%d,%.0f,%.1f,%.1f\n" % (m, i, pk, r, CAP / i, CAP / i * 0.7))
f.close()
for m, i, pk, r in res[1:]:
    print("%s 比 base 省 %.0f %%，續航變成 %.1f 倍" % (m, (res[0][1] - i) / res[0][1] * 100, res[0][1] / i))
c.disconnect()
