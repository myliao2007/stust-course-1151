import myid                        # 身份指紋（第一行）
import cfg, picobee
g = input("要加入哪一組的 AP？（開 AP 當協調器的那一片直接按 Enter）")
bee = picobee.PicoBee(join_group=int(g) if g else None)
bee.start()
print("先 +++，ATID 設成協調器那一組的 PAN，ATNI 取名字（例如 G07-B），ATCN；再 ATND、ATDN")
bee.term()
