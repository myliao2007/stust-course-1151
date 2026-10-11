# wsn_decode.py：電腦端的封包解碼器（主題 5 PicoBee、主題 8 6LoWPAN、主題 10 RPL）
#
# 用法 1（最常用）：在 Thonny 打開這個檔案按「執行」，把 Pico 印出來的十六進位貼到下方 Shell，
#                   最後再按一次 Enter（送出一行空白），就會一層一層解開，印出欄位樹和檢查結果。
# 用法 2：python wsn_decode.py 封包.txt            一次解一整個文字檔（Pico 存下來的紀錄）
# 用法 3：python wsn_decode.py 41 88 02 cd ab ...   直接把位元組寫在後面
#
# 可以貼的格式：41 88 02、418802、41:88:02、0x41,0x88、\x41\x88、b'A\x88\x02'（MicroPython 印 bytes 的樣子），
#              或是開頭有位移的傾印格式（0000  41 88 …／0010  …）。空白行或位移從 0000 重新開始，就是下一個封包。
# 會自動判斷：XBee API 訊框（0x7E 開頭）、802.15.4 訊框有沒有附 FCS，然後解到 6LoWPAN／IPv6／UDP／ICMPv6／RPL。
#
# 只用 Python 標準函式庫，不用另外安裝。解碼用的是和 Pico 同一份 wsnproto.py／wsntree.py：
# 放在同一個資料夾就用那一份；找不到就用這個檔案最後面內建的同一版本，兩者解出來一模一樣。

import ast
import os
import sys

HELP = '''指令（直接打在 Shell 裡）：
  help            顯示這段說明
  fcs auto        自動判斷有沒有附 FCS（預設）
  fcs on／fcs off 強制當成「有附 FCS」／「沒附 FCS」
  ctx 0 2001:db8:1::/64   設定 6LoWPAN context 0 的前綴（SAC／DAC＝1 時要用）
  ctx             列出目前的 context；ctx clear 清掉
  reset           清掉分片重組的緩衝（重新開始收 FRAG1／FRAGN）
  demo            解幾個範例封包給你看
  q               離開'''


def _load_lib():
    # 載入 wsnproto／wsntree：同資料夾有就用那一份，沒有就用檔案最後面內建的備用版本
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import wsnproto
        import wsntree
        return wsnproto, wsntree, '同資料夾的 wsnproto.py'
    except ImportError:
        pass
    import base64
    import json
    import types
    import zlib
    srcs = json.loads(zlib.decompress(base64.b64decode(''.join(_EMBED.split()))).decode('utf-8'))
    for name in ('wsnproto', 'wsntree'):
        m = types.ModuleType(name)
        m.__file__ = '<內建 {}.py>'.format(name)
        sys.modules[name] = m
        exec(compile(srcs[name], m.__file__, 'exec'), m.__dict__)
    return sys.modules['wsnproto'], sys.modules['wsntree'], '內建的備用版本'


def _is_hex(tok):
    # 這個字是不是一串偶數位的十六進位（可以有 0x 前綴、冒號）
    t = tok.replace(':', '').replace('-', '')
    if t[:2] in ('0x', '0X'):
        t = t[2:]
    if not t or len(t) % 2:
        return False
    for c in t:
        if c not in '0123456789abcdefABCDEF':
            return False
    return True


def packets_from_text(text, unhex):
    # 把貼上的文字變成封包清單：空白行、或位移從 0000 重新開始，就是下一個封包；回傳（封包清單, 看不懂的行）
    pkts = []
    bad = []
    cur = []

    def flush():
        # 目前累積的位元組收成一個封包
        if cur:
            pkts.append(b''.join(cur))
            del cur[:]

    for raw in text.splitlines():
        line = raw.split('#')[0].strip()
        if not line:
            flush()
            continue
        if line.startswith(("b'", 'b"', 'bytearray(b')):
            lit = line[len('bytearray('):-1] if line.startswith('bytearray(') else line
            try:
                flush()
                pkts.append(bytes(ast.literal_eval(lit)))
            except (ValueError, SyntaxError):
                bad.append(raw)
            continue
        toks = line.replace('\\x', ' ').replace(',', ' ').replace(';', ' ').split()
        while toks and not _is_hex(toks[0]):           # 去掉開頭的標籤，例如「RX:」「收到」
            toks.pop(0)
        if not toks:
            bad.append(raw)
            continue
        have = sum(len(c) for c in cur)
        t0 = toks[0]
        if (len(toks) >= 2 and 4 <= len(t0) <= 8 and ':' not in t0 and _is_hex(t0)
                and len(toks[1]) == 2 and _is_hex(toks[1]) and int(t0, 16) in (0, have)):
            if int(t0, 16) == 0:
                flush()
            body = []
            for t in toks[1:]:                           # 傾印格式：後面的 ASCII 欄不要
                if len(t) == 2 and _is_hex(t):
                    body.append(t)
                else:
                    break
            toks = body
        if not all(_is_hex(t) for t in toks):
            bad.append(raw)
            continue
        cur.append(unhex(' '.join(toks)))
    flush()
    return pkts, bad


