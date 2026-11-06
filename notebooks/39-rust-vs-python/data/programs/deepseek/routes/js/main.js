"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const dataLen = data.length;
let pos = 0;

function nextInt() {
    let i = pos;
    while (i < dataLen) {
        const c = data[i] - 48;
        if (c >= 0 && c <= 9) break;
        ++i;
    }
    let x = 0;
    while (i < dataLen) {
        const c = data[i] - 48;
        if (c < 0 || c > 9) break;
        x = x * 10 + c;
        ++i;
    }
    pos = i;
    return x;
}

const N = nextInt();
const M = nextInt();
const Q = nextInt();

const eu = new Int32Array(M);
const ev = new Int32Array(M);
const ew = new Int32Array(M);
const deg = new Int32Array(N + 1);
for (let i = 0; i < M; ++i) {
    const u = nextInt(), v = nextInt(), w = nextInt();
    eu[i] = u; ev[i] = v; ew[i] = w;
    ++deg[u]; ++deg[v];
}
const src = new Int32Array(Q);
for (let i = 0; i < Q; ++i) src[i] = nextInt();

const off = new Int32Array(N + 1);
let acc = 0;
for (let i = 0; i < N; ++i) { off[i] = acc; acc += deg[i]; }
off[N] = acc;

const fill = off.slice();
const adj = new Int32Array(2 * M);
for (let i = 0; i < M; ++i) {
    const u = eu[i], v = ev[i], w = ew[i];
    let p = fill[u]++; adj[p] = (v << 10) | w;
    p = fill[v]++; adj[p] = (u << 10) | w;
}

const INF = 0x3f3f3f3f;
const dist = new Int32Array(N);

let shift = 0;
while ((2 ** shift) < N) ++shift;
const mult = 2 ** shift;
const mask = mult - 1;

let heap = new Float64Array(2 * M + 16);
let heapSize = 0;

function heapPush(x) {
    let i = heapSize++;
    if (i >= heap.length) {
        const nh = new Float64Array(heap.length * 2);
        nh.set(heap);
        heap = nh;
    }
    const h = heap;
    while (i > 0) {
        const p = (i - 1) >> 1;
        if (h[p] <= x) break;
        h[i] = h[p];
        i = p;
    }
    h[i] = x;
}

function heapPop() {
    const h = heap;
    const top = h[0];
    const x = h[--heapSize];
    const n = heapSize;
    if (n > 0) {
        let i = 0;
        for (;;) {
            let c = (i << 1) + 1;
            if (c >= n) break;
            if (c + 1 < n && h[c + 1] < h[c]) ++c;
            if (h[c] >= x) break;
            h[i] = h[c];
            i = c;
        }
        h[i] = x;
    }
    return top;
}

const lines = [];

for (let qi = 0; qi < Q; ++qi) {
    const s = src[qi];
    dist.fill(INF);
    heapSize = 0;
    dist[s] = 0;
    heapPush(s);

    let total = 0;
    let reach = 0;
    let far = 0;
    let farNode = s;

    while (heapSize > 0) {
        const key = heapPop();
        const v = key % mult;
        const d = (key - v) / mult;
        if (d !== dist[v]) continue;

        ++reach;
        total += d;
        if (d > far) { far = d; farNode = v; }

        const end = off[v + 1];
        for (let e = off[v]; e < end; ++e) {
            const a = adj[e];
            const u = a >>> 10;
            const nd = d + (a & 1023);
            if (nd < dist[u]) {
                dist[u] = nd;
                heapPush(nd * mult + u);
            }
        }
    }

    lines.push(s + " " + reach + " " + total + " " + far + " " + farNode);
}

process.stdout.write(lines.join("\n") + "\n");
