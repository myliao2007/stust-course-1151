import myid                        # 身份指紋（第一行）
import cfg, picobee, random
import wsnproto as w
bee = picobee.PicoBee()            # A 板：協調器，B 是它的子節點
bee.start()
print("切到 API 模式：", picobee.api_on(bee))
B64 = w.unhex(input("輸入 B 的 SH SL："))
DARK = 1400                        # 光線值低於這個算暗（Faludi 書上 350／1023，換成 12 位元約 1400）
n = [0]

def ask(f, api, ms):               # 送一個 API 訊框，等某一種回應；回傳（毫秒, 解出來的 dict）
    t0 = picobee.now_ms()
    bee.write(f)
    g = picobee.frames(bee, ms, 1, lambda d: d.get("api") == api)
    return picobee.since(t0), (w.parse_xbee(g[0]) if g else None)

def led(on):                       # 遠端 AT：D4＝5 點亮、D4＝4 熄滅 B 的 LED（GP15）
    n[0] = n[0] % 200 + 1
    ms, d = ask(w.xb_remote_at(n[0], B64, "D4", bytes([5 if on else 4])), 0x97, 30000)
    print("  遠端 ATD4 %d：%s，%d 毫秒" % (5 if on else 4, "OK" if d and d["status"] == 0 else "失敗", ms))

def light(sec, react):             # 3-1 收 I/O 取樣（0x92）；react＝True：太暗就點亮 B 的 LED
    state, t_ref, t0 = None, 0, picobee.now_ms()
    while picobee.since(t0) < sec * 1000:
        for f in picobee.frames(bee, 1500, 1, lambda d: d.get("api") == 0x92):
            v = w.parse_xbee(f)["analog"][0][1]
            print("光線 AD0 =", v, "（暗）" if v < DARK else "（亮）")
            if react and (state != (v < DARK) or picobee.since(t_ref) > 10000):   # 變了，或每 10 秒刷新
                state, t_ref = v < DARK, picobee.now_ms()
                led(state)

def delay(sp):                     # 3-2 間接傳輸：隨機挑時間送 5 包給睡著的 B，量多久等到 0x8B
    ok = []
    for i in range(5):
        bee.wait(random.getrandbits(16) % (sp * 10))
        ms, d = ask(w.xb_tx(0x10 + i, B64, ("PING %d\r" % i).encode()), 0x8B, 40000)
        st = d["delivery"] if d else 0xFF
        print("  第 %d 包：遞送狀態 0x%02X，%d 毫秒" % (i + 1, st, ms))
        if st == 0:
            ok.append(ms)
    if ok:
        print("成功 %d 包，平均 %d 毫秒；SP/2 ＝ %d 毫秒" % (len(ok), sum(ok) // len(ok), sp * 5))

while True:
    k = input("1 看光線 10 秒｜2 浪漫燈光 30 秒｜3 間接傳輸延遲｜q 離開：")
    if k == "1":
        light(10, False)
    elif k == "2":
        light(30, True)
    elif k == "3":
        sp = int(input("B 的 SP（十六進位，例如 1F4）："), 16)
        a = input("A 的 SP（十六進位；直接按 Enter＝不改）：")
        if a:
            ask(w.xb_at(0x01, "SP", bytes([int(a, 16) >> 8, int(a, 16) & 0xFF])), 0x88, 1000)
        delay(sp)
    elif k == "q":
        break
