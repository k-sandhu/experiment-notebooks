"use strict";
const fs = require("fs");

const buf = fs.readFileSync(process.argv[2]);
let p = 0;
function readInt() {
  while (p < buf.length && (buf[p] < 48 || buf[p] > 57)) p++;
  let v = 0;
  while (p < buf.length && buf[p] >= 48 && buf[p] <= 57) v = v * 10 + (buf[p++] - 48);
  return v;
}
const H = readInt(), W = readInt(), S = readInt();
const w2 = W + 2, n = w2 * (H + 2);
let a = new Int32Array(n), b = new Int32Array(n);
const c = new Int32Array(n).fill(8), m = new Int32Array(n);
const open = new Uint8Array(n), wall = new Uint8Array(n).fill(1);
for (let r = 0; r < H; r++) {
  while (p < buf.length && buf[p] !== 46 && buf[p] !== 35 && (buf[p] < 49 || buf[p] > 57)) p++;
  for (let col = 0; col < W; col++) {
    const ch = buf[p++];
    const idx = (r + 1) * w2 + col + 1;
    if (ch === 46) { open[idx] = 1; wall[idx] = 0; m[idx] = -1; }
    else if (ch !== 35) { a[idx] = 1000 * (ch - 48); wall[idx] = 0; }
  }
}
for (let r = 1; r <= H; r++) {
  for (let col = 1; col <= W; col++) {
    const idx = r * w2 + col;
    if (!open[idx]) continue;
    c[idx] = 4 + wall[idx - 1] + wall[idx + 1] + wall[idx - w2] + wall[idx + w2];
  }
}
b.set(a);

function step(a, b, c, m, lo, hi, w2) {
  for (let i = lo; i < hi; i++) {
    b[i] = (c[i] * a[i] + ((a[i - 1] + a[i + 1] + a[i - w2] + a[i + w2]) & m[i])) >> 3;
  }
}

const lo = w2 + 1, hi = (H + 1) * w2 - 1;
for (let s = 0; s < S; s++) {
  step(a, b, c, m, lo, hi, w2);
  const t = a; a = b; b = t;
}
let sum = 0, best = -1, br = 0, bc = 0, chk = 0n, chkSmall = 0;
for (let r = 0; r < H; r++) {
  for (let col = 0; col < W; col++) {
    const idx = (r + 1) * w2 + col + 1;
    if (!open[idx]) continue;
    const v = a[idx];
    sum += v;
    if (v > best) { best = v; br = r; bc = col; }
    // flush to BigInt before the double accumulator can lose exactness
    chkSmall += v * (r * W + col + 1);
    if (chkSmall > 4e15) { chk += BigInt(chkSmall); chkSmall = 0; }
  }
}
chk += BigInt(chkSmall);
console.log(`sum ${sum}\nmax ${best} ${br} ${bc}\nchecksum ${chk}`);
