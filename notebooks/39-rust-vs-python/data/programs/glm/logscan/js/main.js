"use strict";

const fs = require("fs");

// ---- open-addressing hash map: template (bytes) -> stats ----
let cap = 1024;          // table capacity (power of 2)
let mask = cap - 1;
let table = new Int32Array(cap); // entry index + 1, 0 = empty
let used = 0;
let numEntries = 0;

let keys = [];      // array of Uint8Array
let hashes = [];    // uint32
let counts = [];    // doubles (exact up to 2^53)
let lats = [];      // array of Int32Array (growable)
let latLens = [];

function growTable() {
  cap *= 2;
  mask = cap - 1;
  table = new Int32Array(cap);
  for (let e = 0; e < numEntries; e++) {
    let i = hashes[e] & mask;
    while (table[i] !== 0) i = (i + 1) & mask;
    table[i] = e + 1;
  }
}

function lookupKey(tbuf, len, h) {
  let i = h & mask;
  while (table[i] !== 0) {
    const e = table[i] - 1;
    if (hashes[e] === h) {
      const k = keys[e];
      if (k.length === len) {
        let eq = true;
        for (let z = 0; z < len; z++) {
          if (k[z] !== tbuf[z]) { eq = false; break; }
        }
        if (eq) return e;
      }
    }
    i = (i + 1) & mask;
  }
  // insert new entry
  keys.push(tbuf.slice(0, len));
  hashes.push(h);
  counts.push(0);
  lats.push(new Int32Array(16));
  latLens.push(0);
  numEntries++;
  table[i] = numEntries;
  used++;
  if (used * 10 >= cap * 7) growTable();
  return numEntries - 1;
}

function isd(c) { return c >= 48 && c <= 57; }

let tlen, tenths, cls, ps, pe;
let tbuf = new Uint8Array(512);

// validate line data[pos:pos+n]; on success fills ps, pe, tenths, cls, tbuf/tlen
function parse(data, base, n) {
  if (n < 50) return false;
  const end = base + n;
  let i = base;
  // timestamp: dddd-dd-ddTdd:dd:dd.dddZ
  if (!(isd(data[i]) && isd(data[i + 1]) && isd(data[i + 2]) && isd(data[i + 3]) &&
        data[i + 4] === 45 && isd(data[i + 5]) && isd(data[i + 6]) && data[i + 7] === 45 &&
        isd(data[i + 8]) && isd(data[i + 9]) && data[i + 10] === 84 &&
        isd(data[i + 11]) && isd(data[i + 12]) && data[i + 13] === 58 &&
        isd(data[i + 14]) && isd(data[i + 15]) && data[i + 16] === 58 &&
        isd(data[i + 17]) && isd(data[i + 18]) && data[i + 19] === 46 &&
        isd(data[i + 20]) && isd(data[i + 21]) && isd(data[i + 22]) && data[i + 23] === 90))
    return false;
  i += 24;
  if (data[i++] !== 32) return false;
  // host [a-z]+-\d+
  let st = i;
  while (i < end && data[i] >= 97 && data[i] <= 122) i++;
  if (i === st || i >= end || data[i] !== 45) return false;
  i++;
  st = i;
  while (i < end && isd(data[i])) i++;
  if (i === st || i >= end || data[i] !== 32) return false;
  i++;
  // method
  const rem = end - i;
  if (rem >= 4 && data[i] === 71 && data[i + 1] === 69 && data[i + 2] === 84 && data[i + 3] === 32) i += 4;
  else if (rem >= 4 && data[i] === 80 && data[i + 1] === 85 && data[i + 2] === 84 && data[i + 3] === 32) i += 4;
  else if (rem >= 5 && data[i] === 80 && data[i + 1] === 79 && data[i + 2] === 83 && data[i + 3] === 84 && data[i + 4] === 32) i += 5;
  else if (rem >= 6 && data[i] === 80 && data[i + 1] === 65 && data[i + 2] === 84 && data[i + 3] === 67 && data[i + 4] === 72 && data[i + 5] === 32) i += 6;
  else if (rem >= 7 && data[i] === 68 && data[i + 1] === 69 && data[i + 2] === 76 && data[i + 3] === 69 && data[i + 4] === 84 && data[i + 5] === 69 && data[i + 6] === 32) i += 7;
  else return false;
  if (end - i < 17) return false;
  if (data[i] !== 47) return false;
  ps = i;
  i++;
  while (i < end) {
    const c = data[i];
    if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122) || isd(c) || c === 95 || c === 45 || c === 47) i++;
    else break;
  }
  pe = i;
  if (i < end && data[i] === 63) {
    i++;
    while (i < end && data[i] !== 32) i++;
  }
  if (i >= end || data[i] !== 32) return false;
  i++;
  if (end - i < 15) return false;
  if (!(isd(data[i]) && isd(data[i + 1]) && isd(data[i + 2]))) return false;
  cls = data[i] - 48;
  i += 3;
  if (data[i++] !== 32) return false;
  if (end - i < 11) return false;
  st = i;
  while (i < end && isd(data[i])) i++;
  if (i === st || data[i] !== 66) return false;
  i++;
  if (data[i++] !== 32) return false;
  st = i;
  let v = 0;
  let nd = 0;
  while (i < end && isd(data[i])) {
    if (nd < 15) v = v * 10 + (data[i] - 48);
    i++; nd++;
  }
  if (i === st || data[i] !== 46) return false;
  i++;
  if (!isd(data[i])) return false;
  v = v * 10 + (data[i] - 48);
  i++;
  if (data[i] !== 109 || data[i + 1] !== 115 || data[i + 2] !== 32) return false;
  tenths = v > 4294967295 ? 4294967295 : v;
  i += 3;
  if (data[i] !== 34) return false;
  i++;
  while (i < end && data[i] !== 34) i++;
  if (i + 1 !== end) return false;

  // build template
  const need = (pe - ps) * 5 + 8;
  if (tbuf.length < need) tbuf = new Uint8Array(need * 2);
  let t = 0;
  let k = ps;
  while (k < pe) {
    tbuf[t++] = 47;
    k++;
    const s0 = k;
    while (k < pe && data[k] !== 47) k++;
    const slen = k - s0;
    let dig = slen > 0;
    for (let z = 0; dig && z < slen; z++) {
      if (!isd(data[s0 + z])) { dig = false; break; }
    }
    if (dig) {
      tbuf[t] = 123; tbuf[t + 1] = 105; tbuf[t + 2] = 100; tbuf[t + 3] = 125;
      t += 4;
    } else {
      for (let z = 0; z < slen; z++) tbuf[t + z] = data[s0 + z];
      t += slen;
    }
  }
  tlen = t;
  return true;
}

