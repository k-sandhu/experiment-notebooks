"use strict";
// Log scan: reads the file in large chunks into a Buffer, matches each line with a
// hand-written byte parser and interns path templates in an open-addressing hash table
// built on typed arrays, so no per-line strings are created.

const fs = require("fs");

const C_DIGIT = 1, C_LOWER = 2, C_PATH = 4;
const CT = new Uint8Array(256);
for (let c = 48; c <= 57; c++) CT[c] |= C_DIGIT | C_PATH;
for (let c = 97; c <= 122; c++) CT[c] |= C_LOWER | C_PATH;
for (let c = 65; c <= 90; c++) CT[c] |= C_PATH;
CT[95] |= C_PATH; // _
CT[45] |= C_PATH; // -
CT[47] |= C_PATH; // /

const NL = 10, SP = 32, QUOTE = 34, SLASH = 47, QMARK = 63;

// Template table
let arena = new Uint8Array(1 << 16);
let arenaLen = 0;
let tOff = new Int32Array(256), tLen = new Int32Array(256), tCount = new Int32Array(256);
let nTemplates = 0;
let slotId = new Int32Array(1024); // id + 1, 0 = empty
let slotHash = new Int32Array(1024);
let mask = 1023;

// Per well-formed line
let ids = new Int32Array(1 << 20);
let lats = new Float64Array(1 << 20);
let nGood = 0;

let lines = 0, malformed = 0;
const status = new Float64Array(10);

let tbuf = new Uint8Array(4096);

function intern(t, len, h) {
  let i = h & mask;
  for (;;) {
    const s = slotId[i];
    if (s === 0) break;
    if (slotHash[i] === h) {
      const id = s - 1;
      if (tLen[id] === len) {
        const off = tOff[id];
        let k = 0;
        while (k < len && arena[off + k] === t[k]) k++;
        if (k === len) {
          tCount[id]++;
          return id;
        }
      }
    }
    i = (i + 1) & mask;
  }
  const id = nTemplates++;
  if (id === tOff.length) {
    tOff = grownI32(tOff, id * 2);
    tLen = grownI32(tLen, id * 2);
    tCount = grownI32(tCount, id * 2);
  }
  if (arenaLen + len > arena.length) {
    const na = new Uint8Array(Math.max(arena.length * 2, arenaLen + len));
    na.set(arena.subarray(0, arenaLen));
    arena = na;
  }
  arena.set(t.subarray(0, len), arenaLen);
  tOff[id] = arenaLen;
  tLen[id] = len;
  tCount[id] = 1;
  arenaLen += len;
  slotId[i] = id + 1;
  slotHash[i] = h;
  if (nTemplates * 2 > slotId.length) grow();
  return id;
}

function grownI32(a, n) {
  const b = new Int32Array(n);
  b.set(a);
  return b;
}

function grow() {
  const oldId = slotId, oldHash = slotHash;
  slotId = new Int32Array(oldId.length * 2);
  slotHash = new Int32Array(oldId.length * 2);
  mask = slotId.length - 1;
  for (let j = 0; j < oldId.length; j++) {
    if (oldId[j] === 0) continue;
    let i = oldHash[j] & mask;
    while (slotId[i] !== 0) i = (i + 1) & mask;
    slotId[i] = oldId[j];
    slotHash[i] = oldHash[j];
  }
}

function isDigit(c) {
  return (c - 48) >>> 0 < 10;
}

