import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數
import asyncio, aioble, bluetooth, struct, time
N = 200                 # 每一輪送幾筆
U = bluetooth.UUID
svc = aioble.Service(U(cfg.SVC_UUID))
data = aioble.Characteristic(svc, U(cfg.DATA_UUID),
                             notify=True, indicate=True)
cmd = aioble.Characteristic(svc, U(cfg.CMD_UUID),
                            write=True)
aioble.register_services(svc)
async def burst(conn, mode):        # b"N" 通知、b"I" 指示
    t0 = time.ticks_ms()
    for seq in range(N):            # 每筆 20 位元組
        now = time.ticks_ms()
        pkt = struct.pack("<HI", seq, now) + bytes(14)
        if mode == b"N":
            data.notify(conn, pkt)          # 送出就算
            await asyncio.sleep_ms(0)
        else:
            await data.indicate(conn, pkt)  # 等確認
    ms = time.ticks_diff(time.ticks_ms(), t0)
    print(mode, "送完", N, "筆", ms, "ms")

async def main():
    while True:
        conn = await aioble.advertise(
            100000, name=cfg.BLE_NAME)
        print("已連線：", conn.device)
        while conn.is_connected():
            try:            # 等 B 寫指令；逾時或斷線就略過
                await cmd.written(timeout_ms=1000)
                await burst(conn, cmd.read())
            except Exception:
                pass
        print("已斷線，重新廣播")

asyncio.run(main())
