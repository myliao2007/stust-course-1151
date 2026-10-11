import myid                        # 身份指紋（第一行）
import cfg, picobee
bee = picobee.PicoBee()            # B 板：GP26 接光敏電阻分壓、GP15 接 LED
bee.start()
print("3-1：+++ → ATD0 2、ATD4 4、ATIR 3E8 → ATCN（路由器，每秒送一次光線）")
print("3-2：+++ → ATSM 4、ATSP 1F4、ATST C8 → ATCN（變成會睡覺的終端裝置）")
bee.term(sniff=0)                  # 想看資料請求和 Frame Pending：打 .sniff 1
