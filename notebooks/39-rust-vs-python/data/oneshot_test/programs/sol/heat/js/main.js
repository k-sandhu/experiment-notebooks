'use strict';

const fs = require('fs');

function main() {
  let input = fs.readFileSync(process.argv[2]);
  let cursor = 0;

  function readInteger() {
    while (input[cursor] <= 32) cursor++;
    let value = 0;
    while (input[cursor] >= 48 && input[cursor] <= 57) {
      value = value * 10 + input[cursor++] - 48;
    }
    return value;
  }

  const H = readInteger();
  const W = readInteger();
  const steps = readInteger();
  const stride = W + 2;
  const size = (H + 2) * stride;

  const kind = new Uint8Array(size);
  const opens = new Uint32Array(H * W);
  let current = new Uint16Array(size);
  let next = new Uint16Array(size);
  let openCount = 0;
  let sourceCount = 0;

  for (let r = 0; r < H; r++) {
    while (input[cursor] <= 32) cursor++;

    let p = (r + 1) * stride + 1;
    for (let c = 0; c < W; c++, p++) {
      const ch = input[cursor++];
      if (ch === 46) {
        kind[p] = 1;
        opens[openCount++] = p;
      } else if (ch !== 35) {
        kind[p] = 2;
        const value = (ch - 48) * 1000;
        current[p] = value;
        next[p] = value;
        sourceCount++;
      }
    }
  }
  input = null;

  if (steps === 0 || sourceCount === 0) {
    const p = opens[0];
    const r = Math.floor(p / stride) - 1;
    const c = p - (r + 1) * stride - 1;
    process.stdout.write(`sum 0\nmax 0 ${r} ${c}\nchecksum 0\n`);
    return;
  }

  let regularCount = 0;
  for (let i = 0; i < openCount; i++) {
    const p = opens[i];
    if (
      kind[p - stride] !== 0 &&
      kind[p + stride] !== 0 &&
      kind[p - 1] !== 0 &&
      kind[p + 1] !== 0
    ) {
      kind[p] = 3;
      regularCount++;
    }
  }

  const boundaryCount = openCount - regularCount;
  const regular = new Uint32Array(regularCount);
  const boundary = new Uint32Array(boundaryCount);
  const up = new Uint32Array(boundaryCount);
  const down = new Uint32Array(boundaryCount);
  const left = new Uint32Array(boundaryCount);
  const right = new Uint32Array(boundaryCount);

  let ri = 0;
  let bi = 0;
  for (let i = 0; i < openCount; i++) {
    const p = opens[i];
    if (kind[p] === 3) {
      regular[ri++] = p;
    } else {
      boundary[bi] = p;
      up[bi] = kind[p - stride] !== 0 ? p - stride : p;
      down[bi] = kind[p + stride] !== 0 ? p + stride : p;
      left[bi] = kind[p - 1] !== 0 ? p - 1 : p;
      right[bi] = kind[p + 1] !== 0 ? p + 1 : p;
      bi++;
    }
  }

  for (let step = 0; step < steps; step++) {
    let changed = 0;

    for (let i = 0; i < regularCount; i++) {
      const p = regular[i];
      const old = current[p];
      const value = (
        (old << 2) +
        current[p - stride] +
        current[p + stride] +
        current[p - 1] +
        current[p + 1]
      ) >>> 3;

      next[p] = value;
      changed |= value ^ old;
    }

    for (let i = 0; i < boundaryCount; i++) {
      const p = boundary[i];
      const old = current[p];
      const value = (
        (old << 2) +
        current[up[i]] +
        current[down[i]] +
        current[left[i]] +
        current[right[i]]
      ) >>> 3;

      next[p] = value;
      changed |= value ^ old;
    }

    const temporary = current;
    current = next;
    next = temporary;

    if (changed === 0) break;
  }

  let sum = 0;
  let maximum = -1;
  let maximumPosition = 0;
  let checksumPart = 0;
  let checksumLarge = 0n;
  const safeLimit = Number.MAX_SAFE_INTEGER;

  for (let i = 0; i < openCount; i++) {
    const p = opens[i];
    const value = current[p];

    sum += value;

    if (value > maximum) {
      maximum = value;
      maximumPosition = p;
    }

    const paddedRow = Math.floor(p / stride);
    const weight = p - 2 * paddedRow - W;
    const term = value * weight;

    if (checksumPart > safeLimit - term) {
      checksumLarge += BigInt(checksumPart);
      checksumPart = term;
    } else {
      checksumPart += term;
    }
  }

  const maximumRow = Math.floor(maximumPosition / stride) - 1;
  const maximumColumn =
    maximumPosition - (maximumRow + 1) * stride - 1;
  const checksum = checksumLarge + BigInt(checksumPart);

  process.stdout.write(
    `sum ${sum}\n` +
    `max ${maximum} ${maximumRow} ${maximumColumn}\n` +
    `checksum ${checksum}\n`
  );
}

main();
