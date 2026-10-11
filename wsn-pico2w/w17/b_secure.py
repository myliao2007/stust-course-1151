import myid                      # 身份指紋（第一行；B 板）
import cfg                       # 本組參數、主題、金鑰
import time
import netlink, seal
# b_secure.py（任務二）：B 先驗 MAC、再比計數器，最後才解密
# 收下 5 包之後，把第 5 包原封不動重發一次（只發到自己組的主題），看它被擋下

N_OK = 5
last, got, seen = 0, [], [0]     # seen[0]：B 總共收到幾包（含被擋的）

def on_msg(topic, pkt):
    global last
    if topic == cfg.T_ST:
        print("A 狀態：", pkt.decode())
        return
    seen[0] += 1
    r, ctr, body = seal.unseal(cfg.ENC_KEY, cfg.MAC_KEY, pkt, last)
    if r == "ok":
        last = ctr
        got.append(pkt)
        c.publish(cfg.T_ACK, b"%d" % ctr)
        print("收下 #%d（%d B）" % (ctr, len(pkt)), body.decode())
    else:
        print("擋下：%s（封包的計數器 #%s，B 收過最大 #%d）" % (r, ctr, last))

def wait(n):                     # 一直收，直到總共收到 n 包
    tp = time.ticks_ms()
    while seen[0] < n:
        c.check_msg()
        if time.ticks_diff(time.ticks_ms(), tp) > 20000:
            c.ping()             # 保持連線（keepalive）
            tp = time.ticks_ms()
        time.sleep_ms(20)

c = netlink.mqtt_up(cfg.CID_B, None, on_msg, (cfg.T_SEC, cfg.T_ST))
print("B 訂閱", cfg.T_SEC.decode())
wait(N_OK)
p = got[-1]
print("重放：把 #%d 原封不動再發一次" % int.from_bytes(p[:4], "big"))
c.publish(cfg.T_SEC, p)          # 只發到自己組的主題，只發這一次
wait(N_OK + 3)                   # 重放那一包＋A 接著送的兩包
print("對照：只驗 MAC、不比計數器 →", seal.unseal(cfg.ENC_KEY, cfg.MAC_KEY, p, -1)[0])
c.disconnect()
