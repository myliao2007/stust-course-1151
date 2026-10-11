import myid                        # 身份指紋（第一行）
import cfg, picobee
bee = picobee.PicoBee()            # B 板：維持 AT（透明）模式，PAN 已在 Lab 1 存好
bee.start()
print("B 收到的空中訊框會印十六進位和欄位樹；把十六進位那一行貼到電腦的 wsn_decode.py 對照")
bee.term(sniff=2)                  # sniff=2：每個空中訊框印摘要＋十六進位，收到的資料再印整棵欄位樹
