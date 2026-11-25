import sys
import re
import heapq
from collections import defaultdict


def main():
    sys.set_int_max_str_digits(0)

    with open(sys.argv[1], "rb") as file:
        data = file.read()

    line_count = data.count(b"\n")

    pattern = re.compile(
        rb"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
        rb"[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z "
        rb"[a-z]+-[0-9]+ "
        rb"(?:GET|POST|PUT|DELETE|PATCH) "
        rb"(/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? "
        rb"([0-9])[0-9]{2} [0-9]+B "
        rb"([0-9]+)\.([0-9])ms "
        rb'"[^"\n]*"\n',
        re.MULTILINE,
    )
    substitute = re.compile(rb"/[0-9]+(?=/|$)").sub

    statuses = [0] * 10
    paths = defaultdict(list)

    for match in pattern.finditer(data):
        path, status, whole, fraction = match.groups()
        statuses[status[0] - 48] += 1
        template = substitute(b"/{id}", path)
        paths[template].append(int(whole) * 10 + fraction[0] - 48)

    output = [
        f"lines {line_count}",
        f"malformed {line_count - sum(statuses)}",
    ]

    for status, count in enumerate(statuses):
        if count:
            output.append(f"status {status}xx {count}")

    busiest = heapq.nsmallest(
        10,
        paths.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )

    for template, latencies in busiest:
        count = len(latencies)
        latencies.sort()
        p50 = latencies[(count - 1) // 2]
        p95 = latencies[(95 * count - 1) // 100]
        maximum = latencies[-1]
        output.append(
            f"path {template.decode('ascii')} {count} "
            f"{p50 // 10}.{p50 % 10} "
            f"{p95 // 10}.{p95 % 10} "
            f"{maximum // 10}.{maximum % 10}"
        )

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
