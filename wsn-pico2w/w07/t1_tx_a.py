import myid                        # 身份指紋（第一行）
import ap_a, time
from airtime import toa_ms, off_s
SF, SIZE, N = 7, 20, 5             # 改這裡：SF、每包幾個位元組、送幾包
OLD = False                        # True＝照原版 lora_tx.py 每包 sleep(10)

s, b = ap_a.up()                   # 開 AP、等 B 報到
t = toa_ms(SF, SIZE)
for seq in range(1, N + 1):
    time.sleep_ms(round(t))        # 模擬：這段時間電波在空中
    s.sendto(b"T1,%d,%d,%d" % (seq, SF, SIZE), b)   # 告訴 B：送完了
    quiet = 10 if OLD else off_s(t)
    print("第 %d 包 SF%d %d B：空中 %.1f ms，接著安靜 %.1f s" % (seq, SF, SIZE, t, quiet))
    if seq < N:
        time.sleep(quiet)
