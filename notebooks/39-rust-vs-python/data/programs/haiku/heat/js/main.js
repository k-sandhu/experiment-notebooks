"use strict";

// Heat on a grid (see SPEC.md).
//
// The grid is stored padded with a one-cell border of zeros, row stride W + 2, so every
// neighbour lookup is a plain offset. Walls and border cells always hold 0, so a wall
// neighbour contributes 0 and the "use own old value" rule becomes (8 - valid) * old.
// Values are int32 in typed arrays; all sums stay far below 2^53, so Numbers are exact.

const fs = require("fs");

const DOT = 46;  // '.'
const HASH = 35; // '#'

// One simulation step over the flat index range [begin, end).
// mask is -1 for open cells and 0 otherwise; fixed holds the constant value of sources.
function step(cur, nxt, mult, mask, fixed, begin, end, stride) {
  for (let i = begin; i < end; i++) {
    const sum = mult[i] * cur[i] + cur[i - 1] + cur[i + 1] + cur[i - stride] + cur[i + stride];
    nxt[i] = ((sum >> 3) & mask[i]) | fixed[i];
  }
}

function main() {
  const buf = fs.readFileSync(process.argv[2]);
  let p = 0;
  const readInt = () => {
    while (p < buf.length && (buf[p] < 48 || buf[p] > 57)) p++;
    let v = 0;
    while (p < buf.length && buf[p] >= 48 && buf[p] <= 57) v = v * 10 + (buf[p++] - 48);
    return v;
  };
  const H = readInt();
  const W = readInt();
  const S = readInt();

  const P = W + 2;
  const N = (H + 2) * P;
  const kind = new Uint8Array(N); // 0 = wall or border, 1 = open, 2 = source
  const mult = new Int32Array(N);
  const mask = new Int32Array(N);
  const fixed = new Int32Array(N);

  for (let r = 1; r <= H; r++) {
    for (let c = 1; c <= W; c++) {
      while (p < buf.length && !(buf[p] === DOT || buf[p] === HASH || (buf[p] >= 49 && buf[p] <= 57))) p++;
      if (p >= buf.length) break;
      const ch = buf[p++];
      const i = r * P + c;
      if (ch === DOT) {
        kind[i] = 1;
      } else if (ch !== HASH) {
        kind[i] = 2;
        fixed[i] = 1000 * (ch - 48);
      }
    }
  }

  for (let r = 1; r <= H; r++) {
    for (let c = 1; c <= W; c++) {
      const i = r * P + c;
      if (kind[i] === 1) {
        const valid = (kind[i - 1] !== 0) + (kind[i + 1] !== 0) + (kind[i - P] !== 0) + (kind[i + P] !== 0);
        mult[i] = 8 - valid;
        mask[i] = -1;
      }
    }
  }

  let cur = fixed.slice(); // sources start at their fixed value
  let nxt = fixed.slice();
  const rowsBegin = P;
  const rowsEnd = (H + 1) * P;
  for (let s = 0; s < S; s++) {
    step(cur, nxt, mult, mask, fixed, rowsBegin, rowsEnd, P);
    const t = cur;
    cur = nxt;
    nxt = t;
  }

  let total = 0;
  let checksum = 0;
  let bestV = -1;
  let bestR = -1;
  let bestC = -1;
  for (let r = 0; r < H; r++) {
    for (let c = 0; c < W; c++) {
      const i = (r + 1) * P + c + 1;
      if (kind[i] !== 1) continue;
      const v = cur[i];
      total += v;
      if (v > bestV) {
        bestV = v;
        bestR = r;
        bestC = c;
      }
      checksum += v * (r * W + c + 1);
    }
  }

  process.stdout.write(`sum ${total}\nmax ${bestV} ${bestR} ${bestC}\nchecksum ${checksum}\n`);
}

main();
