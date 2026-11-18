# 14 nRF24L01 收集端（收）：接線和送的那片一樣
from machine import Pin, SPI
from nrf24l01 import NRF24L01
import struct

spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
nrf = NRF24L01(spi, Pin(17), Pin(20),
               channel=76, payload_size=8)
nrf.open_rx_pipe(1, b"NODE1")     # 聽同一個地址
nrf.start_listening()

while True:
    if nrf.any():
        t, h, n = struct.unpack("<hhi", nrf.recv())
        print("第", n, "筆：", t, "°C", h, "%")
