"use strict";
const fs = require("fs");

// ---- word table: open addressing, ids into a byte arena ----
let wSlot, wHash, wOff, wLen, wArena, wArenaLen = 0, wMask, wCount = 0;
let wbuf = new Uint8Array(256); // arena uses Buffer for latin1 toString

function wGrow() {
  const cap = wMask + 1, cap2 = cap * 2;
  const s2 = new Int32Array(cap2), h2 = new Int32Array(cap2);
  const m2 = cap2 - 1;
  for (let i = 0; i < cap; i++) {
    if (wSlot[i] !== 0) {
      let j = wHash[i] & m2;
      while (s2[j] !== 0) j = (j + 1) & m2;
      s2[j] = wSlot[i];
      h2[j] = wHash[i];
    }
  }
  wSlot = s2; wHash = h2; wMask = m2;
}

function wordFindOrAdd(buf, wl, h) {
  let i = h & wMask;
  const hi = h | 0;
  while (wSlot[i] !== 0) {
    const id = wSlot[i] - 1;
    if (wHash[i] === hi && wLen[id] === wl) {
      const o = wOff[id];
      let eq = true;
      for (let k = 0; k < wl; k++) {
        if (wArena[o + k] !== buf[k]) { eq = false; break; }
      }
      if (eq) return id;
    }
    i = (i + 1) & wMask;
  }
  if ((wCount + 1) * 3 > (wMask + 1) * 2) {
    wGrow();
    i = h & wMask;
    while (wSlot[i] !== 0) i = (i + 1) & wMask;
  }
  const id = wCount;
  const o = wArenaLen;
  if (wArenaLen + wl > wArena.length) {
    let nc = wArena.length;
    while (wArenaLen + wl > nc) nc *= 2;
    const a2 = Buffer.allocUnsafe(nc);
    wArena.copy(a2, 0, 0, wArenaLen);
    wArena = a2;
  }
  for (let k = 0; k < wl; k++) wArena[wArenaLen + k] = buf[k];
  wArenaLen += wl;
  if (id >= wOff.length) {
    const no = new Int32Array(wOff.length * 2), nl = new Int32Array(wLen.length * 2);
    no.set(wOff); nl.set(wLen);
    wOff = no; wLen = nl;
  }
  wOff[id] = o;
  wLen[id] = wl;
  wSlot[i] = id + 1;
  wHash[i] = hi;
  wCount = id + 1;
  return id;
}

function cmpWords(a, b) {
  const la = wLen[a], lb = wLen[b];
  const oa = wOff[a], ob = wOff[b];
  const m = la < lb ? la : lb;
  for (let i = 0; i < m; i++) {
    const d = wArena[oa + i] - wArena[ob + i];
    if (d !== 0) return d;
  }
  return la - lb;
}

// ---- pair table ----
const PEMPTY = -1;
let pKey1, pKey2, pCnt, pMask, pCount = 0;

function mix32(x) {
  x = (x ^ 0x9E3779B9) >>> 0;
  x = Math.imul(x ^ (x >>> 16), 0x21F0AA2C) >>> 0;
  x = Math.imul(x ^ (x >>> 15), 0x735A2D97) >>> 0;
  return (x ^ (x >>> 15)) >>> 0;
}

function pGrow() {
  const cap = pMask + 1, cap2 = cap * 2, m2 = cap2 - 1;
  const k1 = new Int32Array(cap2).fill(PEMPTY);
  const k2 = new Int32Array(cap2).fill(PEMPTY);
  const c2 = new Int32Array(cap2);
  for (let i = 0; i < cap; i++) {
    if (pKey1[i] !== PEMPTY) {
      let j = mix32(Math.imul(pKey1[i], 668265261) ^ pKey2[i]) & m2;
      while (k1[j] !== PEMPTY) j = (j + 1) & m2;
      k1[j] = pKey1[i]; k2[j] = pKey2[i]; c2[j] = pCnt[i];
    }
  }
  pKey1 = k1; pKey2 = k2; pCnt = c2; pMask = m2;
}

function pairAdd(id1, id2) {
  let i = mix32(Math.imul(id1, 668265261) ^ id2) & pMask;
  while (pKey1[i] !== PEMPTY) {
    if (pKey1[i] === id1 && pKey2[i] === id2) { pCnt[i]++; return; }
    i = (i + 1) & pMask;
  }
  if ((pCount + 1) * 3 > (pMask + 1) * 2) {
    pGrow();
    i = mix32(Math.imul(id1, 668265261) ^ id2) & pMask;
    while (pKey1[i] !== PEMPTY) i = (i + 1) & pMask;
  }
  pKey1[i] = id1; pKey2[i] = id2; pCnt[i] = 1;
  pCount++;
}

// negative if (c1,w1) ranks better (earlier in output) than (c2,w2)
function worse(c1, i1a, i1b, c2, i2a, i2b) {
  if (c1 !== c2) return c2 - c1;
  const d = cmpWords(i1a, i2a);
  if (d !== 0) return d;
  return cmpWords(i1b, i2b);
}

function siftDown(hCnt, hId1, hId2, size) {
  let p = 0;
  for (;;) {
    const l = 2 * p + 1, r = l + 1;
    let s = p;
    if (l < size && worse(hCnt[l], hId1[l], hId2[l], hCnt[s], hId1[s], hId2[s]) > 0) s = l;
    if (r < size && worse(hCnt[r], hId1[r], hId2[r], hCnt[s], hId1[s], hId2[s]) > 0) s = r;
    if (s === p) break;
    const tc = hCnt[p]; hCnt[p] = hCnt[s]; hCnt[s] = tc;
    const t1 = hId1[p]; hId1[p] = hId1[s]; hId1[s] = t1;
    const t2 = hId2[p]; hId2[p] = hId2[s]; hId2[s] = t2;
    p = s;
  }
}

