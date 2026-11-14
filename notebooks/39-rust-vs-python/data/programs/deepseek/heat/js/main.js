"use strict";

const fs = require("fs");

const buf = fs.readFileSync(process.argv[2]);
const len = buf.length;
let pos = 0;

function readInt() {
    while (pos < len && buf[pos] <= 32) pos++;
    let x = 0;
    while (pos < len && buf[pos] >= 48 && buf[pos] <= 57) {
        x = x * 10 + (buf[pos] - 48);
        pos++;
    }
    return x;
}

const H = readInt();
const W = readInt();
const S = readInt();
while (pos < len && buf[pos] !== 10) pos++;
if (pos < len) pos++;

const W2 = W + 2;
const N = (H + 2) * W2;
let cur = new Int32Array(N);
let nxt = new Int32Array(N);
const kind = new Uint8Array(N); // 0 wall, 1 open, 2 source
const open = new Int32Array(H * W);
let nOpen = 0;

for (let r = 0; r < H; r++) {
    const rowStart = pos;
    const base = (r + 1) * W2 + 1;
    for (let c = 0; c < W; c++) {
        const ch = buf[rowStart + c];
        const idx = base + c;
        if (ch === 46) { // '.'
            kind[idx] = 1;
            open[nOpen++] = idx;
        } else if (ch >= 49 && ch <= 57) { // '1'..'9'
            kind[idx] = 2;
            const v = (ch - 48) * 1000;
            cur[idx] = v;
            nxt[idx] = v;
        }
    }
    pos += W;
    while (pos < len && buf[pos] !== 10) pos++;
    if (pos < len) pos++;
}

const coef = new Uint8Array(nOpen);
for (let j = 0; j < nOpen; j++) {
    const i = open[j];
    const a = kind[i - W2] !== 0 ? 1 : 0;
    const b = kind[i + W2] !== 0 ? 1 : 0;
    const l = kind[i - 1] !== 0 ? 1 : 0;
    const r = kind[i + 1] !== 0 ? 1 : 0;
    coef[j] = 4 + (1 - a) + (1 - b) + (1 - l) + (1 - r);
}

for (let s = 0; s < S; s++) {
    for (let j = 0; j < nOpen; j++) {
        const i = open[j];
        nxt[i] = (coef[j] * cur[i]
                + cur[i - W2] + cur[i + W2] + cur[i - 1] + cur[i + 1]) >> 3;
    }
    const tmp = cur; cur = nxt; nxt = tmp;
}

let sum = 0n;
let chk = 0n;
let maxv = -1;
let bestR = 0, bestC = 0;
for (let j = 0; j < nOpen; j++) {
    const i = open[j];
    const v = cur[i];
    const r = (i / W2 | 0) - 1;
    const col = (i % W2) - 1;
    sum += BigInt(v);
    chk += BigInt(v) * BigInt(r * W + col + 1);
    if (v > maxv) { maxv = v; bestR = r; bestC = col; }
}

process.stdout.write("sum " + sum + "\nmax " + maxv + " " + bestR + " " + bestC + "\nchecksum " + chk + "\n");
