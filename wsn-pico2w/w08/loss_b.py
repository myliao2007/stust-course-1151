import myid                        # 身份指紋（第一行）
import cfg, sta_b, random, wsnproto as w
from machine import ADC
# 任務六（B 板）：每片擲骰子，機率 P 假裝掉了；統計拼回幾包
USE_KNOB = False                   # 接了 GP26 旋鈕就改 True（0～50%）
P = 0.10                           # 沒接旋鈕：每片掉的機率
random.seed(cfg.GROUP)             # 種子用組號：重跑結果一樣
if USE_KNOB:
    P = ADC(cfg.KNOB_ADC).read_u16() / 65535 * 0.5
s, mac_a = sta_b.hello()
s.settimeout(None)
print("模擬遺失率 p = %.1f%%，等 A 送完（約 1 分鐘）…" % (P * 100))
r = w.Reassembler(timeout_ms=5000)
got, lost, done = {}, {}, {}
while True:
    f = s.recvfrom(256)[0]
    if f[:1] == b"#":              # A 的控制訊息 #ROUND,n／#END,包數
        key, v = f[1:].decode().split(",")
        if key == "END":
            break
        n = int(v)
        got[n] = lost[n] = done[n] = 0
        continue
    got[n] += 1
    if random.getrandbits(16) < P * 65536:   # 這一片掉了
        lost[n] += 1
        continue
    d = w.decode(f, True, None, r)
    if w.layer(d, "udp") and w.ok(d):
        done[n] += 1
count = int(v)
print(" n  收到片  丟掉片  拼回包  成功率  理論 (1-p)^n")
for n in sorted(got):
    print("%2d  %6d  %6d  %6d  %5.1f%%  %6.1f%%" % (n, got[n], lost[n],
          done[n], done[n] * 100 / count, (1 - P) ** n * 100))
print("Wi-Fi 本身掉了 %d 片（應該是 0）" % (count * sum(got) - sum(got.values())))
