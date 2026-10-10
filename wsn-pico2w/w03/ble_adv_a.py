import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import bluetooth

ble = bluetooth.BLE()
ble.active(True)
print("本機 BLE 位址：", ble.config("mac"))

# 廣播資料格式：長度 + 型別 + 內容
# 型別 0x01 是旗標，0x09 是完整裝置名稱
name = cfg.BLE_NAME.encode()      # 例如 b"wsn-g07-A"（含組號）
flags = bytes((2, 0x01, 0x06))
payload = flags + bytes((len(name) + 1, 0x09)) + name

ble.gap_advertise(200000, adv_data=payload)   # 每 200ms 廣播
print("開始廣播", cfg.BLE_NAME, "共", len(payload), "位元組")
