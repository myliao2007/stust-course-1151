import myid                      # 身份指紋（第一行；B 板＝邊界路由器）
import cfg
import time, gc, machine
import netlink, util, border, packet
# br_b.py（B 板）：收 A 的 6LoWPAN 訊框 → 驗 FCS、解壓縮、拆欄位 → JSON → MQTT（主題 12 的儀表板）
# 非阻塞主迴圈：每圈只花幾毫秒，收訊框、上行、狀態、閃燈各照自己的節奏
UPLINK = True                    # 任務二先改 False：只看 B 的 Shell，不上傳
led = machine.Pin("LED", machine.Pin.OUT)
btn = machine.Pin(cfg.BTN, machine.Pin.IN, machine.Pin.PULL_UP)   # 按一下：模擬上行斷網

print("B 的 IP", util.retry(netlink.wifi_up), "｜收 A 的訊框：UDP", cfg.PORT_B)
util.sync_time(cfg.NTP_HOST)
if cfg.WDT_ON:                   # 看門狗：8 秒沒餵就重開
    util.use_wdt(machine.WDT(timeout=cfg.WDT_MS))
br = border.Border()
util.log("開機，邊界路由器開始工作")
c, box, wait, a_on = None, [], 1, None
t0 = t_try = t_led = t_st = t_ping = time.ticks_ms()
while True:
    now = time.ticks_ms()
    # 工作一：收 A 的訊框（沒有就馬上回來），翻成 JSON 放進待送箱
    x = br.poll()
    if x:
        j = packet.to_json(x, x["n"], br.loss.rate(), util.ts()).encode()
        if UPLINK:
            box = (box + [j])[-cfg.BOX:]
        print("→", j.decode(), "｜待送", len(box))
        gc.collect()
    fresh = br.last is not None and time.ticks_diff(now, br.last) < cfg.STALE_S * 1000
    # 工作二：上行 MQTT；斷線就退避重試，但不卡住收訊框
    if UPLINK and c is None and time.ticks_diff(now, t_try) >= 0:
        try:
            c = netlink.mqtt_up(cfg.CID_B, cfg.ST_B, None, ())
            c.publish(cfg.ST_B, b"online", True)
            util.log("上行連上 broker，補送 %d 筆" % len(box))
            wait, a_on, t_ping = 1, None, now
        except Exception as e:
            c, t_try = None, time.ticks_add(now, wait * 1000)
            util.log("上行失敗 %s，%d 秒後再試" % (e, wait))
            wait = min(wait * 2, 60)
    if c:
        try:
            if br.last and fresh != a_on:   # A 的狀態變了才發（retain，晚來的也看得到）
                c.publish(cfg.ST_A, b"online" if fresh else b"offline", True)
                a_on = fresh
            while box:                   # 待送箱清空；送到一半斷線，沒送的還留著
                c.publish(cfg.DATA_A, box[0])
                box.pop(0)
            if time.ticks_diff(now, t_ping) > 30000:
                c.ping()                 # 沒資料時也讓 broker 知道 B 還在
                t_ping = now
            c.check_msg()                # 收 PINGRESP（沒有就馬上回來）
        except Exception as e:
            util.log("上行斷線：%s" % e)
            try:
                c.sock.close()           # 不送 DISCONNECT，broker 才會發遺囑
            except Exception:
                pass
            c, t_try = None, now
    # 工作三：按鈕模擬上行斷網（Wi-Fi 還在，A 的訊框照收）
    if btn.value() == 0 and c and not util.down():
        util.drop(cfg.DROP_S)
        util.log("按鈕：模擬上行斷網 %d 秒" % cfg.DROP_S)
        c.sock.close()
        c, t_try = None, now
    # 工作四：每 0.5 秒閃燈；每 60 秒印一行運作紀錄
    if time.ticks_diff(now, t_led) >= 500:
        t_led = now
        led.toggle()
    if time.ticks_diff(now, t_st) >= 60000:
        t_st = now
        print("[%s 運作 %d 秒] %s｜上行 %s、待送 %d｜mem_free %d" % (
            myid.STUDENT_ID, time.ticks_diff(now, t0) // 1000, br.line(),
            "ok" if c else ("斷" if UPLINK else "關"), len(box), gc.mem_free()))
    util.nap(10)                         # 休息 10 ms，順便餵狗
