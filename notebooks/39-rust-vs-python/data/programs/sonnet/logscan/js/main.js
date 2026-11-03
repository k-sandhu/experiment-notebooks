"use strict";

const fs = require("fs");

let arena = new Uint8Array(1 << 16);
let arenaLen = 0;
let eOff = new Int32Array(256);
let eLen = new Int32Array(256);
let eCount = new Int32Array(256);
let eHash = new Int32Array(256);
let nEntries = 0;
let table = null;
let tableMask = 0;
let recTid = new Int32Array(1 << 16);
let recLat = new Float64Array(1 << 16);
let nRec = 0;
let tmpl = new Uint8Array(1024);

let lines = 0;
let malformed = 0;
const statusCount = new Array(10).fill(0);

function growTable() {
  const cap = table === null ? 1024 : table.length * 2;
  table = new Int32Array(cap).fill(-1);
  tableMask = cap - 1;
  for (let i = 0; i < nEntries; i++) {
    let h = eHash[i] & tableMask;
    while (table[h] >= 0) h = (h + 1) & tableMask;
    table[h] = i;
  }
}

function lookup(t, len) {
  let h = 0x811c9dc5 | 0;
  for (let i = 0; i < len; i++) h = Math.imul(h ^ t[i], 0x01000193);
  h ^= h >>> 15;
  h = Math.imul(h, 0x2c1b3c6d);
  h ^= h >>> 13;
  let slot = h & tableMask;
  for (;;) {
    const id = table[slot];
    if (id < 0) break;
    if (eHash[id] === h && eLen[id] === len) {
      const off = eOff[id];
      let i = 0;
      while (i < len && arena[off + i] === t[i]) i++;
      if (i === len) return id;
    }
    slot = (slot + 1) & tableMask;
  }
  if (nEntries === eOff.length) {
    const c = nEntries * 2;
    let a;
    a = new Int32Array(c); a.set(eOff); eOff = a;
    a = new Int32Array(c); a.set(eLen); eLen = a;
    a = new Int32Array(c); a.set(eCount); eCount = a;
    a = new Int32Array(c); a.set(eHash); eHash = a;
  }
  if (arenaLen + len > arena.length) {
    const a = new Uint8Array(Math.max(arena.length * 2, arenaLen + len));
    a.set(arena);
    arena = a;
  }
  arena.set(t.subarray(0, len), arenaLen);
  const id = nEntries++;
  eOff[id] = arenaLen;
  eLen[id] = len;
  eCount[id] = 0;
  eHash[id] = h;
  arenaLen += len;
  if (nEntries * 2 > table.length) growTable();
  else table[slot] = id;
  return id;
}

function pathChar(c) {
  return (c >= 97 && c <= 122) || (c >= 65 && c <= 90) || (c >= 48 && c <= 57) || c === 95 || c === 47 || c === 45;
}

function dig(c) {
  return c >= 48 && c <= 57;
}

function match(b, p, w) {
  for (let i = 0; i < w.length; i++) if (b[p + i] !== w[i]) return false;
  return true;
}

const GET = [71, 69, 84, 32];
const PUT = [80, 85, 84, 32];
const POST = [80, 79, 83, 84, 32];
const PATCH = [80, 65, 84, 67, 72, 32];
const DELETE = [68, 69, 76, 69, 84, 69, 32];

