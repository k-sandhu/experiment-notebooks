"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const n = data.length;

let scratch = Buffer.alloc(1024);

const tmpl = [];
const count = [];
const lat = [];
const latN = [];
let nEntries = 0;

let table = new Int32Array(2048);

let stStatus = 0;
let stLat = 0;
let stTlen = 0;

function hashScratch(len) {
  let h = 0x811c9dc5 | 0;
  const s = scratch;
  for (let i = 0; i < len; i++) {
    h = Math.imul(h ^ s[i], 16777619);
  }
  h ^= h >>> 16;
  return h;
}

function hashBytes(b) {
  let h = 0x811c9dc5 | 0;
  for (let i = 0; i < b.length; i++) {
    h = Math.imul(h ^ b[i], 16777619);
  }
  h ^= h >>> 16;
  return h;
}

function findEntry(len) {
  const mask = table.length - 1;
  let idx = hashScratch(len) & mask;
  for (;;) {
    const s = table[idx];
    if (s === 0) return -1;
    const e = s - 1;
    const t = tmpl[e];
    if (t.length === len) {
      let k = 0;
      while (k < len && t[k] === scratch[k]) k++;
      if (k === len) return e;
    }
    idx = (idx + 1) & mask;
  }
}

function addEntry(len) {
  const e = nEntries++;
  tmpl[e] = new Uint8Array(scratch.subarray(0, len));
  count[e] = 0;
  lat[e] = new Float64Array(16);
  latN[e] = 0;
  if (nEntries * 2 >= table.length) {
    const t2 = new Int32Array(table.length * 2);
    const mask = t2.length - 1;
    for (let i = 0; i < nEntries; i++) {
      let idx = hashBytes(tmpl[i]) & mask;
      while (t2[idx] !== 0) idx = (idx + 1) & mask;
      t2[idx] = i + 1;
    }
    table = t2;
  } else {
    const mask = table.length - 1;
    let idx = hashBytes(tmpl[e]) & mask;
    while (table[idx] !== 0) idx = (idx + 1) & mask;
    table[idx] = e + 1;
  }
}

function parseLine(p, le) {
  const d = data;
  if (le - p < 25) return false;
  if (!(d[p] >= 48 && d[p] <= 57 && d[p + 1] >= 48 && d[p + 1] <= 57 &&
        d[p + 2] >= 48 && d[p + 2] <= 57 && d[p + 3] >= 48 && d[p + 3] <= 57 && d[p + 4] === 45 &&
        d[p + 5] >= 48 && d[p + 5] <= 57 && d[p + 6] >= 48 && d[p + 6] <= 57 && d[p + 7] === 45 &&
        d[p + 8] >= 48 && d[p + 8] <= 57 && d[p + 9] >= 48 && d[p + 9] <= 57 && d[p + 10] === 84 &&
        d[p + 11] >= 48 && d[p + 11] <= 57 && d[p + 12] >= 48 && d[p + 12] <= 57 && d[p + 13] === 58 &&
        d[p + 14] >= 48 && d[p + 14] <= 57 && d[p + 15] >= 48 && d[p + 15] <= 57 && d[p + 16] === 58 &&
        d[p + 17] >= 48 && d[p + 17] <= 57 && d[p + 18] >= 48 && d[p + 18] <= 57 && d[p + 19] === 46 &&
        d[p + 20] >= 48 && d[p + 20] <= 57 && d[p + 21] >= 48 && d[p + 21] <= 57 &&
        d[p + 22] >= 48 && d[p + 22] <= 57 && d[p + 23] === 90 && d[p + 24] === 32)) {
    return false;
  }

  let j = p + 25;
  const i = j;
  while (j < le && d[j] >= 97 && d[j] <= 122) j++;
  if (j === i || j >= le || d[j] !== 45) return false;
  j++;
  const ds = j;
  while (j < le && d[j] >= 48 && d[j] <= 57) j++;
  if (j === ds || j >= le || d[j] !== 32) return false;
  j++;

  if (j + 4 <= le && d[j] === 71 && d[j + 1] === 69 && d[j + 2] === 84 && d[j + 3] === 32) {
    j += 4;
  } else if (j + 5 <= le && d[j] === 80 && d[j + 1] === 79 && d[j + 2] === 83 && d[j + 3] === 84 && d[j + 4] === 32) {
    j += 5;
  } else if (j + 4 <= le && d[j] === 80 && d[j + 1] === 85 && d[j + 2] === 84 && d[j + 3] === 32) {
    j += 4;
  } else if (j + 7 <= le && d[j] === 68 && d[j + 1] === 69 && d[j + 2] === 76 && d[j + 3] === 69 && d[j + 4] === 84 && d[j + 5] === 69 && d[j + 6] === 32) {
    j += 7;
  } else if (j + 6 <= le && d[j] === 80 && d[j + 1] === 65 && d[j + 2] === 84 && d[j + 3] === 67 && d[j + 4] === 72 && d[j + 5] === 32) {
    j += 6;
  } else {
    return false;
  }

  if (j >= le || d[j] !== 47) return false;
  let q = j + 1;
  while (q < le) {
    const c = d[q];
    if ((c >= 48 && c <= 57) || (c >= 65 && c <= 90) || (c >= 97 && c <= 122) ||
        c === 95 || c === 47 || c === 45) {
      q++;
    } else {
      break;
    }
  }

  let fieldEnd;
  if (q < le && d[q] === 63) {
    let r = q + 1;
    while (r < le && d[r] !== 32) r++;
    if (r >= le) return false;
    fieldEnd = r;
  } else if (q < le && d[q] === 32) {
    fieldEnd = q;
  } else {
    return false;
  }

  const need = (q - j) * 4 + 16;
  if (need > scratch.length) scratch = Buffer.alloc(need);
  const sc = scratch;
  let t = 0;
  let s = j;
  while (s < q) {
    if (d[s] === 47) {
      sc[t++] = 47;
      s++;
      continue;
    }
    let e = s;
    let allDig = true;
    while (e < q && d[e] !== 47) {
      if (d[e] < 48 || d[e] > 57) allDig = false;
      e++;
    }
    if (allDig) {
      sc[t] = 123; sc[t + 1] = 105; sc[t + 2] = 100; sc[t + 3] = 125;
      t += 4;
    } else {
      for (let k = s; k < e; k++) sc[t++] = d[k];
    }
    s = e;
  }

  let k = fieldEnd;
  if (k + 4 >= le) return false;
  if (!(d[k + 1] >= 48 && d[k + 1] <= 57 && d[k + 2] >= 48 && d[k + 2] <= 57 &&
        d[k + 3] >= 48 && d[k + 3] <= 57 && d[k + 4] === 32)) return false;
  stStatus = d[k + 1] - 48;
  k += 5;

  let e = k;
  while (e < le && d[e] >= 48 && d[e] <= 57) e++;
  if (e === k || e >= le || d[e] !== 66) return false;
  e++;
  if (e >= le || d[e] !== 32) return false;
  e++;

  const ls = e;
  let v = 0;
  while (e < le && d[e] >= 48 && d[e] <= 57) {
    v = v * 10 + (d[e] - 48);
    e++;
  }
  if (e === ls || e >= le || d[e] !== 46) return false;
  e++;
  if (e >= le || d[e] < 48 || d[e] > 57) return false;
  v = v * 10 + (d[e] - 48);
  e++;
  if (e + 3 >= le || d[e] !== 109 || d[e + 1] !== 115 || d[e + 2] !== 32) return false;
  e += 3;
  if (d[e] !== 34) return false;
  e++;
  let r = e;
  while (r < le && d[r] !== 34) r++;
  if (r !== le - 1) return false;

  stLat = v;
  stTlen = t;
  return true;
}

