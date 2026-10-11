import myid                        # 身份指紋（第一行）
import cfg, sta_b, os, lwcrypto as lw
NET_ID = 0x000000                  # NetID 0：實驗用網路
used = set()                       # 用過的 DevNonce（擋重播）

s, a = sta_b.hello()               # 連上 A、報到
while True:
    r = s.recvfrom(64)[0][2:]      # MHDR 1＋JoinEUI 8＋DevEUI 8＋DevNonce 2＋MIC 4
    ok = lw.cmac(cfg.APP_KEY, r[:19])[:4] == r[19:23]
    dn, eui = lw.u(r[17:19]), lw.rev(r[9:17]).hex()
    mic = "正確" if ok else "錯誤"
    print("Join Request：DevEUI %s｜DevNonce %04X｜MIC %s" % (eui, dn, mic))
    if not ok or dn in used:
        print("拒絕入網（MIC 錯，或 DevNonce 用過了）")
        continue
    used.add(dn)
    an = lw.u(os.urandom(3))       # AppNonce（JoinNonce）：伺服器出的隨機數
    s.sendto(b"JA" + lw.join_accept(cfg.APP_KEY, an, NET_ID, cfg.DEV_ADDR), a)
    nwk, app = lw.skeys(cfg.APP_KEY, an, NET_ID, dn)
    print("AppNonce %06X｜NetID %06X｜DevNonce %04X" % (an, NET_ID, dn))
    print("DevAddr %08X" % cfg.DEV_ADDR)
    print("NwkSKey", nwk.hex())
    print("AppSKey", app.hex())