function processLine(b, s, e) {
  lines++;
  let p = s;
  if (e - s < 40) { malformed++; return; }
  if (!(dig(b[p]) && dig(b[p + 1]) && dig(b[p + 2]) && dig(b[p + 3]) && b[p + 4] === 45 && dig(b[p + 5]) &&
    dig(b[p + 6]) && b[p + 7] === 45 && dig(b[p + 8]) && dig(b[p + 9]) && b[p + 10] === 84 && dig(b[p + 11]) &&
    dig(b[p + 12]) && b[p + 13] === 58 && dig(b[p + 14]) && dig(b[p + 15]) && b[p + 16] === 58 && dig(b[p + 17]) &&
    dig(b[p + 18]) && b[p + 19] === 46 && dig(b[p + 20]) && dig(b[p + 21]) && dig(b[p + 22]) && b[p + 23] === 90 &&
    b[p + 24] === 32)) { malformed++; return; }
  p += 25;
  let q = p;
  while (q < e && b[q] >= 97 && b[q] <= 122) q++;
  if (q === p || q >= e || b[q] !== 45) { malformed++; return; }
  q++;
  p = q;
  while (q < e && dig(b[q])) q++;
  if (q === p || q >= e || b[q] !== 32) { malformed++; return; }
  p = q + 1;
  if (e - p < 8) { malformed++; return; }
  const m = b[p];
  if (m === 71 && match(b, p, GET)) p += 4;
  else if (m === 80 && match(b, p, PUT)) p += 4;
  else if (m === 80 && match(b, p, POST)) p += 5;
  else if (m === 80 && match(b, p, PATCH)) p += 6;
  else if (m === 68 && match(b, p, DELETE)) p += 7;
  else { malformed++; return; }
  if (p >= e || b[p] !== 47) { malformed++; return; }
  const pathStart = p;
  p++;
  while (p < e && pathChar(b[p])) p++;
  const pathEnd = p;
  if (p >= e) { malformed++; return; }
  if (b[p] === 63) {
    p++;
    while (p < e && b[p] !== 32) p++;
    if (p >= e) { malformed++; return; }
  }
  if (b[p] !== 32) { malformed++; return; }
  p++;
  if (e - p < 5 || !(dig(b[p]) && dig(b[p + 1]) && dig(b[p + 2]) && b[p + 3] === 32)) { malformed++; return; }
  const cls = b[p] - 48;
  p += 4;
  q = p;
  while (q < e && dig(b[q])) q++;
  if (q === p || e - q < 2 || b[q] !== 66 || b[q + 1] !== 32) { malformed++; return; }
  p = q + 2;
  let lat = 0;
  q = p;
  while (q < e && dig(b[q])) { lat = lat * 10 + (b[q] - 48); q++; }
  if (q === p || e - q < 6 || b[q] !== 46 || !dig(b[q + 1]) || b[q + 2] !== 109 || b[q + 3] !== 115 ||
    b[q + 4] !== 32 || b[q + 5] !== 34) { malformed++; return; }
  lat = lat * 10 + (b[q + 1] - 48);
  p = q + 6;
  const last = e - 1;
  if (p > last || b[last] !== 34) { malformed++; return; }
  for (let i = p; i < last; i++) if (b[i] === 34) { malformed++; return; }

  statusCount[cls]++;
  const plen = pathEnd - pathStart;
  if (tmpl.length < plen * 4 + 8) tmpl = new Uint8Array(plen * 4 + 8);
  const t = tmpl;
  let o = 0;
  t[o++] = 47;
  let segStart = o;
  let allDigits = true;
  for (let c = pathStart + 1; ; c++) {
    if (c === pathEnd || b[c] === 47) {
      if (allDigits && o > segStart) {
        o = segStart;
        t[o++] = 123; t[o++] = 105; t[o++] = 100; t[o++] = 125;
      }
      if (c === pathEnd) break;
      t[o++] = 47;
      segStart = o;
      allDigits = true;
    } else {
      const ch = b[c];
      t[o++] = ch;
      if (ch < 48 || ch > 57) allDigits = false;
    }
  }
  const id = lookup(t, o);
  eCount[id]++;
  if (nRec === recTid.length) {
    let a = new Int32Array(nRec * 2); a.set(recTid); recTid = a;
    let d = new Float64Array(nRec * 2); d.set(recLat); recLat = d;
  }
  recTid[nRec] = id;
  recLat[nRec++] = lat;
}

function fmtLat(v) {
  return Math.floor(v / 10) + "." + (v % 10);
}

function main() {
  growTable();
  const fd = fs.openSync(process.argv[2], "r");
  let cap = 1 << 22;
  let buf = Buffer.allocUnsafe(cap);
  let have = 0;
  for (;;) {
    const n = fs.readSync(fd, buf, have, cap - have, null);
    const eof = n <= 0;
    if (!eof) have += n;
    const view = buf.subarray(0, have);
    let cur = 0;
    while (cur < have) {
      const nl = view.indexOf(10, cur);
      if (nl < 0) break;
      processLine(view, cur, nl);
      cur = nl + 1;
    }
    if (eof) {
      if (cur < have) processLine(view, cur, have);
      break;
    }
    const rest = have - cur;
    if (cur > 0) buf.copy(buf, 0, cur, have);
    have = rest;
    if (have === cap) {
      cap *= 2;
      const nb = Buffer.allocUnsafe(cap);
      buf.copy(nb, 0, 0, have);
      buf = nb;
    }
  }
  fs.closeSync(fd);

  const out = [];
  out.push("lines " + lines);
  out.push("malformed " + malformed);
  for (let c = 0; c < 10; c++) if (statusCount[c]) out.push("status " + c + "xx " + statusCount[c]);
  const order = [];
  for (let i = 0; i < nEntries; i++) order.push(i);
  const name = (i) => Buffer.from(arena.buffer, arena.byteOffset + eOff[i], eLen[i]);
  order.sort((a, b) => {
    if (eCount[a] !== eCount[b]) return eCount[b] - eCount[a];
    return Buffer.compare(name(a), name(b));
  });
  const top = Math.min(10, nEntries);
  for (let k = 0; k < top; k++) {
    const id = order[k];
    const cnt = eCount[id];
    const v = new Float64Array(cnt);
    let j = 0;
    let mx = 0;
    for (let i = 0; i < nRec; i++) {
      if (recTid[i] === id) {
        const x = recLat[i];
        v[j++] = x;
        if (x > mx) mx = x;
      }
    }
    const r50 = Math.floor((50 * cnt + 99) / 100);
    const r95 = Math.floor((95 * cnt + 99) / 100);
    let p50 = -1;
    let p95 = -1;
    if (mx < (1 << 22)) {
      const hist = new Int32Array(mx + 1);
      for (let i = 0; i < cnt; i++) hist[v[i]]++;
      let acc = 0;
      for (let b = 0; b <= mx; b++) {
        acc += hist[b];
        if (p50 < 0 && acc >= r50) p50 = b;
        if (acc >= r95) { p95 = b; break; }
      }
    } else {
      v.sort();
      p50 = v[r50 - 1];
      p95 = v[r95 - 1];
    }
    out.push("path " + name(id).toString("latin1") + " " + cnt + " " + fmtLat(p50) + " " + fmtLat(p95) + " " + fmtLat(mx));
  }
  fs.writeSync(1, out.join("\n") + "\n");
}

main();
