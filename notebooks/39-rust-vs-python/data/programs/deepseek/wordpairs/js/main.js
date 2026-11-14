"use strict";

const fs = require("fs");

const LOWER = new Uint8Array(256);
for (let c = 97; c <= 122; c++) LOWER[c] = c;
for (let c = 65; c <= 90; c++) LOWER[c] = c + 32;

const path = process.argv[2];
const fd = fs.openSync(path, "r");
const size = fs.fstatSync(fd).size;
const fileBuf = Buffer.allocUnsafe(size + 16);
let got = 0;
while (got < size) {
  const r = fs.readSync(fd, fileBuf, got, size - got, got);
  if (r <= 0) break;
  got += r;
}
fs.closeSync(fd);
fileBuf.fill(0, got, size + 16);
const buf = fileBuf;
const n = got;

// ---- word interner --------------------------------------------------------
// Each slot holds 4 x 32-bit prefix words (first 16 letters), the length and
// the word id.  The prefixes zero-padded identify a word of <= 16 letters
// exactly; longer words are verified against the text.
let tab = new Int32Array(4096 * 6).fill(-1);
let mask = 4095;
let nWords = 0;
const wOff = [];
const wLen = [];

const M = [0, 0xff, 0xffff, 0xffffff, -1];

function mixKey(w0, w1, w2, w3, len) {
  let h = Math.imul(w0 ^ 0x9e3779b9, 0x85ebca6b);
  h = Math.imul(h ^ w1, 0xc2b2ae35);
  h = Math.imul(h ^ w2, 0x27d4eb2f);
  h = Math.imul(h ^ w3, 0x165667b1);
  h = Math.imul(h ^ len, 0x85ebca6b);
  h ^= h >>> 15;
  return h;
}

function rehash(slots) {
  const t = new Int32Array(slots * 6).fill(-1);
  const m = slots - 1;
  const oldSlots = tab.length / 6;
  for (let s = 0; s < oldSlots; s++) {
    const b = s * 6;
    const id = tab[b + 5];
    if (id < 0) continue;
    const w0 = tab[b], w1 = tab[b + 1], w2 = tab[b + 2], w3 = tab[b + 3], len = tab[b + 4];
    let idx = mixKey(w0, w1, w2, w3, len) & m;
    while (t[idx * 6 + 5] >= 0) idx = (idx + 1) & m;
    const d = idx * 6;
    t[d] = w0; t[d + 1] = w1; t[d + 2] = w2; t[d + 3] = w3; t[d + 4] = len; t[d + 5] = id;
  }
  tab = t;
  mask = m;
}

function eqTail(a, b, len) {
  for (let i = 16; i < len; i++) if (buf[a + i] !== buf[b + i]) return false;
  return true;
}

function intern(w0, w1, w2, w3, len, off) {
  let idx = mixKey(w0, w1, w2, w3, len) & mask;
  for (;;) {
    const b = idx * 6;
    const id = tab[b + 5];
    if (id < 0) break;
    if (tab[b + 4] === len && tab[b] === w0 && tab[b + 1] === w1 &&
        tab[b + 2] === w2 && tab[b + 3] === w3) {
      if (len <= 16 || eqTail(wOff[id], off, len)) return id;
    }
    idx = (idx + 1) & mask;
  }
  const id = nWords++;
  wOff.push(off);
  wLen.push(len);
  const d = idx * 6;
  tab[d] = w0; tab[d + 1] = w1; tab[d + 2] = w2; tab[d + 3] = w3;
  tab[d + 4] = len; tab[d + 5] = id;
  if (nWords * 10 > (tab.length / 6) * 7) rehash((tab.length / 6) * 2);
  return id;
}

function load4(s) {
  return (buf[s] | (buf[s + 1] << 8) | (buf[s + 2] << 16) | (buf[s + 3] << 24)) | 0;
}

// ---- scan -----------------------------------------------------------------
let cap = Math.max(1024, (n / 6 | 0) + 1024);
let pLo = new Uint32Array(cap);
let pHi = new Uint32Array(cap);
let np = 0;
let prev = -1;
let W = 0;
let T = 0;
let i = 0;

while (i < n) {
  let lc = LOWER[buf[i]];
  if (lc !== 0) {
    const start = i;
    do {
      buf[i] = lc;
      i++;
      lc = (i < n) ? LOWER[buf[i]] : 0;
    } while (lc !== 0);
    const len = i - start;

    const l16 = len < 16 ? len : 16;
    const w0 = load4(start) & M[l16 > 4 ? 4 : l16];
    let w1 = 0, w2 = 0, w3 = 0;
    if (l16 > 4) { const r = l16 - 4; w1 = load4(start + 4) & M[r > 4 ? 4 : r]; }
    if (l16 > 8) { const r = l16 - 8; w2 = load4(start + 8) & M[r > 4 ? 4 : r]; }
    if (l16 > 12) { const r = l16 - 12; w3 = load4(start + 12) & M[r > 4 ? 4 : r]; }

    const id = intern(w0, w1, w2, w3, len, start);
    W++;
    if (prev >= 0) {
      if (np === cap) {
        const nc = cap + (cap >> 1) + 64;
        const nl = new Uint32Array(nc); nl.set(pLo); pLo = nl;
        const nh = new Uint32Array(nc); nh.set(pHi); pHi = nh;
        cap = nc;
      }
      pHi[np] = prev;
      pLo[np] = id;
      np++;
      T++;
    }
    prev = id;
  } else {
    const c = buf[i];
    if (c === 46 || c === 33 || c === 63) prev = -1;
    i++;
  }
}

