'use strict';

const fs = require('fs');
const input = fs.readFileSync(process.argv[2]);
let cursor = 0;

function readInteger() {
  while (input[cursor] <= 32) cursor++;
  let value = 0;
  while (cursor < input.length) {
    const digit = input[cursor] - 48;
    if (digit < 0 || digit > 9) break;
    value = value * 10 + digit;
    cursor++;
  }
  return value;
}

const H = readInteger();
const W = readInteger();
const S = readInteger();
while (input[cursor] <= 32) cursor++;

const size = H * W;
const ids = new Int32Array(size);
let current = new Uint16Array(size);
let next = new Uint16Array(size);
let openCount = 0;
let sourceCount = 0;

for (let r = 0, cell = 0; r < H; r++) {
  for (let c = 0; c < W; c++, cell++) {
    const ch = input[cursor++];
    if (ch === 46) {
      ids[cell] = openCount++;
    } else if (ch === 35) {
      ids[cell] = -1;
    } else {
      const id = size - 1 - sourceCount++;
      ids[cell] = id;
      current[id] = (ch - 48) * 1000;
    }
  }
  cursor++;
}
next.set(current);

const up = new Uint32Array(openCount);
const down = new Uint32Array(openCount);
const left = new Uint32Array(openCount);
const right = new Uint32Array(openCount);

for (let r = 0, cell = 0; r < H; r++) {
  for (let c = 0; c < W; c++, cell++) {
    const id = ids[cell];
    if (id < 0 || id >= openCount) continue;

    let neighbor = r > 0 ? ids[cell - W] : -1;
    up[id] = neighbor >= 0 ? neighbor : id;

    neighbor = r + 1 < H ? ids[cell + W] : -1;
    down[id] = neighbor >= 0 ? neighbor : id;

    neighbor = c > 0 ? ids[cell - 1] : -1;
    left[id] = neighbor >= 0 ? neighbor : id;

    neighbor = c + 1 < W ? ids[cell + 1] : -1;
    right[id] = neighbor >= 0 ? neighbor : id;
  }
}

for (let step = 0; step < S; step++) {
  for (let i = 0; i < openCount; i++) {
    next[i] = (
      (current[i] << 2) +
      current[up[i]] +
      current[down[i]] +
      current[left[i]] +
      current[right[i]]
    ) >>> 3;
  }

  const temporary = current;
  current = next;
  next = temporary;
}

let total = 0n;
let checksum = 0n;
let partialSum = 0;
let partialChecksum = 0;
let maximum = -1;
let maximumCell = 0;

for (let cell = 0; cell < size; cell++) {
  const id = ids[cell];
  if (id < 0 || id >= openCount) continue;

  const value = current[id];
  partialSum += value;
  partialChecksum += value * (cell + 1);

  if (value > maximum) {
    maximum = value;
    maximumCell = cell;
  }

  if (partialChecksum >= 4503599627370496) {
    total += BigInt(partialSum);
    checksum += BigInt(partialChecksum);
    partialSum = 0;
    partialChecksum = 0;
  }
}

total += BigInt(partialSum);
checksum += BigInt(partialChecksum);

const maximumRow = Math.floor(maximumCell / W);
const maximumColumn = maximumCell % W;

process.stdout.write(
  `sum ${total}\n` +
  `max ${maximum} ${maximumRow} ${maximumColumn}\n` +
  `checksum ${checksum}\n`
);
