import myid                        # 身份指紋（第一行）
import cfg, picobee
bee = picobee.PicoBee()            # B 板：連上 A 的 AP，模組開機
bee.start()
PAN = "%X" % cfg.PAN               # 本組的 PAN ID（第 7 組是 "1007"）
def at(cmd, wait=300):
    bee.write((cmd + "\r").encode())
    bee.wait(wait)
    r = bee.read()
    print(cmd, "->", r)
    return r
bee.wait(1100)                     # 進入命令模式前要先靜默 1 秒
bee.write(b"+++")
bee.wait(1200)                     # 之後再靜默 1 秒，模組才回 OK
print("命令模式：", bee.read())
at("ATID " + PAN)                  # 設成你這組的 PAN ID
at("ATWR")                         # 寫進快閃記憶體（斷電不消失）
at("ATCN")                         # 離開命令模式：套用設定、重新入網
bee.term()                         # 進終端機：查 ATAI、ATMY，和 A 聊天
