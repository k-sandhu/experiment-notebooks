import sys
import json
from heapq import nsmallest


def main():
    sys.set_int_max_str_digits(0)
    scan = json.JSONDecoder().scan_once

    accounts = {}
    channels = {}
    account_get = accounts.get
    channel_get = channels.get
    counted = 0
    net = 0

    with open(
        sys.argv[1],
        "r",
        encoding="utf-8",
        buffering=1024 * 1024,
        newline="\n",
    ) as source:
        rates = scan(source.readline().lstrip(), 0)[0]["rates"]

        for line in source:
            transaction = scan(line.lstrip(), 0)[0]
            kind = transaction["type"]
            if kind == "void" or "test" in transaction["tags"]:
                continue

            amount = transaction["amount"]
            hundredths = int(amount.replace(".", ""))
            if amount[-3:-2] != ".":
                hundredths *= 10 if amount[-2:-1] == "." else 100

            value = hundredths * rates[transaction["currency"]] // 1_000_000
            if kind == "debit":
                value = -value

            counted += 1
            net += value

            account = transaction["account"]
            accounts[account] = account_get(account, 0) + value

            channel = transaction["meta"]["channel"]
            stats = channel_get(channel)
            if stats is None:
                channels[channel] = [1, value]
            else:
                stats[0] += 1
                stats[1] += value

    write = sys.stdout.buffer.write
    write(f"counted {counted}\nnet {net}\n".encode("ascii"))

    for channel in sorted(channels):
        count, total = channels[channel]
        write(f"channel {channel} {count} {total}\n".encode("ascii"))

    top = nsmallest(
        10,
        accounts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    for account, total in top:
        write(f"account {account} {total}\n".encode("ascii"))


if __name__ == "__main__":
    main()
