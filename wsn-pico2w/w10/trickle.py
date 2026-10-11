# trickle.py：Trickle 計時器（RFC 6206）。RPL 用它決定 DIO 什麼時候送
import time, random


class Trickle:
    def __init__(self, imin_exp, doublings, k):
        self.imin = 2 ** imin_exp              # Imin（毫秒）＝2^DIOIntervalMin
        self.imax = self.imin * 2 ** doublings # Imax＝Imin×2^DIOIntervalDoublings
        self.k = k                             # 冗餘常數：聽到 k 則一致的 DIO 就不送
        self.i = self.imin
        self._start(time.ticks_ms())

    def _start(self, now):                     # 新的一段：c 歸零，t 取 [I/2, I) 的亂數
        self.t0, self.c, self.fired = now, 0, False
        self.t = self.i // 2 + random.getrandbits(16) % (self.i // 2)

    def reset(self):                           # 不一致：I 縮回 Imin
        if self.i > self.imin:                 # 已經是 Imin 就不用動（RFC 6206）
            self.i = self.imin
            self._start(time.ticks_ms())

    def heard(self):                           # 聽到一則一致的 DIO：c 加 1
        self.c += 1

    def poll(self):                            # 到 t 時回傳 True（送）或 False（壓下）
        now = time.ticks_ms()
        el = time.ticks_diff(now, self.t0)
        out = None
        if not self.fired and el >= self.t:
            self.fired = True
            out = self.c < self.k              # 聽到的一致 DIO 不到 k 則才送
        if el >= self.i:                       # 這一段結束：I 加倍，最多到 Imax
            self.i = min(self.i * 2, self.imax)
            self._start(now)
        return out
