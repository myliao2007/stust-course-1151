import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（A 的名稱…）
import asyncio, aioble, bluetooth, time
from ble_central import find_a, _ENV, _TEMP

async def count(ch, ms):           # ms 毫秒內收到幾則
    n, t0 = 0, time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < ms:
        try:
            await ch.notified(timeout_ms=500)
            n += 1
        except asyncio.TimeoutError:
            pass
    return n

async def main():
    dev = await find_a()
    if dev is None:
        print("沒掃到", cfg.A_NAME)
        return
    conn = await dev.connect(timeout_ms=5000)
    async for s in conn.services():   # 列出服務
        print(s)
    svc = await conn.service(_ENV)
    ch = await svc.characteristic(_TEMP)
    print(ch)
    cccd = await ch.descriptor(bluetooth.UUID(0x2902))
    now = await cccd.read()
    print(cccd, "目前值", now.hex(" "))
    for v in (b"\x01\x00", b"\x00\x00"):   # 開、再關
        await cccd.write(v, response=True)
        n = await count(ch, 10000)
        print("寫入", v.hex(" "), "→ 10 秒收到", n, "則")
    await conn.disconnect()

asyncio.run(main())
