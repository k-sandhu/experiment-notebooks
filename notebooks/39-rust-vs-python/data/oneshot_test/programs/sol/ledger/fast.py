import sys
import json
from heapq import nsmallest


def main():
    sys.set_int_max_str_digits(0)

    decoder = json.JSONDecoder()
    scan = decoder.scan_once

    accounts = {}
    channels = {}
    account_get = accounts.get
    channel_get = channels.get

    with open(
        sys.argv[1], "r", encoding="utf-8", buffering=1024 * 1024
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

            account = transaction["account"]
            accounts[account] = account_get(account, 0) + value

            channel = transaction["meta"]["channel"]
            stats = channel_get(channel)
            if stats is None:
                channels[channel] = [1, value]
            else:
                stats[0] += 1
                stats[1] += value

    counted = sum(stats[0] for stats in channels.values())
    net = sum(stats[1] for stats in channels.values())
    output = [f"counted {counted}", f"net {net}"]

    for channel in sorted(channels):
        count, value = channels[channel]
        output.append(f"channel {channel} {count} {value}")

    top_accounts = nsmallest(
        10, accounts.items(), key=lambda item: (-item[1], item[0])
    )
    for account, value in top_accounts:
        output.append(f"account {account} {value}")

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
