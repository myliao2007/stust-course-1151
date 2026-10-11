import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（組號…）
import bluetooth, struct, time
import aht20                       # 改用 AHT20（原版用 ADC(4)）
from adtool import ad
ADV_MS = 1000                      # 廣播間隔：先 1000，再 200

ble = bluetooth.BLE()
ble.active(True)
seq = 0
while True:
    t, h = aht20.read()
    data = struct.pack("<HBBhH", cfg.MFG_ID, cfg.GROUP, seq,
                       round(t * 100), round(h * 100))
    p = ad(0x01, b"\x06") + ad(0xFF, data)   # 3＋10＝13 位元組
    ble.gap_advertise(ADV_MS * 1000, adv_data=p, connectable=False)
    print("seq %3d  %.2f 度  %.2f %%  " % (seq, t, h), p.hex(" "))
    seq = (seq + 1) % 256          # 序號 0～255 循環
    time.sleep_ms(2000)            # 每 2 秒換一次資料
