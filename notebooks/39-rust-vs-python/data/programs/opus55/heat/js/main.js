"use strict";
// Heat on a grid: exact integer diffusion with walls and fixed sources.
//
// The grid is zero-padded, walls hold 0, and for an open cell with w wall/outside neighbours
//   new = ((4 + w) * old + up + down + left + right) >> 3,
// which matches the spec's rule of replacing a missing neighbour by the cell's own value.
// One int per cell ("kind") drives a branch-free row loop:
//   open cell:   kind = (1 << 31) | (4 + w)   (negative, low bits = coefficient)
//   source/wall: kind = fixed value (0 for walls)
// Values never exceed 9000, so they live in Uint16Arrays.
//
// The iteration is monotone non-decreasing, so a row whose neighbourhood of rows did not change in the
// previous step cannot change; such rows are skipped, and a step with no change ends the run.

const fs = require("fs");

function row(src, dst, kind, from, to, stride) {
  let diff = 0;
  for (let i = from; i < to; i++) {
    const o = src[i];
    const k = kind[i];
    const open = k >> 31;
    let v = ((k & 15) * o + src[i - 1] + src[i + 1] + src[i - stride] + src[i + stride]) >> 3;
    v = (v & open) | (k & ~open);
    dst[i] = v;
    diff |= v ^ o;
  }
  return diff !== 0;
}

function simulate(a, b, kind, h, w, stride, steps) {
  let changed = new Uint8Array(h + 2);
  let nextChanged = new Uint8Array(h + 2);
  for (let r = 1; r <= h; r++) changed[r] = 1;
  let cur = a, nxt = b;
  for (let step = 0; step < steps; step++) {
    let any = false;
    for (let r = 1; r <= h; r++) {
      if ((changed[r - 1] | changed[r] | changed[r + 1]) === 0) {
        nextChanged[r] = 0;
        continue;
      }
      const from = r * stride + 1;
      const ch = row(cur, nxt, kind, from, from + w, stride);
      nextChanged[r] = ch ? 1 : 0;
      if (ch) any = true;
    }
    // Skipped rows hold equal values in both buffers, so swapping is safe.
    const t = cur; cur = nxt; nxt = t;
    const tc = changed; changed = nextChanged; nextChanged = tc;
    if (!any) break;
  }
  return cur;
}

function main() {
  const data = fs.readFileSync(process.argv[2]);
  let pos = 0;
  const readInt = () => {
    while (pos < data.length && (data[pos] < 48 || data[pos] > 57)) pos++;
    let v = 0;
    while (pos < data.length && data[pos] >= 48 && data[pos] <= 57) v = v * 10 + (data[pos++] - 48);
    return v;
  };
  const h = readInt();
  const w = readInt();
  const steps = readInt();

  const WALL = -1; // temporary marker during setup
  const OPEN = 1 << 31;
  const stride = w + 2;
  const total = (h + 2) * stride;
  const a = new Uint16Array(total);
  const kind = new Int32Array(total).fill(WALL);
  for (let r = 0; r < h; r++) {
    while (data[pos] === 13 || data[pos] === 10 || data[pos] === 32 || data[pos] === 9) pos++;
    const base = (r + 1) * stride + 1;
    for (let c = 0; c < w; c++) {
      const ch = data[pos + c];
      if (ch === 35) continue; // '#'
      const i = base + c;
      if (ch >= 49 && ch <= 57) {
        kind[i] = 1000 * (ch - 48);
        a[i] = kind[i];
      } else {
        kind[i] = OPEN;
      }
    }
    pos += w;
  }
  for (let r = 1; r <= h; r++) {
    for (let c = 1; c <= w; c++) {
      const i = r * stride + c;
      if (kind[i] === OPEN) {
        const walls = (kind[i - 1] === WALL) + (kind[i + 1] === WALL) +
          (kind[i - stride] === WALL) + (kind[i + stride] === WALL);
        kind[i] = OPEN | (4 + walls);
      }
    }
  }
  for (let i = 0; i < total; i++) if (kind[i] === WALL) kind[i] = 0;
  const b = a.slice();

  const cur = simulate(a, b, kind, h, w, stride, steps);

  let sum = 0, checksum = 0n, best = -1, bestR = 0, bestC = 0;
  for (let r = 0; r < h; r++) {
    const base = (r + 1) * stride + 1;
    let rowChk = 0; // sum of v * (c + 1) for this row; fits in a double exactly for any sane width
    let rowSum = 0;
    for (let c = 0; c < w; c++) {
      if (kind[base + c] >= 0) continue;
      const v = cur[base + c];
      rowSum += v;
      rowChk += v * (c + 1);
      if (v > best) { best = v; bestR = r; bestC = c; }
    }
    sum += rowSum;
    checksum += BigInt(rowSum) * BigInt(r) * BigInt(w) + BigInt(rowChk);
  }
  process.stdout.write(`sum ${sum}\nmax ${best} ${bestR} ${bestC}\nchecksum ${checksum}\n`);
}

main();
