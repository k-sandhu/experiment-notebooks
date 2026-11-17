"use strict";
// Weighted edit distance for many pairs.
//
// With Q[j] = sum of column (insert) costs of C[1..j], the kernels store E[i][j] = D[i][j] - Q[j]:
//   E[i][j] = min(E[i-1][j] + rc, E[i-1][j-1] + adj[j], E[i][j-1]),  adj[j] = M[r][C_j] - cc[C_j]
// so the loop-carried dependency is a single min instead of add+min.
// V8 compiles int32 Math.min and comparisons to branches, which mispredict constantly here, so the
// kernels use the branchless min(a, b) = b + ((a - b) & ((a - b) >> 31)). All values stay within
// +-2^30 on the int32 path, so the differences cannot overflow.

const fs = require("fs");

// Two rows per pass: two independent running-min chains and half the row traffic.
function rows2(row, len, d1, d2, adj1, o1, adj2, o2) {
  let diag1 = row[0];
  let left1 = (diag1 + d1) | 0;
  let left2 = (left1 + d2) | 0;
  row[0] = left2;
  for (let j = 1; j < len; j++) {
    const up = row[j];
    let b = (diag1 + adj1[o1 + j]) | 0;
    let t = (up + d1 - b) | 0;
    let v1 = (b + (t & (t >> 31))) | 0;
    t = (v1 - left1) | 0;
    v1 = (left1 + (t & (t >> 31))) | 0;
    b = (left1 + adj2[o2 + j]) | 0;
    t = (v1 + d2 - b) | 0;
    let v2 = (b + (t & (t >> 31))) | 0;
    t = (v2 - left2) | 0;
    v2 = (left2 + (t & (t >> 31))) | 0;
    row[j] = v2;
    diag1 = up;
    left1 = v1;
    left2 = v2;
  }
}

function row1(row, len, d, adj, o) {
  let diag = row[0];
  let left = (diag + d) | 0;
  row[0] = left;
  for (let j = 1; j < len; j++) {
    const up = row[j];
    const b = (diag + adj[o + j]) | 0;
    let t = (up + d - b) | 0;
    let v = (b + (t & (t >> 31))) | 0;
    t = (v - left) | 0;
    v = (left + (t & (t >> 31))) | 0;
    row[j] = v;
    left = v;
    diag = up;
  }
}

function dp32(R, n, m, rc, adjStore, adjOff, row) {
  const len = m + 1;
  row.fill(0, 0, len);
  let i = 0;
  for (; i + 1 < n; i += 2) {
    const a1 = R[i], a2 = R[i + 1];
    rows2(row, len, rc[a1], rc[a2], adjStore, adjOff[a1], adjStore, adjOff[a2]);
  }
  if (i < n) row1(row, len, rc[R[i]], adjStore, adjOff[R[i]]);
  return row[m];
}

// adj[off + j] = M[base + C_j] - cc[C_j] for j = 1..m.
function buildAdj(adjStore, off, M, base, cc, C, m) {
  adjStore[off] = 0;
  for (let j = 0; j < m; j++) {
    const c = C[j];
    adjStore[off + 1 + j] = M[base + c] - cc[c];
  }
}

function markUsed(used, R, n) {
  used.fill(0);
  let nUsed = 0;
  for (let i = 0; i < n; i++) if (used[R[i]] === 0) { used[R[i]] = 1; nUsed++; }
  return nUsed;
}

function sumCosts(cc, C, m) {
  let q = 0;
  for (let j = 0; j < m; j++) q += cc[C[j]];
  return q;
}

// Double-precision fallback for extremely long strings, where values could exceed int32.
// All values stay far below 2^53, so doubles are exact.
function dp64(R, n, m, rc, adjStore, adjOff) {
  const row = new Float64Array(m + 1);
  for (let i = 0; i < n; i++) {
    const a = R[i];
    const d = rc[a];
    const o = adjOff[a];
    let diag = row[0];
    let left = diag + d;
    row[0] = left;
    for (let j = 1; j <= m; j++) {
      const up = row[j];
      let v = up + d;
      const t = diag + adjStore[o + j];
      if (t < v) v = t;
      if (left < v) v = left;
      row[j] = v;
      left = v;
      diag = up;
    }
  }
  return row[m];
}

function main() {
  const data = fs.readFileSync(process.argv[2]);
  const len = data.length;
  let p = 0;

  const idx = new Int8Array(256).fill(-1);
  let A = 0;
  while (p < len && data[p] >= 65 && data[p] <= 90) idx[data[p++]] = A++;

  function readInt() {
    while (p < len && (data[p] < 48 || data[p] > 57)) p++;
    let v = 0;
    while (p < len && data[p] >= 48 && data[p] <= 57) v = v * 10 + (data[p++] - 48);
    return v;
  }

  const insC = new Int32Array(26), delC = new Int32Array(26);
  const subM = new Int32Array(26 * 26), subT = new Int32Array(26 * 26);
  for (let i = 0; i < A; i++) insC[i] = readInt();
  for (let i = 0; i < A; i++) delC[i] = readInt();
  for (let i = 0; i < A; i++) {
    for (let j = 0; j < A; j++) {
      const v = readInt();
      subM[i * 26 + j] = v;
      subT[j * 26 + i] = v;
    }
  }
  const P = readInt();

  const words = [new Uint8Array(1024), new Uint8Array(1024)];
  let adjStore = new Int32Array(26 * 1024), row = new Int32Array(1024);
  const adjOff = new Int32Array(26);
  const used = new Uint8Array(26);
  const out = [];
  let total = 0n;

  // Reads the next word as letter indices into words[slot]; returns its length.
  function readWord(slot) {
    while (p < len && (data[p] < 65 || data[p] > 90)) p++;
    const q = p;
    while (p < len && data[p] >= 65 && data[p] <= 90) p++;
    const n = p - q;
    let w = words[slot];
    if (w.length < n) w = words[slot] = new Uint8Array(Math.max(n, w.length * 2));
    for (let k = 0; k < n; k++) w[k] = idx[data[q + k]];
    return n;
  }

  for (let k = 0; k < P; k++) {
    const ns = readWord(0), nt = readWord(1);
    const sBuf = words[0], tBuf = words[1];

    // Put the longer string on the inner (column) axis: transposing swaps insert/delete
    // and transposes the substitution table, leaving D[n][m] unchanged.
    let R, C, n, m, rc, cc, M;
    if (ns <= nt) { R = sBuf; n = ns; C = tBuf; m = nt; rc = delC; cc = insC; M = subM; }
    else { R = tBuf; n = nt; C = sBuf; m = ns; rc = insC; cc = delC; M = subT; }

    const nUsed = markUsed(used, R, n);
    const Q = sumCosts(cc, C, m);

    const stride = m + 1;
    if (adjStore.length < stride * nUsed) adjStore = new Int32Array(Math.max(stride * nUsed, adjStore.length * 2));
    let slot = 0;
    for (let a = 0; a < A; a++) {
      if (used[a] === 0) continue;
      const off = stride * slot++;
      adjOff[a] = off;
      buildAdj(adjStore, off, M, a * 26, cc, C, m);
    }

    let cost;
    if ((n + m + 4) * 1000 < 1 << 30) {
      if (row.length < stride) row = new Int32Array(Math.max(stride, row.length * 2));
      cost = dp32(R, n, m, rc, adjStore, adjOff, row) + Q;
    } else {
      cost = dp64(R, n, m, rc, adjStore, adjOff) + Q;
    }
    total += BigInt(cost);
    out.push(cost);
  }
  out.push("total " + total);
  fs.writeSync(1, out.join("\n") + "\n");
}

main();
