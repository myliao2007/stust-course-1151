# ota.py：MicroPython 上的簡易 .py 更新（延伸挑戰，不計分）
# 修正原版 apply()：舊版用「複製」留成 .bak，新檔一次 rename 蓋過 main.py
# （rp2 的檔案系統是 littlefs，rename 是原子動作：斷電後不是舊版就是新版，main.py 不會不見）
import urequests, os, hashlib, binascii, machine

def fetch(url, tmp='new.tmp'):
    r = urequests.get(url)
    if r.status_code != 200:
        r.close()
        raise OSError('下載失敗 %d' % r.status_code)
    with open(tmp, 'wb') as f:
        f.write(r.content)      # 先寫暫存檔，不動舊檔
    r.close()
    return tmp

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(256)     # 分段讀，避免吃光記憶體
            if not b:
                break
            h.update(b)
    return binascii.hexlify(h.digest()).decode()

def copy(src, dst):             # 一段一段複製，src 一個字都不動
    with open(src, 'rb') as a:
        with open(dst, 'wb') as b:
            while True:
                x = a.read(256)
                if not x:
                    break
                b.write(x)

def apply(tmp, target, expect):
    if sha256_of(tmp) != expect:
        os.remove(tmp)
        raise ValueError('雜湊不符，放棄更新')
    copy(target, target + '.bak')     # ① 舊版複製一份留著回滾，target 本身不動
    os.rename(tmp, target)            # ② 新檔一次蓋過舊檔：沒有「找不到 main.py」的空窗
    machine.reset()

def rollback(target='main.py'):       # 新版有問題：把 .bak 一次蓋回去
    os.rename(target + '.bak', target)
    machine.reset()
