import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、埠號…）
import socket, ap_a
ap = ap_a.up()                     # 先開好自己組的 AP

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("0.0.0.0", 5005))   # 監聽所有介面的 5005 埠
s.settimeout(5)

got = set()                        # 收過的序號：算 B→A 單程遺失
while True:
    try:
        data, addr = s.recvfrom(128)
        print(addr, data.decode())
        s.sendto(b"ACK," + data, addr)   # 回 ACK，並帶回序號與時間
        got.add(int(data.split(b",")[0]))
    except OSError:
        print("5 秒內沒有收到任何封包")
        if got:
            print("這一輪收到", len(got), "包，最大序號", max(got))
            got = set()
    ap_a.led.value(1 if ap.status("stations") else 0)
