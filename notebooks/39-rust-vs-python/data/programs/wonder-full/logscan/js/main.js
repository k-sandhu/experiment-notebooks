"use strict";
const fs = require("fs");

const str = fs.readFileSync(process.argv[2], "latin1");
const N = str.length;

// classification tables (latin1 => char codes 0..255)
const DIG = new Uint8Array(256);
const PCLS = new Uint8Array(256); // path char class: 0 invalid, 1 digit, 2 other, 3 '/'
for (let c = 48; c <= 57; c++) { DIG[c] = 1; PCLS[c] = 1; }
for (let c = 65; c <= 90; c++) PCLS[c] = 2;
for (let c = 97; c <= 122; c++) PCLS[c] = 2;
PCLS[95] = 2; PCLS[45] = 2; PCLS[47] = 3;

let gStatus = 0, gLatency = 0, gPathS = 0, gPathE = 0;
let segS = new Int32Array(32), segE = new Int32Array(32), segD = new Uint8Array(32);
let segN = 0, anyDigSeg = false;

function parseLine(s, e) {
  let i = s;
  if (i + 25 > e) return false;
  // timestamp: fixed 24 chars + space
  if (!(DIG[str.charCodeAt(i)] && DIG[str.charCodeAt(i+1)] && DIG[str.charCodeAt(i+2)] && DIG[str.charCodeAt(i+3)] &&
        str.charCodeAt(i+4) === 45 &&
        DIG[str.charCodeAt(i+5)] && DIG[str.charCodeAt(i+6)] && str.charCodeAt(i+7) === 45 &&
        DIG[str.charCodeAt(i+8)] && DIG[str.charCodeAt(i+9)] && str.charCodeAt(i+10) === 84 &&
        DIG[str.charCodeAt(i+11)] && DIG[str.charCodeAt(i+12)] && str.charCodeAt(i+13) === 58 &&
        DIG[str.charCodeAt(i+14)] && DIG[str.charCodeAt(i+15)] && str.charCodeAt(i+16) === 58 &&
        DIG[str.charCodeAt(i+17)] && DIG[str.charCodeAt(i+18)] && str.charCodeAt(i+19) === 46 &&
        DIG[str.charCodeAt(i+20)] && DIG[str.charCodeAt(i+21)] && DIG[str.charCodeAt(i+22)] &&
        str.charCodeAt(i+23) === 90 && str.charCodeAt(i+24) === 32)) return false;
  i += 25;
  // host [a-z]+-\d+
  {
    const hs = i;
    while (i < e) { const c = str.charCodeAt(i); if (c >= 97 && c <= 122) i++; else break; }
    if (i === hs) return false;
    if (i >= e || str.charCodeAt(i) !== 45) return false;
    i++;
    const ds = i;
    while (i < e && DIG[str.charCodeAt(i)]) i++;
    if (i === ds) return false;
    if (i >= e || str.charCodeAt(i) !== 32) return false;
    i++;
  }
  // method
  if (i >= e) return false;
  {
    const c0 = str.charCodeAt(i);
    if (c0 === 71) { // GET
      if (!(i + 4 <= e && str.charCodeAt(i+1) === 69 && str.charCodeAt(i+2) === 84 && str.charCodeAt(i+3) === 32)) return false;
      i += 4;
    } else if (c0 === 68) { // DELETE
      if (!(i + 7 <= e && str.charCodeAt(i+1) === 69 && str.charCodeAt(i+2) === 76 && str.charCodeAt(i+3) === 69 &&
            str.charCodeAt(i+4) === 84 && str.charCodeAt(i+5) === 69 && str.charCodeAt(i+6) === 32)) return false;
      i += 7;
    } else if (c0 === 80) { // P...
      if (i + 1 >= e) return false;
      const c1 = str.charCodeAt(i + 1);
      if (c1 === 79) { // POST
        if (!(i + 5 <= e && str.charCodeAt(i+2) === 83 && str.charCodeAt(i+3) === 84 && str.charCodeAt(i+4) === 32)) return false;
        i += 5;
      } else if (c1 === 85) { // PUT
        if (!(i + 4 <= e && str.charCodeAt(i+2) === 84 && str.charCodeAt(i+3) === 32)) return false;
        i += 4;
      } else if (c1 === 65) { // PATCH
        if (!(i + 6 <= e && str.charCodeAt(i+2) === 84 && str.charCodeAt(i+3) === 67 && str.charCodeAt(i+4) === 72 && str.charCodeAt(i+5) === 32)) return false;
        i += 6;
      } else return false;
    } else return false;
  }
  // path, collecting segments
  if (i >= e || str.charCodeAt(i) !== 47) return false;
  gPathS = i;
  segN = 0; anyDigSeg = false;
  {
    let ss = i, allDig = true;
    while (i < e) {
      const cls = PCLS[str.charCodeAt(i)];
      if (cls === 0) break;
      if (cls === 3) {
        if (segN === segS.length) {
          const a = new Int32Array(segN * 2); a.set(segS); segS = a;
          const b = new Int32Array(segN * 2); b.set(segE); segE = b;
          const c = new Uint8Array(segN * 2); c.set(segD); segD = c;
        }
        const dig = allDig && i > ss;
        segS[segN] = ss; segE[segN] = i; segD[segN] = dig ? 1 : 0; segN++;
        if (dig) anyDigSeg = true;
        ss = i + 1; allDig = true;
      } else if (cls === 2) allDig = false;
      i++;
    }
    if (segN === segS.length) {
      const a = new Int32Array(segN * 2 + 2); a.set(segS); segS = a;
      const b = new Int32Array(segN * 2 + 2); b.set(segE); segE = b;
      const c = new Uint8Array(segN * 2 + 2); c.set(segD); segD = c;
    }
    const dig = allDig && i > ss;
    segS[segN] = ss; segE[segN] = i; segD[segN] = dig ? 1 : 0; segN++;
    if (dig) anyDigSeg = true;
  }
  gPathE = i;
  // optional query ?[^ ]*
  if (i < e && str.charCodeAt(i) === 63) {
    const sp = str.indexOf(" ", i + 1);
    if (sp === -1 || sp >= e) return false;
    i = sp;
  }
  if (i >= e || str.charCodeAt(i) !== 32) return false;
  i++;
  // status \d{3}
  if (i + 3 > e || !DIG[str.charCodeAt(i)] || !DIG[str.charCodeAt(i+1)] || !DIG[str.charCodeAt(i+2)]) return false;
  gStatus = str.charCodeAt(i) - 48;
  i += 3;
  if (i >= e || str.charCodeAt(i) !== 32) return false;
  i++;
  // bytes \d+B
  {
    const ds = i;
    while (i < e && DIG[str.charCodeAt(i)]) i++;
    if (i === ds) return false;
    if (i >= e || str.charCodeAt(i) !== 66) return false;
    i++;
    if (i >= e || str.charCodeAt(i) !== 32) return false;
    i++;
  }
  // latency \d+\.\dms
  {
    const ds = i;
    let v = 0;
    while (i < e && DIG[str.charCodeAt(i)]) { v = v * 10 + (str.charCodeAt(i) - 48); i++; }
    if (i === ds) return false;
    if (i >= e || str.charCodeAt(i) !== 46) return false;
    i++;
    if (i >= e || !DIG[str.charCodeAt(i)]) return false;
    v = v * 10 + (str.charCodeAt(i) - 48);
    i++;
    gLatency = v;
    if (i + 2 > e || str.charCodeAt(i) !== 109 || str.charCodeAt(i+1) !== 115) return false;
    i += 2;
    if (i >= e || str.charCodeAt(i) !== 32) return false;
    i++;
  }
  // quoted UA "[^"]*" to end of line
  if (i >= e || str.charCodeAt(i) !== 34) return false;
  if (e - i < 2) return false;
  if (str.charCodeAt(e - 1) !== 34) return false;
  if (str.indexOf('"', i + 1) !== e - 1) return false;
  return true;
}

