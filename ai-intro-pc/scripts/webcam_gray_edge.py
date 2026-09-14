"""W08 任務四：用電腦攝影機做灰階／邊緣／縮放（本機 Python，不是 Colab）

這三件事，正是模型「看到」一張圖之前會先做的前處理。

怎麼裝
------
在命令提示字元（或 Anaconda Prompt）輸入：

    python -m pip install opencv-python

用 `python -m pip` 而不是 `pip`，可以避免裝到別的 Python 環境
（教室電腦常常同時有好幾個 Python，這是最常見的「裝了卻 import 失敗」原因）。

怎麼跑
------
把這個檔案下載到電腦，切到它所在的資料夾，然後：

    python webcam_gray_edge.py

視窗出現後，按 Esc 或 q 離開。跑之前請先關掉 Teams／Meet／相機 App，
攝影機同一時間只能被一支程式佔用。

跑不動時的 Colab 備援
--------------------
教室電腦裝不了套件、或攝影機權限被鎖住時，改用
`ai-intro-pc/notebooks/w08_cv_opencv.ipynb` 裡的「任務四備援」那一格：
改成讀示範影片、用 cv2_imshow 顯示，做的是同樣三件事，觀念完全一樣。

填空
----
下面兩行標了「← 自己寫」的地方要你自己補，補完才跑得動。
參考解在 w08_cv_opencv.ipynb 最後的「參考解」摺疊區塊。
"""

import cv2

cap = cv2.VideoCapture(0)        # 0 是內建攝影機
while True:
    ok, frame = cap.read()
    if not ok:
        break
    gray = ____                  # ← 自己寫：轉成灰階
    edge = cv2.Canny(gray, 100, 200)
    small = cv2.resize(frame, ____)  # ← 自己寫：縮成 224
    cv2.imshow("gray", gray)
    cv2.imshow("edge", edge)
    key = cv2.waitKey(1) & 0xFF  # ←投影片未含，執行所需：讓 Esc 與 q 都能離開
    if key == 27 or key == ord("q"):   # 按 Esc 或 q 離開
        break
cap.release()
cv2.destroyAllWindows()
