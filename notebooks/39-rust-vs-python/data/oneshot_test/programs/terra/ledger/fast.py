import heapq
import json
import sys


def main():
    sys.set_int_max_str_digits(0)
    decode = json.JSONDecoder().decode

    with open(sys.argv[1], "r", encoding="utf-8", buffering=1024 * 1024) as source:
        rates = decode(source.readline())["rates"]
        accounts = {}
        channels = {}
        counted = 0
        net = 0

        for line in source:
            transaction = decode(line)
            kind = transaction["type"]
            if kind == "void" or "test" in transaction["tags"]:
                continue

            amount = transaction["amount"]
            point = amount.find(".")
            if point < 0:
                hundredths = int(amount) * 100
            else:
                whole = int(amount[:point])
                fraction = amount[point + 1:]
                hundredths = whole * 100 + int(fraction) * (10 if len(fraction) == 1 else 1)

            value = hundredths * rates[transaction["currency"]] // 1_000_000
            if kind == "debit":
                value = -value

            counted += 1
            net += value

            account = transaction["account"]
            accounts[account] = accounts.get(account, 0) + value

            channel = transaction["meta"]["channel"]
            totals = channels.get(channel)
            if totals is None:
                channels[channel] = [1, value]
            else:
                totals[0] += 1
                totals[1] += value

    output = [f"counted {counted}", f"net {net}"]
    for channel in sorted(channels):
        count, total = channels[channel]
        output.append(f"channel {channel} {count} {total}")

    top_accounts = heapq.nsmallest(
        10, accounts.items(), key=lambda item: (-item[1], item[0])
    )
    for account, total in top_accounts:
        output.append(f"account {account} {total}")

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
