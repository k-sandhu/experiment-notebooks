"use strict";
const fs = require("fs");
const buf = fs.readFileSync(process.argv[2]);
const n = buf.length;
let p = 0;
const hdr = [0, 0, 0];
for (let k = 0; k < 3; k++) {
  while (p < n && (buf[p] < 48 || buf[p] > 57)) p++;
  let v = 0;
  while (p < n && buf[p] >= 48 && buf[p] <= 57) { v = v * 10 + (buf[p] - 48); p++; }
  hdr[k] = v;
}
const H = hdr[0], W = hdr[1], S = hdr[2];
while (p < n && buf[p] !== 10) p++;
if (p < n) p++;
const N = H * W;
let cur = new Int32Array(N);
let nxt = new Int32Array(N);
const kind = new Uint8Array(N);
for (let r = 0; r < H; r++) {
  while (p < n && (buf[p] === 13 || buf[p] === 10)) p++;
  for (let c = 0; c < W; c++) {
    const ch = p < n ? buf[p++] : 46;
    const i = r * W + c;
    if (ch === 35) kind[i] = 0;
    else if (ch === 46) kind[i] = 1;
    else { kind[i] = 2; const v = 1000 * (ch - 48); cur[i] = v; nxt[i] = v; }
  }
}
const openIdx = new Int32Array(N); let nOpen = 0;
const runStart = new Int32Array(N); const runLen = new Int32Array(N); let nRuns = 0;
const eIdx = new Int32Array(N); const eU = new Int32Array(N); const eD = new Int32Array(N); const eL = new Int32Array(N); const eR = new Int32Array(N); let nEdge = 0;
for (let r = 0; r < H; r++) {
  let c = 0;
  while (c < W) {
    const i = r * W + c;
    if (kind[i] !== 1) { c++; continue; }
    const fast = r > 0 && r + 1 < H && c > 0 && c + 1 < W && kind[i - W] !== 0 && kind[i + W] !== 0 && kind[i - 1] !== 0 && kind[i + 1] !== 0;
    if (fast) {
      const start = i; let len = 0;
      while (c < W) {
        const j = r * W + c;
        if (kind[j] !== 1) break;
        if (!(r > 0 && r + 1 < H && c > 0 && c + 1 < W && kind[j - W] !== 0 && kind[j + W] !== 0 && kind[j - 1] !== 0 && kind[j + 1] !== 0)) break;
        openIdx[nOpen++] = j; len++; c++;
      }
      runStart[nRuns] = start; runLen[nRuns] = len; nRuns++;
    } else {
      openIdx[nOpen++] = i;
      eIdx[nEdge] = i;
      eU[nEdge] = (r > 0 && kind[i - W] !== 0) ? i - W : i;
      eD[nEdge] = (r + 1 < H && kind[i + W] !== 0) ? i + W : i;
      eL[nEdge] = (c > 0 && kind[i - 1] !== 0) ? i - 1 : i;
      eR[nEdge] = (c + 1 < W && kind[i + 1] !== 0) ? i + 1 : i;
      nEdge++; c++;
    }
  }
}
for (let step = 0; step < S; step++) {
  for (let ri = 0; ri < nRuns; ri++) {
    const start = runStart[ri], len = runLen[ri];
    for (let k = 0; k < len; k++) {
      const i = start + k;
      const old = cur[i];
      nxt[i] = ((old << 2) + cur[i - W] + cur[i + W] + cur[i - 1] + cur[i + 1]) >> 3;
    }
  }
  for (let k = 0; k < nEdge; k++) {
    const i = eIdx[k];
    const old = cur[i];
    nxt[i] = ((old << 2) + cur[eU[k]] + cur[eD[k]] + cur[eL[k]] + cur[eR[k]]) >> 3;
  }
  const t = cur; cur = nxt; nxt = t;
}
let sum = 0, checksum = 0;
let best = -1, bestIdx = nOpen > 0 ? openIdx[0] : 0;
for (let k = 0; k < nOpen; k++) {
  const i = openIdx[k], v = cur[i];
  sum += v; checksum += v * (i + 1);
  if (v > best) { best = v; bestIdx = i; }
}
const br = W !== 0 ? (bestIdx / W) | 0 : 0;
const bc = W !== 0 ? bestIdx % W : 0;
process.stdout.write(`sum ${sum}\nmax ${best} ${br} ${bc}\nchecksum ${checksum}\n`);
