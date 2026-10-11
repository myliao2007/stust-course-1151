import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（BLE 名稱…）
import asyncio, aioble, bluetooth, struct

_ENV = bluetooth.UUID(0x181A)    # 環境感測服務
_TEMP = bluetooth.UUID(0x2A6E)   # 溫度特徵，sint16
_HUMI = bluetooth.UUID(0x2A6F)   # 濕度特徵，uint16

service = aioble.Service(_ENV)
temp_char = aioble.Characteristic(
    service, _TEMP, read=True, notify=True)
humi_char = aioble.Characteristic(
    service, _HUMI, read=True, notify=True)
aioble.register_services(service)
aioble.config(gap_name=cfg.BLE_NAME)   # 連上後的裝置名稱

async def advertise_task():
    while True:
        async with await aioble.advertise(
                250000, name=cfg.BLE_NAME,
                services=[_ENV]) as conn:
            print("已連線：", conn.device)
            led.on()
            await conn.disconnected()
            led.off()
            print("已斷線，重新廣播")

from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
i2c.writeto(0x38, b"\xbe\x08\x00")
time.sleep_ms(10)
led = Pin(15, Pin.OUT)             # GP15：連線時點亮

def read_aht20():
    i2c.writeto(0x38, b"\xac\x33\x00")
    time.sleep_ms(80)
    d = i2c.readfrom(0x38, 7)
    raw = ((d[3] & 0x0F) << 16) | (d[4] << 8) | d[5]
    t = raw / 1048576 * 200 - 50
    raw_h = (d[1] << 12) | (d[2] << 4) | (d[3] >> 4)
    return t, raw_h / 1048576 * 100

async def sensor_task():
    while True:
        t, h = read_aht20()
        v = struct.pack("<h", round(t * 100))
        temp_char.write(v, send_update=True)
        w = struct.pack("<H", round(h * 100))
        humi_char.write(w, send_update=True)
        print("溫度 %.2f 度、濕度 %.2f %%" % (t, h))
        await asyncio.sleep_ms(2000)   # 讓出時間

async def main():                  # 兩個工作一起跑
    await asyncio.gather(advertise_task(), sensor_task())

asyncio.run(main())
