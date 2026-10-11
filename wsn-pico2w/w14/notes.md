# 主題 14 感測網路安全機制：上機程式（Pico 2 W ×2）

A 板＝感測節點（讀晶片溫度、加密、送出），B 板＝閘道（開 AP、先驗 MAC 再解密），B 也兼任「自己組的攻擊者」。

## 先做這三件事
1. 兩片板子都存一份 `myid.py`（全課共用），只改前三行：`STUDENT_ID`（組長學號）、`GROUP`（組號）、`BOARD`（這片是 A 還是 B）。
2. 兩片板子都存一份 `mysecret.py`，填老師上課給的**種子**、教室 Wi-Fi 密碼、HiveMQ Cloud 的叢集網址與帳密。
   **填好的 mysecret.py 不要上傳 GitHub、不要貼到群組**；外流了就請老師換一組。
3. `cfg.py`、`mac.py`、`seal.py`、`counter.py` 原封不動存到兩片板子。cfg.py 會用組號＋種子算出本組的 AP 名稱、密碼和兩把金鑰
   （`ENC_KEY` 加密用 16 B、`MAC_KEY` 算訊息驗證碼用 32 B），同組兩片算出來一模一樣。

每支程式第一行都是 `import myid`，截圖（整個螢幕）要看得到它印出的那一行（學號｜第幾組｜板子 A／B｜序號｜MAC 位址｜時間）和右下角的日期時間。
Thonny 第二次執行沒印出這一行時，先按 Stop 再執行。兩片板子各截各的。

## 誰跑哪支程式
| 任務 | A 板（感測節點） | B 板（閘道） | 配分 |
|---|---|---|---|
| 一 AES-CBC 加解密 | `aes_demo.py` 跑兩次；`node_a.py`：`MODE` 先 `"plain"` 再 `"aes"` | `gw_b.py`：`MODE` 跟 A 一樣 | 20% |
| 二之一 訊息驗證碼＋計數器 | `node_a.py`：`MODE = "seal"`；跑一陣子按 Stop 再執行一次 | `gw_b.py`：`MODE = "seal"` | 15% |
| 二之二 B 兼任攻擊者 | `node_a.py`（`"seal"`，繼續跑） | `attack_b.py`；填 `w14_attack.csv` | 20% |
| 三 MQTTS（TLS 8883） | `mqtts_a.py` | `mqtts_b.py` | 25% |
| 四 比較表＋150 字 | 填 `w14_record.csv` | 同左 | 20% |

- 任務一、二：B 先執行（它要先開 AP），A 再執行。A 會連上 B 開的 `wsn14-gNN`，用 UDP 5014 埠送給 B。
- 任務三：兩片都改連教室可以上網的 Wi-Fi（mysecret.py 裡的 `WIFI_SSID`），A 發布、B 訂閱 `stust/wsn14/gNN/sec`。

## 訊息驗證碼不用另外安裝
本主題用 `mac.py`（用內建 hashlib 寫的 HMAC-SHA256，十幾行）。另一條路是連上網路後 `import mip; mip.install("hmac")`，
再用 `hmac.new(KEY, msg, hashlib.sha256).digest()`，算出來一模一樣；兩條路選一條就好，本主題的程式都用 mac.py。
`cryptolib`（AES）是 MicroPython 內建的，不用裝；它只有 ECB、CBC 兩種模式，沒有 CCM、GCM。

## 攻擊實驗的規矩（一定要遵守）
- `attack_b.py` 只把改過的封包丟進**自己這片 B** 的收件口 `handle()`，不從空中送出去。
- `mqtts_b.py` 的重放測試只發到**自己組**的主題，而且只發一次。
- 不可以對別組、教室或校園的任何設備、網路做這些測試。

## 任務三要先準備
- `ca.der`（老師提供的根憑證）存到兩片板子。
- `umqtt.simple`：主題 11 裝過；沒有的話連上網路後 `mip.install("umqtt.simple")`。
- 連不上 8883：先 `print(time.localtime())` 看年份對不對（沒校時）、再看帳密和叢集網址。
- `mqtts_b.py` 的 keepalive 用預設的 0：B 只收不發，umqtt.simple 不會自己送 PINGREQ（主題 11），設成 60 會在 90 秒後被 broker 踢掉。

## 延伸挑戰 B：`ccm_pc.py` 在電腦端跑
板子做不到 CCM／GCM，改在電腦端 Thonny 跑：先「工具 → 管理套件」安裝 `cryptography`，再執行 `ccm_pc.py`。

## 記錄表
- `w14_attack.csv`：任務二之二，五種攻擊各一列（改了哪裡、閘道印出什麼、被哪一關擋下、為什麼）。
- `w14_record.csv`：任務四的比較表，用 Excel 開，量完當場填。

`test_w14.py` 是老師備課用的驗算程式（電腦端 Python），同學不用跑。
