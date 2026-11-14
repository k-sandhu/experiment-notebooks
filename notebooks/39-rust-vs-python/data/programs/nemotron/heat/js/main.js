"use strict";

const fs = require("fs");

function main() {
    const data = fs.readFileSync(process.argv[2]);
    const n = data.length;
    let pos = 0;

    const readInt = () => {
        while (pos < n && data[pos] <= 32) {
            pos++;
        }
        let sign = 1;
        if (pos < n && data[pos] === 45) { // '-'
            sign = -1;
            pos++;
        }
        let v = 0;
        while (pos < n && data[pos] > 32) {
            v = v * 10 + (data[pos] - 48);
            pos++;
        }
        return sign * v;
    };

    const H = readInt();
    const W = readInt();
    const S = readInt();

    const N = H * W;
    const grid = new Uint8Array(N);
    let gi = 0;
    while (gi < N) {
        const b = data[pos++];
        if (b > 32) {
            grid[gi++] = b;
        }
    }

    let cur = new Int32Array(N);
    let nxt = new Int32Array(N);
    // For each open cell: self, up, down, left, right neighbour indices.
    const nb = new Int32Array(N * 5);
    let count = 0;

    for (let r = 0; r < H; r++) {
        const base = r * W;
        for (let c = 0; c < W; c++) {
            const i = base + c;
            const b = grid[i];
            if (b === 46) { // '.'
                const p = count * 5;
                nb[p] = i;
                nb[p + 1] = (r > 0 && grid[i - W] !== 35) ? i - W : i;
                nb[p + 2] = (r + 1 < H && grid[i + W] !== 35) ? i + W : i;
                nb[p + 3] = (c > 0 && grid[i - 1] !== 35) ? i - 1 : i;
                nb[p + 4] = (c + 1 < W && grid[i + 1] !== 35) ? i + 1 : i;
                count++;
            } else if (b >= 49 && b <= 57) { // '1'..'9'
                const v = 1000 * (b - 48);
                cur[i] = v;
                nxt[i] = v;
            }
        }
    }

    for (let step = 0; step < S; step++) {
        for (let k = 0; k < count; k++) {
            const p = k * 5;
            const i = nb[p];
            let v = cur[i];
            let s = 4 * v + cur[nb[p + 1]] + cur[nb[p + 2]] +
                    cur[nb[p + 3]] + cur[nb[p + 4]];
            nxt[i] = s >> 3; // all values non-negative
        }
        const tmp = cur;
        cur = nxt;
        nxt = tmp;
    }

    let total = 0;
    let checksum = 0;
    let bestV = -1;
    let bestR = 0;
    let bestC = 0;
    for (let k = 0; k < count; k++) {
        const p = k * 5;
        const i = nb[p];
        const v = cur[i];
        total += v;
        if (v > bestV) {
            bestV = v;
            bestR = (i / W) | 0;
            bestC = i % W;
        }
        checksum += v * (i + 1);
    }

    process.stdout.write(
        "sum " + total + "\n" +
        "max " + bestV + " " + bestR + " " + bestC + "\n" +
        "checksum " + checksum + "\n"
    );
}

main();
