import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（名稱、組號…）
# lowpower_a.py（延伸挑戰，不計分）：A 改成電池節點——不開 AP、只廣播；醒來讀值、廣播 AWAKE_MS，再 lightsleep
# A 拔掉 USB 改用行動電源；B 跑 listen_b.py 量遺失率（B 這時沒有 AP 可以連，不能跑 gw_b.py）
import bluetooth, machine, time
import sensors, packet
AWAKE_MS, SLEEP_MS = 1000, 4000

ble = bluetooth.BLE()
ble.active(True)
sensors.init()
seq = 0
while True:
    d = sensors.read_all()
    p = packet.pack(cfg.MFG_ID, cfg.GROUP, seq, d, cfg.BLE_NAME)
    ble.gap_advertise(cfg.ADV_MS * 1000, adv_data=p, connectable=False)
    time.sleep_ms(AWAKE_MS)        # 醒著廣播這一段，B 要在這段時間聽到
    ble.gap_advertise(None)        # 停止廣播
    seq += 1
    machine.lightsleep(SLEEP_MS)   # CPU 真的停住；醒來從下一行接著跑，seq 還在
