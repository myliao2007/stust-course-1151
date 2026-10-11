import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（BLE 名稱、組號…）
import bluetooth, struct
from adtool import ad

adv = ad(0x01, b"\x06") + ad(0xFF, struct.pack("<HB", cfg.MFG_ID, cfg.GROUP))
rsp = ad(0x09, cfg.BLE_NAME.encode())      # 名稱只放在掃描回應
ble = bluetooth.BLE()
ble.active(True)
ble.gap_advertise(100000, adv_data=adv, resp_data=rsp, connectable=False)
print("廣播", len(adv), "位元組：", adv.hex(" "))
print("掃描回應", len(rsp), "位元組：", rsp.hex(" "))
