import heapq
import json
import sys


def main():
    sys.set_int_max_str_digits(0)

    decode = json.JSONDecoder().decode
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
        buffering=1048576,
        newline="\n",
    ) as source:
        rates = decode(next(source))["rates"]

        for line in source:
            transaction = decode(line)
            kind = transaction["type"]

            if kind == "void" or "test" in transaction["tags"]:
                continue

            amount = transaction["amount"]
            dot = amount.find(".")
            if dot < 0:
                hundredths = int(amount) * 100
            else:
                hundredths = int(amount.replace(".", ""))
                if len(amount) - dot == 2:
                    hundredths *= 10

            value = hundredths * rates[transaction["currency"]] // 1000000
            if kind == "debit":
                value = -value

            counted += 1
            net += value

            account = transaction["account"]
            accounts[account] = account_get(account, 0) + value

            channel = transaction["meta"]["channel"]
            totals = channel_get(channel)
            if totals is None:
                channels[channel] = [1, value]
            else:
                totals[0] += 1
                totals[1] += value

    output = [f"counted {counted}", f"net {net}"]

    for channel in sorted(channels):
        count, total = channels[channel]
        output.append(f"channel {channel} {count} {total}")

    best_accounts = heapq.nsmallest(
        10, accounts.items(), key=lambda item: (-item[1], item[0])
    )
    for account, total in best_accounts:
        output.append(f"account {account} {total}")

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
