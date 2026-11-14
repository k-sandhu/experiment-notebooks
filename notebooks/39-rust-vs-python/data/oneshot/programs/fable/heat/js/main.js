'use strict';
const fs = require('fs');

function main() {
  const data = fs.readFileSync(process.argv[2]);
  const n = data.length;
  let pos = 0;

  function readInt() {
    while (pos < n) {
      const ch = data[pos];
      if (ch >= 48 && ch <= 57) break;
      pos++;
    }
    let v = 0;
    while (pos < n) {
      const ch = data[pos];
      if (ch < 48 || ch > 57) break;
      v = v * 10 + (ch - 48);
      pos++;
    }
    return v;
  }

  const H = readInt();
  const W = readInt();
  const S = readInt();

  const W2 = W + 2;
  const total = (H + 2) * W2;

  let cur = new Int32Array(total);
  let nxt = new Int32Array(total);
  const kind = new Uint8Array(total); // 0 = wall/outside, 1 = open, 2 = source
  const coef = new Int32Array(total);

  for (let r = 0; r < H; r++) {
    while (pos < n && (data[pos] === 10 || data[pos] === 13)) pos++;
    const base = (r + 1) * W2 + 1;
    for (let c = 0; c < W; c++) {
      const ch = pos < n ? data[pos] : 35;
      pos++;
      const i = base + c;
      if (ch === 46) {
        kind[i] = 1;
      } else if (ch >= 49 && ch <= 57) {
        kind[i] = 2;
        const v = (ch - 48) * 1000;
        cur[i] = v;
        nxt[i] = v;
      }
    }
  }

  // coef: for open cells 4 + number of wall/outside neighbours; for fixed cells 8.
  for (let i = 0; i < total; i++) coef[i] = 8;
  for (let r = 1; r <= H; r++) {
    const base = r * W2;
    for (let i = base + 1, e = base + W; i <= e; i++) {
      if (kind[i] === 1) {
        let k = 4;
        if (kind[i - 1] === 0) k++;
        if (kind[i + 1] === 0) k++;
        if (kind[i - W2] === 0) k++;
        if (kind[i + W2] === 0) k++;
        coef[i] = k;
      }
    }
  }

  for (let s = 0; s < S; s++) {
    const a = cur;
    const b = nxt;
    for (let r = 1; r <= H; r++) {
      const base = r * W2;
      const e = base + W;
      for (let i = base + 1; i <= e; i++) {
        const c = coef[i];
        b[i] =
          (Math.imul(c, a[i]) +
            ((a[i - 1] + a[i + 1] + a[i - W2] + a[i + W2]) & ((c - 8) >> 31))) >> 3;
      }
    }
    cur = b;
    nxt = a;
  }

  let T = 0n;
  let K = 0n;
  let V = -1;
  let R = 0;
  let C = 0;
  const bigW = BigInt(W);
  for (let r = 0; r < H; r++) {
    const base = (r + 1) * W2 + 1;
    let rowSum = 0;
    let rowWeighted = 0;
    for (let c = 0; c < W; c++) {
      const i = base + c;
      if (kind[i] === 1) {
        const v = cur[i];
        rowSum += v;
        rowWeighted += v * (c + 1);
        if (v > V) {
          V = v;
          R = r;
          C = c;
        }
      }
    }
    if (rowSum !== 0) {
      const bs = BigInt(rowSum);
      T += bs;
      K += bs * (BigInt(r) * bigW) + BigInt(rowWeighted);
    }
  }

  process.stdout.write(
    'sum ' + T.toString() + '\n' +
    'max ' + V + ' ' + R + ' ' + C + '\n' +
    'checksum ' + K.toString() + '\n'
  );
}

main();
