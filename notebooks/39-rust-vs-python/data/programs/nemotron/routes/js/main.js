'use strict';

const fs = require('fs');

const data = fs.readFileSync(process.argv[2]);
let pos = 0;
const len = data.length;

function readInt() {
    while (pos < len && (data[pos] < 48 || data[pos] > 57)) pos++;
    let x = 0;
    while (pos < len && data[pos] >= 48 && data[pos] <= 57) {
        x = x * 10 + (data[pos] - 48);
        pos++;
    }
    return x;
}

const N = readInt();
const M = readInt();
const Q = readInt();

const eu = new Int32Array(M);
const ev = new Int32Array(M);
const ew = new Int32Array(M);
const deg = new Int32Array(N);
for (let i = 0; i < M; i++) {
    const u = readInt();
    const v = readInt();
    const w = readInt();
    eu[i] = u;
    ev[i] = v;
    ew[i] = w;
    deg[u]++;
    deg[v]++;
}

const off = new Int32Array(N + 1);
for (let i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
const to = new Int32Array(2 * M);
const wt = new Int32Array(2 * M);
const cur = new Int32Array(N);
cur.set(off.subarray(0, N));
for (let i = 0; i < M; i++) {
    const u = eu[i];
    const v = ev[i];
    const w = ew[i];
    const p = cur[u]++;
    to[p] = v;
    wt[p] = w;
    const q = cur[v]++;
    to[q] = u;
    wt[q] = w;
}

const sources = new Int32Array(Q);
for (let i = 0; i < Q; i++) sources[i] = readInt();

const INF = 0x7fffffff;
const dist = new Int32Array(N);

// Binary heap over (distance, node) pairs.
const hpD = [];
const hpV = [];
function heapPush(d, v) {
    const i = hpD.length;
    hpD.push(d);
    hpV.push(v);
    let ci = i;
    while (ci > 0) {
        const p = (ci - 1) >> 1;
        if (hpD[p] <= d) break;
        hpD[ci] = hpD[p];
        hpV[ci] = hpV[p];
        ci = p;
    }
    hpD[ci] = d;
    hpV[ci] = v;
}
function heapPop() {
    const topD = hpD[0];
    const topV = hpV[0];
    const n = hpD.length - 1;
    const lastD = hpD[n];
    const lastV = hpV[n];
    hpD.length = n;
    hpV.length = n;
    if (n > 0) {
        const d = lastD;
        const v = lastV;
        hpD[0] = lastD;
        hpV[0] = lastV;
        let ci = 0;
        for (;;) {
            const c1 = 2 * ci + 1;
            if (c1 >= n) break;
            let c = c1;
            const c2 = c1 + 1;
            if (c2 < n && hpD[c2] < hpD[c1]) c = c2;
            if (hpD[c] >= d) break;
            hpD[ci] = hpD[c];
            hpV[ci] = hpV[c];
            ci = c;
        }
        hpD[ci] = d;
        hpV[ci] = v;
    }
    return [topD, topV];
}

const out = [];
for (let i = 0; i < Q; i++) {
    const s = sources[i];
    for (let v = 0; v < N; v++) dist[v] = INF;
    dist[s] = 0;
    hpD.length = 0;
    hpV.length = 0;
    heapPush(0, s);

    while (hpD.length > 0) {
        const pair = heapPop();
        const d = pair[0];
        const v = pair[1];
        if (d > dist[v]) continue; // stale entry
        const e0 = off[v];
        const e1 = off[v + 1];
        for (let e = e0; e < e1; e++) {
            const t = to[e];
            const nd = d + wt[e];
            if (nd < dist[t]) {
                dist[t] = nd;
                heapPush(nd, t);
            }
        }
    }

    let reach = 0;
    let total = 0;
    let far = -1;
    let node = -1;
    for (let v = 0; v < N; v++) {
        const dv = dist[v];
        if (dv !== INF) {
            reach++;
            total += dv;
            if (dv > far) {
                far = dv;
                node = v;
            }
        }
    }

    out.push(`${s} ${reach} ${total} ${far} ${node}`);
}

process.stdout.write(out.join('\n') + '\n');
