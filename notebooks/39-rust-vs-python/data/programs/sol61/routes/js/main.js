"use strict";

const fs = require("node:fs");

class Scanner {
    constructor(path) { this.data = fs.readFileSync(path); this.pos = 0; }
    read() {
        const data = this.data;
        let p = this.pos;
        while (data[p] <= 32) ++p;
        let x = 0;
        while (p < data.length && data[p] >= 48 && data[p] <= 57) {
            x = x * 10 + data[p++] - 48;
        }
        this.pos = p;
        return x;
    }
}

// One live entry per node. Signed 32-bit masks also handle bucket 1,023.
class BucketQueue {
    constructor(n) {
        this.head = new Int32Array(1024);
        this.bits = new Int32Array(32);
        this.next = new Int32Array(n);
        this.prev = new Int32Array(n);
        this.summary = 0;
        this.current = 0;
    }
    reset() {
        this.head.fill(-1); this.bits.fill(0);
        this.summary = 0; this.current = 0;
    }
    insert(v, b) {
        const h = this.head[b];
        this.next[v] = h; this.prev[v] = -1;
        if (h >= 0) this.prev[h] = v;
        else {
            this.bits[b >>> 5] |= 1 << (b & 31);
            this.summary |= 1 << (b >>> 5);
        }
        this.head[b] = v;
    }
    remove(v, b) {
        const p = this.prev[v], n = this.next[v];
        if (p >= 0) this.next[p] = n; else this.head[b] = n;
        if (n >= 0) this.prev[n] = p;
        if (this.head[b] < 0) {
            const g = b >>> 5;
            this.bits[g] &= ~(1 << (b & 31));
            if (this.bits[g] === 0) this.summary &= ~(1 << g);
        }
    }
    pop() {
        let b = this.current;
        if (this.head[b] < 0) {
            let g = b >>> 5;
            let word = this.bits[g] & (-1 << (b & 31));
            if (word === 0) {
                let groups = this.summary & (-2 << g);
                if (groups === 0) groups = this.summary;
                g = 31 - Math.clz32(groups & -groups);
                word = this.bits[g];
            }
            this.current = b = (g << 5) + 31 - Math.clz32(word & -word);
        }
        const v = this.head[b]; this.remove(v, b); return v;
    }
}

function main() {
    const input = new Scanner(process.argv[2]);
    const n = input.read(), m = input.read(), q = input.read();
    const edgeStart = input.pos;
    const offset = new Uint32Array(n + 1);
    for (let i = 0; i < m; ++i) {
        const u = input.read(), v = input.read(); input.read();
        if (u !== v) { ++offset[u + 1]; ++offset[v + 1]; }
    }
    for (let i = 1; i <= n; ++i) offset[i] += offset[i - 1];
    const to = new Int32Array(offset[n]);
    const weight = new Uint16Array(offset[n]);
    const queue = new BucketQueue(n);
    queue.next.set(offset.subarray(0, n));
    input.pos = edgeStart;
    for (let i = 0; i < m; ++i) {
        const u = input.read(), v = input.read(), w = input.read();
        if (u === v) continue;
        const a = queue.next[u]++, b = queue.next[v]++;
        to[a] = v; weight[a] = w;
        to[b] = u; weight[b] = w;
    }
    const sources = new Int32Array(q);
    for (let i = 0; i < q; ++i) sources[i] = input.read();
    input.data = null;
    const dist = new Float64Array(n);
    const output = [];
    for (const s of sources) {
        dist.fill(Infinity);
        queue.reset(); dist[s] = 0; queue.insert(s, 0);
        let reached = 0, subtotal = 0, total = 0n, far = 0, farNode = s;
        while (queue.summary !== 0) {
            const u = queue.pop(), d = dist[u];
            ++reached;
            subtotal += d;
            // Flush exact integer chunks before a Number can lose precision.
            // Each individual distance is <= 1,000 * (n - 1).
            if (subtotal >= 4503599627370496) {
                total += BigInt(subtotal); subtotal = 0;
            }
            if (d > far) { far = d; farNode = u; }
            else if (d === far && u < farNode) farNode = u;
            for (let e = offset[u], end = offset[u + 1]; e < end; ++e) {
                const v = to[e], nd = d + weight[e], old = dist[v];
                if (nd >= old) continue;
                if (old !== Infinity) queue.remove(v, old & 1023);
                dist[v] = nd; queue.insert(v, nd & 1023);
            }
        }
        const sum = total === 0n ? String(subtotal) : String(total + BigInt(subtotal));
        output.push(`${s} ${reached} ${sum} ${far} ${farNode}\n`);
    }
    process.stdout.write(output.join(""));
}

main();
