import sys
from json import loads
from collections import defaultdict


def main():
    path = sys.argv[1]

    counted = 0
    net = 0
    ch_net = defaultdict(int)
    ch_cnt = defaultdict(int)
    acc_net = defaultdict(int)

    with open(path, 'r', encoding='utf-8', newline='\n') as f:
        rates = loads(f.readline())['rates']

        for line in f:
            t = loads(line)
            typ = t['type']
            if typ == 'void':
                continue
            if 'test' in t['tags']:
                continue

            amt = t['amount']
            ip, dot, fp = amt.partition('.')
            h = int(ip) * 100
            if dot:
                h += int(fp.ljust(2, '0'))

            usd = (h * rates[t['currency']]) // 1000000
            if typ == 'debit':
                usd = -usd

            counted += 1
            net += usd
            ch = t['meta']['channel']
            ch_net[ch] += usd
            ch_cnt[ch] += 1
            acc_net[t['account']] += usd

    out = ["counted %d" % counted, "net %d" % net]
    for ch in sorted(ch_net):
        out.append("channel %s %d %d" % (ch, ch_cnt[ch], ch_net[ch]))
    top = sorted(acc_net.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for a, v in top:
        out.append("account %s %d" % (a, v))

    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
