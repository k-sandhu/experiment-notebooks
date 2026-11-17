"use strict";

const fs = require("node:fs");
const data = fs.readFileSync(process.argv[2]);
let position = 0, start = 0, length = 0;
function token() {
    while (position < data.length && data[position] <= 32) ++position;
    start = position;
    while (position < data.length && data[position] > 32) ++position;
    length = position - start;
}
function number() {
    token();
    let value = 0;
    for (let i = start; i < position; ++i) value = value * 10 + data[i] - 48;
    return value;
}

const ins = [new Int32Array(26), new Int32Array(26)];
const del = [new Int32Array(26), new Int32Array(26)];
const sub = Array.from({length: 2}, () => Array.from({length: 26}, () => new Int32Array(26)));
const profile = Array.from({length: 26}, () => new Int32Array(0));
let insertion = new Int32Array(0), row32 = new Int32Array(0), row64 = new Float64Array(0);

function evaluate32(s, n, m, deletion) {
    if (row32.length < m) row32 = new Int32Array(m);
    const row = row32, insert = insertion;
    let prefix = 0;
    for (let j = 0; j < m; ++j) row[j] = prefix += insert[j];
    let boundary = 0;
    for (let i = 0; i < n; ++i) {
        const c = data[s + i] - 65, d = deletion[c], costs = profile[c];
        let diagonal = boundary;
        let left = boundary += d;
        for (let j = 0; j < m; ++j) {
            const above = row[j];
            // All candidates are in [0, INT_MAX], so these signed
            // differences cannot overflow. Avoid floating-point min here.
            const across = left + insert[j];
            let difference = above + d - across;
            const best = across + (difference & (difference >> 31));
            const replace = diagonal + costs[j];
            difference = best - replace;
            left = replace + (difference & (difference >> 31));
            row[j] = left;
            diagonal = above;
        }
    }
    return row[m - 1];
}

function evaluate64(s, n, m, deletion) {
    if (row64.length < m) row64 = new Float64Array(m);
    const row = row64, insert = insertion;
    let prefix = 0;
    for (let j = 0; j < m; ++j) row[j] = prefix += insert[j];
    let boundary = 0;
    for (let i = 0; i < n; ++i) {
        const c = data[s + i] - 65, d = deletion[c], costs = profile[c];
        let diagonal = boundary;
        let left = boundary += d;
        for (let j = 0; j < m; ++j) {
            const above = row[j];
            left = Math.min(above + d, left + insert[j], diagonal + costs[j]);
            row[j] = left;
            diagonal = above;
        }
    }
    return row[m - 1];
}

// Only needed if a pair's bound exceeds the exact integer range of Number.
// Keeping this loop separate leaves the normal numeric loops monomorphic.
function evaluateBig(s, n, m, deletion) {
    const row = new BigInt64Array(m);
    const insert = Array.from(insertion.subarray(0, m), BigInt);
    const deletions = Array.from(deletion, BigInt);
    const profiles = profile.map(p => Array.from(p.subarray(0, m), BigInt));
    let prefix = 0n;
    for (let j = 0; j < m; ++j) row[j] = prefix += insert[j];
    let boundary = 0n;
    for (let i = 0; i < n; ++i) {
        const c = data[s + i] - 65, d = deletions[c], costs = profiles[c];
        let diagonal = boundary;
        let left = boundary += d;
        for (let j = 0; j < m; ++j) {
            const above = row[j];
            let best = above + d;
            const across = left + insert[j], replace = diagonal + costs[j];
            if (across < best) best = across;
            if (replace < best) best = replace;
            row[j] = left = best;
            diagonal = above;
        }
    }
    return row[m - 1];
}

function cost(s, n, t, m) {
    if (n === m) {
        let j = 0;
        while (j < n && data[s + j] === data[t + j]) ++j;
        if (j === n) return 0;
    }
    let direction = 0;
    if (n < m) {
        let swap = s; s = t; t = swap;
        swap = n; n = m; m = swap;
        direction = 1;
    }
    const deletion = del[direction], insert = ins[direction];
    if (insertion.length < m) insertion = new Int32Array(m);
    let bound = 0, used = 0;
    for (let i = 0; i < n; ++i) {
        const c = data[s + i] - 65;
        bound += deletion[c];
        used |= 1 << c;
    }
    for (let j = 0; j < m; ++j) {
        const value = insert[data[t + j] - 65];
        insertion[j] = value;
        bound += value;
    }
    if (bound === 0) return 0;
    for (let c = 0; c < 26; ++c) {
        if ((used & (1 << c)) === 0) continue;
        if (profile[c].length < m) profile[c] = new Int32Array(m);
        const costs = profile[c], table = sub[direction][c];
        for (let j = 0; j < m; ++j) costs[j] = table[data[t + j] - 65];
    }
    // A candidate can exceed a DP entry by at most 1000.
    if (bound <= 2147483647 - 1000) return evaluate32(s, n, m, deletion);
    if (bound < Number.MAX_SAFE_INTEGER - 1000) return evaluate64(s, n, m, deletion);
    return evaluateBig(s, n, m, deletion);
}

token();
const alphabet = start, size = length;
for (let i = 0; i < size; ++i) ins[0][data[alphabet + i] - 65] = number();
for (let i = 0; i < size; ++i) del[0][data[alphabet + i] - 65] = number();
for (let i = 0; i < size; ++i)
    for (let j = 0; j < size; ++j)
        sub[0][data[alphabet + i] - 65][data[alphabet + j] - 65] = number();
for (let i = 0; i < 26; ++i) {
    ins[1][i] = del[0][i];
    del[1][i] = ins[0][i];
    for (let j = 0; j < 26; ++j) sub[1][i][j] = sub[0][j][i];
}
const pairs = number(), output = [];
let total = 0n;
for (let p = 0; p < pairs; ++p) {
    token();
    const s = start, n = length;
    token();
    const result = cost(s, n, start, length);
    total += BigInt(result);
    output.push(String(result));
}
output.push("total " + total);
process.stdout.write(output.join("\n") + "\n");
