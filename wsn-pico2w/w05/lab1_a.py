import myid                        # 身份指紋（第一行）
import cfg                         # 本組參數（SSID、PAN…）
import picobee                     # 老師給的 PicoBee：Pico 扮演 ZigBee 模組

bee = picobee.PicoBee()            # A 板：開 AP（wsn-gNN），模組開機
bee.start()                        # 模組在背景一直跑（每 20 毫秒一輪）
print("本組 PAN：ATID %X｜A 的 AP：%s（Wi-Fi 頻道 %d）" % (cfg.PAN, cfg.SSID, cfg.CHANNEL))
bee.term()                         # PicoBee 終端機：+++、AT 指令、聊天
