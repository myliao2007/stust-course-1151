import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、PAN ID、OF…）
import network, socket, time, machine
import wsnproto as w
from rplnode import Node, kind
# root_a.py（A 板）：開自己組的 AP，當 DODAG 的 root（閘道器）
# 接線（任務四）：按鈕一腳接 GP14（第 19 腳）、另一腳接 GND（第 23 腳）：按一下做全域修復（版本加 1）
ap = network.WLAN(network.AP_IF)
ap.config(ssid=cfg.SSID, key=cfg.PASSWORD, channel=cfg.CHANNEL)
ap.active(True)
while not ap.active():
    time.sleep_ms(100)
print("AP 已開：", cfg.SSID, "｜A 的 IP：", ap.ifconfig()[0], "｜PAN 0x%04x" % cfg.PAN_ID,
      "｜目標函數", "MRHOF" if cfg.OCP else "OF0")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", cfg.PORT))       # 這個埠收 B 板送來的訊框（原本收不到，現在補上）
sock.settimeout(0)
btn = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
B, shown = None, []


def show(f, d, how):                   # 每一種只印第一次：十六進位（＋欄位樹）
    k = kind(d)
    if k in cfg.SHOW_A and k not in shown:
        shown.append(k)
        print("==== %s的第一則 %s（%d 位元組）：貼到電腦的 wsn_decode.py ====" % (how, k, len(f)))
        print(w.hexdump(f))
        if how == "收到":
            w.tree(d)


def tx(src, f):                        # root 要送出的訊框：經 Wi-Fi 交給 B 板的「無線電」
    if B is None:
        return                         # B 還沒連上，先不送
    if "DIO" not in shown:
        show(f, w.decode(f), "送出")
    sock.sendto(f, B)


root = Node(cfg.ROOT, tx, root=True)
t_btn, was = 0, 1
while True:
    try:
        f, addr = sock.recvfrom(256)   # B 板送來的訊框（N1、N2 送給 root 的）
        if B is None:
            B = addr
            print("B 板連上了：", addr)
        d = w.decode(f)
        show(f, d, "收到")
        root.rx(d)
    except OSError:
        pass
    if btn.value() == 0 and was == 1 and time.ticks_diff(time.ticks_ms(), t_btn) > 300:
        t_btn = time.ticks_ms()        # 全域修復：版本加 1，大家重新建樹
        root.ver = (root.ver + 1) & 0xFF
        root.routes = {}
        root.log("全域修復：DODAG 版本 → %d，下行路由清空" % root.ver)
        root.trickle.reset()
        root.dio()
    was = btn.value()
    root.tick()
    time.sleep_ms(5)
