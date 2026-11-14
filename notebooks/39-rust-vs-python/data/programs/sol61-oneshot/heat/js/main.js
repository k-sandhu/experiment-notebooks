'use strict';

const fs = require('fs');

function main() {
  const input = fs.readFileSync(process.argv[2]);
  let p = 0;

  function readInt() {
    while (input[p] <= 32) p++;
    let value = 0;
    while (p < input.length) {
      const digit = input[p] - 48;
      if (digit < 0 || digit > 9) break;
      value = value * 10 + digit;
      p++;
    }
    return value;
  }

  const H = readInt();
  const W = readInt();
  const S = readInt();

  while (p < input.length && input[p] <= 32) p++;

  const cellCount = H * W;
  const stride = W + 2;
  const grid = new Uint32Array((H + 2) * stride);

  let current = new Uint16Array(cellCount + 1);
  let next = new Uint16Array(cellCount + 1);

  let openCount = 0;
  let sourceCount = 0;
  let firstOpen = 0;

  for (let r = 0; r < H; r++) {
    let q = (r + 1) * stride + 1;

    for (let c = 0; c < W; c++, q++) {
      const ch = input[p++];

      if (ch === 46) {
        if (openCount === 0) firstOpen = r * W + c;
        grid[q] = ++openCount;
      } else if (ch >= 49 && ch <= 57) {
        const id = cellCount - sourceCount++;
        const value = (ch - 48) * 1000;
        grid[q] = id;
        current[id] = value;
        next[id] = value;
      }
    }

    if (input[p] === 13) p++;
    if (input[p] === 10) p++;
  }

  if (S === 0 || sourceCount === 0) {
    const row = Math.floor(firstOpen / W);
    const col = firstOpen - row * W;
    process.stdout.write(`sum 0\nmax 0 ${row} ${col}\nchecksum 0\n`);
    return;
  }

  const neighbors = new Uint32Array(openCount * 4);
  const positions = new Uint32Array(openCount + 1);

  for (let r = 0; r < H; r++) {
    let q = (r + 1) * stride + 1;

    for (let c = 0; c < W; c++, q++) {
      const id = grid[q];
      if (id === 0 || id > openCount) continue;

      const j = (id - 1) * 4;
      neighbors[j] = grid[q - stride] || id;
      neighbors[j + 1] = grid[q + stride] || id;
      neighbors[j + 2] = grid[q - 1] || id;
      neighbors[j + 3] = grid[q + 1] || id;
      positions[id] = r * W + c;
    }
  }

  for (let step = 0; step < S; step++) {
    let j = 0;

    for (let i = 1; i <= openCount; i++, j += 4) {
      next[i] = (
        4 * current[i] +
        current[neighbors[j]] +
        current[neighbors[j + 1]] +
        current[neighbors[j + 2]] +
        current[neighbors[j + 3]]
      ) >>> 3;
    }

    const temporary = current;
    current = next;
    next = temporary;
  }

  const batchSize = Math.max(
    1,
    Math.min(
      16384,
      Math.floor(Number.MAX_SAFE_INTEGER / (9000 * cellCount))
    )
  );

  let total = 0n;
  let checksum = 0n;
  let maximum = -1;
  let bestPosition = firstOpen;

  for (let start = 1; start <= openCount; start += batchSize) {
    const end = Math.min(start + batchSize, openCount + 1);
    let partialTotal = 0;
    let partialChecksum = 0;

    for (let i = start; i < end; i++) {
      const value = current[i];
      const position = positions[i];

      partialTotal += value;
      partialChecksum += value * (position + 1);

      if (value > maximum) {
        maximum = value;
        bestPosition = position;
      }
    }

    total += BigInt(partialTotal);
    checksum += BigInt(partialChecksum);
  }

  const bestRow = Math.floor(bestPosition / W);
  const bestCol = bestPosition - bestRow * W;

  process.stdout.write(
    `sum ${total}\n` +
    `max ${maximum} ${bestRow} ${bestCol}\n` +
    `checksum ${checksum}\n`
  );
}

main();
