"use strict";

// Random walkers: J independent SplitMix64-driven walks inside a box, spread over WORKERS worker threads.

const fs = require("node:fs");
const { Worker, isMainThread, parentPort, workerData } = require("node:worker_threads");

const MASK64 = (1n << 64n) - 1n;
const MASK32 = 0xffffffffn;

// 64-bit constants split into 32-bit halves. The state is kept as two int32 values (high, low)
// because BigInt is far too slow for the inner loop. Everything stays int32 so V8 never switches to doubles.
const GAMMA_HI = 0x9e3779b9 | 0;
const GAMMA_LO = 0x7f4a7c15 | 0;
const C1_HI = 0xbf58476d | 0;
const C1_LO = 0x1ce4e5b9 | 0;
const C2_HI = 0x94d049bb | 0;
const C2_LO = 0x133111eb | 0;

// High 32 bits of the unsigned 64-bit product of two 32-bit values (int32 bit patterns).
// Works on 16-bit pieces so that each partial product fits in 32 bits, using Math.imul for the low bits.
function mulHi32(a, b) {
  const a0 = a & 0xffff;
  const a1 = a >>> 16;
  const b0 = b & 0xffff;
  const b1 = b >>> 16;
  const p01 = Math.imul(a0, b1);
  const p10 = Math.imul(a1, b0);
  const mid = (Math.imul(a0, b0) >>> 16) + (p01 & 0xffff) + (p10 & 0xffff);
  return (Math.imul(a1, b1) + (p01 >>> 16) + (p10 >>> 16) + (mid >>> 16)) | 0;
}

// Walks walkers [first, last) and returns their totals.
function walkRange(first, last, steps, box, seed) {
  let spread = 0n;
  let bumps = 0;
  let returns = 0;
  let farDist = -1;
  let farWalker = 0;
  for (let j = first; j < last; j++) {
    const start = (seed + BigInt(j)) & MASK64;
    let sh = Number(start >> 32n) | 0;
    let sl = Number(start & MASK32) | 0;
    let x = 0;
    let y = 0;
    for (let i = 0; i < steps; i++) {
      // state += GAMMA on the two halves. The carry out of the low half is computed with bit operations
      // (no branch, since it is effectively random).
      const lo = (sl + GAMMA_LO) | 0;
      const carry = ((sl & GAMMA_LO) | ((sl | GAMMA_LO) & ~lo)) >>> 31;
      sh = (sh + GAMMA_HI + carry) | 0;
      sl = lo;

      // z = state; z ^= z >>> 30; z *= C1.
      let zh = sh;
      let zl = sl;
      zl ^= (zl >>> 30) | (zh << 2);
      zh ^= zh >>> 30;
      const h1 = (mulHi32(zl, C1_LO) + Math.imul(zh, C1_LO) + Math.imul(zl, C1_HI)) | 0;
      zl = Math.imul(zl, C1_LO);
      zh = h1;

      // z ^= z >>> 27; z *= C2.
      zl ^= (zl >>> 27) | (zh << 5);
      zh ^= zh >>> 27;
      const h2 = (mulHi32(zl, C2_LO) + Math.imul(zh, C2_LO) + Math.imul(zl, C2_HI)) | 0;
      zl = Math.imul(zl, C2_LO);
      zh = h2;

      // The top two bits of the final output are those of zh (the last xorshift cannot change them).
      // Step direction from d: sign is +1 or -1, and the masks select which axis moves.
      // Masks and bit operations keep every value an int32 (a multiply by 0 could give -0 and turn x into a double).
      const d = zh >>> 30;
      const maskY = -(d >>> 1);
      const maskSign = -(d & 1);
      const sign = (1 ^ maskSign) - maskSign;
      const nx = x + (sign & ~maskY);
      const ny = y + (sign & maskY);
      if (nx > box || nx < -box || ny > box || ny < -box) {
        bumps++;
      } else {
        x = nx;
        y = ny;
        if ((x | y) === 0) {
          returns++;
        }
      }
    }
    const dist = Math.abs(x) + Math.abs(y);
    const bx = BigInt(x);
    const by = BigInt(y);
    spread += bx * bx + by * by;
    // Walkers are visited in increasing order, so a strict comparison keeps the smallest index on a tie.
    if (dist > farDist) {
      farDist = dist;
      farWalker = j;
    }
  }
  return { spread, bumps, returns, farDist, farWalker };
}

async function main() {
  const [inputPath, workersArg] = process.argv.slice(2);
  const fields = fs.readFileSync(inputPath, "utf8").trim().split(/\s+/);
  const walkers = Number(fields[0]);
  const steps = Number(fields[1]);
  const box = Number(fields[2]);
  const seed = BigInt(fields[3]);

  const workers = Math.max(1, Math.min(Number(workersArg ?? 1), walkers));
  let results;
  if (workers === 1) {
    results = [walkRange(0, walkers, steps, box, seed)];
  } else {
    // Worker w handles the contiguous walkers [first, last).
    const jobs = [];
    for (let w = 0; w < workers; w++) {
      const first = Math.floor((walkers * w) / workers);
      const last = Math.floor((walkers * (w + 1)) / workers);
      jobs.push(
        new Promise((resolve, reject) => {
          const worker = new Worker(__filename, {
            workerData: { first, last, steps, box, seed: seed.toString() },
          });
          worker.once("message", resolve);
          worker.once("error", reject);
        }),
      );
    }
    results = await Promise.all(jobs);
  }

  // Results are in walker order, so the first part holding the maximum also holds the smallest index.
  let spread = 0n;
  let bumps = 0;
  let returns = 0;
  let farDist = -1;
  let farWalker = 0;
  for (const r of results) {
    spread += r.spread;
    bumps += r.bumps;
    returns += r.returns;
    if (r.farDist > farDist) {
      farDist = r.farDist;
      farWalker = r.farWalker;
    }
  }
  if (farDist < 0) {
    farDist = 0;
  }
  process.stdout.write(
    `spread ${spread}\nbumps ${bumps}\nreturns ${returns}\nfarthest ${farWalker} ${farDist}\n`,
  );
}

if (isMainThread) {
  main().catch((err) => {
    console.error(err);
    process.exitCode = 1;
  });
} else {
  const w = workerData;
  parentPort.postMessage(walkRange(w.first, w.last, w.steps, w.box, BigInt(w.seed)));
}
