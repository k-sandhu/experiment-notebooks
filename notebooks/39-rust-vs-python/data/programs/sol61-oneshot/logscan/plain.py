import heapq
import re
import sys


def main():
    sys.set_int_max_str_digits(0)

    match_line = re.compile(
        rb'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z '
        rb'[a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) '
        rb'(/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? '
        rb'(\d)\d{2} \d+B (\d+)\.(\d)ms "[^"]*"\n'
    ).fullmatch
    normalize = re.compile(rb'/[0-9]+(?=/|$)').sub

    paths = {}
    get_path = paths.get
    statuses = [0] * 10
    total = 0
    malformed = 0

    with open(sys.argv[1], "rb", buffering=1024 * 1024) as source:
        for line in source:
            total += 1
            match = match_line(line)
            if match is None:
                malformed += 1
                continue

            path, status, whole, tenth = match.groups()
            statuses[status[0] - 48] += 1
            latency = int(whole) * 10 + tenth[0] - 48
            template = normalize(b'/{id}', path)

            values = get_path(template)
            if values is None:
                paths[template] = [latency]
            else:
                values.append(latency)

    output = [f"lines {total}", f"malformed {malformed}"]
    for status, count in enumerate(statuses):
        if count:
            output.append(f"status {status}xx {count}")

    busiest = heapq.nsmallest(
        10, paths.items(), key=lambda item: (-len(item[1]), item[0])
    )

    for template, values in busiest:
        values.sort()
        count = len(values)
        p50 = values[(count - 1) // 2]
        p95 = values[(95 * count - 1) // 100]
        maximum = values[-1]
        output.append(
            f"path {template.decode('ascii')} {count} "
            f"{p50 // 10}.{p50 % 10} "
            f"{p95 // 10}.{p95 % 10} "
            f"{maximum // 10}.{maximum % 10}"
        )

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
