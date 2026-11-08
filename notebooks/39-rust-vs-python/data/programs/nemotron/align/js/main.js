'use strict';

const fs = require('fs');

// Weighted edit distance for many string pairs (exact DP recurrence from SPEC.md).
// Two rolling rows as plain JS arrays (V8 stores them as packed smis); all cell
// values fit in a 32-bit integer, the grand total stays exact as a JS number.

function main() {
    const buf = fs.readFileSync(process.argv[2]);
    const len = buf.length;
    let p = 0;

    function skipWs() {
        while (p < len && buf[p] <= 32) p++;
    }

    function nextInt() {
        skipWs();
        let x = 0;
        while (p < len && buf[p] > 32) {
            x = x * 10 + (buf[p] - 48);
            p++;
        }
        return x;
    }

    function readTokenIdx(idx) {
        skipWs();
        const start = p;
        while (p < len && buf[p] > 32) p++;
        const n = p - start;
        const a = new Array(n);
        for (let i = 0; i < n; i++) a[i] = idx[buf[start + i]];
        return a;
    }

    skipWs();
    const alphaStart = p;
    while (p < len && buf[p] > 32) p++;
    const A = p - alphaStart;

    const idx = new Array(256);
    for (let i = 0; i < 256; i++) idx[i] = -1;
    for (let i = 0; i < A; i++) idx[buf[alphaStart + i]] = i;

    const ins = new Array(A);
    const del = new Array(A);
    const sub = new Array(A * A);
    for (let i = 0; i < A; i++) ins[i] = nextInt();
    for (let i = 0; i < A; i++) del[i] = nextInt();
    for (let i = 0; i < A * A; i++) sub[i] = nextInt();

    const P = nextInt();

    let prev = null;
    let cur = null;
    let total = 0;
    const lines = [];

    for (let pair = 0; pair < P; pair++) {
        const s = readTokenIdx(idx);
        const t = readTokenIdx(idx);
        const n = s.length;
        const m = t.length;

        if (prev == null || prev.length < m + 1) {
            prev = new Int32Array(m + 1);
            cur = new Int32Array(m + 1);
        }

        prev[0] = 0;
        for (let j = 1; j <= m; j++) prev[j] = prev[j - 1] + ins[t[j - 1]];

        for (let i = 0; i < n; i++) {
            const si = s[i];
            const d = del[si];
            const base = si * A;
            cur[0] = prev[0] + d;
            let diag = prev[0];
            for (let j = 1; j <= m; j++) {
                const tj = t[j - 1];
                let best = prev[j] + d;
                let v = cur[j - 1] + ins[tj];
                if (v < best) best = v;
                v = diag + sub[base + tj];
                if (v < best) best = v;
                cur[j] = best;
                diag = prev[j];
            }
            const tmp = prev;
            prev = cur;
            cur = tmp;
        }

        total += prev[m];
        lines.push(String(prev[m]));
    }

    lines.push('total ' + String(total));
    process.stdout.write(lines.join('\n') + '\n');
}

main();
