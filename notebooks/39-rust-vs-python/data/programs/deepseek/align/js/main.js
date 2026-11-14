"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const dlen = data.length;
let pos = 0;

function skipWs() {
    while (pos < dlen && data[pos] <= 32) ++pos;
}

function nextInt() {
    while (pos < dlen && data[pos] <= 32) ++pos;
    let v = 0;
    while (pos < dlen) {
        const c = data[pos];
        if (c < 48 || c > 57) break;
        v = v * 10 + (c - 48);
        ++pos;
    }
    return v;
}

skipWs();
const abStart = pos;
while (pos < dlen && data[pos] > 32) ++pos;
const A = pos - abStart;
const mp = new Int32Array(256);
for (let i = 0; i < A; ++i) mp[data[abStart + i]] = i;

const ins = new Int32Array(A);
const delc = new Int32Array(A);
const sub = new Int32Array(A * A);
for (let i = 0; i < A; ++i) ins[i] = nextInt();
for (let i = 0; i < A; ++i) delc[i] = nextInt();
for (let i = 0; i < A * A; ++i) sub[i] = nextInt();

const P = nextInt();

let sBuf = new Uint8Array(1024);
let tBuf = new Uint8Array(1024);
let tins = new Int32Array(1024);
let row = new Int32Array(1024);

const out = [];
let total = 0;

for (let q = 0; q < P; ++q) {
    skipWs();
    let sl = 0;
    while (pos < dlen && data[pos] > 32) {
        if (sl === sBuf.length) {
            const n = new Uint8Array(sBuf.length * 2);
            n.set(sBuf);
            sBuf = n;
        }
        sBuf[sl++] = mp[data[pos]];
        ++pos;
    }
    skipWs();
    let tl = 0;
    while (pos < dlen && data[pos] > 32) {
        if (tl === tBuf.length) {
            const n = new Uint8Array(tBuf.length * 2);
            n.set(tBuf);
            tBuf = n;
        }
        tBuf[tl++] = mp[data[pos]];
        ++pos;
    }

    const n = sl;
    const m = tl;

    let same = n === m;
    if (same) {
        for (let i = 0; i < n; ++i) {
            if (sBuf[i] !== tBuf[i]) { same = false; break; }
        }
    }
    if (same) {
        out.push("0");
        continue;
    }

    if (tins.length < m) tins = new Int32Array(m * 2 + 1);
    if (row.length < m + 1) row = new Int32Array((m + 1) * 2);

    for (let j = 0; j < m; ++j) tins[j] = ins[tBuf[j]];
    row[0] = 0;
    for (let j = 1; j <= m; ++j) row[j] = row[j - 1] + tins[j - 1];

    for (let i = 0; i < n; ++i) {
        const si = sBuf[i];
        const dc = delc[si];
        const sbase = si * A;

        let diag = row[0];
        let left = diag + dc;
        row[0] = left;

        for (let j = 1; j <= m; ++j) {
            const up = row[j];
            const a = up + dc;
            const b = diag + sub[sbase + tBuf[j - 1]];
            let d = b - a;
            let mn = a + (d & (d >> 31));
            const x = left + tins[j - 1];
            d = x - mn;
            mn = mn + (d & (d >> 31));
            diag = up;
            row[j] = mn;
            left = mn;
        }
    }

    const cost = row[m];
    total += cost;
    out.push(String(cost));
}

out.push("total " + total);
process.stdout.write(out.join("\n") + "\n");
