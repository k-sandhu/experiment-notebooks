import sys
import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        h, w, steps = map(int, f.readline().split())
        raw = b''.join(f.readline().strip() for _ in range(h))
    chars = np.frombuffer(raw, dtype=np.uint8).reshape(h, w)
    is_open = chars == ord('.')
    wall = np.ones((h + 2, w + 2), dtype=np.int32)
    wall[1:-1, 1:-1] = chars == ord('#')
    weight = 4 + wall[:-2, 1:-1] + wall[2:, 1:-1] + wall[1:-1, :-2] + wall[1:-1, 2:]
    a = np.zeros((h + 2, w + 2), dtype=np.int32)
    center = a[1:-1, 1:-1]
    source = (chars >= ord('1')) & (chars <= ord('9'))
    center[source] = (chars[source].astype(np.int32) - ord('0')) * 1000
    b = a.copy()
    temp = np.empty((h, w), dtype=np.int32)
    for _ in range(steps):
        center = a[1:-1, 1:-1]
        np.multiply(center, weight, out=temp)
        np.add(temp, a[:-2, 1:-1], out=temp)
        np.add(temp, a[2:, 1:-1], out=temp)
        np.add(temp, a[1:-1, :-2], out=temp)
        np.add(temp, a[1:-1, 2:], out=temp)
        np.right_shift(temp, 3, out=temp)
        np.copyto(b[1:-1, 1:-1], temp, where=is_open)
        a, b = b, a
    values = a[1:-1, 1:-1]
    open_values = values[is_open]
    total = int(open_values.sum(dtype=np.int64))
    max_value = int(open_values.max())
    max_index = int(np.flatnonzero(is_open & (values == max_value))[0])
    indices = np.flatnonzero(is_open).astype(np.int64) + 1
    checksum = int(np.dot(open_values.astype(np.int64), indices))
    sys.stdout.buffer.write(f'sum {total}\nmax {max_value} {max_index // w} {max_index % w}\nchecksum {checksum}\n'.encode())


if __name__ == '__main__':
    main()
