"use strict";
const fs = require("fs");
const os = require("os");
const { Worker, isMainThread, parentPort, workerData } = require("worker_threads");

// SplitMix64 in 32-bit halves (signed int32 bit patterns). Lo/hi constants:
const GOLD_LO_U = 0x7f4a7c15; // unsigned value for carry arithmetic
const GOLD_HI = 0x9e3779b9 | 0;
const C1_LO = 0x1ce4e5b9 | 0;
const C1_HI = 0xbf58476d | 0;
const C2_LO = 0x133111eb | 0;
const C2_HI = 0x94d049bb | 0;
const DX = [1, -1, 0, 0];
const DY = [0, 0, 1, -1];

// High 32 bits of the unsigned 32x32 product a*b (a, b are int32 patterns).
function mulHi(a, b) {
  const a0 = a & 0xffff, a1 = a >>> 16;
  const b0 = b & 0xffff, b1 = b >>> 16;
  const p0 = a0 * b0;
  const p1 = a0 * b1;
  const p2 = a1 * b0;
  const p3 = a1 * b1;
  const t1 = (p0 >>> 16) + (p1 & 0xffff) + (p2 & 0xffff);
  const t2 = (p1 >>> 16) + (p2 >>> 16) + (p3 & 0xffff) + (t1 >>> 16);
  return (((p3 >>> 16) + (t2 >>> 16)) << 16) | (t2 & 0xffff);
}

// Direction (top 2 bits of SplitMix64 output) for the given state value.
function dirFromState(sLo, sHi) {
  // z = s; z ^= z >>> 30
  let zlo = sLo ^ ((sHi << 2) | (sLo >>> 30));
  let zhi = sHi ^ (sHi >>> 30);
  // z *= C1
  let nlo = Math.imul(zlo, C1_LO);
  let nhi = (mulHi(zlo, C1_LO) + Math.imul(zlo, C1_HI) + Math.imul(zhi, C1_LO)) | 0;
  zlo = nlo; zhi = nhi;
  // z ^= z >>> 27
  zlo = zlo ^ ((zhi << 5) | (zlo >>> 27));
  zhi = zhi ^ (zhi >>> 27);
  // z *= C2 -- only the high word is needed for the top 2 bits
  // (top bits of z ^ (z>>>31) equal top bits of z).
  nhi = (mulHi(zlo, C2_LO) + Math.imul(zlo, C2_HI) + Math.imul(zhi, C2_LO)) | 0;
  return nhi >>> 30;
}

// One walker's hot loop in its own function, so V8 tiers it up once and
// reuses the optimized code for every walker (instead of re-entering an
// inner loop). Returns [x, y, bumps, returns].
function walkOne(L, B, negB, sLo, sHi) {
  let x = 0, y = 0;
  let b = 0, r = 0;
  for (let i = 0; i < L; i++) {
    // state += GOLD
    const sumLo = (sLo >>> 0) + GOLD_LO_U;
    sLo = sumLo | 0;
    sHi = (sHi + GOLD_HI + (sumLo >= 4294967296 ? 1 : 0)) | 0;
    const d = dirFromState(sLo, sHi);
    const nx = x + DX[d], ny = y + DY[d];
    if (nx > B || nx < negB || ny > B || ny < negB) {
      b++;
    } else {
      x = nx; y = ny;
      if (x === 0 && y === 0) r++;
    }
  }
  return [x, y, b, r];
}

function runRange(begin, end, L, B, seedLo, seedHi) {
  let spread = 0, bumps = 0, returns = 0;
  let farIdx = begin, farDist = -1;
  const negB = -B;
  const seedLoU = seedLo >>> 0;
  for (let j = begin; j < end; j++) {
    // state = seed + j (mod 2^64)
    const jLoU = j % 4294967296;
    const jHi = Math.floor(j / 4294967296);
    const sumLo = seedLoU + jLoU;
    const sLo = sumLo | 0;
    const sHi = (seedHi + jHi + (sumLo >= 4294967296 ? 1 : 0)) | 0;
    const res = walkOne(L, B, negB, sLo, sHi);
    const x = res[0], y = res[1];
    bumps += res[2]; returns += res[3];
    spread += x * x + y * y;
    const dist = Math.abs(x) + Math.abs(y);
    if (dist > farDist) { farDist = dist; farIdx = j; }
  }
  return { spread, bumps, returns, farIdx, farDist };
}

function printResult(p) {
  const farDist = p.farDist < 0 ? 0 : p.farDist;
  process.stdout.write(
    "spread " + p.spread + "\nbumps " + p.bumps + "\nreturns " + p.returns +
    "\nfarthest " + p.farIdx + " " + farDist + "\n");
}

if (!isMainThread) {
  const wd = workerData;
  const res = runRange(wd.begin, wd.end, wd.L, wd.B, wd.seedLo, wd.seedHi);
  parentPort.postMessage(res);
} else {
  const text = fs.readFileSync(process.argv[2], "utf8").trim();
  const tok = text.split(/\s+/);
  const J = Number(tok[0]);
  const L = Number(tok[1]);
  let B = Number(tok[2]);
  if (B > 2147483647) B = 2147483647;
  const seed = BigInt(tok[3]);
  const seedLo = Number(seed & 0xffffffffn) | 0;
  const seedHi = Number((seed >> 32n) & 0xffffffffn) | 0;

  let workers = process.argv.length >= 4 ? parseInt(process.argv[3], 10)
    : os.availableParallelism();
  if (!(workers >= 1)) workers = 1;
  if (workers > 32) workers = 32;
  if (J > 0 && workers > J) workers = J;
  if (workers < 1) workers = 1;

  if (J <= 0) {
    process.stdout.write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
  } else if (workers === 1) {
    printResult(runRange(0, J, L, B, seedLo, seedHi));
  } else {
    const ranges = [];
    const base = Math.floor(J / workers), rem = J % workers;
    let start = 0;
    for (let w = 0; w < workers; w++) {
      const cnt = base + (w < rem ? 1 : 0);
      ranges.push([start, start + cnt]);
      start += cnt;
    }
    const promises = [];
    for (let w = 1; w < workers; w++) {
      const worker = new Worker(__filename, {
        workerData: { begin: ranges[w][0], end: ranges[w][1], L, B, seedLo, seedHi },
      });
      promises.push(new Promise((resolve, reject) => {
        worker.once("message", resolve);
        worker.once("error", reject);
      }));
    }
    // Main thread does the first chunk while workers run.
    const first = runRange(ranges[0][0], ranges[0][1], L, B, seedLo, seedHi);
    Promise.all(promises).then((rest) => {
      const parts = [first, ...rest];
      let spread = 0, bumps = 0, returns = 0, farIdx = 0, farDist = -1;
      for (const pt of parts) {
        spread += pt.spread; bumps += pt.bumps; returns += pt.returns;
        if (pt.farDist > farDist) { farDist = pt.farDist; farIdx = pt.farIdx; }
      }
      printResult({ spread, bumps, returns, farIdx, farDist });
    }, (err) => {
      console.error(err);
      process.exit(1);
    });
  }
}