// Parses the line starting at b[p] (terminated by '\n'). Returns the start of the next line
// if well-formed, otherwise ~pos where pos is inside the line, at or before its '\n'.
function parseLine(b, p) {
  if (!(isDigit(b[p]) && isDigit(b[p + 1]) && isDigit(b[p + 2]) && isDigit(b[p + 3]) && b[p + 4] === 45 &&
        isDigit(b[p + 5]) && isDigit(b[p + 6]) && b[p + 7] === 45 && isDigit(b[p + 8]) && isDigit(b[p + 9]) &&
        b[p + 10] === 84 && isDigit(b[p + 11]) && isDigit(b[p + 12]) && b[p + 13] === 58 && isDigit(b[p + 14]) &&
        isDigit(b[p + 15]) && b[p + 16] === 58 && isDigit(b[p + 17]) && isDigit(b[p + 18]) && b[p + 19] === 46 &&
        isDigit(b[p + 20]) && isDigit(b[p + 21]) && isDigit(b[p + 22]) && b[p + 23] === 90 && b[p + 24] === SP)) {
    return ~p;
  }
  p += 25;
  // Host: [a-z]+-\d+
  if ((CT[b[p]] & C_LOWER) === 0) return ~p;
  do p++; while ((CT[b[p]] & C_LOWER) !== 0);
  if (b[p] !== 45) return ~p;
  p++;
  if (!isDigit(b[p])) return ~p;
  do p++; while (isDigit(b[p]));
  if (b[p] !== SP) return ~p;
  p++;
  // Method
  switch (b[p]) {
    case 71: // G
      if (b[p + 1] !== 69 || b[p + 2] !== 84) return ~p;
      p += 3;
      break;
    case 80: // P
      if (b[p + 1] === 85 && b[p + 2] === 84) p += 3; // PUT
      else if (b[p + 1] === 79 && b[p + 2] === 83 && b[p + 3] === 84) p += 4; // POST
      else if (b[p + 1] === 65 && b[p + 2] === 84 && b[p + 3] === 67 && b[p + 4] === 72) p += 5; // PATCH
      else return ~p;
      break;
    case 68: // D
      if (b[p + 1] !== 69 || b[p + 2] !== 76 || b[p + 3] !== 69 || b[p + 4] !== 84 || b[p + 5] !== 69) return ~p;
      p += 6;
      break;
    default:
      return ~p;
  }
  if (b[p] !== SP) return ~p;
  p++;
  // Path, building the template as we go.
  if (b[p] !== SLASH) return ~p;
  p++;
  let t = tbuf;
  let o = 0;
  t[o++] = SLASH;
  let c;
  for (;;) {
    const seg = p;
    let allDigit = true;
    while (((CT[(c = b[p])] & C_PATH) !== 0) && c !== SLASH) {
      if ((c - 48) >>> 0 >= 10) allDigit = false;
      p++;
    }
    const n = p - seg;
    if (o + n + 5 > t.length) {
      const nt = new Uint8Array((o + n + 5) * 2);
      nt.set(t);
      tbuf = t = nt;
    }
    if (n !== 0 && allDigit) {
      t[o] = 123; // {
      t[o + 1] = 105; // i
      t[o + 2] = 100; // d
      t[o + 3] = 125; // }
      o += 4;
    } else {
      for (let k = seg; k < p; k++) t[o++] = b[k];
    }
    if (c !== SLASH) break;
    t[o++] = SLASH;
    p++;
  }
  if (c === QMARK) {
    do p++; while (b[p] !== SP && b[p] !== NL);
  }
  if (b[p] !== SP) return ~p;
  p++;
  // Status
  if (!(isDigit(b[p]) && isDigit(b[p + 1]) && isDigit(b[p + 2]) && b[p + 3] === SP)) return ~p;
  const cls = b[p] - 48;
  p += 4;
  // Size
  if (!isDigit(b[p])) return ~p;
  do p++; while (isDigit(b[p]));
  if (b[p] !== 66 || b[p + 1] !== SP) return ~p;
  p += 2;
  // Latency
  if (!isDigit(b[p])) return ~p;
  let lat = 0;
  do lat = lat * 10 + (b[p++] - 48); while (isDigit(b[p]));
  if (b[p] !== 46 || !isDigit(b[p + 1]) || b[p + 2] !== 109 || b[p + 3] !== 115 || b[p + 4] !== SP ||
      b[p + 5] !== QUOTE) {
    return ~p;
  }
  lat = lat * 10 + (b[p + 1] - 48);
  p += 6;
  // User agent
  while (b[p] !== QUOTE && b[p] !== NL) p++;
  if (b[p] !== QUOTE || b[p + 1] !== NL) return ~p;

  let h = 0x9e3779b9 ^ o;
  for (let i = 0; i < o; i++) h = Math.imul(h ^ t[i], 0x01000193);
  h ^= h >>> 15;
  h = Math.imul(h, 0x2c1b3c6d);
  h ^= h >>> 13;
  const id = intern(t, o, h);
  status[cls]++;
  if (nGood === ids.length) {
    const ni = new Int32Array(nGood * 2);
    ni.set(ids);
    ids = ni;
    const nl = new Float64Array(nGood * 2);
    nl.set(lats);
    lats = nl;
  }
  ids[nGood] = id;
  lats[nGood] = lat;
  nGood++;
  return p + 2;
}

// Processes all lines in b[0..lastNl]; returns the start of the unprocessed tail.
function processLines(b, lastNl) {
  let p = 0;
  let nLines = 0, nBad = 0;
  while (p <= lastNl) {
    nLines++;
    const r = parseLine(b, p);
    if (r >= 0) {
      p = r;
    } else {
      nBad++;
      p = ~r;
      while (b[p] !== NL) p++;
      p++;
    }
  }
  lines += nLines;
  malformed += nBad;
  return p;
}

