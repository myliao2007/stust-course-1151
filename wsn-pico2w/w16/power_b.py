import myid                      # 身份指紋（第一行；B 板：任務五，B 量 A）
import cfg
import time, array
from machine import Pin, I2C
import ina219, netlink, util, border
# power_b.py（B 板）：A 拔掉 USB、改由 B 供電（B 的 VBUS → INA219 → A 的 VSYS），A 跑 main.py
# 每 10 ms 讀一次 A 的電流與 VSYS，量 60 秒；同時當邊界路由器（回 DIS、收 A 的訊框）
i2c = I2C(0, sda=Pin(cfg.SDA), scl=Pin(cfg.SCL), freq=400_000)
print("I2C 掃描：", [hex(a) for a in i2c.scan()])        # 要看到 0x40
ina = ina219.INA219(i2c, cfg.ZERO_MA)
print("B 的 IP", util.retry(netlink.wifi_up))
br = border.Border(show=0)
N = cfg.MEAS_S * 100
ia = array.array("h", bytes(2 * N))      # 分流電壓原始值（1＝0.1 mA）
va = array.array("H", bytes(2 * N))      # 匯流排電壓原始值（1＝4 mV）：A 的 VSYS
print("等 A 送來第一筆資料（最多 90 秒）……")
t = time.ticks_ms()
while br.poll() is None:
    if time.ticks_diff(time.ticks_ms(), t) > 90000:
        raise OSError("90 秒沒收到 A：查 VSYS、GND 兩條線，A 有沒有存 main.py")
    time.sleep_ms(10)
k, got = 0, 1
nxt = time.ticks_ms()
while k < N:                             # 非阻塞：時間到才讀 INA219，其餘時間收訊框
    if time.ticks_diff(time.ticks_ms(), nxt) >= 0:
        nxt = time.ticks_add(nxt, 10)
        ia[k] = ina.shunt_raw()
        va[k] = ina.read(0x02) >> 3
        k += 1
        if k % 1000 == 0:
            print("%2d 秒：A 的訊框 %d 筆" % (k // 100, got))
    if br.poll():
        got += 1
s = sorted(ia)
avg = ina.ma(sum(ia) / N)
low, med, top = ina.ma(s[N // 10]), ina.ma(s[N // 2]), ina.ma(s[-1])
vavg, vmin = sum(va) / N * 0.004, min(va) * 0.004
sx, sy = sum(ia), sum(va)                # 最小平方法：VSYS 對電流的斜率＝路徑電阻
sxx = sum(i * i for i in ia)
sxy = sum(i * v for i, v in zip(ia, va))
den = N * sxx - sx * sx
r = 0 if den == 0 else -(N * sxy - sx * sy) / den * 0.004 / 0.0001
print("=== A 的電流預算（%d 秒，%d 筆，A 送了 %d 筆）===" % (cfg.MEAS_S, N, got))
print("平均 %.1f mA｜待機（最低一成）%.1f｜中位數 %.1f｜最大 %.1f mA" % (avg, low, med, top))
print("VSYS 平均 %.3f V、最低 %.3f V（掉 %d mV）" % (vavg, vmin, round((vavg - vmin) * 1000)))
print("電源路徑電阻約 %.2f Ω：每多 100 mA，VSYS 掉 %d mV" % (r, round(r * 100)))
print("最大電流佔 USB 500 mA 的 %d %%" % round(top / 5))
f = open("w16_power.csv", "w")
f.write("平均mA,待機mA,中位數mA,最大mA,VSYS平均V,VSYS最低V,路徑電阻Ω,A訊框\n")
f.write("%.1f,%.1f,%.1f,%.1f,%.3f,%.3f,%.2f,%d\n" % (avg, low, med, top, vavg, vmin, r, got))
f.close()
print(br.line())
