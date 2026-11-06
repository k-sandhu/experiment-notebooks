"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const dlen = data.length;
let pos = 0;

function readInt() {
    while (pos < dlen && data[pos] <= 32) pos++;
    let x = 0;
    while (pos < dlen && data[pos] >= 48 && data[pos] <= 57) {
        x = x * 10 + (data[pos] - 48);
        pos++;
    }
    return x;
}

const map = new Int32Array(256).fill(-1);
while (pos < dlen && data[pos] <= 32) pos++;
const astart = pos;
while (pos < dlen && data[pos] > 32) pos++;
const A = pos - astart;
for (let i = 0; i < A; i++) map[data[astart + i]] = i;

const insC = new Int32Array(A);
const delC = new Int32Array(A);
const subC = new Int32Array(A * A);
for (let i = 0; i < A; i++) insC[i] = readInt();
for (let i = 0; i < A; i++) delC[i] = readInt();
for (let i = 0; i < A * A; i++) subC[i] = readInt();

const P = readInt();

let sIdx = new Uint8Array(4096);
let tIdx = new Uint8Array(4096);
let insT = new Int32Array(4096);
let prev = new Int32Array(4097);
let cur = new Int32Array(4097);

const outLines = new Array(P + 1);
let total = 0;

for (let q = 0; q < P; q++) {
    while (pos < dlen && data[pos] <= 32) pos++;
    const s0 = pos;
    while (pos < dlen && data[pos] > 32) pos++;
    const n = pos - s0;
    if (n > sIdx.length) {
        sIdx = new Uint8Array(n);
        tIdx = new Uint8Array(n);
        insT = new Int32Array(n);
        prev = new Int32Array(n + 1);
        cur = new Int32Array(n + 1);
    }
    for (let i = 0; i < n; i++) sIdx[i] = map[data[s0 + i]];

    while (pos < dlen && data[pos] <= 32) pos++;
    const t0 = pos;
    while (pos < dlen && data[pos] > 32) pos++;
    const m = pos - t0;
    if (m > tIdx.length) {
        tIdx = new Uint8Array(m);
        insT = new Int32Array(m);
        if (m + 1 > prev.length) {
            prev = new Int32Array(m + 1);
            cur = new Int32Array(m + 1);
        }
    }
    for (let j = 0; j < m; j++) {
        const c = map[data[t0 + j]];
        tIdx[j] = c;
        insT[j] = insC[c];
    }

    prev[0] = 0;
    for (let j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j - 1];

    let pr = prev;
    let cu = cur;

    for (let i = 1; i <= n; i++) {
        const c = sIdx[i - 1];
        const d = delC[c];
        const sr = c * A;
        let v = pr[0] + d;
        cu[0] = v;
        for (let j = 1; j <= m; j++) {
            const best0 = pr[j] + d;
            let best = v + insT[j - 1];
            if (best0 < best) best = best0;
            const x = pr[j - 1] + subC[sr + tIdx[j - 1]];
            if (x < best) best = x;
            v = best;
            cu[j] = best;
        }
        const tmp = pr;
        pr = cu;
        cu = tmp;
    }

    prev = pr;
    cur = cu;
    const cost = pr[m];
    total += cost;
    outLines[q] = String(cost);
}

outLines[P] = "total " + total;
process.stdout.write(outLines.join("\n") + "\n");