let lines = 0, malformed = 0;
const statusCnt = new Int32Array(10);
const templates = [];
const counts = [];
const map = new Map();

let cap = (N / 100 | 0) + 16;
let lats = new Int32Array(cap), ids = new Int32Array(cap);
let pairs = 0;

let pos = 0;
while (pos < N) {
  lines++;
  let lineEnd = str.indexOf("\n", pos);
  if (lineEnd === -1) lineEnd = N;
  if (parseLine(pos, lineEnd)) {
    statusCnt[gStatus]++;
    let tmpl;
    if (!anyDigSeg) {
      tmpl = str.slice(gPathS, gPathE);
    } else {
      tmpl = "";
      for (let k = 0; k < segN; k++) {
        if (k > 0) tmpl += "/";
        tmpl += segD[k] ? "{id}" : str.slice(segS[k], segE[k]);
      }
    }
    let id = map.get(tmpl);
    if (id === undefined) {
      id = templates.length;
      map.set(tmpl, id);
      templates.push(tmpl);
      counts.push(0);
    }
    counts[id]++;
    if (pairs === cap) {
      cap *= 2;
      const nl = new Int32Array(cap); nl.set(lats); lats = nl;
      const ni = new Int32Array(cap); ni.set(ids); ids = ni;
    }
    lats[pairs] = gLatency; ids[pairs] = id; pairs++;
  } else {
    malformed++;
  }
  pos = lineEnd + 1;
  if (lineEnd === N) break;
}

const T = templates.length;
const order = new Array(T);
for (let k = 0; k < T; k++) order[k] = k;
order.sort((a, b) => {
  if (counts[a] !== counts[b]) return counts[b] - counts[a];
  const ta = templates[a], tb = templates[b];
  return ta < tb ? -1 : ta > tb ? 1 : 0;
});
const K = Math.min(T, 10);
const tops = new Array(K);
const slot = new Int32Array(T).fill(-1);
for (let k = 0; k < K; k++) { slot[order[k]] = k; tops[k] = new Int32Array(counts[order[k]]); }
const fill = new Int32Array(K);
for (let q = 0; q < pairs; q++) {
  const s = slot[ids[q]];
  if (s >= 0) tops[s][fill[s]++] = lats[q];
}
for (let k = 0; k < K; k++) tops[k].sort();

function fmtLat(v) { return (v / 10 | 0) + "." + (v % 10); }
let out = "lines " + lines + "\n" + "malformed " + malformed + "\n";
for (let dig = 0; dig < 10; dig++) if (statusCnt[dig] > 0)
  out += "status " + dig + "xx " + statusCnt[dig] + "\n";
for (let k = 0; k < K; k++) {
  const id = order[k], vec = tops[k], nn = vec.length;
  const p50 = vec[Math.ceil(50 * nn / 100) - 1];
  const p95 = vec[Math.ceil(95 * nn / 100) - 1];
  const mx = vec[nn - 1];
  out += "path " + templates[id] + " " + counts[id] + " " + fmtLat(p50) + " " + fmtLat(p95) + " " + fmtLat(mx) + "\n";
}
process.stdout.write(out);
