'use strict';
const fs = require('fs');

const data = fs.readFileSync(process.argv[2], 'latin1').split('\n');
const first = data[0].trim().split(/\s+/).map(Number);
const H = first[0], W = first[1], S = first[2];
const W2 = W + 2;
const total = (H + 2) * W2;

let a = new Int32Array(total);
let b = new Int32Array(total);
const isWall = new Uint8Array(total).fill(1); // padding counts as wall

const idxList = [];
for (let r = 0; r < H; r++) {
  const line = data[1 + r];
  for (let c = 0; c < W; c++) {
    const ch = line.charCodeAt(c);
    const p = (r + 1) * W2 + c + 1;
    if (ch === 35) { // '#'
      // wall
    } else if (ch === 46) { // '.'
      isWall[p] = 0;
      idxList.push(p);
    } else {
      isWall[p] = 0;
      const v = (ch - 48) * 1000;
      a[p] = v;
      b[p] = v;
    }
  }
}

const n = idxList.length;
const idx = Int32Array.from(idxList);
const wt = new Int32Array(n);
for (let k = 0; k < n; k++) {
  const i = idx[k];
  wt[k] = 4 + isWall[i - 1] + isWall[i + 1] + isWall[i - W2] + isWall[i + W2];
}

let cur = a, nxt = b;
for (let s = 0; s < S; s++) {
  for (let k = 0; k < n; k++) {
    const i = idx[k];
    nxt[i] = (wt[k] * cur[i] + cur[i - 1] + cur[i + 1] + cur[i - W2] + cur[i + W2]) >> 3;
  }
  const t = cur; cur = nxt; nxt = t;
}

let sum = 0, best = -1, bestIdx = 0, checksum = 0;
for (let k = 0; k < n; k++) {
  const i = idx[k];
  const v = cur[i];
  sum += v;
  if (v > best) { best = v; bestIdx = i; }
  const r = Math.floor(i / W2) - 1;
  const c = (i % W2) - 1;
  checksum += v * (r * W + c + 1);
}
const R = Math.floor(bestIdx / W2) - 1;
const C = (bestIdx % W2) - 1;
console.log('sum ' + sum + '\nmax ' + best + ' ' + R + ' ' + C + '\nchecksum ' + checksum);
