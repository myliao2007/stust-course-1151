# myid.py：印出學號、板子序號、Wi-Fi MAC（每個練習都會用到）
import machine, network, binascii

STUDENT = "4A1G0001"        # ← 改成組長的學號

wlan = network.WLAN(network.STA_IF)
wlan.active(True)           # 先打開 Wi-Fi 晶片，MAC 才讀得到
SN  = binascii.hexlify(machine.unique_id()).decode().upper()
MAC = binascii.hexlify(wlan.config("mac"), ":").decode().upper()

print("學號", STUDENT, "| 序號", SN, "| MAC", MAC)
wlan.active(False)          # 讀完就關掉 Wi-Fi，晶片才不會一直發熱
