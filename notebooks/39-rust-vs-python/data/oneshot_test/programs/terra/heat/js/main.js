'use strict';

const fs = require('fs');
const input = fs.readFileSync(process.argv[2]);
let pos = 0;

function readInt() {
  while (pos < input.length && input[pos] <= 32) pos++;
  let value = 0;
  while (pos < input.length) {
    const ch = input[pos];
    if (ch < 48 || ch > 57) break;
    value = value * 10 + ch - 48;
    pos++;
  }
  return value;
}

const H = readInt();
const W = readInt();
const S = readInt();

const stride = W + 2;
const size = (H + 2) * stride;
let current = new Int32Array(size);
let next = new Int32Array(size);
current.fill(-1);
next.fill(-1);

const cells = new Uint32Array(H * W);
let count = 0;

for (let r = 0; r < H; r++) {
  while (pos < input.length && input[pos] <= 32) pos++;
  let index = (r + 1) * stride + 1;
  for (let c = 0; c < W; c++, index++, pos++) {
    const ch = input[pos];
    if (ch === 46) {
      current[index] = 0;
      next[index] = 0;
      cells[count++] = index;
    } else if (ch !== 35) {
      const value = (ch - 48) * 1000;
      current[index] = value;
      next[index] = value;
    }
  }
}

const up = new Uint32Array(count);
const down = new Uint32Array(count);
const left = new Uint32Array(count);
const right = new Uint32Array(count);

for (let j = 0; j < count; j++) {
  const i = cells[j];
  up[j] = current[i - stride] < 0 ? i : i - stride;
  down[j] = current[i + stride] < 0 ? i : i + stride;
  left[j] = current[i - 1] < 0 ? i : i - 1;
  right[j] = current[i + 1] < 0 ? i : i + 1;
}

for (let step = 0; step < S; step++) {
  let changed = 0;
  for (let j = 0; j < count; j++) {
    const i = cells[j];
    const old = current[i];
    const value = (
      4 * old +
      current[up[j]] +
      current[down[j]] +
      current[left[j]] +
      current[right[j]]
    ) >> 3;
    next[i] = value;
    changed |= old ^ value;
  }

  const temp = current;
  current = next;
  next = temp;
  if (changed === 0) break;
}

let sum = 0;
let max = -1;
let maxRow = 0;
let maxCol = 0;
let checksum = 0n;
let checksumPart = 0;

for (let j = 0; j < count; j++) {
  const i = cells[j];
  const value = current[i];
  const row = Math.floor(i / stride) - 1;
  const col = i % stride - 1;

  sum += value;
  if (value > max) {
    max = value;
    maxRow = row;
    maxCol = col;
  }

  checksumPart += value * (row * W + col + 1);
  if (checksumPart >= 281474976710656) {
    checksum += BigInt(checksumPart);
    checksumPart = 0;
  }
}

checksum += BigInt(checksumPart);

process.stdout.write(
  `sum ${sum}\nmax ${max} ${maxRow} ${maxCol}\nchecksum ${checksum}\n`
);
