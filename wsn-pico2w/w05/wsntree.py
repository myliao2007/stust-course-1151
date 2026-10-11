# wsntree.py：把 wsnproto 的解碼結果印成「欄位樹」（中文欄位名＋英文縮寫）
#
# 平常不用直接 import 它：呼叫 wsnproto.tree(d)、wsnproto.tree_lines(d)、wsnproto.summary(d) 時才會自動載入，
# 這樣 Pico 只在需要印字時才多花這一份記憶體。電腦端的 wsn_decode.py 也用同一份，Pico 和電腦印出來一模一樣。

import wsnproto as w

FT_NAMES = {0: '信標 Beacon', 1: '資料 Data', 2: '確認 Ack', 3: 'MAC 命令 Command'}
AM_NAMES = {0: '沒有位址', 1: '保留', 2: '16 位元短位址', 3: '64 位元長位址'}
VER_NAMES = {0: 'IEEE 802.15.4-2003', 1: 'IEEE 802.15.4-2006', 2: 'IEEE 802.15.4-2015', 3: '保留'}
CMD_NAMES = {1: '入網請求 Association Request', 2: '入網回應 Association Response',
             3: '離網通知 Disassociation Notification', 4: '資料請求 Data Request',
             5: 'PAN ID 衝突通知 PAN ID Conflict Notification', 6: '孤兒通知 Orphan Notification',
             7: '信標請求 Beacon Request', 8: '協調器重新校正 Coordinator Realignment',
             9: 'GTS 請求 GTS Request'}

XB_TYPES = {0x08: 'AT 指令 AT Command', 0x09: 'AT 指令（排隊）AT Command - Queue Parameter Value',
            0x10: '傳送要求 Transmit Request', 0x11: '明確定址傳送 Explicit Addressing Command',
            0x17: '遠端 AT 指令 Remote AT Command Request', 0x88: 'AT 指令回應 AT Command Response',
            0x8A: '模組狀態 Modem Status', 0x8B: '傳送狀態 Transmit Status',
            0x90: '收到封包 Receive Packet', 0x91: '明確定址收到 Explicit Rx Indicator',
            0x92: 'I/O 取樣 IO Data Sample Rx Indicator', 0x95: '節點識別 Node Identification Indicator',
            0x97: '遠端 AT 回應 Remote AT Command Response'}
XB_AT_STATUS = {0: '成功 OK', 1: '錯誤 ERROR', 2: '指令無效 Invalid Command', 3: '參數無效 Invalid Parameter',
                4: '傳送失敗 Transmission Failure'}
XB_DELIVERY = {0x00: '成功 Success', 0x01: 'MAC ACK 失敗 MAC ACK Failure', 0x02: 'CCA 失敗（頻道忙）CCA Failure',
               0x15: '目的端點無效 Invalid Destination Endpoint', 0x21: '網路 ACK 失敗 Network ACK Failure',
               0x22: '還沒入網 Not Joined to Network', 0x23: '送給自己 Self-addressed',
               0x24: '找不到位址 Address Not Found', 0x25: '找不到路由 Route Not Found',
               0x26: '廣播沒聽到鄰居轉送 Broadcast Source Failed to Hear a Neighbor Relay',
               0x2B: '綁定表索引無效 Invalid Binding Table Index', 0x2C: '資源不足 Resource Error',
               0x2D: 'APS 傳送不能廣播 Attempted Broadcast with APS Transmission',
               0x2E: 'APS 單播但 EE＝0 Attempted Unicast with APS Transmission, but EE = 0',
               0x32: '資源不足 Resource Error', 0x74: '資料太長 Data Payload Too Large',
               0x75: '間接訊息沒人來拿 Indirect Message Unrequested'}
XB_DISCOVERY = {0x00: '不用探索 No Discovery Overhead', 0x01: '位址探索 Address Discovery',
                0x02: '路由探索 Route Discovery', 0x03: '位址＋路由探索 Address and Route Discovery',
                0x40: '終端裝置延長逾時 Extended Timeout Discovery'}
XB_MODEM = {0x00: '硬體重置或開機 Hardware Reset or Power Up', 0x01: '看門狗重置 Watchdog Timer Reset',
            0x02: '已入網 Joined Network', 0x03: '已離網 Disassociated', 0x06: '協調器已啟動 Coordinator Started',
            0x07: '網路金鑰已更新 Network Security Key Updated',
            0x0D: '電壓超過上限 Voltage Supply Limit Exceeded',
            0x11: '入網途中改了設定 Modem Configuration Changed While Join in Progress'}