function main() {
  const path = process.argv[2];
  if (!path) process.exit(1);
  const data = fs.readFileSync(path);
  const n = data.length;
  let totalWords = 0, totalPairs = 0;

  wMask = (1 << 16) - 1;
  wSlot = new Int32Array(1 << 16);
  wHash = new Int32Array(1 << 16);
  wOff = new Int32Array(4096);
  wLen = new Int32Array(4096);
  wArena = Buffer.allocUnsafe(1 << 16);

  pMask = (1 << 20) - 1;
  pKey1 = new Int32Array(1 << 20).fill(PEMPTY);
  pKey2 = new Int32Array(1 << 20).fill(PEMPTY);
  pCnt = new Int32Array(1 << 20);
  let wl = 0;
  let prev = -1;

  for (let i = 0; i < n; i++) {
    const c = data[i];
    const lc = c | 0x20;
    if (lc >= 97 && lc <= 122) {
      if (wl === wbuf.length) {
        const nb = new Uint8Array(wbuf.length * 2);
        nb.set(wbuf);
        wbuf = nb;
      }
      wbuf[wl++] = lc;
    } else {
      if (wl > 0) {
        totalWords++;
        let h = 2166136261 >>> 0;
        for (let k = 0; k < wl; k++) h = Math.imul(h ^ wbuf[k], 16777619) >>> 0;
        if (h === 0) h = 1;
        const id = wordFindOrAdd(wbuf, wl, h);
        if (prev >= 0) { totalPairs++; pairAdd(prev, id); }
        prev = id;
        wl = 0;
      }
      if (c === 46 || c === 33 || c === 63) prev = -1;
    }
  }
  if (wl > 0) {
    totalWords++;
    let h = 2166136261 >>> 0;
    for (let k = 0; k < wl; k++) h = Math.imul(h ^ wbuf[k], 16777619) >>> 0;
    if (h === 0) h = 1;
    const id = wordFindOrAdd(wbuf, wl, h);
    if (prev >= 0) { totalPairs++; pairAdd(prev, id); }
  }

  // top 20 via bounded min-heap (root = worst)
  let hc = 0;
  const hCnt = new Int32Array(21), hId1 = new Int32Array(21), hId2 = new Int32Array(21);
  for (let i = 0; i <= pMask; i++) {
    if (pKey1[i] === PEMPTY) continue;
    const c1 = pCnt[i], id1 = pKey1[i], id2 = pKey2[i];
    if (hc < 20) {
      let q = hc++;
      hCnt[q] = c1; hId1[q] = id1; hId2[q] = id2;
      while (q > 0) {
        const par = (q - 1) >> 1;
        if (worse(hCnt[q], hId1[q], hId2[q], hCnt[par], hId1[par], hId2[par]) <= 0) break;
        swapH(hCnt, hId1, hId2, q, par);
        q = par;
      }
    } else if (worse(c1, id1, id2, hCnt[0], hId1[0], hId2[0]) < 0) {
      hCnt[0] = c1; hId1[0] = id1; hId2[0] = id2;
      siftDown(hCnt, hId1, hId2, hc);
    }
  }

  const m = hc;
  const rCnt = new Int32Array(m), rId1 = new Int32Array(m), rId2 = new Int32Array(m);
  for (let idx = m - 1; idx >= 0; idx--) {
    rCnt[idx] = hCnt[0]; rId1[idx] = hId1[0]; rId2[idx] = hId2[0];
    hc--;
    hCnt[0] = hCnt[hc]; hId1[0] = hId1[hc]; hId2[0] = hId2[hc];
    siftDown(hCnt, hId1, hId2, hc);
  }
  for (let a = 1; a < m; a++) {
    const c = rCnt[a], i1 = rId1[a], i2 = rId2[a];
    let b = a - 1;
    while (b >= 0 && worse(rCnt[b], rId1[b], rId2[b], c, i1, i2) > 0) {
      rCnt[b + 1] = rCnt[b]; rId1[b + 1] = rId1[b]; rId2[b + 1] = rId2[b];
      b--;
    }
    rCnt[b + 1] = c; rId1[b + 1] = i1; rId2[b + 1] = i2;
  }

  // output
  const parts = [];
  parts.push("words " + totalWords + "\npairs " + totalPairs + "\ndistinct " + pCount + "\n");
  for (let idx = 0; idx < m; idx++) {
    const w1 = wArena.toString("latin1", wOff[rId1[idx]], wOff[rId1[idx]] + wLen[rId1[idx]]);
    const w2 = wArena.toString("latin1", wOff[rId2[idx]], wOff[rId2[idx]] + wLen[rId2[idx]]);
    parts.push(rCnt[idx] + " " + w1 + " " + w2 + "\n");
  }
  process.stdout.write(parts.join(""));
}

function swapH(hCnt, hId1, hId2, i, j) {
  let t = hCnt[i]; hCnt[i] = hCnt[j]; hCnt[j] = t;
  t = hId1[i]; hId1[i] = hId1[j]; hId1[j] = t;
  t = hId2[i]; hId2[i] = hId2[j]; hId2[j] = t;
}

main();
