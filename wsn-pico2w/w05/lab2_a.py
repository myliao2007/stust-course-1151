import myid                        # 身份指紋（第一行）
import cfg, picobee
import wsnproto as w
bee = picobee.PicoBee()            # A 板：協調器（Lab 1 已用 ATWR 存好 CE＝1、PAN）
bee.start()

def send(f, ms=1500):              # 送進模組（DIN），印出模組回的 API 訊框（DOUT）
    print("→ 送進模組", w.hexs(f).upper())
    bee.write(f)
    got = picobee.frames(bee, ms)
    for g in got:
        print("← 模組送出", w.hexs(g).upper())
        w.tree(w.parse_xbee(g))
    if not got:
        print("← %d 毫秒內沒有回應：檢查碼不對，模組整個丟掉" % ms)
    return got

def my_checksum(data):             # 2-2 自己算：加總 → 只留最低 8 位元 → 用 0xFF 減
    s = 0
    for b in data:
        s = s + b
    return 0xFF - (s & 0xFF)

print("切到 API 模式：", picobee.api_on(bee))   # +++、ATAP 1、ATCN → 三個 OK
input("2-1 手算例 ATNJ，按 Enter 送出")
send(w.unhex("7E 00 04 08 52 4E 4A 0D"))
input("2-1 檢查碼故意改成 0C，按 Enter 送出")
send(w.unhex("7E 00 04 08 52 4E 4A 0C"))
input("2-2 自己組 ATMY 查詢（訊框編號 01），按 Enter 送出")
data = bytes([0x08, 0x01]) + b"MY"
print("my_checksum =", hex(my_checksum(data)), "｜wsnproto =", hex(w.xb_checksum(data)))
send(b"\x7e" + bytes([0, len(data)]) + data + bytes([my_checksum(data)]))
b64 = w.unhex(input("2-3 輸入 B 的 SH SL（B 打 ATSH、ATSL 查）："))
st = send(w.xb_tx(0x02, b64, b"T=25.3 from A\r"))         # 16 位元填 FFFE：模組要先找位址
b16 = w.parse_xbee(st[0])["dst16"]
send(w.xb_tx(0x03, b64, b"T=25.4 again\r", b16))          # 16 位元填剛學到的位址
input("2-4 換 B 打字送給 A（A 收到 0x90），按 Enter 進終端機")
bee.term()
