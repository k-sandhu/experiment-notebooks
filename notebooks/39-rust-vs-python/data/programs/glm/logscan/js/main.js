"use strict";
const fs = require("fs");

const buf = fs.readFileSync(process.argv[2]);
const n = buf.length;

// ---- custom open-addressing hash map: template bytes (in arena) -> aggregate ----
let cap = 1024;
let mask = cap - 1;
let keyOff = new Int32Array(cap).fill(-1); // offset into arena, -1 = empty
let keyLen = new Int32Array(cap);
let aggIdx = new Int32Array(cap).fill(-1);
let used = 0;
let arena = new Uint8Array(1 << 16);
let arenaLen = 0;
const aggs = []; // { count, lats, n, capA }

function allocAgg() {
  const a = { count: 0, lats: new Float64Array(64), n: 0, capA: 64 };
  aggs.push(a);
  return aggs.length - 1;
}

function hashArena(off, len) {
  let h = 0x811c9dc5;
  for (let i = 0; i < len; i++) {
    h ^= arena[off + i];
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

function growMap() {
  const ncap = cap << 1;
  const noff = new Int32Array(ncap).fill(-1);
  const nlen = new Int32Array(ncap);
  const nidx = new Int32Array(ncap).fill(-1);
  const nmask = ncap - 1;
  for (let i = 0; i < cap; i++) {
    if (aggIdx[i] < 0) continue;
    const h = hashArena(keyOff[i], keyLen[i]);
    let slot = h & nmask;
    while (noff[slot] >= 0) slot = (slot + 1) & nmask;
    noff[slot] = keyOff[i];
    nlen[slot] = keyLen[i];
    nidx[slot] = aggIdx[i];
  }
  cap = ncap;
  mask = nmask;
  keyOff = noff;
  keyLen = nlen;
  aggIdx = nidx;
}

// ---- parsing ----
let scratch = new Uint8Array(4096);
let rCls = 0;
let rLat = 0;

const TS_DIGITS = [0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22];

function isDig(c) { return c >= 48 && c <= 57; }

// returns template length (>0) on success, else 0
function parseLine(s, e) {
  let p = s;
  if (e - p < 26) return 0;
  if (buf[p + 4] !== 45 || buf[p + 7] !== 45 || buf[p + 10] !== 84 || buf[p + 13] !== 58 ||
      buf[p + 16] !== 58 || buf[p + 19] !== 46 || buf[p + 23] !== 90 || buf[p + 24] !== 32) return 0;
  for (let t = 0; t < 17; t++) {
    const c = buf[p + TS_DIGITS[t]];
    if (c < 48 || c > 57) return 0;
  }
  p += 25;
  const s0 = p;
  while (p < e && buf[p] >= 97 && buf[p] <= 122) p++;
  if (p === s0 || p + 1 >= e || buf[p] !== 45) return 0;
  p++;
  const d0 = p;
  while (p < e && isDig(buf[p])) p++;
  if (p === d0 || p + 1 >= e || buf[p] !== 32) return 0;
  p++;
  // method: GET POST PUT DELETE PATCH
  if (e - p >= 4 && buf[p] === 71 && buf[p+1] === 69 && buf[p+2] === 84 && buf[p+3] === 32) p += 4;
  else if (e - p >= 5 && buf[p] === 80 && buf[p+1] === 79 && buf[p+2] === 83 && buf[p+3] === 84 && buf[p+4] === 32) p += 5;
  else if (e - p >= 4 && buf[p] === 80 && buf[p+1] === 85 && buf[p+2] === 84 && buf[p+3] === 32) p += 4;
  else if (e - p >= 7 && buf[p] === 68 && buf[p+1] === 69 && buf[p+2] === 76 && buf[p+3] === 69 && buf[p+4] === 84 && buf[p+5] === 69 && buf[p+6] === 32) p += 7;
  else if (e - p >= 6 && buf[p] === 80 && buf[p+1] === 65 && buf[p+2] === 84 && buf[p+3] === 67 && buf[p+4] === 72 && buf[p+5] === 32) p += 6;
  else return 0;
  // path: /[A-Za-z0-9_/-]* with all-digit segments -> {id}
  if (buf[p] !== 47) return 0;
  let tl = 0;
  const need = ((e - p) << 2) + 16;
  if (need > scratch.length) {
    let c2 = scratch.length;
    while (c2 < need) c2 <<= 1;
    scratch = new Uint8Array(c2);
  }
  const sc = scratch;
  while (true) {
    const segStart = tl;
    while (p < e) {
      const ch = buf[p];
      if ((ch >= 65 && ch <= 90) || (ch >= 97 && ch <= 122) || (ch >= 48 && ch <= 57) || ch === 95 || ch === 45) {
        sc[tl++] = ch;
        p++;
      } else break;
    }
    let allDig = tl > segStart;
    for (let q = segStart; allDig && q < tl; q++) {
      const ch = sc[q];
      if (ch < 48 || ch > 57) allDig = false;
    }
    if (allDig) {
      tl = segStart;
      sc[tl++] = 123; sc[tl++] = 105; sc[tl++] = 100; sc[tl++] = 125;
    }
    if (p < e && buf[p] === 47) { sc[tl++] = 47; p++; continue; }
    break;
  }
  if (p < e && buf[p] === 63) { p++; while (p < e && buf[p] !== 32) p++; }
  if (p + 1 >= e || buf[p] !== 32) return 0;
  p++;
  // status \d{3}
  if (e - p < 4 || !isDig(buf[p]) || !isDig(buf[p+1]) || !isDig(buf[p+2])) return 0;
  rCls = buf[p] - 48;
  p += 3;
  if (p + 1 >= e || buf[p] !== 32) return 0;
  p++;
  // size \d+B
  const b0 = p;
  while (p < e && isDig(buf[p])) p++;
  if (p === b0 || e - p < 2 || buf[p] !== 66 || buf[p+1] !== 32) return 0;
  p += 2;
  // latency \d+.\dms
  let l0 = p;
  while (p < e && isDig(buf[p])) p++;
  if (p === l0 || e - p < 5 || buf[p] !== 46 || !isDig(buf[p+1]) || buf[p+2] !== 109 || buf[p+3] !== 115 || buf[p+4] !== 32) return 0;
  let v;
  if (p - l0 > 18) {
    v = 1e15;  // saturate absurdly large latencies
  } else {
    v = 0;
    while (l0 < p) v = v * 10 + (buf[l0++] - 48);
    v = v * 10 + (buf[p+1] - 48);
    if (v > 1e15) v = 1e15;
  }
  p += 5;
  // user agent "[^"]*"
  if (buf[p] !== 34) return 0;
  p++;
  while (p < e && buf[p] !== 34) p++;
  if (p !== e - 1) return 0;

  rLat = v;
  return tl;
}

// ---- main loop ----
let lines = 0, malformed = 0;
const statusCnt = new Int32Array(10);
let i = 0;
outer:
while (i < n) {
  let j = buf.indexOf(10, i);
  if (j < 0) j = n;
  lines++;
  const tl = parseLine(i, j);
  if (tl > 0) {
    statusCnt[rCls]++;
    let h = 0x811c9dc5;
    for (let q = 0; q < tl; q++) {
      h ^= scratch[q];
      h = Math.imul(h, 0x01000193);
    }
    h = h >>> 0;
    let slot = h & mask;
    while (keyOff[slot] >= 0) {
      if (keyLen[slot] === tl) {
        const offA = keyOff[slot];
        let match = true;
        for (let q = 0; q < tl; q++) {
          if (arena[offA + q] !== scratch[q]) { match = false; break; }
        }
        if (match) {
          const a = aggs[aggIdx[slot]];
          a.count++;
          if (a.n === a.capA) {
            const nl = new Float64Array(a.capA << 1);
            nl.set(a.lats);
            a.lats = nl;
            a.capA <<= 1;
          }
          a.lats[a.n++] = rLat;
          i = j + 1;
          continue outer;
        }
      }
      slot = (slot + 1) & mask;
    }
    // miss: insert
    if (used + 1 > ((cap * 3) >> 2)) {
      growMap();
      slot = h & mask;
      while (keyOff[slot] >= 0) slot = (slot + 1) & mask;
    }
    if (arenaLen + tl > arena.length) {
      let na = arena.length;
      while (na < arenaLen + tl) na <<= 1;
      const nb = new Uint8Array(na);
      nb.set(arena);
      arena = nb;
    }
    keyOff[slot] = arenaLen;
    keyLen[slot] = tl;
    arena.set(scratch.subarray(0, tl), arenaLen);
    arenaLen += tl;
    const idx = allocAgg();
    aggIdx[slot] = idx;
    const a = aggs[idx];
    a.count = 1;
    a.lats[0] = rLat;
    a.n = 1;
    used++;
  } else {
    malformed++;
  }
  i = j + 1;
}

// ---- output ----
const parts = [];
parts.push("lines " + lines + "\nmalformed " + malformed + "\n");
for (let d = 0; d < 10; d++) {
  if (statusCnt[d] === 0) continue;
  parts.push("status " + d + "xx " + statusCnt[d] + "\n");
}
const tmplOf = new Array(aggs.length);
for (let s2 = 0; s2 < cap; s2++) {
  if (aggIdx[s2] >= 0) {
    tmplOf[aggIdx[s2]] = Buffer.from(arena.buffer, arena.byteOffset + keyOff[s2], keyLen[s2]).toString("latin1");
  }
}
const order = [];
for (let k = 0; k < aggs.length; k++) order.push(k);
order.sort((x, y) => {
  const cx = aggs[x].count, cy = aggs[y].count;
  if (cx !== cy) return cy - cx;
  return tmplOf[x] < tmplOf[y] ? -1 : tmplOf[x] > tmplOf[y] ? 1 : 0;
});
const top = Math.min(10, order.length);
for (let t = 0; t < top; t++) {
  const a = aggs[order[t]];
  const l = a.lats.subarray(0, a.n);
  l.sort();
  const m = a.n;
  const p50 = l[(((50 * m + 99) / 100) | 0) - 1];
  const p95 = l[(((95 * m + 99) / 100) | 0) - 1];
  const mx = l[m - 1];
  parts.push("path " + tmplOf[order[t]] + " " + a.count + " " +
    Math.floor(p50 / 10) + "." + (p50 % 10) + " " +
    Math.floor(p95 / 10) + "." + (p95 % 10) + " " +
    Math.floor(mx / 10) + "." + (mx % 10) + "\n");
}
process.stdout.write(parts.join(""));
