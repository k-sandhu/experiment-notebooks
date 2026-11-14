'use strict';
const fs = require('fs');

const text = fs.readFileSync(process.argv[2], 'latin1');
const len = text.length;
let pos = 0;

function readInt() {
  while (pos < len && text.charCodeAt(pos) <= 32) pos++;
  let x = 0;
  let c = text.charCodeAt(pos);
  while (c >= 48 && c <= 57) {
    x = x * 10 + (c - 48);
    pos++;
    c = text.charCodeAt(pos);
  }
  return x;
}

const H = readInt();
const W = readInt();
const S = readInt();

// Padded grid: one wall cell of border on every side, so neighbour reads never go out of range.
const P = W + 2;
const N = (H + 2) * P;
const op = new Uint8Array(N);      // 1 for open cell ('.') or source (digit)
let cur = new Int32Array(N);       // values, walls and border stay 0
let nxt = new Int32Array(N);

const total = H * W;
const updIdx = new Int32Array(total); // padded indices of '.' cells, row-major
const lin = new Int32Array(total);    // R*W + C + 1 for each such cell
let M = 0;

for (let r = 0; r < H; r++) {
  while (pos < len && text.charCodeAt(pos) <= 32) pos++;
  const base = pos;
  const rowBase = (r + 1) * P + 1;
  for (let c = 0; c < W; c++) {
    const ch = text.charCodeAt(base + c);
    if (ch === 46) {          // '.'
      const idx = rowBase + c;
      op[idx] = 1;
      updIdx[M] = idx;
      lin[M] = r * W + c + 1;
      M++;
    } else if (ch >= 49 && ch <= 57) { // '1'..'9'
      const idx = rowBase + c;
      op[idx] = 1;
      const v = 1000 * (ch - 48);
      cur[idx] = v;
      nxt[idx] = v;           // sources are fixed in both buffers
    }
  }
  pos = base + W;
}

// new = ((8 - k) * old + sum of open/source neighbour values) >> 3
// where k = number of open-or-source neighbours (walls contribute 0 to the array sum).
const wt = new Int32Array(M);
for (let j = 0; j < M; j++) {
  const i = updIdx[j];
  wt[j] = 8 - (op[i - 1] + op[i + 1] + op[i - P] + op[i + P]);
}

let a = cur, b = nxt;
for (let s = 0; s < S; s++) {
  for (let j = 0; j < M; j++) {
    const i = updIdx[j];
    b[i] = (wt[j] * a[i] + a[i - 1] + a[i + 1] + a[i - P] + a[i + P]) >> 3;
  }
  const t = a; a = b; b = t;
}

// Output over '.' cells only (sources are not open cells for output).
let T = 0;
let maxV = -1, maxJ = 0;
let K = 0, KB = 0n;
for (let j = 0; j < M; j++) {
  const v = a[updIdx[j]];
  T += v;
  if (v > maxV) { maxV = v; maxJ = j; }
  K += v * lin[j];
  if (K > 4e15) { KB += BigInt(K); K = 0; }
}
if (M === 0) maxV = 0;
const ml = M > 0 ? lin[maxJ] - 1 : 0;
const R = Math.floor(ml / W);
const C = ml - R * W;
KB += BigInt(K);

process.stdout.write(`sum ${T}\nmax ${maxV} ${R} ${C}\nchecksum ${KB}\n`);
