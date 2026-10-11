import myid                        # 身份指紋（第一行）
import ap_a, time
from airtime import toa_ms
SF = 7                             # 上行的 SF；RX1 同 SF，RX2 固定 SF10（AS923）
GUARD = 20                         # 模擬才需要：多留 20 ms 給 Wi-Fi 延遲
W1 = 8 * (1 << SF) / 125 + GUARD   # 窗長＝8 個符元（一段前導碼）＋保護（ms）
W2 = 8 * (1 << 10) / 125 + GUARD


def judge(dt):                     # 下行在上行送完後 dt 毫秒到：落在哪個窗？
    if 1000 <= dt < 1000 + W1:
        return "RX1 收到（%d ms）" % dt
    if 2000 <= dt < 2000 + W2:
        return "RX2 收到（%d ms）" % dt
    return "錯過：%d ms 才到，接收機關著" % dt


s, b = ap_a.up()                   # 開 AP、等 B 報到
s.settimeout(3.2)
print("RX1 開 %.1f ms、RX2 開 %.1f ms" % (W1, W2))
for fcnt in range(1, 8):
    time.sleep_ms(round(toa_ms(SF, 12)))       # 12 位元組的上行在空中
    t0 = time.ticks_ms()                       # 上行送完：從這裡數 1 秒、2 秒
    s.sendto(b"UP,%d" % fcnt, b)               # 告訴 B：上行送完了
    try:
        while not s.recvfrom(64)[0].startswith(b"DN"):
            pass                               # 不是下行就再等
        got = judge(time.ticks_diff(time.ticks_ms(), t0))
    except OSError:
        got = "3.2 秒內沒有下行"
    print("FCnt %d：%s" % (fcnt, got))
    time.sleep(3.5)                # 模擬只等幾秒；真的要照任務一的工作週期等
