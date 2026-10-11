# 老師示範用（選用，要一台 Linux 當 6LBR），學生不用跑
# 修正：原版先 ble.irq(irq_handler) 才定義函式，
#       會 NameError；這一版先定義、再註冊
import bluetooth, struct
_IRQ_L2CAP_ACCEPT = 22
_IRQ_L2CAP_CONNECT = 23
_IRQ_L2CAP_RECV = 25
IPSP_PSM = 0x0023

buf = bytearray(1280)

def irq_handler(event, data):
    if event == _IRQ_L2CAP_ACCEPT:
        conn, cid, psm, our_mtu, peer_mtu = data
        print("接受連線 PSM=0x%04X MTU=%d" % (psm, peer_mtu))
        return 0            # 回傳 0 表示接受這個通道
    elif event == _IRQ_L2CAP_CONNECT:
        print("L2CAP 通道已建立")
    elif event == _IRQ_L2CAP_RECV:
        conn, cid = data
        n = ble.l2cap_recvinto(conn, cid, buf)
        print("收到", n, "位元組：", bytes(buf[:n]).hex())

ble = bluetooth.BLE()
ble.active(True)
ble.irq(irq_handler)
ble.l2cap_listen(IPSP_PSM, 1280)   # RFC 7668 要求 MTU 1280

# 廣播帶上 IPSP 服務 UUID 0x1820，型別 0x03
flags = bytes((2, 0x01, 0x06))
uuid = struct.pack("<BBH", 3, 0x03, 0x1820)
name = b"pico-6ln"
ble.gap_advertise(100000, adv_data=flags + uuid +
                  bytes((len(name) + 1, 0x09)) + name)
