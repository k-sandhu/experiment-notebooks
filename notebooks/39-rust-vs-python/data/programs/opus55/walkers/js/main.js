"use strict";

const { Worker, isMainThread, parentPort, workerData } = require("node:worker_threads");
const fs = require("node:fs");

// SplitMix64 works on 64-bit integers; here each one is split into 32-bit halves (lo, hi).
const GAMMA_LO = 0x7f4a7c15, GAMMA_HI = 0x9e3779b9;
const MUL1_LO = 0x1ce4e5b9, MUL1_HI = 0xbf58476d;
const MUL2_LO = 0x133111eb, MUL2_HI = 0x94d049bb;
const INV_2_32 = 2.3283064365386963e-10;

// Runs shorter than this are not worth a trip through the unchecked loop.
const MIN_FAST_RUN = 4;

const DX = new Int32Array([1, -1, 0, 0]);
const DY = new Int32Array([0, 0, 1, -1]);

// Walks one walker from 64-bit state (sHi, sLo). Returns [x, y, bumps, returns].
//
// Each 64x64 multiply needs the high half of a 32x32 product: the double product is within 2^12 of the
// exact one, and subtracting the exact low half (Math.imul) leaves a multiple of 2^32 to round to.
// Only the top two bits of the output are used, and the final z ^ (z >>> 31) never changes them.
function walk(sHi, sLo, steps, bound) {
  const span = 2 * bound;
  let x = 0, y = 0, bumps = 0, returns = 0;
  let left = steps;
  while (left > 0) {
    const ax = Math.abs(x), ay = Math.abs(y);
    // Within `run` steps the walker can neither reach a wall nor the origin,
    // so those steps need no checks at all.
    let run = Math.min(bound - Math.max(ax, ay), ax + ay - 1);
    let checked = false;
    if (run >= MIN_FAST_RUN) {
      run = Math.min(run, left);
    } else {
      run = Math.min(MIN_FAST_RUN, left);
      checked = true;
    }
    left -= run;
    for (let i = 0; i < run; i++) {
      sLo = (sLo + GAMMA_LO) >>> 0;
      sHi = (sHi + GAMMA_HI + (sLo < GAMMA_LO ? 1 : 0)) >>> 0;
      let zl = (sLo ^ ((sLo >>> 30) | (sHi << 2))) >>> 0;
      let zh = sHi ^ (sHi >>> 30);
      let lo = Math.imul(zl, MUL1_LO) >>> 0;
      let hi = (((zl * MUL1_LO - lo) * INV_2_32 + 0.5) | 0) + Math.imul(zh, MUL1_LO) + Math.imul(zl, MUL1_HI);
      zl = (lo ^ ((lo >>> 27) | (hi << 5))) >>> 0;
      zh = hi ^ (hi >>> 27);
      lo = Math.imul(zl, MUL2_LO) >>> 0;
      hi = (((zl * MUL2_LO - lo) * INV_2_32 + 0.5) | 0) + Math.imul(zh, MUL2_LO) + Math.imul(zl, MUL2_HI);
      const d = (hi >>> 30) & 3;
      if (!checked) {
        x += DX[d];
        y += DY[d];
        continue;
      }
      // Checked step near a wall or the origin.
      const nx = x + DX[d], ny = y + DY[d];
      if (nx + bound >= 0 && nx + bound <= span && ny + bound >= 0 && ny + bound <= span) {
        x = nx;
        y = ny;
        if (x === 0 && y === 0) returns++;
      } else {
        bumps++;
      }
    }
  }
  return [x, y, bumps, returns];
}

// Walks walkers [from, to) and returns their results flattened, four numbers per walker.
function walkRange(from, to, seed, steps, bound) {
  const out = new Float64Array(4 * (to - from));
  const mask = (1n << 64n) - 1n;
  for (let j = from; j < to; j++) {
    const s = (seed + BigInt(j)) & mask;
    const r = walk(Number(s >> 32n), Number(s & 0xffffffffn), steps, bound);
    out.set(r, 4 * (j - from));
  }
  return out;
}

function main() {
  const fields = fs.readFileSync(process.argv[2], "latin1").trim().split(/\s+/);
  const walkers = Number(fields[0]);
  const steps = Number(fields[1]);
  // A walker never gets farther than `steps` from the origin, so a larger box behaves the same.
  const bound = Math.min(Number(fields[2]), steps);
  const seed = BigInt(fields[3]);
  const workers = Math.max(1, parseInt(process.argv[3] || "1", 10) || 1);

  const results = new Float64Array(4 * Math.max(walkers, 0));
  const threads = Math.min(workers, walkers);
  const rangeStart = (t) => Math.floor((walkers * t) / threads);
  let pending = threads > 0 ? threads - 1 : 0;

  const finish = () => {
    let spread = 0n, bumps = 0, returns = 0, bestJ = 0, bestD = -1;
    for (let j = 0; j < walkers; j++) {
      const x = results[4 * j], y = results[4 * j + 1];
      spread += BigInt(x * x + y * y);
      bumps += results[4 * j + 2];
      returns += results[4 * j + 3];
      const d = Math.abs(x) + Math.abs(y);
      if (d > bestD) {
        bestD = d;
        bestJ = j;
      }
    }
    if (bestD < 0) bestD = 0;
    process.stdout.write(`spread ${spread}\nbumps ${bumps}\nreturns ${returns}\nfarthest ${bestJ} ${bestD}\n`);
  };

  for (let t = 1; t < threads; t++) {
    const from = rangeStart(t), to = rangeStart(t + 1);
    const worker = new Worker(__filename, { workerData: { from, to, seed, steps, bound } });
    worker.once("message", (part) => {
      results.set(part, 4 * from);
      if (--pending === 0) finish();
    });
  }
  if (threads > 0) results.set(walkRange(0, rangeStart(1), seed, steps, bound), 0);
  if (pending === 0) finish();
}

if (isMainThread) {
  main();
} else {
  const { from, to, seed, steps, bound } = workerData;
  const part = walkRange(from, to, seed, steps, bound);
  parentPort.postMessage(part, [part.buffer]);
}