class Decoder:
    # 解碼器的狀態：FCS 模式、context、分片重組緩衝
    def __init__(self, w, wt):
        # w、wt 是 wsnproto、wsntree 模組
        self.w = w
        self.wt = wt
        self.fcs = None
        self.ctx = {}
        self.reasm = w.Reassembler(timeout_ms=10 * 60 * 1000, max_bufs=16)
        self.count = 0

    def decode(self, pkt):
        # 解一個封包，回傳要印的每一行文字
        self.count += 1
        lines = ['', '=' * 16 + ' 封包 {}（{} 位元組）'.format(self.count, len(pkt)) + '=' * 16]
        lines.extend(self.w.hexdump(pkt).split('\n'))
        d = self.w.decode_any(pkt, ctx=self.ctx or None, reasm=self.reasm, fcs=self.fcs)
        lines.extend(self.wt.tree_lines(d))
        lines.append('摘要：' + self.wt.summary(d))
        return lines

    def command(self, line):
        # 處理指令；是指令就回傳要印的文字，不是指令回傳 None
        p = line.split()
        if not p:
            return None
        c = p[0].lower()
        if c in ('help', '?', '說明'):
            return HELP
        if c == 'fcs' and len(p) == 2:
            v = p[1].lower()
            self.fcs = {'on': True, 'off': False}.get(v)
            return 'FCS 模式：' + {'on': '一定有附 FCS', 'off': '一定沒附 FCS'}.get(v, '自動判斷')
        if c == 'ctx':
            if len(p) == 1:
                if not self.ctx:
                    return '目前沒有設定 context'
                return '\n'.join('context {} = {}/64'.format(k, self.w.ip6str(self.w.ip6(v) if ':' in v else v))
                                 for k, v in sorted(self.ctx.items()))
            if p[1].lower() == 'clear':
                self.ctx = {}
                return '已清掉全部 context'
            if len(p) == 3 and p[1].isdigit() and 0 <= int(p[1]) <= 15:
                try:
                    self.w.ip6(p[2])
                except ValueError as ex:
                    return '前綴寫錯：{}'.format(ex)
                self.ctx[int(p[1])] = p[2]
                return 'context {} = {}'.format(p[1], p[2])
            return '用法：ctx 0 2001:db8:1::/64'
        if c == 'reset':
            self.reasm = self.w.Reassembler(timeout_ms=10 * 60 * 1000, max_bufs=16)
            return '分片重組緩衝已清空'
        if c == 'demo':
            return '\n'.join(self.demo())
        return None

    def demo(self):
        # 解幾個範例：IPHC＋UDP、RPL DIO、XBee 傳送要求
        w = self.w
        a, b = 0x0001, 0x0002
        out = ['範例 1：主題 8 的 IPHC＋NHC-UDP（B → A，沒附 FCS）']
        pkt = w.ipv6_udp(w.link_local(b), w.link_local(a), 0xF0B1, 0xF0B2, b'T=25.3C RH')
        out.extend(self.decode(w.frames_ipv6(2, 0xABCD, b, a, pkt, fcs=False)[0]))
        out.append('')
        out.append('範例 2：主題 10 的 RPL DIO（根廣播，附 FCS）')
        mac_a = w.unhex('28:cd:c1:01:02:03')
        dio = w.rpl_dio(256, '2001:db8:1::1', options=w.opt_conf())
        out.extend(self.decode(w.frames_ipv6(6, 0xABCD, mac_a, w.BROADCAST,
                                             w.ipv6_icmp(w.link_local(mac_a), w.ALL_RPL_NODES, 155, w.RPL_DIO, dio, hlim=255))[0]))
        out.append('')
        out.append('範例 3：主題 5 的 XBee 0x10 傳送要求（Digi 手冊範例）')
        out.extend(self.decode(w.unhex('7E 00 14 10 52 00 13 A2 00 12 34 56 78 FF FE 00 00 54 78 44 61 74 61 91')))
        return out


def _say(lines):
    # 印出多行文字（遇到主控台不支援的字就換成 ?，不會當掉）
    for line in lines if isinstance(lines, list) else [lines]:
        print(line)


def main(argv):
    # 主程式：有給檔名或位元組就一次解完；沒有就進入互動模式
    try:
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    w, wt, where = _load_lib()
    dec = Decoder(w, wt)
    args = list(argv[1:])
    while args and args[0].startswith('--'):
        opt = args.pop(0)
        if opt == '--fcs' and args:
            dec.command('fcs ' + args.pop(0))
        elif opt == '--ctx' and args:
            k, _, v = args.pop(0).partition('=')
            dec.command('ctx {} {}'.format(k, v))
        elif opt == '--quiet':
            where = None
    if where:
        print('wsn_decode：使用{}（wsnproto {}）'.format(where, w.VERSION))
    if args:
        if len(args) == 1 and os.path.isfile(args[0]):
            with open(args[0], encoding='utf-8', errors='replace') as f:
                text = f.read()
        else:
            text = ' '.join(args)
        pkts, bad = packets_from_text(text, w.unhex)
        for line in bad:
            print('看不懂這一行，跳過：' + line)
        for pkt in pkts:
            _say(dec.decode(pkt))
        return 0
    print('貼上十六進位（可以好幾行），最後再按一次 Enter 送出空白行就開始解碼；打 help 看指令，打 q 離開。')
    while True:
        buf = []
        try:
            while True:
                line = input('' if buf else '> ')
                s = line.strip()
                if not buf and s.lower() in ('q', 'quit', 'exit', '離開'):
                    return 0
                if not buf:
                    msg = dec.command(s)
                    if msg is not None:
                        print(msg)
                        continue
                if not s:
                    if buf:
                        break
                    continue
                buf.append(line)
        except EOFError:
            if not buf:
                return 0
        pkts, bad = packets_from_text('\n'.join(buf), w.unhex)
        for line in bad:
            print('看不懂這一行，跳過：' + line)
        for pkt in pkts:
            _say(dec.decode(pkt))
        print()


# ---- 備用：找不到 wsnproto.py／wsntree.py 時用的內建版本（由 test_wsnproto.py --embed 產生，請不要手動修改）----
_EMBED_VERSION = '2026-10-10'
_EMBED = '''
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
28r5mg==
'''

if __name__ == '__main__':
    sys.exit(main(sys.argv))
