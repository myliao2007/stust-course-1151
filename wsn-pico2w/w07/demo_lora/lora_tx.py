import time
from lora_init import modem   # 修正：先初始化，拿到 modem

seq = 0
while True:
    seq += 1
    msg = "N1,{},hello".format(seq).encode()
    t0 = time.ticks_ms()
    modem.send(msg)
    dt = time.ticks_diff(time.ticks_ms(), t0)
    print("送出", seq, "空中時間約", dt, "ms")
    time.sleep(dt * 99 / 1000)   # 修正：安靜 99 倍，守 1%
