"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const n = data.length;
const BATCH = 512;
const NONE = -1;

// words
let wcap = 1 << 15;
let wstart = new Int32Array(wcap);
let wlen = new Int32Array(wcap);
let whash = new Int32Array(wcap);
let wcount = 0;
let wtab = new Int32Array(1 << 16); // id+1, 0 = empty
let wmask = (1 << 16) - 1;

function growWords() {
    const ncap = wtab.length * 2;
    const nt = new Int32Array(ncap);
    const nmask = ncap - 1;
    for (let id = 0; id < wcount; id++) {
        let p = whash[id] & nmask;
        while (nt[p] !== 0) p = (p + 1) & nmask;
        nt[p] = id + 1;
    }
    wtab = nt;
    wmask = nmask;
}

function lookupWord(start, len, h) {
    let p = h & wmask;
    for (;;) {
        const e = wtab[p];
        if (e === 0) break;
        const id = e - 1;
        if (whash[id] === h && wlen[id] === len) {
            const t = wstart[id];
            let k = 0;
            while (k < len && ((data[start + k] ^ data[t + k]) | 0x20) === 0x20) k++;
            if (k === len) return id;
        }
        p = (p + 1) & wmask;
    }
    const id = wcount++;
    if (id === wcap) {
        wcap *= 2;
        let a = new Int32Array(wcap); a.set(wstart); wstart = a;
        a = new Int32Array(wcap); a.set(wlen); wlen = a;
        a = new Int32Array(wcap); a.set(whash); whash = a;
    }
    wstart[id] = start;
    wlen[id] = len;
    whash[id] = h;
    wtab[p] = id + 1;
    if (wcount * 2 > wtab.length) growWords();
    return id;
}

// pairs: 4 ints per slot: [a+1 (0 = empty), b, count, unused]
let pbits = 16;
while ((1 << pbits) < n / 12 && pbits < 26) pbits++;
let pshift = 32 - pbits;
let pmask = (1 << pbits) - 1;
let ptab = new Int32Array(4 << pbits);
let distinct = 0;
let tcount = 0;
let sink = 0;

function growPairs() {
    const ocap = pmask + 1;
    const nbits = 32 - pshift + 1;
    const nmask = (1 << nbits) - 1;
    const nshift = pshift - 1;
    const nt = new Int32Array(4 << nbits);
    const ot = ptab;
    for (let q = 0; q < ocap; q++) {
        const a1 = ot[q * 4];
        if (a1 === 0) continue;
        const b = ot[q * 4 + 1];
        let p = (Math.imul(Math.imul(a1, 0x9E3779B1) ^ b, 0x85EBCA6B) >>> nshift);
        while (nt[p * 4] !== 0) p = (p + 1) & nmask;
        nt[p * 4] = a1;
        nt[p * 4 + 1] = b;
        nt[p * 4 + 2] = ot[q * 4 + 2];
    }
    ptab = nt;
    pshift = nshift;
    pmask = nmask;
}

// ids[0] is the previous word (or NONE); NONE marks a sentence end.
function flush(ids, cnt) {
    let acc = 0;
    let tab = ptab;
    let sh = pshift;
    for (let k = 1; k <= cnt; k++) {
        const p = Math.imul(Math.imul(ids[k - 1] + 1, 0x9E3779B1) ^ ids[k], 0x85EBCA6B) >>> sh;
        acc += tab[p * 4];
    }
    sink += acc;
    for (let k = 1; k <= cnt; k++) {
        const a = ids[k - 1], b = ids[k];
        if (a === NONE || b === NONE) continue;
        tcount++;
        const a1 = a + 1;
        let t = ptab;
        let p = Math.imul(Math.imul(a1, 0x9E3779B1) ^ b, 0x85EBCA6B) >>> pshift;
        for (;;) {
            const q = p * 4;
            const ka = t[q];
            if (ka === a1 && t[q + 1] === b) {
                t[q + 2]++;
                break;
            }
            if (ka === 0) {
                t[q] = a1;
                t[q + 1] = b;
                t[q + 2] = 1;
                distinct++;
                if (distinct * 10 > (pmask + 1) * 7) growPairs();
                break;
            }
            p = (p + 1) & pmask;
        }
    }
}