function main() {
  const data = fs.readFileSync(process.argv[2]);
  const n = data.length;

  let lines = 0, malformed = 0;
  const clsCount = new Float64Array(10);

  let i = 0;
  while (i < n) {
    let le = data.indexOf(10, i);
    if (le === -1) le = n;
    const len = le - i;
    lines++;

    if (parse(data, i, len)) {
      let h = 2166136261;
      for (let z = 0; z < tlen; z++) {
        h ^= tbuf[z];
        h = Math.imul(h, 16777619);
      }
      const e = lookupKey(tbuf, tlen, h >>> 0);
      counts[e]++;
      let la = lats[e];
      if (latLens[e] === la.length) {
        const nl = new Int32Array(la.length * 2);
        nl.set(la);
        lats[e] = nl;
        la = nl;
      }
      la[latLens[e]++] = tenths;
      clsCount[cls]++;
    } else {
      malformed++;
    }
    i = le + 1;
  }

  const ord = [];
  for (let e = 0; e < numEntries; e++) ord.push(e);
  ord.sort((a, b) => {
    if (counts[a] !== counts[b]) return counts[b] - counts[a];
    const ka = keys[a], kb = keys[b];
    const mn = Math.min(ka.length, kb.length);
    for (let z = 0; z < mn; z++) {
      if (ka[z] !== kb[z]) return ka[z] - kb[z];
    }
    return ka.length - kb.length;
  });

  let out = "lines " + lines + "\nmalformed " + malformed + "\n";
  for (let dd = 0; dd < 10; dd++) {
    if (clsCount[dd] > 0) out += "status " + dd + "xx " + clsCount[dd] + "\n";
  }
  const top = Math.min(10, numEntries);
  for (let r = 0; r < top; r++) {
    const e = ord[r];
    const la = lats[e].subarray(0, latLens[e]);
    la.sort(); // Int32Array sort is numeric
    const nn = la.length;
    const p50 = la[Math.ceil(50 * nn / 100) - 1];
    const p95 = la[Math.ceil(95 * nn / 100) - 1];
    const mx = la[nn - 1];
    out += "path " + Buffer.from(keys[e]).toString("latin1") + " " + counts[e] +
      " " + Math.floor(p50 / 10) + "." + (p50 % 10) +
      " " + Math.floor(p95 / 10) + "." + (p95 % 10) +
      " " + Math.floor(mx / 10) + "." + (mx % 10) + "\n";
  }
  process.stdout.write(out);
}

main();
