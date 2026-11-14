"""Streaming ledger aggregation using only the Python standard library."""

import heapq
import json
import sys


# Unknown fields may be nested more deeply than the C decoder's recursion limit.
# This path is only used after RecursionError; it decodes the shallow required
# fields and skips extra values with an iterative structural scan.
def selected_object(text, start, fields, scan, whitespace):
    import re

    tokens = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"|[{}\[\]]')
    primitive = re.compile(r'[^\s,\]}]+')

    def skip(index):
        char = text[index]
        if char == '"':
            return tokens.match(text, index).end()
        if char not in "[{":
            return primitive.match(text, index).end()
        depth = 0
        for token in tokens.finditer(text, index):
            char = text[token.start()]
            if char == '"':
                continue
            if char in "[{":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    return token.end()
        raise ValueError("unterminated JSON value")

    index = start + 1
    result = {}
    while True:
        index = whitespace(text, index).end()
        if text[index] == "}":
            return result, index + 1
        key, index = scan(text, index)
        index = whitespace(text, index).end() + 1  # colon
        index = whitespace(text, index).end()
        if key in fields:
            nested = fields[key]
            if nested is None:
                result[key], index = scan(text, index)
            else:
                result[key], index = selected_object(text, index, nested, scan, whitespace)
        else:
            index = skip(index)
        index = whitespace(text, index).end()
        if text[index] == "}":
            return result, index + 1
        index += 1  # comma


TRANSACTION_FIELDS = dict.fromkeys(("account", "type", "amount", "currency", "tags"))
TRANSACTION_FIELDS["meta"] = {"channel": None}


def main(path):
    accounts = {}
    channels = {}
    account_get = accounts.get
    channel_get = channels.get
    # Text buffering decodes UTF-8 in blocks rather than once per transaction.
    scan = json.JSONDecoder().scan_once
    whitespace = json.decoder.WHITESPACE.match
    with open(path, "r", encoding="utf-8", buffering=1024 * 1024, newline="\n") as source:
        header = next(source)
        try:
            rates = json.loads(header)["rates"]
        except RecursionError:
            start = whitespace(header, 0).end()
            rates = selected_object(header, start, {"rates": None}, scan, whitespace)[0]["rates"]
        for line in source:
            start = 0 if line[0] == "{" else whitespace(line, 0).end()
            try:
                transaction = scan(line, start)[0]
            except RecursionError:
                transaction = selected_object(line, start, TRANSACTION_FIELDS, scan, whitespace)[0]
            kind = transaction["type"]
            if kind == "void" or "test" in transaction["tags"]:
                continue

            whole, dot, fraction = transaction["amount"].partition(".")
            hundredths = int(whole) * 100
            if dot:
                hundredths += int(fraction) * (10 if len(fraction) == 1 else 1)
            value = hundredths * rates[transaction["currency"]] // 1_000_000
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
    output.extend(
        f"channel {name} {channels[name][0]} {channels[name][1]}"
        for name in sorted(channels)
    )
    best = heapq.nsmallest(10, accounts.items(), key=lambda item: (-item[1], item[0]))
    output.extend(f"account {account} {value}" for account, value in best)
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    sys.set_int_max_str_digits(0)
    sys.stdout.reconfigure(newline="\n")
    main(sys.argv[1])
