import heapq
import re
import sys


def main():
    sys.set_int_max_str_digits(0)

    match_line = re.compile(
        rb'[0-9]{4}-[0-9]{2}-[0-9]{2}T'
        rb'[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z '
        rb'[a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) '
        rb'(/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? '
        rb'([0-9])[0-9]{2} [0-9]+B '
        rb'([0-9]+)\.([0-9])ms "[^"]*"\n'
    ).fullmatch
    normalize_path = re.compile(rb'/[0-9]+(?=/|$)').sub

    statuses = [0] * 10
    paths = {}
    cache = {}
    paths_get = paths.get
    cache_get = cache.get
    malformed = 0
    line_count = 0

    with open(sys.argv[1], "rb", buffering=1024 * 1024) as source:
        for line_count, line in enumerate(source, 1):
            match = match_line(line)
            if match is None:
                malformed += 1
                continue

            path, status, whole, fraction = match.group(1, 2, 3, 4)
            statuses[status[0] - 48] += 1
            latency = int(whole) * 10 + fraction[0] - 48

            values = cache_get(path)
            if values is None:
                template = normalize_path(b'/{id}', path)
                values = paths_get(template)
                if values is None:
                    values = []
                    paths[template] = values

                if len(cache) >= 16384:
                    cache.clear()
                cache[path] = values

            values.append(latency)

    output = [
        f"lines {line_count}",
        f"malformed {malformed}",
    ]
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
