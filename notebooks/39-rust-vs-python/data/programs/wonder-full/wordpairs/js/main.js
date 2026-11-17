'use strict';
const fs = require('fs');

function mix32(x) {
  x = (x + 0x9e3779b9) | 0;
  x = Math.imul(x ^ (x >>> 15), 0x85ebca6b);
  x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35);
  return (x ^ (x >>> 16)) | 0;
}

const data = fs.readFileSync(process.argv[2]);
const n = data.length;

let wcap = 1024;
while (wcap < (1 << 17) && wcap * 64 < n) wcap <<= 1;
let wtab = new Int32Array(wcap).fill(-1);
let wmask = wcap - 1;

let arena = new Uint8Array(1 << 20);
let arenaLen = 0;
let woff = new Int32Array(65536);
let wlen = new Int32Array(65536);
let whash = new Int32Array(65536);
let V = 0;

let est = (n / 6 | 0) + 1024;
if (est > (1 << 24)) est = 1 << 24;
let pairA = new Int32Array(est);
let pairB = new Int32Array(est);
let pc = 0;

let W = 0;
let prev = -1;
let i = 0;
while (i < n) {
  let b = data[i];
  let lo = b | 32;
  if ((lo - 97) >>> 0 < 26) {
    const start = i;
    let h = 0x811c9dc5 | 0;
    for (;;) {
      h = Math.imul(h ^ lo, 0x01000193);
      i++;
      if (i >= n) break;
      b = data[i]; lo = b | 32;
      if ((lo - 97) >>> 0 >= 26) break;
    }
    const len = i - start;
    const mh = mix32(h);
    let idx = mh & wmask;
    let id;
    for (;;) {
      id = wtab[idx];
      if (id < 0) {
        id = V++;
        wtab[idx] = id;
        if (V >= whash.length) {
          const nc = whash.length << 1;
          let t;
          t = new Int32Array(nc); t.set(whash); whash = t;
          t = new Int32Array(nc); t.set(woff); woff = t;
          t = new Int32Array(nc); t.set(wlen); wlen = t;
        }
        whash[id] = mh;
        woff[id] = arenaLen;
        wlen[id] = len;
        if (arenaLen + len > arena.length) {
          let nc = arena.length;
          while (nc < arenaLen + len) nc <<= 1;
          const t = new Uint8Array(nc); t.set(arena); arena = t;
        }
        for (let k = 0; k < len; k++) arena[arenaLen++] = data[start + k] | 32;
        if (V * 4 > wcap * 3) {
          const ncap = wcap << 1;
          const nt = new Int32Array(ncap).fill(-1);
          const nmask = ncap - 1;
          for (let wi = 0; wi < V; wi++) {
            let j = whash[wi] & nmask;
            while (nt[j] >= 0) j = (j + 1) & nmask;
            nt[j] = wi;
          }
          wtab = nt; wcap = ncap; wmask = nmask;
        }
        break;
      }
      if (whash[id] === mh && wlen[id] === len) {
        const off = woff[id];
        let eq = true;
        for (let k = 0; k < len; k++) {
          if (arena[off + k] !== (data[start + k] | 32)) { eq = false; break; }
        }
        if (eq) break;
      }
      idx = (idx + 1) & wmask;
    }
    W++;
    if (prev >= 0) {
      if (pc === pairA.length) {
        const nc = pairA.length << 1;
        let t = new Int32Array(nc); t.set(pairA); pairA = t;
        t = new Int32Array(nc); t.set(pairB); pairB = t;
      }
      pairA[pc] = prev; pairB[pc] = id; pc++;
    }
    prev = id;
  } else {
    if (b === 46 || b === 33 || b === 63) prev = -1;
    i++;
  }
}
const T = pc;

// rank
const ids = new Array(V);
for (let k = 0; k < V; k++) ids[k] = k;
ids.sort((a, b) => {
  const la = wlen[a], lb = wlen[b], oa = woff[a], ob = woff[b];
  const m = la < lb ? la : lb;
  for (let k = 0; k < m; k++) {
    const d = arena[oa + k] - arena[ob + k];
    if (d !== 0) return d;
  }
  return la - lb;
});
const rankv = new Int32Array(V);
for (let k = 0; k < V; k++) rankv[ids[k]] = k;

