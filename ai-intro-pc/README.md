# 人工智慧導論（電腦教室版）115-1 上機教材

**四技電子一乙（課號 30D1G803）｜電腦教室，每人一台電腦**

同名課程另有一班用手機上課（四技電子一甲等合開／國專一甲，課號 30D1G801），
教材在 [`../ai-intro/`](../ai-intro/)。**兩班理論完全相同、共用考卷，差別只在上機。**
拿錯版本的話：這一版每週要你自己敲程式，手機版只要改參數。

## 學生怎麼用

1. 掃投影幕上的 QR 碼（或點下表連結）→ Colab 開啟 → **按「複製到雲端硬碟」**再開始寫，否則改的東西不會留下。
2. 筆記本是**填空式**：看到 `____` 或 `# ← 這一行你自己寫` 就是你要動手的地方。
   卡住了先看該格上方的 markdown 說明，真的過不去再展開每本最後的「參考解」。
3. 寫完存檔（自動存在你的雲端硬碟），照該週投影片指示交作業。

## 18 週上機總表

| 週 | 上機主題 | 開啟 | 你要自己寫的程式 |
|---|---|---|---|
| W01 | Colab 環境與第一支程式 | [w01_first_run](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w01_first_run.ipynb) | 印出上課證的 5 行；垃圾信規則 if/else |
| W02 | Python 基礎 | [w02_python_basics](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w02_python_basics.ipynb) | for 乘法表、if/elif 分級、bmi() 函式、while 猜數字 |
| W03 | 班級資料與 pandas | [w03_class_data](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w03_class_data.ipynb) | describe／篩選／groupby、缺失值三法、clean() |
| W04 | 資料視覺化 | [w04_charts](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w04_charts.ipynb) | 長條／直方／散布圖、2×2 子圖、存 PNG |
| W05 | Teachable Machine 批次推論 | [w05_teachable_batch](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w05_teachable_batch.ipynb) | 批次推論函式、正確率、手寫混淆矩陣 |
| W06 | 迴歸與分類 | [w06_regression_knn](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w06_regression_knn.ipynb) | 掃描 k=1..15、畫兩條曲線、決策樹深度、交叉驗證 |
| W07 | 類神經網路 | [w07_neural_net](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w07_neural_net.ipynb) | numpy 手算神經元、MLPClassifier、學習曲線 |
| W08 | 電腦視覺與 OpenCV | [w08_cv_opencv](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w08_cv_opencv.ipynb) | 混淆矩陣與召回率、灰階／邊緣／縮放 |
| W09 | 期中考（紙筆，電腦教室） | — | — |
| W10 | 中文情緒分析 | [w10_sentiment](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w10_sentiment.ipynb) | jieba 斷詞、停用詞、TF-IDF＋LR、錯誤分析 |
| W11 | Prompt 四種寫法比較 | [w11_prompt_compare](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w11_prompt_compare.ipynb) | 評分 DataFrame、平均分、長條圖 |
| W12 | AI 繪圖五次迭代 | [w12_image_iteration](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w12_image_iteration.ipynb) | 迭代紀錄 diff()、2×3 拼圖、提示詞變體迴圈 |
| W13 | 語音辨識與錯字率 | [w13_whisper_cer](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w13_whisper_cer.ipynb) | cer() 錯字率、show_diff() 差異對照 |
| W14 | 感測器活動辨識 | [w14_motion_window](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w14_motion_window.ipynb) | windows() 切窗、mean/std 特徵、KNN |
| W15 | 隱私與偏誤檢查 | [w15_privacy_bias](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w15_privacy_bias.ipynb) | sha256 去識別化、資料平衡、check_bias() |
| W16 | 模型評估與常見陷阱 | [w16_evaluation](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w16_evaluation.ipynb) | my_confusion() 四格、precision／recall／F1、門檻掃描與 PR 曲線、修好一次資料洩漏 |
| W17 | 邊緣 AI：Keras 轉 TFLite 與量化 | [w17_tflite](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/ai-intro-pc/notebooks/w17_tflite.ipynb) | representative_dataset、自己寫 bench() 量中位數延遲、decide() 判斷函式 |
| W18 | 期末考（紙筆，範圍 W10–W17）| 無需筆記本 | — |

## 本機 Python 腳本（scripts/）

只有 W08 需要離開瀏覽器；教室電腦裝不起來就走筆記本裡的 Colab 備援，**不會少學到東西**。

| 檔案 | 週次 | 用途 | 怎麼跑 |
|---|---|---|---|
| `scripts/webcam_gray_edge.py` | W08 | 讀電腦攝影機做灰階／邊緣／縮放 | `pip install opencv-python` → `python webcam_gray_edge.py`（Esc 或 q 離開） |

## 資料

班級示範資料沿用手機版那一份（不重複放）：
`https://raw.githubusercontent.com/myliao2007/stust-course-1151/main/ai-intro-pc/data/demo_class.csv`。
筆記本裡的 `SHEET_ID` 留空白就會自動改讀它，所以還沒收到全班資料也能先跑。

## 老師課前要準備的

Google 表單（每週繳交）、班級資料試算表 ID（W03/W04/W06）、W05/W08 的 Teachable Machine 示範專案。
W16 要投影門檻紀錄表（當堂收）；W17 第 1 格全班同時下載 fashion_mnist 會吃一波網路，
請先示範一次再讓全班一起跑，模型訓練完之後就完全不吃網路。表單無法程式化建立，連結由老師上課公布。

## W16 與 W17 這兩週要注意的

- **W16**：`sklearn` 只拿來造資料與訓練，四個指標一律自己算。第 2、3 格寫出來的
  `my_confusion()` 與 `metrics()`，第 4、5、6 格會一直重複用到，**一定要當堂寫對**。
  第 1 格沒跑成功，後面每一格都會報 `NameError`。`&` 的優先序比 `==` 高，
  不加括號會直接丟 `ValueError`——讓他們先踩一次再講。門檻掃到 0.9 時可能出現
  `ZeroDivisionError`，這是要寫進紀錄表的觀察，不是錯誤。PR 曲線存成 `pr_curve.png`
  之後在左邊檔案列表按右鍵下載，這是電腦教室才做得到的一步。
- **W17**：`representative_dataset` 最常見的錯是寫成 `rep_data()`——轉檔器要的是**函式本身**。
  三個檔案大小約 2.7 MB／920 KB／244 KB，實測約剩 1/3.8，對得上「參數量 235146 × 4 ÷ 1024 ≈ 919 KB」。
  `bench()` 的計時**只能包住 `set_tensor` → `invoke` → `get_tensor` 三行**，
  把建直譯器也包進去量到的會是載入時間。**要誠實講**：模型太小、x86 浮點又太強，
  int8 在教室電腦上常常沒有變快甚至略慢——量測要在目標裝置上做，
  不能拿開發機的數字當結論，這本身就是很好的教材。

## archive/

`archive/` 放的是 115-1 原本的期末專題教材（`w16_batch_data.ipynb`、`w17_gradio_demo.ipynb`、
`batch_prepare.py`），課程改為期末考後停用，保留供日後參考，不再出現在 18 週總表裡。
