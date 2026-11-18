# 13 nRF24L01 感測節點（送）：SCK GP18、MOSI GP19、MISO GP16、CSN GP17、CE GP20
# 第一次用：連上 Wi-Fi 後 import mip; mip.install("nrf24l01")
from machine import Pin, SPI
from nrf24l01 import NRF24L01
import struct, time

spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
nrf = NRF24L01(spi, Pin(17), Pin(20),
               channel=76, payload_size=8)
nrf.open_tx_pipe(b"NODE1")        # 地址固定 5 個位元組

n = 0
while True:
    n += 1
    data = struct.pack("<hhi", 25, 60, n)   # 溫度、濕度、序號
    try:
        nrf.send(data)
        print("送出第", n, "筆")
    except OSError:
        print("第", n, "筆沒收到回應")
    time.sleep(2)
