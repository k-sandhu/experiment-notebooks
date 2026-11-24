import sys
from json import JSONDecoder
from heapq import nsmallest


def main():
    sys.set_int_max_str_digits(0)

    decode = JSONDecoder().decode
    accounts = {}
    channels = {}
    account_get = accounts.get
    channel_get = channels.get

    with open(
        sys.argv[1],
        "r",
        encoding="utf-8",
        buffering=1024 * 1024,
        newline="\n",
    ) as source:
        rates = decode(next(source))["rates"]

        for line in source:
            transaction = decode(line)
            kind = transaction["type"]
            if kind == "void" or "test" in transaction["tags"]:
                continue

            whole, _, fraction = transaction["amount"].partition(".")
            hundredths = int(whole + fraction)
            if len(fraction) != 2:
                hundredths *= 10 if fraction else 100

            value = (
                hundredths * rates[transaction["currency"]]
            ) // 1_000_000
            if kind == "debit":
                value = -value

            account = transaction["account"]
            accounts[account] = account_get(account, 0) + value

            channel = transaction["meta"]["channel"]
            totals = channel_get(channel)
            if totals is None:
                channels[channel] = [1, value]
            else:
                totals[0] += 1
                totals[1] += value

    counted = sum(totals[0] for totals in channels.values())
    net = sum(totals[1] for totals in channels.values())
    output = [f"counted {counted}", f"net {net}"]

    for channel in sorted(channels):
        count, value = channels[channel]
        output.append(f"channel {channel} {count} {value}")

    top_accounts = nsmallest(
        10,
        accounts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    for account, value in top_accounts:
        output.append(f"account {account} {value}")

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
