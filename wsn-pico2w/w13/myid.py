# myid.py：身份指紋＋組別。兩片板子都要存一份；只改前三行
STUDENT_ID = "請改成組長學號"   # 組長學號（兩片一樣）
GROUP = 1                       # 組號（1～20，兩片一樣）
BOARD = "A"                     # 這一片是 "A" 還是 "B"

import machine, network, rp2, time, binascii
rp2.country("TW")                        # 台灣的無線電規範，要在打開無線晶片之前設定
wlan = network.WLAN(network.STA_IF)
was_on = wlan.active()
wlan.active(True)                        # 無線晶片要開著才讀得到 MAC
MAC = binascii.hexlify(wlan.config("mac"), ":").decode().upper()
wlan.active(was_on)                      # 讀完放回原本的狀態
SN = binascii.hexlify(machine.unique_id()).decode().upper()
t = time.localtime()                     # Thonny 連線時會幫板子對時
WHEN = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4])
print("學號", STUDENT_ID, "| 第", GROUP, "組 | 板子", BOARD, "| 序號", SN, "| MAC", MAC, "|", WHEN)
