"use strict";
const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
let pos = 0;
function parseInt() {
  while (pos < data.length && (data[pos] < 48 || data[pos] > 57)) pos++;
  let v = 0;
  while (pos < data.length && data[pos] >= 48 && data[pos] <= 57) v = v * 10 + (data[pos++] - 48);
  return v;
}
const H = parseInt(), W = parseInt(), S = parseInt();
while (pos < data.length && data[pos] !== 10) pos++;
if (pos < data.length) pos++;
const N = H * W;
const grid = new Uint8Array(N); // 0 open, 1 wall, 2..10 source (digit+1)
let gi = 0;
for (let q = pos; q < data.length && gi < N; q++) {
  const c = data[q];
  if (c === 46) grid[gi++] = 0;        // '.'
  else if (c === 35) grid[gi++] = 1;   // '#'
  else if (c >= 49 && c <= 57) grid[gi++] = c - 47; // digit+1
}

let cur = new Int32Array(N);
let nxt = new Int32Array(N);
for (let i = 0; i < N; i++) {
  const g = grid[i];
  if (g >= 2) { const v = 1000 * (g - 1); cur[i] = v; nxt[i] = v; }
}

const runs = [];   // start,len
const spec = [];   // idx,up,down,left,right
const openIdx = [];
for (let r = 0; r < H; r++) {
  let runStart = -1;
  for (let c = 0; c < W; c++) {
    const i = r * W + c;
    if (grid[i] !== 0) {
      if (runStart >= 0) { runs.push(runStart, i - runStart); runStart = -1; }
      continue;
    }
    openIdx.push(i);
    const interior = r > 0 && r < H - 1 && c > 0 && c < W - 1
      && grid[i - W] !== 1 && grid[i + W] !== 1 && grid[i - 1] !== 1 && grid[i + 1] !== 1;
    if (interior) {
      if (runStart < 0) runStart = i;
    } else {
      if (runStart >= 0) { runs.push(runStart, i - runStart); runStart = -1; }
      const up = (r > 0 && grid[i - W] !== 1) ? i - W : i;
      const dn = (r < H - 1 && grid[i + W] !== 1) ? i + W : i;
      const lf = (c > 0 && grid[i - 1] !== 1) ? i - 1 : i;
      const rt = (c < W - 1 && grid[i + 1] !== 1) ? i + 1 : i;
      spec.push(i, up, dn, lf, rt);
    }
  }
  if (runStart >= 0) runs.push(runStart, r * W + W - runStart);
}
const runsA = Int32Array.from(runs);
const specA = Int32Array.from(spec);
const openA = Int32Array.from(openIdx);

function simulate(cur, nxt, runsA, specA, W, S) {
  for (let step = 0; step < S; step++) {
    const cp = cur, np = nxt;
    for (let ri = 0; ri < runsA.length; ri += 2) {
      const start = runsA[ri], len = runsA[ri + 1];
      const up = start - W, dn = start + W;
      for (let k = 0; k < len; k++) {
        const i = start + k;
        np[i] = (4 * cp[i] + cp[up + k] + cp[dn + k] + cp[i - 1] + cp[i + 1]) >> 3;
      }
    }
    for (let si = 0; si < specA.length; si += 5) {
      const i = specA[si];
      np[i] = (4 * cp[i] + cp[specA[si + 1]] + cp[specA[si + 2]] + cp[specA[si + 3]] + cp[specA[si + 4]]) >> 3;
    }
    const t = cur; cur = nxt; nxt = t;
  }
  return cur;
}
cur = simulate(cur, nxt, runsA, specA, W, S);

// checksum/sum can exceed 2^53? SPEC guarantees fit in int64; JS number is exact
// only to 2^53. Benchmark: max checksum ~ sum(v*(i+1)) <= 9000 * sum(1..160000)
// ~ 9000*1.28e10 = 1.15e14 < 9e15, safe. But use BigInt accumulation to be exact
// for any valid input within int64 range, at negligible cost (once over cells).
let sum = 0n, checksum = 0n;
let best = -1, bestIdx = openA.length > 0 ? openA[0] : 0;
for (let k = 0; k < openA.length; k++) {
  const i = openA[k];
  const v = cur[i];
  sum += BigInt(v);
  checksum += BigInt(v) * BigInt(i + 1);
  if (v > best) { best = v; bestIdx = i; }
}
if (best < 0) best = 0;
const br = W > 0 ? (bestIdx / W) | 0 : 0, bc = W > 0 ? bestIdx % W : 0;
process.stdout.write(`sum ${sum}\nmax ${best} ${br} ${bc}\nchecksum ${checksum}\n`);
