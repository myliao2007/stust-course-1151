from lora_init import modem   # 修正：先初始化，拿到 modem

blk, log = None, []           # 修正：照序號分點
while True:
    rx = modem.recv(timeout_ms=10000)
    if rx:
        print("收到：", rx.decode())
        print("RSSI =", rx.rssi, "dBm  SNR =", rx.snr, "dB")
        b = (int(rx.decode().split(",")[1]) - 1) // 10
        if b != blk:          # 換到下一點：重新統計
            blk, log = b, []
        log.append(rx.rssi)
        n = len(log)          # 修正：除以實際收到的包數
        print("第", blk + 1, "點：", n, "包，平均 RSSI =", sum(log) / n)
    else:
        print("10 秒內沒有收到封包")
