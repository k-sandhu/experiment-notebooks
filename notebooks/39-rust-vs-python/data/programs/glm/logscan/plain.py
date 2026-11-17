"""Log scan, plain Python 3 (standard library only)."""

import re
import sys

# Same pattern as SPEC.md; status captures only its first digit (the class).
PAT = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+"
    r" (?:GET|PUT|POST|PATCH|DELETE)"
    r" (/[A-Za-z0-9_/-]*)(?:\?[^ ]*)?"
    r" (\d)\d\d \d+B (\d+)\.(\d)ms \"[^\"]*\"",
    re.ASCII,
)


def template(path: str) -> str:
    return "/".join(["{id}" if seg.isdigit() else seg for seg in path.split("/")])


def main() -> None:
    sys.stdout.reconfigure(newline="\n")
    classes = [0] * 10
    paths: dict[str, list[int]] = {}
    lines = ok = 0
    fullmatch = PAT.fullmatch
    with open(sys.argv[1], "r", encoding="ascii", errors="replace", newline="\n") as f:
        for line in f:
            lines += 1
            # Match the line without its trailing newline without copying it.
            m = fullmatch(line, 0, len(line) - 1) if line.endswith("\n") else fullmatch(line)
            if m is not None:
                ok += 1
                classes[int(m.group(2))] += 1
                tpl = template(m.group(1))
                lats = paths.get(tpl)
                if lats is None:
                    paths[tpl] = [int(m.group(3)) * 10 + int(m.group(4))]
                else:
                    lats.append(int(m.group(3)) * 10 + int(m.group(4)))

    w = sys.stdout.write
    w(f"lines {lines}\nmalformed {lines - ok}\n")
    for c, cnt in enumerate(classes):
        if cnt:
            w(f"status {c}xx {cnt}\n")
    top = sorted(paths.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]
    for tpl, lats in top:
        lats.sort()
        n = len(lats)
        p50 = lats[(50 * n + 99) // 100 - 1]
        p95 = lats[(95 * n + 99) // 100 - 1]
        mx = lats[-1]
        w(
            f"path {tpl} {n} {p50 // 10}.{p50 % 10}"
            f" {p95 // 10}.{p95 % 10} {mx // 10}.{mx % 10}\n"
        )


if __name__ == "__main__":
    main()
