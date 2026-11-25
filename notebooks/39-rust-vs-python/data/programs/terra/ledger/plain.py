import sys
import json
import heapq


def main():
    sys.set_int_max_str_digits(0)
    with open(sys.argv[1], 'r', encoding='utf-8', buffering=1024 * 1024) as f:
        rates = json.loads(f.readline())['rates']
        accounts = {}
        channels = {}
        count = net = 0
        loads = json.loads
        for line in f:
            tx = loads(line)
            kind = tx['type']
            if kind == 'void' or 'test' in tx['tags']:
                continue
            amount = tx['amount']
            whole, dot, frac = amount.partition('.')
            cents = int(whole) * 100
            if dot:
                cents += int(frac) * (10 if len(frac) == 1 else 1)
            value = cents * rates[tx['currency']] // 1000000
            if kind == 'debit':
                value = -value
            count += 1
            net += value
            account = tx['account']
            accounts[account] = accounts.get(account, 0) + value
            channel = tx['meta']['channel']
            entry = channels.get(channel)
            if entry is None:
                channels[channel] = [1, value]
            else:
                entry[0] += 1
                entry[1] += value
    lines = [f'counted {count}', f'net {net}']
    lines.extend(f'channel {name} {n} {value}' for name, (n, value) in sorted(channels.items()))
    top = heapq.nsmallest(10, accounts.items(), key=lambda item: (-item[1], item[0]))
    lines.extend(f'account {name} {value}' for name, value in top)
    sys.stdout.buffer.write(('\n'.join(lines) + '\n').encode('ascii'))


if __name__ == '__main__':
    main()
