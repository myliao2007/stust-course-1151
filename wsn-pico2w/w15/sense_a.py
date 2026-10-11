import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（名稱、組號…）
# sense_a.py（A 板，任務二）：最小路徑第一段——讀感測器、打包成廣播封包、再拆回來對一次
import sensors, packet, time

sensors.init()                     # 印出 I2C 掃描結果：要看到 0x23、0x38（還有 0x77）
for seq in range(3):               # 讀 3 次，每次都打包
    d = sensors.read_all()
    p = packet.pack(cfg.MFG_ID, cfg.GROUP, seq, d, cfg.BLE_NAME)
    print("seq", seq, d)
    print("  廣播封包共 %d 位元組：" % len(p), p.hex(" "))
    print("  拆回來：", packet.unpack(p, cfg.MFG_ID, cfg.GROUP))
    time.sleep_ms(500)