XB_RXOPT = ((0x01, '已確認 Acknowledged'), (0x02, '廣播 Broadcast'), (0x10, '安全工作階段加密 Secure Session'),
            (0x20, 'APS 加密 APS Encrypted'), (0x40, '來自終端裝置 From End Device'))

NH_NAMES = {0: '逐跳選項 Hop-by-Hop Options', 6: 'TCP', 17: 'UDP', 43: '路由標頭 Routing', 44: '分片標頭 Fragment',
            58: 'ICMPv6', 59: '沒有下一個標頭 No Next Header', 60: '目的地選項 Destination Options'}
ICMP_NAMES = {1: '目的地無法到達 Destination Unreachable', 2: '封包太大 Packet Too Big', 3: '逾時 Time Exceeded',
              4: '參數問題 Parameter Problem', 128: 'Echo 請求 Echo Request', 129: 'Echo 回覆 Echo Reply',
              133: '路由器請求 Router Solicitation', 134: '路由器通告 Router Advertisement',
              135: '鄰居請求 Neighbor Solicitation', 136: '鄰居通告 Neighbor Advertisement',
              155: 'RPL 控制訊息 RPL Control Message'}
TF_TEXT = ('00：流量類別與流標籤都帶著（4 位元組）', '01：只帶 ECN＋流標籤（3 位元組）',
           '10：只帶 ECN＋DSCP（1 位元組）', '11：都省略（都是 0）')
HLIM_TEXT = ('00：直接帶著（1 位元組）', '01：省略，代表 1', '10：省略，代表 64', '11：省略，代表 255')
PORT_TEXT = ('來源埠、目的埠都帶 16 位元', '目的埠 0xF0xx 只帶低 8 位元', '來源埠 0xF0xx 只帶低 8 位元',
             '兩個埠都是 0xF0Bx，各帶 4 位元')

RPL_NAMES = {0: 'DIS（DODAG 資訊請求 DODAG Information Solicitation）',
             1: 'DIO（DODAG 資訊物件 DODAG Information Object）',
             2: 'DAO（目的地通告物件 Destination Advertisement Object）',
             3: 'DAO-ACK（DAO 確認 Destination Advertisement Object Acknowledgment）',
             0x8A: 'CC（一致性檢查 Consistency Check）'}
OPT_NAMES = {0: 'Pad1（補 1 位元組）', 1: 'PadN（補 N 位元組）', 2: 'DAG 度量容器 DAG Metric Container',
             3: '路由資訊 Route Information', 4: 'DODAG 設定 DODAG Configuration', 5: 'RPL 目標 RPL Target',
             6: '轉送資訊 Transit Information', 7: '請求資訊 Solicited Information',
             8: '前綴資訊 Prefix Information', 9: '目標描述 RPL Target Descriptor'}
MOP_NAMES = {0: '不支援下行路由', 1: 'non-storing（只有根記下行路由）', 2: 'storing，不支援群播',
             3: 'storing，支援群播'}
OCP_NAMES = {0: 'OF0（RFC 6552）', 1: 'MRHOF（RFC 6719）'}


def _ok_text(good, right):
    # 檢查結果的文字
    return '正確' if good else '錯誤（應該是 {}）'.format(right)


def _bits2(x):
    # 2 位元的值印成 00／01／10／11
    return ('00', '01', '10', '11')[x & 3]


