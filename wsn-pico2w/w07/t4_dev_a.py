import myid                        # 身份指紋（第一行）
import cfg, ap_a, os, lwcrypto as lw
DEV_EUI = bytes.fromhex(myid.SN)   # A 板的序號當 DevEUI（64 位元）

s, b = ap_a.up()                   # 開 AP、等 B 報到
dn = lw.u(os.urandom(2))           # DevNonce：每次入網換一個隨機數
req = lw.join_request(cfg.APP_KEY, cfg.JOIN_EUI, DEV_EUI, dn)
print("Join Request（%d B）：%s" % (len(req), req.hex()))
s.sendto(b"JR" + req, b)
s.settimeout(6)
acc = s.recvfrom(64)[0][2:]        # 模擬：真的要在 RX1、RX2 收
ok, an, net, dev = lw.open_accept(cfg.APP_KEY, acc)
mic = "正確" if ok else "錯誤"
print("Join Accept（%d B）：%s｜MIC %s" % (len(acc), acc.hex(), mic))
nwk, app = lw.skeys(cfg.APP_KEY, an, net, dn)   # 金鑰自己算，不在空中傳
print("AppNonce %06X｜NetID %06X｜DevNonce %04X" % (an, net, dn))
print("DevAddr %08X" % dev)
print("NwkSKey", nwk.hex())
print("AppSKey", app.hex())
