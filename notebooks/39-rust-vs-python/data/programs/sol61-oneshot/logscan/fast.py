import heapq
import re
import sys


def main():
    sys.set_int_max_str_digits(0)

    with open(sys.argv[1], "rb") as f:
        data = f.read()

    line_count = data.count(b"\n")

    records = re.compile(
        rb"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
        rb"[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z "
        rb"[a-z]+-[0-9]+ "
        rb"(?:GET|POST|PUT|DELETE|PATCH) "
        rb"(/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? "
        rb"([0-9])[0-9]{2} [0-9]+B "
        rb"([0-9]+)\.([0-9])ms "
        rb'"[^"\n]*"$',
        re.MULTILINE,
    )
    template_sub = re.compile(rb"/[0-9]+(?=/|$)").sub

    statuses = [0] * 10
    paths = {}
    get_path = paths.get

    match = None
    for match in records.finditer(data):
        path, status, whole, fractional = match.groups()
        statuses[status[0] - 48] += 1
        latency = int(whole) * 10 + fractional[0] - 48
        template = template_sub(b"/{id}", path)

        values = get_path(template)
        if values is None:
            paths[template] = [latency]
        else:
            values.append(latency)

    match = None
    del data

    busiest = heapq.nsmallest(
        10,
        paths.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )

    output = [
        f"lines {line_count}",
        f"malformed {line_count - sum(statuses)}",
    ]
    for cls, count in enumerate(statuses):
        if count:
            output.append(f"status {cls}xx {count}")

    np = None

    def milliseconds(value):
        return f"{value // 10}.{value % 10}"

    for template, values in busiest:
        n = len(values)
        k50 = (n - 1) // 2
        k95 = (95 * n - 1) // 100

        array = None
        if n >= 4096:
            if np is None:
                import numpy as np
            try:
                array = np.asarray(values, dtype=np.int64)
            except OverflowError:
                pass

        if array is None:
            values.sort()
            p50 = values[k50]
            p95 = values[k95]
            maximum = values[-1]
        else:
            array.partition((k50, k95, n - 1))
            p50 = int(array[k50])
            p95 = int(array[k95])
            maximum = int(array[-1])
            del array

        output.append(
            f"path {template.decode('ascii')} {n} "
            f"{milliseconds(p50)} {milliseconds(p95)} "
            f"{milliseconds(maximum)}"
        )

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
