# seqstat.py：用 seq 算遺失、重複、晚到（B 板的 b_stats.py 匯入；電腦上的 Python 也能跑）
class SeqStat:
    def __init__(self):
        self.seen = set()          # 看過的 seq
        self.first = None          # 第一筆的 seq
        self.top = 0               # 目前看過最大的 seq
        self.dup = 0               # 重複幾筆
        self.late = 0              # 晚到幾筆（比 top 小、但沒看過）

    def add(self, seq):
        """記一筆，回傳判定：第一筆、新、跳號 n、重複、晚到。"""
        if self.first is None or (seq == 1 and self.top > 1):
            self.__init__()        # 第一筆，或 A 重新開始（seq 回到 1）
            self.first = self.top = seq
            self.seen.add(seq)
            return "第一筆"
        if seq in self.seen:
            self.dup += 1
            return "重複"
        self.seen.add(seq)
        if seq < self.top:
            self.late += 1
            return "晚到"
        gap = seq - self.top - 1
        self.top = seq
        return "跳號 %d" % gap if gap else "新"

    def got(self):
        return len(self.seen)

    def lost(self):                # 應該收到的（first～top）減掉真的收到的
        return self.top - self.first + 1 - len(self.seen)

    def line(self):
        if self.first is None:
            return "還沒收到資料"
        return "收到 %d 筆（seq %d～%d），遺失 %d，重複 %d，晚到 %d" % (
            self.got(), self.first, self.top, self.lost(), self.dup, self.late)