def _ms_text(ms):
    # 毫秒數 → 「8388.6 秒（約 2.3 小時）」（只用整數運算，Pico 和電腦印出來一樣）
    if ms < 1000:
        return '{} 毫秒'.format(ms)
    s = '{}.{} 秒'.format(ms // 1000, (ms % 1000) // 100)
    if ms >= 3600000:
        h10 = ms * 10 // 3600000
        s += '（約 {}.{} 小時）'.format(h10 // 10, h10 % 10)
    elif ms >= 60000:
        m10 = ms * 10 // 60000
        s += '（約 {}.{} 分鐘）'.format(m10 // 10, m10 % 10)
    return s


def _flag_list(v, table):
    # 把選項位元變成文字
    names = [n for bit, n in table if v & bit]
    return '、'.join(names) if names else '無'


def _rev_text(a):
    # 長位址在訊框裡是倒過來放的，順便印出來對照
    if isinstance(a, (bytes, bytearray)):
        return '（訊框裡倒過來放：{}）'.format(w.hexs(bytes(reversed(a))))
    return ''


def _tr_mac(d, e):
    # 印 802.15.4 MAC 層
    if 'fcf' not in d:
        e(0, '[IEEE 802.15.4 MAC] {} 位元組'.format(d['len']))
        return
    ft = d['ftype']
    tail = '（含 FCS 2 位元組）' if d['has_fcs'] else '（沒附 FCS）'
    e(0, '[IEEE 802.15.4 MAC] {} 訊框，{} 位元組{}'.format(FT_NAMES.get(ft, '保留 Reserved'), d['len'], tail))
    fcf = d['fcf']
    e(1, '訊框控制 FCF (Frame Control Field) = 0x{:04x}（訊框裡是 {:02x} {:02x}，低位元組先放）'.format(fcf, fcf & 0xFF, fcf >> 8))
    e(2, '位元 0～2 訊框類型 Frame Type = {}：{}'.format(ft, FT_NAMES.get(ft, '保留 Reserved')))
    e(2, '位元 3 安全 Security Enabled = {}'.format(d['sec']))
    e(2, '位元 4 還有資料 Frame Pending = {}{}'.format(d['pending'], '（我這裡還有你的信）' if d['pending'] else ''))
    e(2, '位元 5 要求確認 AR (Ack Request) = {}'.format(d['ar']))
    e(2, '位元 6 PAN ID 壓縮 PAN ID Compression = {}'.format(d['panc']))
    e(2, '位元 10～11 目的位址模式 Dst Addr Mode = {}：{}'.format(d['dmode'], AM_NAMES[d['dmode']]))
    e(2, '位元 12～13 訊框版本 Frame Version = {}：{}'.format(d['ver'], VER_NAMES[d['ver']]))
    e(2, '位元 14～15 來源位址模式 Src Addr Mode = {}：{}'.format(d['smode'], AM_NAMES[d['smode']]))
    if 'seq' in d:
        e(1, '序號 Seq (Sequence Number) = {}'.format(d['seq'] if d['seq'] is not None else '（省略）'))
    if 'dpan' in d:
        e(1, '目的 PAN ID = 0x{:04x}'.format(d['dpan']))
    if d.get('dst') is not None:
        e(1, '目的位址 Dst = {}{}'.format(w.addr_str(d['dst']), _rev_text(d['dst'])))
    if 'span' in d:
        e(1, '來源 PAN ID = 0x{:04x}'.format(d['span']))
    elif d.get('src') is not None and d.get('panc'):
        e(1, '來源 PAN ID：省略（PAN ID 壓縮＝1，和目的 PAN 相同）')
    if d.get('src') is not None:
        e(1, '來源位址 Src = {}{}'.format(w.addr_str(d['src']), _rev_text(d['src'])))
    if 'cmd' in d:
        e(1, 'MAC 命令 Command = 0x{:02x}：{}'.format(d['cmd'], CMD_NAMES.get(d['cmd'], '其他')))
    if 'payload' in d:
        e(1, 'MAC 酬載 Payload = {} 位元組（MAC 標頭 {} 位元組）'.format(len(d['payload']), d['hdr_len']))
    if d['has_fcs'] and 'fcs' in d:
        e(1, 'FCS (Frame Check Sequence) = 0x{:04x}（訊框裡是 {:02x} {:02x}）  {}'.format(
            d['fcs'], d['fcs'] & 0xFF, d['fcs'] >> 8, _ok_text(d['fcs_ok'], '0x{:04x}'.format(d['fcs_calc']))))


def _b64_text(a):
    # XBee 64 位元位址的特殊值
    if a == b'\x00\x00\x00\x00\x00\x00\xff\xff':
        return '（廣播）'
    if a == bytes(8):
        return '（協調器）'
    if a == b'\xff' * 8:
        return '（不用 64 位元位址，看 16 位元位址）'
    return ''


def _pins(mask, name):
    # 遮罩的位元 → 腳位名稱
    out = []
    for i in range(16):
        if mask & (1 << i):
            out.append('供電電壓' if (name == 'AD' and i == 7) else '{}{}'.format(name, i))
    return '、'.join(out) if out else '無'


def _tr_xbee(d, e):
    # 印 XBee API 訊框
    t = d.get('api')
    e(0, '[XBee API 訊框] {}'.format('0x{:02x} {}'.format(t, XB_TYPES.get(t, '未知類型')) if t is not None else ''))
    e(1, '起始字元 Start Delimiter = 0x7e')
    if 'length' in d:
        e(1, '長度 Length = {}（只算訊框資料，不含 7E、長度、檢查碼）'.format(d['length']))
    if t is None:
        return
    e(1, '訊框類型 Frame Type = 0x{:02x}'.format(t))
    if 'fid' in d:
        e(1, '訊框編號 Frame ID = 0x{:02x}{}'.format(d['fid'], '（0＝不要回應）' if d['fid'] == 0 else ''))
    if 'dst64' in d:
        e(1, '64 位元目的位址 = {}{}'.format(w.hexs(d['dst64']), _b64_text(d['dst64'])))
    if 'src64' in d:
        e(1, '64 位元來源位址 = {}{}'.format(w.hexs(d['src64']), _b64_text(d['src64'])))
    if 'dst16' in d:
        e(1, '16 位元目的位址 = 0x{:04x}{}'.format(d['dst16'], '（不知道，請模組自己找）' if d['dst16'] == 0xFFFE else ''))
    if 'src16' in d:
        e(1, '16 位元來源位址 = 0x{:04x}{}'.format(d['src16'], '（不知道）' if d['src16'] == 0xFFFE else ''))
    if 'radius' in d:
        e(1, '廣播半徑 Broadcast Radius = {}{}'.format(d['radius'], '（用預設的最大跳數 NH）' if d['radius'] == 0 else ''))
    if 'cmd' in d:
        e(1, 'AT 指令 = {}（{}）'.format(w._txt(d['cmd']), w.hexs(d['cmd'])))
    if t in (0x08, 0x09, 0x17):
        if d['param']:
            e(1, '參數 Parameter = {}（"{}"）'.format(w.hexs(d['param']), w._txt(d['param'])))
        else:
            e(1, '參數 Parameter：沒有，表示查詢')
    if 'opts' in d:
        if t == 0x17:
            e(1, '遠端指令選項 Options = 0x{:02x}{}'.format(d['opts'], '（馬上套用）' if d['opts'] & 2 else '（先排隊，等 AC 才套用）'))
        elif t == 0x10:
            e(1, '傳送選項 Options = 0x{:02x}{}'.format(d['opts'], '（不要 ACK）' if d['opts'] & 1 else ''))
        else:
            e(1, '接收選項 Options = 0x{:02x}（{}）'.format(d['opts'], _flag_list(d['opts'], XB_RXOPT)))
    if 'status' in d:
        if t == 0x8A:
            e(1, '狀態 Status = 0x{:02x}：{}'.format(d['status'], XB_MODEM.get(d['status'], '堆疊錯誤' if d['status'] >= 0x80 else '其他')))
        else:
            e(1, '指令狀態 Status = {}：{}'.format(d['status'], XB_AT_STATUS.get(d['status'], '其他')))
    if 'value' in d:
        e(1, '回傳值 Value = {}'.format(w.hexs(d['value']) if d['value'] else '（沒有）'))
    if t == 0x8B and 'delivery' in d:
        e(1, '重試次數 Transmit Retry Count = {}'.format(d['retries']))
        e(1, '遞送狀態 Delivery Status = 0x{:02x}：{}'.format(d['delivery'], XB_DELIVERY.get(d['delivery'], '其他')))
        e(1, '探索狀態 Discovery Status = 0x{:02x}：{}'.format(d['discovery'], XB_DISCOVERY.get(d['discovery'], '其他')))
    if t == 0x92 and 'amask' in d:
        e(1, '取樣組數 Number of Samples = {}'.format(d['nsamp']))
        e(1, '數位遮罩 Digital Mask = 0x{:04x}（{}）'.format(d['dmask'], _pins(d['dmask'], 'DIO')))
        e(1, '類比遮罩 Analog Mask = 0x{:02x}（{}）'.format(d['amask'], _pins(d['amask'], 'AD')))
        if 'dsamples' in d:
            hi = [i for i in range(16) if d['dmask'] & (1 << i) and d['dsamples'] & (1 << i)]
            e(1, '數位樣本 Digital Samples = 0x{:04x}（高電位：{}）'.format(
                d['dsamples'], '、'.join('DIO{}'.format(i) for i in hi) if hi else '無'))
        for bit, v in d.get('analog', ()):
            e(1, '類比樣本 {} = 0x{:04x}（{}）'.format(_pins(1 << bit, 'AD'), v, v))
    if 'data' in d:
        e(1, 'RF 資料 Data（{} 位元組）= {}'.format(len(d['data']), w.hexs(d['data'])))
        e(2, '文字："{}"'.format(w._txt(d['data'])))
    if 'raw' in d:
        e(1, '內容 = {}'.format(w.hexs(d['raw'])))
    if 'cksum' in d:
        e(1, '檢查碼 Checksum = 0x{:02x}  {}'.format(d['cksum'], _ok_text(d['cksum'] == d['cksum_calc'], '0x{:02x}'.format(d['cksum_calc']))))
        e(2, '算法：訊框資料加總 0x{:x} → 取最低 8 位元 0x{:02x} → 0xff - 0x{:02x} ＝ 0x{:02x}'.format(
            d['sum'], d['sum'] & 0xFF, d['sum'] & 0xFF, d['cksum_calc']))


def _tr_lowpan(d, e):
    # 印 6LoWPAN 層
    e(0, '[6LoWPAN] {} 位元組'.format(d['len']))
    for h in d['hdrs']:
        k = h['kind']
        if k == 'mesh':
            e(1, 'Mesh 標頭（分派 10xxxxxx）：V = {}、F = {}、剩餘跳數 Hops Left = {}'.format(h['v'], h['f'], h['hops']))
            e(2, '原始來源 Originator = {}'.format(w.addr_str(h['orig'])))
            e(2, '最終目的 Final Destination = {}'.format(w.addr_str(h['final'])))
        elif k == 'bc0':
            e(1, '廣播標頭 BC0（分派 0x50）：序號 = {}'.format(h['seq']))
        elif k == 'frag1':
            e(1, '第一片 FRAG1（分派 11000）：datagram_size = {}、datagram_tag = 0x{:04x}（offset 當成 0）'.format(h['size'], h['tag']))
            e(2, '這一片帶 {} 位元組（從壓縮標頭開始算）'.format(h['data_len']))
        elif k == 'fragn':
            e(1, '後續片 FRAGN（分派 11100）：datagram_size = {}、datagram_tag = 0x{:04x}、datagram_offset = {}'.format(h['size'], h['tag'], h['offset']))
            e(2, 'offset × 8 ＝ 從未壓縮封包的第 {} 位元組開始，這一片帶 {} 位元組'.format(h['offset'] * 8, h['data_len']))
        elif k == 'ipv6':
            e(1, '分派 Dispatch = 0x41：後面是未壓縮的 IPv6 封包')
        elif k == 'nalp':
            e(1, '分派 00xxxxxx：不是 6LoWPAN（NALP）')
        elif k == 'iphc':
            _tr_iphc(h, e)


def _tr_iphc(h, e):
    # 印 IPHC 的每個欄位
    v = h['iphc']
    e(1, 'IPHC 標頭壓縮（RFC 6282）= 0x{:04x}（{:02x} {:02x}），前 3 位元 011'.format(v, v >> 8, v & 0xFF))
    e(2, 'TF（流量類別／流標籤）= {}'.format(TF_TEXT[h['tf']]))
    e(2, 'NH（下一個標頭）= {}：{}'.format(h['nh'], '用 NHC 壓縮（後面接 NHC 位元組）' if h['nh'] else '直接帶著（1 位元組）'))
    e(2, 'HLIM（跳數上限）= {}'.format(HLIM_TEXT[h['hlim']]))
    if h['cid']:
        e(2, 'CID（context 編號延伸）= 1：來源用 context {}、目的用 context {}'.format(h['sci'], h['dci']))
    else:
        e(2, 'CID（context 編號延伸）= 0：要用 context 時用 0 號')
    e(2, 'SAC = {}、SAM = {}：{}'.format(h['sac'], _bits2(h['sam']), h['src_how']))
    e(2, 'M（群播）= {}、DAC = {}、DAM = {}：{}'.format(h['m'], h['dac'], _bits2(h['dam']), h['dst_how']))
    if h['inline']:
        e(2, '直接帶著的欄位（照 IPv6 標頭的順序）：')
        for name, b in h['inline']:
            e(3, '{} = {}'.format(name, w.hexs(b)))
    else:
        e(2, '直接帶著的欄位：沒有，全部省略')
    n = h.get('nhc')
    if n:
        e(2, 'NHC-UDP = 0x{:02x}（11110 C P P）：C = {}（{}）、P = {}（{}）；UDP 長度一定省略'.format(
            n['byte'], n['c'], 'checksum 省略' if n['c'] else 'checksum 帶著', _bits2(n['p']), PORT_TEXT[n['p']]))
        for name, b in n['inline']:
            e(3, '{} = {}'.format(name, w.hexs(b)))
        e(3, '還原：來源埠 {}（0x{:04x}）、目的埠 {}（0x{:04x}）'.format(n['sport'], n['sport'], n['dport'], n['dport']))
    e(2, '壓縮效果：IPv6{}標頭 {} 位元組 → {} 位元組'.format('＋UDP ' if n else ' ', h['unc_len'], h['comp_len']))


def _tr_ipv6(d, e):
    # 印 IPv6 層
    e(0, '[IPv6] {} 位元組（還原後）'.format(d['len']))
    if 'src' not in d:
        return
    e(1, '版本 Version = {}'.format(d['ver']))
    e(1, '流量類別 Traffic Class = 0x{:02x}（DSCP {}、ECN {}）'.format(d['tc'], d['tc'] >> 2, d['tc'] & 3))
    e(1, '流標籤 Flow Label = 0x{:05x}'.format(d['flow']))
    e(1, '酬載長度 Payload Length = {}'.format(d['plen']))
    e(1, '下一個標頭 Next Header = {}：{}'.format(d['nh'], NH_NAMES.get(d['nh'], '其他')))
    e(1, '跳數上限 Hop Limit = {}'.format(d['hlim']))
    e(1, '來源位址 Src = {}'.format(w.ip6str(d['src'])))
    if d.get('src_how'):
        e(2, '怎麼來的：' + d['src_how'])
    e(1, '目的位址 Dst = {}'.format(w.ip6str(d['dst'])))
    if d.get('dst_how'):
        e(2, '怎麼來的：' + d['dst_how'])


def _tr_udp(d, e):
    # 印 UDP 層
    e(0, '[UDP] {} 位元組'.format(d['len']))
    if 'sport' not in d:
        return
    e(1, '來源埠 Src Port = {}（0x{:04x}）'.format(d['sport'], d['sport']))
    e(1, '目的埠 Dst Port = {}（0x{:04x}）'.format(d['dport'], d['dport']))
    e(1, '長度 Length = {}（標頭 8＋資料 {}）'.format(d['ulen'], len(d['data'])))
    if d['chk']:
        e(1, '檢查碼 Checksum = 0x{:04x}  {}'.format(d['cksum'], _ok_text(d['chk'][0][1], d['chk'][0][2])))
    else:
        e(1, '檢查碼 Checksum = 0x{:04x}'.format(d['cksum']))
    e(1, '資料 Data（{} 位元組）= {}'.format(len(d['data']), w.hexs(d['data'])))
    e(2, '文字："{}"'.format(w._txt(d['data'])))


def _tr_icmpv6(d, e):
    # 印 ICMPv6 層
    e(0, '[ICMPv6] {} 位元組'.format(d['len']))
    if 'type' not in d:
        return
    e(1, '類型 Type = {}：{}'.format(d['type'], ICMP_NAMES.get(d['type'], '其他')))
    e(1, '代碼 Code = {}'.format(d['code']))
    e(1, '檢查碼 Checksum = 0x{:04x}  {}'.format(d['cksum'], _ok_text(d['cksum'] == d['cksum_calc'], '0x{:04x}'.format(d['cksum_calc']))))
    if d['type'] != 155:
        e(1, '內容 = {}'.format(w.hexs(d['body'])))


def _tr_rpl(d, e):
    # 印 RPL 控制訊息
    c = d['code']
    e(0, '[RPL 控制訊息] 代碼 0x{:02x}：{}'.format(c, RPL_NAMES.get(c, '其他')))
    min_hop = 256
    for o in d['opts']:
        if o['type'] == 4 and o['min_hop']:
            min_hop = o['min_hop']
    if c == w.RPL_DIS and 'flags' in d:
        e(1, '旗標 Flags = 0x{:02x}、保留 Reserved'.format(d['flags']))
    elif c == w.RPL_DIO and 'rank' in d:
        e(1, 'RPLInstanceID = {}'.format(d['instance']))
        e(1, '版本 Version Number = {}'.format(d['version']))
        e(1, 'Rank = {}（DAGRank ＝ {} ÷ {} ＝ {}{}）'.format(d['rank'], d['rank'], min_hop, w.dag_rank(d['rank'], min_hop),
                                                        '，無限大' if d['rank'] == w.INFINITE_RANK else ''))
        e(1, 'G（接地 Grounded）= {}'.format(d['g']))
        e(1, 'MOP（運作模式 Mode of Operation）= {}：{}'.format(d['mop'], MOP_NAMES.get(d['mop'], '保留')))
        e(1, 'Prf（DODAG 偏好 Preference）= {}'.format(d['prf']))
        e(1, 'DTSN (Destination Advertisement Trigger Sequence Number) = {}'.format(d['dtsn']))
        e(1, '旗標 Flags = 0x{:02x}、保留 Reserved'.format(d['flags']))
        e(1, 'DODAGID = {}'.format(w.ip6str(d['dodagid'])))
    elif c == w.RPL_DAO and 'seq' in d:
        e(1, 'RPLInstanceID = {}'.format(d['instance']))
        e(1, 'K（要求 DAO-ACK）= {}'.format(d['k']))
        e(1, 'D（有帶 DODAGID）= {}'.format(d['d']))
        e(1, 'DAOSequence = {}'.format(d['seq']))
        if 'dodagid' in d:
            e(1, 'DODAGID = {}'.format(w.ip6str(d['dodagid'])))
    elif c == w.RPL_DAO_ACK and 'seq' in d:
        st = d['status']
        e(1, 'RPLInstanceID = {}'.format(d['instance']))
        e(1, 'D（有帶 DODAGID）= {}'.format(d['d']))
        e(1, 'DAOSequence = {}'.format(d['seq']))
        e(1, '狀態 Status = {}：{}'.format(st, '接受' if st == 0 else ('接受，但建議改找別的父節點' if st < 128 else '拒絕')))
        if 'dodagid' in d:
            e(1, 'DODAGID = {}'.format(w.ip6str(d['dodagid'])))
    for o in d['opts']:
        _tr_opt(o, e)


def _tr_opt(o, e):
    # 印一個 RPL 選項
    t = o['type']
    e(1, '選項 Option 0x{:02x} {}（長度 {}）'.format(t, OPT_NAMES.get(t, '未知'), o['len']))
    if t == 3:
        e(2, '前綴 Prefix = {}/{}、偏好 Prf = {}、路由壽命 = {} 秒'.format(w.ip6str(o['prefix']), o['plen'], o['prf'], o['lifetime']))
    elif t == 4:
        imin = 1 << o['imin']
        e(2, 'A（認證）= {}、PCS（路徑控制長度）= {}'.format(o['auth'], o['pcs']))
        e(2, 'DIOIntervalDoublings = {}'.format(o['doublings']))
        e(2, 'DIOIntervalMin = {}（Imin ＝ 2^{} ＝ {}）'.format(o['imin'], o['imin'], _ms_text(imin)))
        e(2, '最長間隔 Imax ＝ Imin × 2^{} ＝ {}'.format(o['doublings'], _ms_text(imin << o['doublings'])))
        e(2, 'DIORedundancyConstant（k）= {}'.format(o['redundancy']))
        e(2, 'MaxRankIncrease = {}'.format(o['max_rank_inc']))
        e(2, 'MinHopRankIncrease = {}'.format(o['min_hop']))
        e(2, 'OCP（目標函數 Objective Code Point）= {}：{}'.format(o['ocp'], OCP_NAMES.get(o['ocp'], '其他')))
        e(2, '預設壽命 Default Lifetime = {}、壽命單位 Lifetime Unit = {} 秒'.format(o['def_lifetime'], o['lifetime_unit']))
    elif t == 5:
        e(2, '目標 Target = {}/{}'.format(w.ip6str(o['prefix']), o['plen']))
    elif t == 6:
        life = o['lifetime']
        e(2, 'E（外部）= {}、Path Control = 0x{:02x}、Path Sequence = {}'.format(o['e'], o['control'], o['pseq']))
        e(2, 'Path Lifetime = {}{}'.format(life, '（無限）' if life == 0xFF else ('（撤銷路由 No-Path）' if life == 0 else '')))
        if 'parent' in o:
            e(2, '父節點 Parent Address = {}（non-storing 模式）'.format(w.ip6str(o['parent'])))
    elif t == 7:
        e(2, 'V／I／D 旗標 = {}／{}／{}'.format(o['vf'], o['if'], o['df']))
        e(2, 'RPLInstanceID = {}、DODAGID = {}、版本 = {}'.format(o['instance'], w.ip6str(o['dodagid']), o['version']))
    elif t == 8:
        e(2, '前綴 Prefix = {}/{}'.format(w.ip6str(o['prefix']), o['plen']))
        e(2, 'L（在鏈路上）= {}、A（自動設定位址）= {}、R（路由器位址）= {}'.format(o['l'], o['a'], o['r']))
        e(2, '有效壽命 = {} 秒、偏好壽命 = {} 秒'.format(o['valid'], o['preferred']))
    elif t == 9:
        e(2, '描述 Descriptor = 0x{:08x}'.format(o['descriptor']))
    elif 'raw' in o:
        e(2, '內容 = {}'.format(w.hexs(o['raw'])))


def _tr_data(d, e):
    # 印應用資料
    e(0, '[應用資料] {} 位元組'.format(d['len']))
    e(1, '十六進位 = {}'.format(w.hexs(d.get('data', b''))))
    e(1, '文字 = "{}"'.format(w._txt(d.get('data', b''))))


_PRINTERS = {'mac': _tr_mac, 'xbee': _tr_xbee, 'lowpan': _tr_lowpan, 'ipv6': _tr_ipv6, 'udp': _tr_udp,
             'icmpv6': _tr_icmpv6, 'rpl': _tr_rpl, 'data': _tr_data}


def tree_lines(d):
    # 把解碼結果變成一行一行的欄位樹文字，回傳清單
    lines = []

    def e(depth, text):
        # 加一行：depth 是縮排層數
        lines.append('  ' * depth + text)
    if d.get('guess'):
        e(0, '判斷：' + d['guess'])
    for x in w.chain(d):
        _PRINTERS.get(x.get('proto'), _tr_data)(x, e)
        for n in x.get('note', ()):
            e(1, '說明：' + n)
        for m in x.get('err', ()):
            e(1, '錯誤：' + m)
    cs = w.checks(d)
    e(0, '[檢查結果]')
    for name, good, right in cs:
        e(1, '{}：{}'.format(name, _ok_text(good, right)))
    if not cs:
        e(1, '（這個訊框沒有可以驗的檢查碼）')
    e(1, '結論：{}'.format('全部正確' if w.ok(d) else '有問題，請看上面標「錯誤」的地方'))
    return lines


def tree(d, out=None):
    # 印出欄位樹；out 可以給一個「收一行文字」的函式（例如寫檔），不給就用 print
    for line in tree_lines(d):
        if out is None:
            print(line)
        else:
            out(line)


def summary(d):
    # 一行摘要（像 Wireshark 的 Info 欄）
    parts = []
    for x in w.chain(d):
        pr = x.get('proto')
        if pr == 'mac' and 'ftype' in x:
            parts.append('802.15.4 {} {}→{}'.format(FT_NAMES.get(x['ftype'], '?').split(' ')[-1],
                                                   w.addr_str(x.get('src')), w.addr_str(x.get('dst'))))
        elif pr == 'xbee':
            parts.append('XBee 0x{:02x} {}'.format(x.get('api', 0), XB_TYPES.get(x.get('api'), '')).rstrip())
        elif pr == 'lowpan':
            parts.append('6LoWPAN ' + '+'.join(h['kind'].upper() for h in x['hdrs']))
        elif pr == 'ipv6' and 'src' in x:
            parts.append('IPv6 {}→{}'.format(w.ip6str(x['src']), w.ip6str(x['dst'])))
        elif pr == 'udp' and 'sport' in x:
            parts.append('UDP {}→{} "{}"'.format(x['sport'], x['dport'], w._txt(x['data'][:24])))
        elif pr == 'icmpv6' and 'type' in x:
            parts.append('ICMPv6 {}/{}'.format(x['type'], x['code']))
        elif pr == 'rpl':
            parts.append('RPL ' + RPL_NAMES.get(x['code'], '?').split('（')[0])
        elif pr == 'data':
            parts.append('資料 "{}"'.format(w._txt(x['data'][:24])))
    return ' | '.join(parts) + ('' if w.ok(d) else ' [有錯誤]')