function compareTemplates(a, b) {
  if (tCount[a] !== tCount[b]) return tCount[a] > tCount[b] ? -1 : 1;
  const la = tLen[a], lb = tLen[b], oa = tOff[a], ob = tOff[b];
  const n = Math.min(la, lb);
  for (let k = 0; k < n; k++) {
    const d = arena[oa + k] - arena[ob + k];
    if (d !== 0) return d;
  }
  return la - lb;
}

// Quickselect: places the k-th smallest at a[k], partitioned around it.
function select(a, lo, hi, k) {
  while (hi > lo) {
    const mid = (lo + hi) >>> 1;
    let x;
    if (a[mid] < a[lo]) { x = a[mid]; a[mid] = a[lo]; a[lo] = x; }
    if (a[hi] < a[lo]) { x = a[hi]; a[hi] = a[lo]; a[lo] = x; }
    if (a[hi] < a[mid]) { x = a[hi]; a[hi] = a[mid]; a[mid] = x; }
    const pivot = a[mid];
    let i = lo, j = hi;
    while (i <= j) {
      while (a[i] < pivot) i++;
      while (a[j] > pivot) j--;
      if (i <= j) {
        x = a[i]; a[i] = a[j]; a[j] = x;
        i++;
        j--;
      }
    }
    if (k <= j) hi = j;
    else if (k >= i) lo = i;
    else return;
  }
}

function fmtLat(v) {
  const whole = Math.floor(v / 10);
  return whole + "." + (v - whole * 10);
}

function main() {
  const fd = fs.openSync(process.argv[2], "r");
  let cap = 1 << 22;
  let buf = Buffer.allocUnsafe(cap + 8);
  let have = 0;
  for (;;) {
    const n = fs.readSync(fd, buf, have, cap - have, null);
    have += n;
    if (have === 0) break;
    let lastNl = buf.lastIndexOf(NL, have - 1);
    if (lastNl < 0) {
      if (n === 0) {
        buf[have] = NL;
        lastNl = have;
        have++;
      } else {
        if (have < cap) continue;
        cap *= 2;
        const nb = Buffer.allocUnsafe(cap + 8);
        buf.copy(nb, 0, 0, have);
        buf = nb;
        continue;
      }
    }
    const p = processLines(buf, lastNl);
    buf.copy(buf, 0, p, have);
    have -= p;
    if (n === 0 && have === 0) break;
  }
  fs.closeSync(fd);

  const top = [];
  for (let id = 0; id < nTemplates; id++) {
    if (top.length === 10 && compareTemplates(id, top[9]) >= 0) continue;
    let pos = top.length < 10 ? top.length : 9;
    if (top.length < 10) top.push(id);
    while (pos > 0 && compareTemplates(id, top[pos - 1]) < 0) {
      top[pos] = top[pos - 1];
      pos--;
    }
    top[pos] = id;
  }

  const rank = new Int32Array(nTemplates).fill(-1);
  const buckets = [];
  const fill = new Int32Array(top.length);
  for (let r = 0; r < top.length; r++) {
    rank[top[r]] = r;
    buckets.push(new Float64Array(tCount[top[r]]));
  }
  for (let i = 0; i < nGood; i++) {
    const r = rank[ids[i]];
    if (r >= 0) buckets[r][fill[r]++] = lats[i];
  }

  let out = "lines " + lines + "\nmalformed " + malformed + "\n";
  for (let c = 0; c < 10; c++) {
    if (status[c] !== 0) out += "status " + c + "xx " + status[c] + "\n";
  }
  for (let r = 0; r < top.length; r++) {
    const v = buckets[r];
    const n = v.length;
    const k50 = Math.floor((50 * n + 99) / 100) - 1, k95 = Math.floor((95 * n + 99) / 100) - 1;
    select(v, 0, n - 1, k50);
    const p50 = v[k50];
    select(v, k50, n - 1, k95);
    const p95 = v[k95];
    let mx = p95;
    for (let i = k95 + 1; i < n; i++) if (v[i] > mx) mx = v[i];
    const id = top[r];
    const key = Buffer.from(arena.buffer, arena.byteOffset + tOff[id], tLen[id]).toString("latin1");
    out += "path " + key + " " + n + " " + fmtLat(p50) + " " + fmtLat(p95) + " " + fmtLat(mx) + "\n";
  }
  fs.writeSync(1, out);
}

main();
