import heapq
import json
import sys


def main():
    sys.set_int_max_str_digits(0)
    loads = json.loads

    with open(sys.argv[1], "r", encoding="utf-8", buffering=1024 * 1024) as f:
        rates = loads(next(f))["rates"]
        accounts = {}
        channels = {}
        count = 0
        net = 0

        for line in f:
            transaction = loads(line)
            kind = transaction["type"]
            if kind == "void" or "test" in transaction["tags"]:
                continue

            amount = transaction["amount"]
            dot = amount.find(".")
            if dot < 0:
                hundredths = int(amount) * 100
            else:
                fraction = amount[dot + 1:]
                hundredths = int(amount[:dot]) * 100 + int(fraction) * (
                    10 if len(fraction) == 1 else 1
                )

            value = hundredths * rates[transaction["currency"]] // 1000000
            if kind == "debit":
                value = -value

            count += 1
            net += value

            account = transaction["account"]
            accounts[account] = accounts.get(account, 0) + value

            channel = transaction["meta"]["channel"]
            stats = channels.get(channel)
            if stats is None:
                channels[channel] = [1, value]
            else:
                stats[0] += 1
                stats[1] += value

    output = [f"counted {count}", f"net {net}"]
    for channel in sorted(channels):
        channel_count, channel_net = channels[channel]
        output.append(f"channel {channel} {channel_count} {channel_net}")

    top_accounts = heapq.nsmallest(
        10, accounts.items(), key=lambda item: (-item[1], item[0])
    )
    for account, account_net in top_accounts:
        output.append(f"account {account} {account_net}")

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
