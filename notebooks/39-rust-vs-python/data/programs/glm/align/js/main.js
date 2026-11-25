"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
let pos = 0;
const end = data.length;
let tokStart = 0;
let tokLen = 0;

function isWs(c) {
  return c === 32 || c === 10 || c === 13 || c === 9;
}

function skipWs() {
  while (pos < end && isWs(data[pos])) pos++;
}

function nextInt() {
  skipWs();
  let neg = false;
  if (pos < end && (data[pos] === 45 || data[pos] === 43)) {
    neg = data[pos] === 45;
    pos++;
  }
  let v = 0;
  while (pos < end) {
    const c = data[pos];
    if (c >= 48 && c <= 57) {
      v = v * 10 + (c - 48);
      pos++;
    } else break;
  }
  return neg ? -v : v;
}

function nextToken() {
  skipWs();
  tokStart = pos;
  while (pos < end && !isWs(data[pos])) pos++;
  tokLen = pos - tokStart;
}

let rowBuf = new Int32Array(64);
let tIdxBuf = new Int32Array(64);
let insTBuf = new Int32Array(64);

function solve(sStart, sLen, tStart, tLen, idx, ins, del, sub) {
  const n = sLen;
  const m = tLen;
  let row = rowBuf;
  if (row.length < m + 1) {
    row = new Int32Array(m + 1);
    rowBuf = row;
  }
  let tIdx = tIdxBuf;
  let insT = insTBuf;
  if (tIdx.length < m) {
    tIdx = new Int32Array(m);
    tIdxBuf = tIdx;
    insT = new Int32Array(m);
    insTBuf = insT;
  }
  for (let j = 0; j < m; j++) {
    const c = idx[data[tStart + j]];
    tIdx[j] = c;
    insT[j] = ins[c];
  }

  row[0] = 0;
  for (let j = 0; j < m; j++) row[j + 1] = row[j] + insT[j];

  for (let i = 0; i < n; i++) {
    const si = idx[data[sStart + i]];
    const dl = del[si];
    const soff = si << 5;
    let diag = row[0];
    row[0] = diag + dl;
    for (let j = 0; j < m; j++) {
      const up = row[j + 1];
      let v = up + dl;
      const x1 = row[j] + insT[j];
      if (x1 < v) v = x1;
      const x2 = diag + sub[soff + tIdx[j]];
      if (x2 < v) v = x2;
      row[j + 1] = v;
      diag = up;
    }
  }
  return row[m];
}

function main() {
  nextToken();
  const A = tokLen;
  const idx = new Int16Array(256).fill(-1);
  for (let i = 0; i < A; i++) idx[data[tokStart + i]] = i;

  const ins = new Int32Array(A);
  const del = new Int32Array(A);
  const sub = new Int32Array(A << 5); // stride 32 rows
  for (let i = 0; i < A; i++) ins[i] = nextInt();
  for (let i = 0; i < A; i++) del[i] = nextInt();
  for (let i = 0; i < A; i++)
    for (let j = 0; j < A; j++) sub[(i << 5) + j] = nextInt();

  const P = nextInt();

  const lines = new Array(P);
  let total = 0;
  for (let q = 0; q < P; q++) {
    nextToken();
    const sStart = tokStart, n = tokLen;
    nextToken();
    const tStart = tokStart, m = tokLen;
    const cost = solve(sStart, n, tStart, m, idx, ins, del, sub);
    total += cost;
    lines[q] = cost;
  }
  lines.push("total " + total);
  process.stdout.write(lines.join("\n") + "\n");
}

main();