function cmpBytes(a, b) {
  const m = a.length < b.length ? a.length : b.length;
  for (let i = 0; i < m; i++) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return a.length - b.length;
}

function better(a, b) {
  if (count[a] !== count[b]) return count[a] > count[b];
  return cmpBytes(tmpl[a], tmpl[b]) < 0;
}

let lines = 0;
let malformed = 0;
const statusCount = new Array(10).fill(0);

let p = 0;
while (p < n) {
  let rel = data.indexOf(10, p);
  let le;
  if (rel < 0) { le = n; rel = -1; } else { le = rel; }
  lines++;
  if (parseLine(p, le)) {
    statusCount[stStatus]++;
    const len = stTlen;
    let e = findEntry(len);
    if (e < 0) {
      addEntry(len);
      e = nEntries - 1;
    }
    count[e]++;
    let a = lat[e];
    const k = latN[e];
    if (k === a.length) {
      const b = new Float64Array(k * 2);
      b.set(a);
      lat[e] = b;
      a = b;
    }
    a[k] = stLat;
    latN[e] = k + 1;
  } else {
    malformed++;
  }
  p = rel < 0 ? n : le + 1;
}

const best = [];
for (let e = 0; e < nEntries; e++) {
  let pos = 0;
  while (pos < best.length && better(best[pos], e)) pos++;
  if (pos < 10) {
    if (best.length < 10) best.push(0);
    best.copyWithin(pos + 1, pos);
    best[pos] = e;
  }
}

const outLines = [];
outLines.push("lines " + lines);
outLines.push("malformed " + malformed);
for (let c = 0; c < 10; c++) {
  if (statusCount[c] !== 0) {
    outLines.push("status " + c + "xx " + statusCount[c]);
  }
}
function tenths(v) {
  const ip = Math.floor(v / 10);
  return ip + "." + (v - ip * 10);
}
for (let bi = 0; bi < best.length; bi++) {
  const e = best[bi];
  const len = latN[e];
  const arr = lat[e].subarray(0, len);
  arr.sort();
  const i50 = Math.floor((50 * len + 99) / 100) - 1;
  const i95 = Math.floor((95 * len + 99) / 100) - 1;
  const tstr = Buffer.from(tmpl[e]).toString("latin1");
  outLines.push("path " + tstr + " " + count[e] + " " + tenths(arr[i50]) + " " +
                tenths(arr[i95]) + " " + tenths(arr[len - 1]));
}
process.stdout.write(outLines.join("\n") + "\n");
