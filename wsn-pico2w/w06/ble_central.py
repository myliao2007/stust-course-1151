import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（A 的名稱…）
import asyncio, aioble, bluetooth, struct
_ENV = bluetooth.UUID(0x181A)
_TEMP = bluetooth.UUID(0x2A6E)

async def find_a():                # 掃 5 秒找自己組的 A
    dev = None
    async with aioble.scan(5000, 30000, 30000,
                           active=True) as scanner:
        async for r in scanner:
            if r.name() == cfg.A_NAME:
                dev = r.device
                break
    return dev

async def main():
    dev = await find_a()
    if dev is None:                # 掃不到：先確認 A 在廣播
        print("沒掃到", cfg.A_NAME)
        return
    conn = await dev.connect(timeout_ms=5000)
    svc = await conn.service(_ENV)
    ch = await svc.characteristic(_TEMP)
    for i in range(5):             # 一問一答讀 5 次
        raw = await ch.read()
        print("溫度 =", struct.unpack("<h", raw)[0] / 100)
        await asyncio.sleep_ms(2000)
    await conn.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
