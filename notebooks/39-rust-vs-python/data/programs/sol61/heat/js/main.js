"use strict";

const fs = require("node:fs");
const input = fs.readFileSync(process.argv[2]);
let pos = 0;
function number() {
    while (input[pos] <= 32) ++pos;
    let value = 0;
    while (pos < input.length && input[pos] >= 48 && input[pos] <= 57)
        value = value * 10 + input[pos++] - 48;
    return value;
}

const h = number(), w = number(), steps = number();
const stride = w + 2, size = (h + 2) * stride;
const begin = stride, end = (h + 1) * stride;
const grid = new Uint8Array(size).fill(35);
// Cell values never exceed the hottest source, 9000.
let a = new Int16Array(size), b = new Int16Array(size);
const weight = new Uint8Array(size);
let openCount = 0, hasSource = false;
for (let r = 1; r <= h; ++r) {
    while (pos < input.length && input[pos] <= 32) ++pos;
    for (let c = 1; c <= w; ++c) {
        const i = r * stride + c, ch = input[pos++];
        grid[i] = ch;
        if (ch === 46) ++openCount;
        if (ch >= 49 && ch <= 57) {
            a[i] = b[i] = (ch - 48) * 1000;
            hasSource = true;
        }
    }
}
const sparse = openCount < Math.floor((end - begin) / 4);
const indices = new Int32Array(sparse ? openCount : end - begin - openCount);
let count = 0;
for (let i = begin; i < end; ++i) {
    if (grid[i] === 46) {
        weight[i] = 4 + (grid[i - stride] === 35) + (grid[i + stride] === 35)
                      + (grid[i - 1] === 35) + (grid[i + 1] === 35);
        if (sparse) indices[count++] = i;
    } else if (!sparse) indices[count++] = i;
}

function simulate(a, b, weight, indices, sparse, stride, begin, end, steps) {
    let aBytes = Buffer.from(a.buffer), bBytes = Buffer.from(b.buffer);
    for (let step = 0; step < steps; ++step) {
        if (sparse) {
            for (let k = 0; k < indices.length; ++k) {
                const i = indices[k];
                b[i] = (Math.imul(weight[i], a[i]) + a[i - stride] + a[i + stride]
                        + a[i - 1] + a[i + 1]) >>> 3;
            }
        } else {
            let left = a[begin - 1], center = a[begin];
            for (let i = begin; i < end; ++i) {
                const right = a[i + 1];
                b[i] = (Math.imul(weight[i], center) + a[i - stride] + a[i + stride]
                        + left + right) >>> 3;
                left = center;
                center = right;
            }
            for (let k = 0; k < indices.length; ++k) {
                const i = indices[k];
                b[i] = a[i];
            }
        }
        const stable = (step & 63) === 63 && aBytes.equals(bBytes);
        let temp = a; a = b; b = temp;
        temp = aBytes; aBytes = bBytes; bBytes = temp;
        if (stable) break;
    }
    return a;
}
if (hasSource) a = simulate(a, b, weight, indices, sparse, stride, begin, end, steps);

// Flush exact Number subtotals before they approach Number's integer limit.
// The usual benchmark never needs a flush; BigInt preserves full 64-bit output.
const flushLimit = 2 ** 52;
let total = 0, checksum = 0, totalHigh = 0n, checksumHigh = 0n;
let best = -1, bestR = 0, bestC = 0;
for (let r = 0; r < h; ++r) {
    for (let c = 0; c < w; ++c) {
        const i = (r + 1) * stride + c + 1;
        if (grid[i] !== 46) continue;
        const value = a[i];
        total += value;
        checksum += value * (r * w + c + 1);
        if (total >= flushLimit) { totalHigh += BigInt(total); total = 0; }
        if (checksum >= flushLimit) { checksumHigh += BigInt(checksum); checksum = 0; }
        if (value > best) { best = value; bestR = r; bestC = c; }
    }
}
process.stdout.write(`sum ${totalHigh + BigInt(total)}\nmax ${best} ${bestR} ${bestC}\nchecksum ${checksumHigh + BigInt(checksum)}\n`);