function better(c1, a1, b1, c2, a2, b2) {
  if (c1 !== c2) return c1 > c2;
  if (rankv[a1] !== rankv[a2]) return rankv[a1] < rankv[a2];
  return rankv[b1] < rankv[b2];
}

const topC = new Int32Array(20), topA = new Int32Array(20), topB = new Int32Array(20);
let topN = 0, worst = 0;
function findWorst() {
  let w = 0;
  for (let q = 1; q < topN; q++) if (better(topC[w], topA[w], topB[w], topC[q], topA[q], topB[q])) w = q;
  return w;
}
function feed(c, a, b) {
  if (topN < 20) {
    topC[topN] = c; topA[topN] = a; topB[topN] = b; topN++;
    if (topN === 20) worst = findWorst();
  } else if (better(c, a, b, topC[worst], topA[worst], topB[worst])) {
    topC[worst] = c; topA[worst] = a; topB[worst] = b;
    worst = findWorst();
  }
}

let D = 0;
if (pc > 0) {
  const cnt = new Int32Array(65536);
  if (V <= 65536) {
    let keys = new Uint32Array(pc);
    for (let k = 0; k < pc; k++) keys[k] = ((pairA[k] << 16) | pairB[k]) >>> 0;
    pairA = pairB = null;
    let aux = new Uint32Array(pc);
    let src = keys, dst = aux;
    for (let shift = 0; shift < 32; shift += 16) {
      cnt.fill(0);
      for (let k = 0; k < pc; k++) cnt[(src[k] >>> shift) & 0xFFFF]++;
      let sum = 0;
      for (let k = 0; k < 65536; k++) { const t = cnt[k]; cnt[k] = sum; sum += t; }
      for (let k = 0; k < pc; k++) { const v = src[k]; dst[cnt[(v >>> shift) & 0xFFFF]++] = v; }
      const tmp = src; src = dst; dst = tmp;
    }
    let k = 0;
    while (k < pc) {
      let j = k + 1;
      const v = src[k];
      while (j < pc && src[j] === v) j++;
      D++;
      feed(j - k, v >>> 16, v & 0xFFFF);
      k = j;
    }
  } else {
    let A2 = new Int32Array(pc), B2 = new Int32Array(pc);
    let sA = pairA, sB = pairB, dA = A2, dB = B2;
    for (let pass = 0; pass < 4; pass++) {
      const sKey = pass < 2 ? sB : sA;
      const shift = (pass & 1) * 16;
      cnt.fill(0);
      for (let k = 0; k < pc; k++) cnt[(sKey[k] >>> shift) & 0xFFFF]++;
      let sum = 0;
      for (let k = 0; k < 65536; k++) { const t = cnt[k]; cnt[k] = sum; sum += t; }
      for (let k = 0; k < pc; k++) {
        const p = cnt[(sKey[k] >>> shift) & 0xFFFF]++;
        dA[p] = sA[k]; dB[p] = sB[k];
      }
      let tmp = sA; sA = dA; dA = tmp;
      tmp = sB; sB = dB; dB = tmp;
    }
    let k = 0;
    while (k < pc) {
      let j = k + 1;
      const va = sA[k], vb = sB[k];
      while (j < pc && sA[j] === va && sB[j] === vb) j++;
      D++;
      feed(j - k, va, vb);
      k = j;
    }
  }
}

for (let a = 1; a < topN; a++) {
  const c = topC[a], x = topA[a], y = topB[a];
  let b = a - 1;
  while (b >= 0 && better(c, x, y, topC[b], topA[b], topB[b])) {
    topC[b + 1] = topC[b]; topA[b + 1] = topA[b]; topB[b + 1] = topB[b]; b--;
  }
  topC[b + 1] = c; topA[b + 1] = x; topB[b + 1] = y;
}

function wordStr(id) {
  let s = '';
  const off = woff[id], len = wlen[id];
  for (let k = 0; k < len; k++) s += String.fromCharCode(arena[off + k]);
  return s;
}

let out = `words ${W}\npairs ${T}\ndistinct ${D}\n`;
for (let k = 0; k < topN; k++) out += `${topC[k]} ${wordStr(topA[k])} ${wordStr(topB[k])}\n`;
process.stdout.write(out);
