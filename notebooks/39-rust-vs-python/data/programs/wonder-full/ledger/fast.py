import sys
import json

import numpy as np

FLUSH_AT = 100_000


def main():
    path = sys.argv[1]
    loads = json.loads
    counted = 0
    net = 0
    chan_count: dict[str, int] = {}
    chan_net: dict[str, int] = {}
    accounts: dict[str, int] = {}

    # Text mode (split only on '\n') plus raw_decode avoids json.loads'
    # per-call encoding detection and bytes->str copy for every line.
    raw_decode = json.JSONDecoder().raw_decode
    with open(path, "r", encoding="utf-8-sig", newline="\n") as f:
        first = f.readline()
        if not first:
            sys.stdout.write("counted 0\nnet 0\n")
            return
        rates: dict[str, int] = loads(first)["rates"]

        acc_l: list[str] = []
        chan_l: list[str] = []
        amt_l: list[str] = []
        cur_l: list[str] = []
        sgn_l: list[int] = []

        def flush_python():
            # Rare fallback (very long amount strings): exact Python arithmetic.
            nonlocal counted, net
            for acc, chan, s, cur, sgn in zip(acc_l, chan_l, amt_l, cur_l, sgn_l):
                dot = s.find(".")
                if dot < 0:
                    h = int(s) * 100
                elif dot == len(s) - 2:
                    h = int(s[:dot]) * 100 + int(s[dot + 1:]) * 10
                else:
                    h = int(s[:dot]) * 100 + int(s[dot + 1:])
                usd = (h * rates[cur]) // 1000000 * sgn
                counted += 1
                net += usd
                chan_count[chan] = chan_count.get(chan, 0) + 1
                chan_net[chan] = chan_net.get(chan, 0) + usd
                accounts[acc] = accounts.get(acc, 0) + usd

        def flush():
            nonlocal counted, net
            if not acc_l:
                return
            amt_arr = np.array(amt_l)
            width = amt_arr.dtype.itemsize // 4
            if width > 15:
                flush_python()
            else:
                # Amount strings -> hundredths, digit by digit over the
                # fixed-width UCS4 view of the string array.
                m = amt_arr.view(np.uint32).reshape(len(amt_arr), -1)
                val = np.zeros(len(amt_arr), dtype=np.int64)
                frac = np.zeros(len(amt_arr), dtype=np.int64)
                seen_dot = np.zeros(len(amt_arr), dtype=bool)
                for j in range(m.shape[1]):
                    col = m[:, j]
                    is_digit = (col >= 48) & (col <= 57)
                    val = np.where(is_digit, val * 10 + (col.astype(np.int64) - 48), val)
                    frac += is_digit & seen_dot
                    seen_dot |= col == 46
                if int(frac.max(initial=0)) > 2:
                    flush_python()
                else:
                    hundredths = val * np.where(frac == 0, 100, np.where(frac == 1, 10, 1))
                    cur_uniq, cur_inv = np.unique(np.array(cur_l), return_inverse=True)
                    rate_of = np.array([rates[c] for c in cur_uniq.tolist()], dtype=np.int64)
                    signed = (hundredths * rate_of[cur_inv]) // 1000000 * np.array(sgn_l, dtype=np.int64)
                    counted += len(signed)
                    net += int(signed.sum())

                    ch_uniq, ch_inv, ch_cnts = np.unique(
                        np.array(chan_l), return_inverse=True, return_counts=True
                    )
                    ch_sums = np.zeros(len(ch_uniq), dtype=np.int64)
                    np.add.at(ch_sums, ch_inv, signed)
                    for name, c, s in zip(ch_uniq.tolist(), ch_cnts.tolist(), ch_sums.tolist()):
                        chan_count[name] = chan_count.get(name, 0) + c
                        chan_net[name] = chan_net.get(name, 0) + s

                    ac_uniq, ac_inv = np.unique(np.array(acc_l), return_inverse=True)
                    ac_sums = np.zeros(len(ac_uniq), dtype=np.int64)
                    np.add.at(ac_sums, ac_inv, signed)
                    for name, s in zip(ac_uniq.tolist(), ac_sums.tolist()):
                        accounts[name] = accounts.get(name, 0) + s
            acc_l.clear()
            chan_l.clear()
            amt_l.clear()
            cur_l.clear()
            sgn_l.clear()

        acc_append = acc_l.append
        chan_append = chan_l.append
        amt_append = amt_l.append
        cur_append = cur_l.append
        sgn_append = sgn_l.append
        for line in f:
            if line[0] == "{":
                d = raw_decode(line)[0]
            elif not line.strip():
                continue
            else:
                # raw_decode doesn't skip leading whitespace; loads does.
                d = loads(line)
            ty = d["type"]
            if ty == "void":
                continue
            if "test" in d["tags"]:
                continue
            acc_append(d["account"])
            chan_append(d["meta"]["channel"])
            amt_append(d["amount"])
            cur_append(d["currency"])
            sgn_append(-1 if ty == "debit" else 1)
            if len(acc_l) >= FLUSH_AT:
                flush()
        flush()

    out = [f"counted {counted}", f"net {net}"]
    # str order == UTF-8 byte order for valid Unicode strings.
    for ch in sorted(chan_count):
        out.append(f"channel {ch} {chan_count[ch]} {chan_net[ch]}")
    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for acc, v in top:
        out.append(f"account {acc} {v}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
