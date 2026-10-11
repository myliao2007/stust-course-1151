import myid                        # 身份指紋（第一行）
import cfg, sta_b, wsnproto as w
from machine import Pin
FCS = None                         # None＝自動判斷；任務四改 True
ok_led = Pin(cfg.LED_OK, Pin.OUT)  # GP15：這個訊框全部正確
act = Pin(cfg.LED_ACT, Pin.OUT)    # GP16：收到就換亮暗
ID = "指紋 學號 %s | 第 %d 組 | 板子 %s | 序號 %s | MAC %s" % (
    myid.STUDENT_ID, myid.GROUP, myid.BOARD, myid.SN, myid.MAC)
me = w.ip6str(w.link_local(myid.MAC))
print("B 的 MAC", myid.MAC, "→ link-local", me)
s, mac_a = sta_b.hello()
r = w.Reassembler(timeout_ms=5000)  # 示範 5 秒（規格最長 60）
n = 0
while True:
    try:
        f = s.recvfrom(256)[0]
    except OSError:                # 1 秒沒收到：丟掉逾時的
        if r.expire():
            print("重組逾時：等了 5 秒還缺片，整包丟掉")
        continue
    n += 1
    act.toggle()
    print("==== 第 %d 個訊框（%d 位元組）====" % (n, len(f)))
    print(ID)                      # 指紋＋十六進位一起複製
    print(w.hexdump(f))
    print()
    d = w.decode_any(f, cfg.CTX, r, FCS)
    w.tree(d)
    ok_led.value(w.ok(d))
