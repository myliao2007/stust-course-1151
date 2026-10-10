# 深度學習框架應用（大學部）

每週上機用的 Colab 筆記本。點下面的連結會直接在 Colab 開啟，
開起來之後先按「複製到雲端硬碟」存一份自己的，再開始做。
請用私人 Google 帳號登入（學校帳號開不了 Colab）。

| 主題 | 筆記本 | 對應投影片 | Colab |
|---|---|---|---|
| 主題 3（上） | `w03-1_tensor.ipynb`：張量形狀、形狀操作、一層乘加、ReLU、折幾次 | 深度學習基礎回顧（上）練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w03-1_tensor.ipynb) |
| 主題 3（下） | `w02_autograd.ipynb`：損失、梯度三步、autograd 驗證、手刻訓練迴圈、兩條 loss | 深度學習基礎回顧（下）練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w02_autograd.ipynb) |
| 主題 3 延伸 | `w03-3_review.ipynb`：張量與 batch、神經元與 ReLU、損失函數、梯度下山、五步訓練迴圈 | 主題 3 延伸：整合複習　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w03-3_review.ipynb) |
| 主題 4 | `w04_mlp.ipynb`：載入 MNIST、定義 MLP、共用的 run_epoch、訓練保存與最終評估 | 全連接神經網路（MLP）　任務一～四 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w04_mlp.ipynb) |
| 主題 5 | `w05_cnn.ipynb`：輸出尺寸與參數量、手刻卷積核、三種池化、小卷積網路、Fashion-MNIST 訓練 | 卷積神經網路（CNN）原理　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w05_cnn.ipynb) |
| 主題 6 | `w06_transfer.ipynb`：殘差區塊、VGG 與瓶頸塊、資料增強、凍結骨幹、解凍微調 | 經典 CNN 架構與遷移學習　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w06_transfer.ipynb) |
| 主題 7 | `w07_training.ipynb`：初始化與梯度、BatchNorm、最佳化器賽跑、學習率排程、Dropout＋權重衰減＋早停 | 模型訓練技巧　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w07_training.ipynb) |
| 主題 8 | `w08_eval.ipynb`：混淆矩陣、PR 與 ROC 曲線、TensorBoard、多類別平均、錯題本 | 模型評估與視覺化　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w08_eval.ipynb) |
| 主題 10 | `w10_rnn.ipynb`：手算 RNN、三種循環層、基準線比較、長距離記憶、字元級語言模型 | 循環神經網路：RNN、LSTM 與 GRU　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w10_rnn.ipynb) |
| 主題 11 | `w11_transformer.ipynb`：點積注意力、兩種遮罩、多頭注意力、位置編碼、TransformerEncoder | 注意力機制與 Transformer　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w11_transformer.ipynb) |
| 主題 12 | `w12_pretrained.ipynb`：tokenizer、pipeline、句子向量、GPT 接龍、凍結 vs 全部微調 | 預訓練模型與遷移應用　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w12_pretrained.ipynb) |
| 主題 13 | `w13_generative.ipynb`：自編碼器、VAE、小 DCGAN、擴散加噪排程、小網路猜雜訊 | 生成式模型概論：GAN 與 Diffusion　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w13_generative.ipynb) |
| 主題 14 | `w14_compress.ipynb`：模型大小、動態量化、全域剪枝、知識蒸餾、效能基準 | 模型最佳化與壓縮　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w14_compress.ipynb) |
| 主題 15 | `w15_deploy.ipynb`：存讀權重、TorchScript、ONNX、FastAPI 服務、批次推論與延遲 | 模型部署：ONNX、TorchScript 與 API 服務化　練習一～五 | [開啟](https://colab.research.google.com/github/myliao2007/stust-course-1151/blob/main/dl-undergrad/notebooks/w15_deploy.ipynb) |

每本的練習一～五與投影片的練習頁一題對一題，每題 20%；主題 4 是任務一～四（合計 60%），另外 40% 在課堂練習。
標 ✏️ 的格子要自己寫，空格寫成 `___`，沒填就執行會出錯；主題 3 標「參考程式」的格子跟投影片一字不差。

**繳交**：交 `.ipynb` 檔＋分享連結，再加上投影片繳交頁列出的截圖或檔案。

1. 先「複製到雲端硬碟」（或「檔案 › 在雲端硬碟中儲存複本」）另存自己的複本，檔名改成 `深度學習_W05_學號_姓名.ipynb`（W 後面換成該主題的編號；主題 3 是 `W03上`、`W03下`、`W03延伸`）。
2. 做完「執行階段 › 重新啟動工作階段並執行所有儲存格」，確認每一格都有輸出。
3. 右上角「分享」→「一般存取權」改成「知道連結的任何人」、角色「檢視者」→「複製連結」；用無痕視窗打得開才算成功。
4. 「檔案 › 下載 › 下載 .ipynb」，上傳 Flipclass，並附上分享連結。

卡住可以問 AI，但答案要自己跑一次、數字要跟投影片對得上；用了哪個 AI、問了什麼，寫在筆記本最後的「AI 使用紀錄」。
