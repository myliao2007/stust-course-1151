from machine import Pin, SPI
from lora import SX1262

spi = SPI(1, baudrate=2000000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))

modem = SX1262(
    spi=spi,
    cs=Pin(13, Pin.OUT, value=1),
    busy=Pin(15, Pin.IN),
    dio1=Pin(20, Pin.IN),
    reset=Pin(14, Pin.OUT, value=1),
    lora_cfg={"freq_khz": 923000, "sf": 7, "bw": "125",
              "coding_rate": 5, "output_power": 14})
print("模組初始化完成")