// ---- sort pair keys: LSD radix over (hi, lo) 8-bit digits ------------------
let srcLo = pLo, srcHi = pHi;
if (np > 1) {
  let orLo = 0, orHi = 0;
  for (let k = 0; k < np; k++) {
    orLo |= pLo[k];
    orHi |= pHi[k];
  }
  let dstLo = new Uint32Array(np);
  let dstHi = new Uint32Array(np);
  const cnt = new Int32Array(256);
  for (let pass = 0; pass < 8; pass++) {
    const useHi = pass >= 4;
    const shift = (pass & 3) * 8;
    const orv = useHi ? orHi : orLo;
    if (((orv >>> shift) & 0xff) === 0) continue;
    const src = useHi ? srcHi : srcLo;
    cnt.fill(0);
    for (let k = 0; k < np; k++) cnt[(src[k] >>> shift) & 0xff]++;
    let sum = 0;
    for (let d = 0; d < 256; d++) {
      const c = cnt[d];
      cnt[d] = sum;
      sum += c;
    }
    for (let k = 0; k < np; k++) {
      const pos = cnt[(src[k] >>> shift) & 0xff]++;
      dstLo[pos] = srcLo[k];
      dstHi[pos] = srcHi[k];
    }
    let t = srcLo; srcLo = dstLo; dstLo = t;
    t = srcHi; srcHi = dstHi; dstHi = t;
  }
}

function cmpWord(x, y) {
  const ox = wOff[x], oy = wOff[y];
  const lx = wLen[x], ly = wLen[y];
  const l = lx < ly ? lx : ly;
  for (let k = 0; k < l; k++) {
    const a = buf[ox + k], b = buf[oy + k];
    if (a !== b) return a - b;
  }
  return lx - ly;
}

function better(c1, a1, a2, c2, b1, b2) {
  if (c1 !== c2) return c1 > c2;
  const c = cmpWord(a1, b1);
  if (c !== 0) return c < 0;
  return cmpWord(a2, b2) < 0;
}

function worse(c1, a1, a2, c2, b1, b2) {
  return better(c2, b1, b2, c1, a1, a2);
}

const bestC = new Int32Array(20);
const bestA = new Int32Array(20);
const bestB = new Int32Array(20);
let bn = 0;
let distinct = 0;

for (let k = 0; k < np;) {
  let j = k + 1;
  const lo = srcLo[k], hi = srcHi[k];
  while (j < np && srcLo[j] === lo && srcHi[j] === hi) j++;
  const c = j - k;
  const a = hi, b2 = lo;
  if (bn < 20) {
    bestC[bn] = c; bestA[bn] = a; bestB[bn] = b2;
    let idx = bn++;
    while (idx > 0) {
      const p = (idx - 1) >> 1;
      if (worse(bestC[idx], bestA[idx], bestB[idx], bestC[p], bestA[p], bestB[p])) {
        let t = bestC[idx]; bestC[idx] = bestC[p]; bestC[p] = t;
        t = bestA[idx]; bestA[idx] = bestA[p]; bestA[p] = t;
        t = bestB[idx]; bestB[idx] = bestB[p]; bestB[p] = t;
        idx = p;
      } else break;
    }
  } else if (better(c, a, b2, bestC[0], bestA[0], bestB[0])) {
    bestC[0] = c; bestA[0] = a; bestB[0] = b2;
    let idx = 0;
    for (;;) {
      const l = 2 * idx + 1, r = l + 1;
      let w = idx;
      if (l < bn && worse(bestC[l], bestA[l], bestB[l], bestC[w], bestA[w], bestB[w])) w = l;
      if (r < bn && worse(bestC[r], bestA[r], bestB[r], bestC[w], bestA[w], bestB[w])) w = r;
      if (w === idx) break;
      let t = bestC[idx]; bestC[idx] = bestC[w]; bestC[w] = t;
      t = bestA[idx]; bestA[idx] = bestA[w]; bestA[w] = t;
      t = bestB[idx]; bestB[idx] = bestB[w]; bestB[w] = t;
      idx = w;
    }
  }
  distinct++;
  k = j;
}

for (let q = 1; q < bn; q++) {
  const cq = bestC[q], aq = bestA[q], bq = bestB[q];
  let r = q - 1;
  while (r >= 0 && better(cq, aq, bq, bestC[r], bestA[r], bestB[r])) {
    bestC[r + 1] = bestC[r]; bestA[r + 1] = bestA[r]; bestB[r + 1] = bestB[r];
    r--;
  }
  bestC[r + 1] = cq; bestA[r + 1] = aq; bestB[r + 1] = bq;
}

let out = "words " + W + "\npairs " + T + "\ndistinct " + distinct + "\n";
for (let q = 0; q < bn; q++) {
  const a = bestA[q], b2 = bestB[q];
  out += bestC[q] + " "
    + buf.toString("latin1", wOff[a], wOff[a] + wLen[a]) + " "
    + buf.toString("latin1", wOff[b2], wOff[b2] + wLen[b2]) + "\n";
}
process.stdout.write(out);
