"use strict";

const fs = require("fs");

const raw = fs.readFileSync(process.argv[2]);
const data = Buffer.allocUnsafe(raw.length + 1);
raw.copy(data);
data[raw.length] = 0;
let pos = 0;

function nextInt() {
    while (data[pos] <= 32) pos++;
    let x = 0;
    while (data[pos] > 32) {
        x = x * 10 + (data[pos] - 48);
        pos++;
    }
    return x;
}

const N = nextInt();
const M = nextInt();
const Q = nextInt();

const eu = new Int32Array(M);
const ev = new Int32Array(M);
const ew = new Int32Array(M);
const deg = new Int32Array(N);
let maxW = 0;

for (let i = 0; i < M; i++) {
    const u = nextInt();
    const v = nextInt();
    const w = nextInt();
    eu[i] = u;
    ev[i] = v;
    ew[i] = w;
    deg[u]++;
    deg[v]++;
    if (w > maxW) maxW = w;
}

const off = new Int32Array(N + 1);
let acc = 0;
for (let i = 0; i < N; i++) {
    off[i] = acc;
    acc += deg[i];
}
off[N] = acc;

const at = new Int32Array(acc);
const aw = new Int32Array(acc);
const curOff = off.slice(0, N + 1);
for (let i = 0; i < M; i++) {
    const u = eu[i], v = ev[i], w = ew[i];
    at[curOff[u]] = v;
    aw[curOff[u]] = w;
    curOff[u]++;
    at[curOff[v]] = u;
    aw[curOff[v]] = w;
    curOff[v]++;
}

const src = new Int32Array(Q);
for (let i = 0; i < Q; i++) src[i] = nextInt();

const small = N * maxW < 2147483646;
const dist = small ? new Int32Array(N) : new Float64Array(N);
const INF = small ? 2147483647 : Infinity;

// Monotone circular bucket queue (Dial); buckets hold node ids, a bitset of
// occupied buckets lets us skip empty distance ranges.
let nb = maxW + 1;
if (nb < 2) nb = 2;
const words = (nb + 31) >> 5;
const bits = new Uint32Array(words);
const buckets = new Array(nb);
for (let i = 0; i < nb; i++) buckets[i] = [];
let qcur = 0;

function nextSetBit(p) {
    const wi = p >> 5;
    let w = bits[wi] & (~0 << (p & 31));
    if (w !== 0) return (wi << 5) + (31 - Math.clz32(w & -w));
    for (let i = wi + 1; i < words; i++) {
        const x = bits[i];
        if (x !== 0) return (i << 5) + (31 - Math.clz32(x & -x));
    }
    for (let i = 0; i < wi; i++) {
        const x = bits[i];
        if (x !== 0) return (i << 5) + (31 - Math.clz32(x & -x));
    }
    const low = bits[wi] & ((1 << (p & 31)) - 1);
    if (low !== 0) return (wi << 5) + (31 - Math.clz32(low & -low));
    return -1;
}

let out = "";

for (let qi = 0; qi < Q; qi++) {
    const s = src[qi];
    if (small) dist.fill(INF);
    else dist.fill(INF);
    for (let i = 0; i < nb; i++) buckets[i].length = 0;
    bits.fill(0);
    qcur = 0;
    dist[s] = 0;
    buckets[0].push(s);
    bits[0] |= 1;

    let reach = 0;
    let total = 0;
    let far = -1;
    let farNode = -1;

    for (;;) {
        const p = qcur % nb;
        const idx = nextSetBit(p);
        if (idx < 0) break;
        let offset = idx - p;
        if (offset < 0) offset += nb;
        qcur += offset;
        const d = qcur;

        const bk = buckets[idx];
        while (bk.length > 0) {
            const u = bk.pop();
            if (dist[u] !== d) continue;

            reach++;
            total += d;
            if (d > far) {
                far = d;
                farNode = u;
            } else if (d === far && u < farNode) {
                farNode = u;
            }

            const end = off[u + 1];
            for (let e = off[u]; e < end; e++) {
                const v = at[e];
                const w = aw[e];
                const nd = d + w;
                if (nd < dist[v]) {
                    dist[v] = nd;
                    let idx2 = idx + w;
                    if (idx2 >= nb) idx2 -= nb;
                    buckets[idx2].push(v);
                    bits[idx2 >> 5] |= 1 << (idx2 & 31);
                }
            }
        }
        bits[idx >> 5] &= ~(1 << (idx & 31));
    }

    out += s + " " + reach + " " + total + " " + far + " " + farNode + "\n";
}

process.stdout.write(out);
