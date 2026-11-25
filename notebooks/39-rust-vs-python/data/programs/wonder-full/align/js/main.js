"use strict";
const fs = require("fs");
const data = fs.readFileSync(process.argv[2]);
const len = data.length;
let pos = 0;

function isWs(c) { return c === 32 || c === 10 || c === 13 || c === 9; }
function skipWs() { while (pos < len && isWs(data[pos])) pos++; }
function nextToken() {
  skipWs();
  const start = pos;
  while (pos < len && !isWs(data[pos])) pos++;
  return [start, pos - start];
}
function nextInt() {
  skipWs();
  let v = 0;
  while (pos < len && data[pos] >= 48 && data[pos] <= 57) v = v * 10 + (data[pos++] - 48);
  return v;
}

const [aStart, A] = nextToken();
const idx = new Int32Array(256);
for (let i = 0; i < A; i++) idx[data[aStart + i]] = i;
const ins = new Int32Array(A), del = new Int32Array(A), sub = new Int32Array(A * A);
for (let i = 0; i < A; i++) ins[i] = nextInt();
for (let i = 0; i < A; i++) del[i] = nextInt();
for (let i = 0; i < A * A; i++) sub[i] = nextInt();
const P = nextInt();

const out = [];
let total = 0;
let sIdx = new Int32Array(0), tIdx = new Int32Array(0);
let prev = new Int32Array(0), curr = new Int32Array(0);
let colIns = new Int32Array(0), subCols = new Int32Array(0);

for (let p = 0; p < P; p++) {
  const [sStart, sLen] = nextToken();
  const [tStart, tLen] = nextToken();
  let ans;
  let equal = sLen === tLen;
  if (equal) {
    for (let i = 0; i < sLen; i++) if (data[sStart + i] !== data[tStart + i]) { equal = false; break; }
  }
  if (equal) {
    ans = 0;
  } else {
    if (sIdx.length < sLen) sIdx = new Int32Array(sLen);
    if (tIdx.length < tLen) tIdx = new Int32Array(tLen);
    for (let i = 0; i < sLen; i++) sIdx[i] = idx[data[sStart + i]];
    for (let i = 0; i < tLen; i++) tIdx[i] = idx[data[tStart + i]];

    let rowStr, colStr, rowCost, colCost, R, C, transposed;
    if (tLen <= sLen) {
      rowStr = sIdx; colStr = tIdx; R = sLen; C = tLen;
      rowCost = del; colCost = ins; transposed = false;
    } else {
      rowStr = tIdx; colStr = sIdx; R = tLen; C = sLen;
      rowCost = ins; colCost = del; transposed = true;
    }

    if (colIns.length < C + 1) colIns = new Int32Array(C + 1);
    for (let j = 0; j < C; j++) colIns[j + 1] = colCost[colStr[j]];

    if (subCols.length < A * C) subCols = new Int32Array(A * C);
    if (!transposed) {
      for (let a = 0; a < A; a++) {
        const base = a * C, sbase = a * A;
        for (let j = 0; j < C; j++) subCols[base + j] = sub[sbase + colStr[j]];
      }
    } else {
      for (let b = 0; b < A; b++) {
        const base = b * C;
        for (let j = 0; j < C; j++) subCols[base + j] = sub[colStr[j] * A + b];
      }
    }

    if (prev.length < C + 1) { prev = new Int32Array(C + 1); curr = new Int32Array(C + 1); }
    prev[0] = 0;
    for (let j = 1; j <= C; j++) prev[j] = prev[j - 1] + colIns[j];

    for (let i = 0; i < R; i++) {
      const rc = rowStr[i];
      const d = rowCost[rc];
      const scBase = rc * C;
      let left = prev[0] + d;
      curr[0] = left;
      let diag = prev[0];
      for (let j = 1; j <= C; j++) {
        const up = prev[j];
        const x1 = diag + subCols[scBase + j - 1];
        const x2 = up + d;
        const x3 = left + colIns[j];
        let diff = x1 - x2;
        let best = x2 + (diff & (diff >> 31));
        diff = best - x3;
        best = x3 + (diff & (diff >> 31));
        curr[j] = best;
        diag = up;
        left = best;
      }
      const tmp = prev; prev = curr; curr = tmp;
    }
    ans = prev[C];
  }
  total += ans;
  out.push(ans);
}
process.stdout.write(out.join("\n") + "\ntotal " + total + "\n");
