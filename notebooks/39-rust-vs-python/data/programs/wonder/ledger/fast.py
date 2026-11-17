import json
import sys

import numpy as np


def _group_sum(inv: np.ndarray, vals: np.ndarray, k: int) -> np.ndarray:
    """Exact int64 sum of vals grouped by inv (values in [0, k)), via sort + cumsum."""
    order = np.argsort(inv, kind="stable")
    sorted_inv = inv[order]
    csum = np.cumsum(vals[order])
    ends = np.flatnonzero(np.diff(sorted_inv))
    seg_ends = np.append(ends, len(vals) - 1)
    totals = csum[seg_ends]
    sums = np.empty(k, dtype=np.int64)
    sums[0] = totals[0]
    if k > 1:
        sums[1:] = totals[1:] - totals[:-1]
    return sums


def main() -> None:
    with open(sys.argv[1], "rb") as f:
        lines = f.read().decode("utf-8").split("\n")

    rates = json.loads(lines[0])["rates"]
    decode = json.JSONDecoder().decode

    hundredths = []
    rate_col = []
    sign_col = []
    chan_idx_col = []
    acc_idx_col = []
    add_h = hundredths.append
    add_r = rate_col.append
    add_s = sign_col.append
    add_ci = chan_idx_col.append
    add_ai = acc_idx_col.append

    chan_names: list[str] = []
    chan_index: dict[str, int] = {}
    acc_names: list[str] = []
    acc_index: dict[str, int] = {}

    for line in lines[1:]:
        if not line:
            continue
        tx = decode(line)
        kind = tx["type"]
        if kind == "void" or "test" in tx["tags"]:
            continue

        amount = tx["amount"]
        dot = amount.find(".")
        if dot < 0:
            add_h(int(amount) * 100)
        else:
            frac = amount[dot + 1:]
            add_h(int(amount[:dot]) * 100 + int(frac) * (10 if len(frac) == 1 else 1))
        add_r(rates[tx["currency"]])
        add_s(-1 if kind == "debit" else 1)

        channel = tx["meta"]["channel"]
        ci = chan_index.get(channel)
        if ci is None:
            ci = len(chan_names)
            chan_index[channel] = ci
            chan_names.append(channel)
        add_ci(ci)

        account = tx["account"]
        ai = acc_index.get(account)
        if ai is None:
            ai = len(acc_names)
            acc_index[account] = ai
            acc_names.append(account)
        add_ai(ai)

    n = len(hundredths)
    if n == 0:
        sys.stdout.buffer.write(b"counted 0\nnet 0\n")
        return

    h = np.array(hundredths, dtype=np.int64)
    r = np.array(rate_col, dtype=np.int64)
    s = np.array(sign_col, dtype=np.int64)
    usd = (h * r // 1_000_000) * s

    out = [f"counted {n}", f"net {int(usd.sum())}"]

    ci_arr = np.array(chan_idx_col, dtype=np.int64)
    chan_count = np.bincount(ci_arr, minlength=len(chan_names))
    chan_net = _group_sum(ci_arr, usd, len(chan_names))
    for i in sorted(range(len(chan_names)), key=chan_names.__getitem__):
        out.append(f"channel {chan_names[i]} {int(chan_count[i])} {int(chan_net[i])}")

    ai_arr = np.array(acc_idx_col, dtype=np.int64)
    acc_net = _group_sum(ai_arr, usd, len(acc_names))
    # Top 10 by net descending, then account id ascending: sort ids ascending
    # first, then take a stable argsort by net descending over that order.
    by_id = sorted(range(len(acc_names)), key=acc_names.__getitem__)
    by_id_arr = np.array(by_id, dtype=np.int64)
    order = by_id_arr[np.argsort(-acc_net[by_id_arr], kind="stable")[:10]]
    for i in order:
        out.append(f"account {acc_names[i]} {int(acc_net[i])}")

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
