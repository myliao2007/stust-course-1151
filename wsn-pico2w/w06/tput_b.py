import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數
import asyncio, aioble, bluetooth, struct, time
from aioble.core import register_irq_handler
from ble_central import find_a
N = 200
U = bluetooth.UUID
got = []                # 每一筆的 (序號, 收到的時間)

def tap(event, data):   # 掛在 aioble 的事件上，一筆不漏
    if event in (18, 19):           # 18 通知、19 指示
        seq = struct.unpack_from("<H", data[2])[0]
        got.append((seq, time.ticks_ms()))
register_irq_handler(tap, None)

def stats(got, n):      # 收到幾筆、掉幾筆、幾 ms、每秒幾筆
    k = len(set(s for s, _ in got))
    if len(got) < 2:
        return k, n - k, 0, 0
    ms = time.ticks_diff(got[-1][1], got[0][1])
    return k, n - k, ms, (len(got) - 1) * 1000 / ms

async def main():
    dev = await find_a()
    if dev is None:
        print("沒掃到", cfg.A_NAME)
        return
    conn = await dev.connect(timeout_ms=5000)
    svc = await conn.service(U(cfg.SVC_UUID))
    ch = await svc.characteristic(U(cfg.DATA_UUID))
    cmd = await svc.characteristic(U(cfg.CMD_UUID))
    for mode in (b"N", b"I"):       # 先通知、再指示
        await ch.subscribe(mode == b"N", mode == b"I")
        got.clear()
        await cmd.write(mode, response=True)
        last = -1
        while len(got) != last:     # 3 秒沒新資料就停
            last = len(got)
            await asyncio.sleep_ms(3000)
        k, x, ms, rate = stats(got, N)
        name = "通知" if mode == b"N" else "指示"
        print(name, "收到", k, "筆，掉", x, "筆")
        print("  %d ms，每秒 %.1f 筆" % (ms, rate))
    await conn.disconnect()

asyncio.run(main())