function cmpWords(x, y) {
    if (x === y) return 0;
    const sx = wstart[x], sy = wstart[y], lx = wlen[x], ly = wlen[y];
    const m = lx < ly ? lx : ly;
    for (let i = 0; i < m; i++) {
        const cx = data[sx + i] | 0x20, cy = data[sy + i] | 0x20;
        if (cx !== cy) return cx < cy ? -1 : 1;
    }
    return lx < ly ? -1 : lx > ly ? 1 : 0;
}

function better(cx, ax, bx, cy, ay, by) {
    if (cx !== cy) return cx > cy;
    const c = cmpWords(ax, ay);
    if (c !== 0) return c < 0;
    return cmpWords(bx, by) < 0;
}

function wordString(id) {
    const s = wstart[id], l = wlen[id];
    const b = Buffer.allocUnsafe(l);
    for (let i = 0; i < l; i++) b[i] = data[s + i] | 0x20;
    return b.toString("latin1");
}

function main() {
    let W = 0;
    const ids = new Int32Array(BATCH + 1);
    ids[0] = NONE;
    let cnt = 0;
    let i = 0;
    while (i < n) {
        let c = data[i];
        let lc = c | 0x20;
        if (lc >= 97 && lc <= 122) {
            const st = i;
            let h = 0x811c9dc5 | 0;
            do {
                h = Math.imul(h ^ lc, 16777619);
                i++;
                lc = i < n ? data[i] | 0x20 : 0;
            } while (lc >= 97 && lc <= 122);
            h ^= h >>> 15;
            h = Math.imul(h, 0x2c1b3c6d);
            h ^= h >>> 12;
            ids[++cnt] = lookupWord(st, i - st, h);
            W++;
            if (cnt === BATCH) {
                flush(ids, cnt);
                ids[0] = ids[BATCH];
                cnt = 0;
            }
        } else {
            if (c === 46 || c === 33 || c === 63) {
                if (ids[cnt] !== NONE) {
                    ids[++cnt] = NONE;
                    if (cnt === BATCH) {
                        flush(ids, cnt);
                        ids[0] = ids[BATCH];
                        cnt = 0;
                    }
                }
            }
            i++;
        }
    }
    flush(ids, cnt);

    const tc = new Array(21).fill(0), ta = new Array(21).fill(0), tb = new Array(21).fill(0);
    let nt = 0;
    const t = ptab;
    const cap = pmask + 1;
    for (let q = 0; q < cap; q++) {
        const a1 = t[q * 4];
        if (a1 === 0) continue;
        const count = t[q * 4 + 2];
        if (nt === 20 && count < tc[19]) continue;
        const a = a1 - 1, b = t[q * 4 + 1];
        if (nt === 20 && !better(count, a, b, tc[19], ta[19], tb[19])) continue;
        let j;
        if (nt < 20) j = nt++; else j = 19;
        while (j > 0 && better(count, a, b, tc[j - 1], ta[j - 1], tb[j - 1])) {
            tc[j] = tc[j - 1]; ta[j] = ta[j - 1]; tb[j] = tb[j - 1];
            j--;
        }
        tc[j] = count; ta[j] = a; tb[j] = b;
    }

    let out = "words " + W + "\npairs " + tcount + "\ndistinct " + distinct + "\n";
    for (let k = 0; k < nt; k++) {
        out += tc[k] + " " + wordString(ta[k]) + " " + wordString(tb[k]) + "\n";
    }
    fs.writeSync(1, out);
    if (sink === 42) console.error("");
}

main();
