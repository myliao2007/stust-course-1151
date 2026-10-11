import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（名稱、組號…）
import bluetooth, struct, time
import aht20                       # AHT20 接在 GP4／GP5
from adtool import ad

def payload(t100):                 # 手刻 5 段 AD 結構
    p = ad(0x01, b"\x06")                            # Flags
    p += ad(0x09, cfg.BLE_NAME.encode())             # 名稱
    p += ad(0x03, struct.pack("<H", 0x181A))         # UUID
    p += ad(0x16, struct.pack("<Hh", 0x181A, t100))  # 溫度
    mfg = struct.pack("<HB", cfg.MFG_ID, cfg.GROUP)
    p += ad(0xFF, mfg)                               # 組號
    return p

ble = bluetooth.BLE()
ble.active(True)
while True:
    t, h = aht20.read()
    p = payload(round(t * 100))
    ble.gap_advertise(250000, adv_data=p)   # 每 250 ms 廣播
    print("%.2f 度，共 %d 位元組：" % (t, len(p)), p.hex(" "))
    time.sleep(5)                           # 每 5 秒換溫度
