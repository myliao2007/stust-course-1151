# -*- coding: utf-8 -*-
"""
W16 批次整理資料（本機 Python 版）　人工智慧導論 電腦教室版　南臺科技大學 電子工程系

這支程式做四件事：批次改檔名 → 統一尺寸 → 找出壞檔 → 產生 data_list.csv。

────────────────────────────────────────────────────────────
一、怎麼裝
    1. 開始功能表 → 搜尋「Anaconda Prompt」→ 開起來（不要用一般的命令提示字元）。
    2. 在裡面打：  pip install pillow
    3. 出現 Successfully installed 就好了。
       如果說權限不足、裝不進去，不要卡在這裡，直接看下面第四點的 Colab 備援。

二、怎麼跑
    1. 把這個檔案存到你自己的資料夾，例如 D:\\ai_project\\batch_prepare.py
    2. 在 Anaconda Prompt 裡打：  python D:\\ai_project\\batch_prepare.py
    3. 跑完會在 raw 資料夾裡多出一個 data_list.csv。

三、要改哪一行
    只有一行：下面的  ROOT = r"D:\\ai_project\\raw"
    換成你們自己放資料的那個資料夾。前面那個 r 不要刪掉，
    它是告訴 Python「這串字裡的反斜線是路徑，不是特殊符號」。

    資料夾要長這樣（一個類別一個子資料夾，名字一律用英文與底線）：
        raw/
          paper/    IMG_0012.jpg ...
          bottle/   ...
          can/      ...

    另外，程式裡有三個 ____ 是要你自己補的（投影片上有講）：
        第 1 段兩處：新檔名、新檔的完整路徑
        第 2 段一處：把圖縮成同一個尺寸
    沒補就跑會看到 NameError: name '____' is not defined，那是正常的。
    補完跑對了會看到：每一類印一行「改名完成」、印出壞檔幾個、印出共幾筆。
    參考解在 notebooks/w16_batch_data.ipynb 最後一格（自己先試過再看）。

四、跑不動的時候：走 Colab 備援
    教室電腦多半沒有安裝權限，pip 裝不起來不是你的錯，也不影響分數。
    判斷原則：五分鐘內裝不起來就換 Colab。
    打開 notebooks/w16_batch_data.ipynb，程式完全一樣，
    只差 ROOT 那一行要換成雲端硬碟的路徑：
        ROOT = "/content/drive/MyDrive/AI115/raw"
    iPhone 拍的 HEIC 檔 Pillow 打不開會被當成壞檔，
    請先在相機設定改成「相容性最佳」，或上傳前轉成 JPG。

⚠️  跑之前一定要先複製一份原始資料！
    os.rename() 與 im.save() 都是直接覆蓋原檔，改壞了救不回來。

⚠️  整理完立刻把資料複製回雲端硬碟共用資料夾，教室電腦重開機會還原。
────────────────────────────────────────────────────────────
"""

# ========== 第 1 段：批次改檔名 ==========
import os, glob
ROOT = r"D:\ai_project\raw"        # 走 Colab 就換成雲端路徑
for cls in os.listdir(ROOT):
    d = os.path.join(ROOT, cls)
    files = sorted(glob.glob(os.path.join(d, "*")))
    for i, old in enumerate(files, 1):
        ext = os.path.splitext(old)[1].lower()
        new = ____          # ← 自己寫：cls_0001.jpg 這種名字
        os.rename(old, ____)   # ← 自己寫：新檔的完整路徑
    print(cls, len(files), "個檔案改名完成")

# ========== 第 2 段：統一尺寸並找出壞檔 ==========
from PIL import Image
SIZE = (224, 224)
bad = []
for f in glob.glob(os.path.join(ROOT, "*", "*")):
    try:
        im = Image.open(f).convert("RGB")
        im = ____              # ← 自己寫：縮成 SIZE 大小
        im.save(f, quality=90)
    except Exception:
        bad.append(f)
print("壞檔", len(bad), "個")
for f in bad:
    print("  ", f)

# ========== 第 3 段：產生 data_list.csv ==========
import csv
rows = []
for cls in sorted(os.listdir(ROOT)):
    for f in sorted(glob.glob(os.path.join(ROOT, cls, "*"))):
        rows.append([os.path.basename(f), cls,
                     os.path.getsize(f) // 1024])
out = os.path.join(ROOT, "data_list.csv")
with open(out, "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["檔名", "類別", "KB"])
    w.writerows(rows)
print("共", len(rows), "筆，已寫出 data_list.csv")

# ========== 第 4 段（進階）：用雜湊找出重複 ==========
import hashlib
seen, dup = {}, []
for f in glob.glob(os.path.join(ROOT, "*", "*")):
    h = hashlib.md5(open(f, "rb").read()).hexdigest()
    if h in seen:
        dup.append((f, seen[h]))
    else:
        seen[h] = f
print("重複的檔案", len(dup), "組")
for a, b in dup[:10]:
    print(os.path.basename(a), "==", os.path.basename(b))
