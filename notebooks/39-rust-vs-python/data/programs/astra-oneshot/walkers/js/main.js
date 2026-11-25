'use strict';

const { Worker, isMainThread, parentPort, workerData } = require('node:worker_threads');

const MASK64 = (1n << 64n) - 1n;
const MAX_SAFE = BigInt(Number.MAX_SAFE_INTEGER);

function simulate(data) {
  if (data.steps > MAX_SAFE) return simulateBig(data);

  const { start, end, seed } = data;
  const steps = Number(data.steps);
  const bound = Number(data.bound < data.steps ? data.bound : data.steps);
  const negativeBound = -bound;

  let initial = (seed + start) & MASK64;
  let initialLo = Number(initial & 0xffffffffn);
  let initialHi = Number(initial >> 32n);

  let spread = 0n;
  let bumps = 0n;
  let returns = 0n;
  let farthestIndex = 0n;
  let farthestDistance = -1;

  for (let j = start; j < end; j++) {
    let stateLo = initialLo;
    let stateHi = initialHi;
    let x = 0;
    let y = 0;
    let walkerBumps = 0;
    let walkerReturns = 0;

    for (let step = 0; step < steps; step++) {
      stateLo = (stateLo + 0x7f4a7c15) >>> 0;
      stateHi = (
        stateHi + 0x9e3779b9 + (stateLo < 0x7f4a7c15 ? 1 : 0)
      ) >>> 0;

      let lo = (stateLo ^ (stateLo >>> 30) ^ (stateHi << 2)) >>> 0;
      let hi = (stateHi ^ (stateHi >>> 30)) >>> 0;

      let low16 = lo & 0xffff;
      let high16 = lo >>> 16;
      let middle =
        high16 * 0xe5b9 +
        low16 * 0x1ce4 +
        ((low16 * 0xe5b9) >>> 16);

      hi = (
        Math.imul(hi, 0x1ce4e5b9) +
        Math.imul(lo, 0xbf58476d) +
        high16 * 0x1ce4 +
        ((middle / 65536) | 0)
      ) >>> 0;
      lo = Math.imul(lo, 0x1ce4e5b9) >>> 0;

      lo = (lo ^ (lo >>> 27) ^ (hi << 5)) >>> 0;
      hi = (hi ^ (hi >>> 27)) >>> 0;

      low16 = lo & 0xffff;
      high16 = lo >>> 16;
      middle =
        high16 * 0x11eb +
        low16 * 0x1331 +
        ((low16 * 0x11eb) >>> 16);

      hi = (
        Math.imul(hi, 0x133111eb) +
        Math.imul(lo, 0x94d049bb) +
        high16 * 0x1331 +
        ((middle / 65536) | 0)
      ) >>> 0;

      // The final xor with z >> 31 cannot change the top two bits.
      switch (hi >>> 30) {
        case 0:
          if (x === bound) {
            walkerBumps++;
            continue;
          }
          x++;
          break;
        case 1:
          if (x === negativeBound) {
            walkerBumps++;
            continue;
          }
          x--;
          break;
        case 2:
          if (y === bound) {
            walkerBumps++;
            continue;
          }
          y++;
          break;
        default:
          if (y === negativeBound) {
            walkerBumps++;
            continue;
          }
          y--;
          break;
      }

      if (x === 0 && y === 0) walkerReturns++;
    }

    const bx = BigInt(x);
    const by = BigInt(y);
    spread += bx * bx + by * by;
    bumps += BigInt(walkerBumps);
    returns += BigInt(walkerReturns);

    const distance = Math.abs(x) + Math.abs(y);
    if (distance > farthestDistance) {
      farthestDistance = distance;
      farthestIndex = j;
    }

    initialLo = (initialLo + 1) >>> 0;
    if (initialLo === 0) initialHi = (initialHi + 1) >>> 0;
  }

  return {
    spread,
    bumps,
    returns,
    farthestIndex,
    farthestDistance: BigInt(farthestDistance)
  };
}

function simulateBig({ start, end, seed, steps, bound }) {
  let spread = 0n;
  let bumps = 0n;
  let returns = 0n;
  let farthestIndex = 0n;
  let farthestDistance = -1n;
  const negativeBound = -bound;

  for (let j = start; j < end; j++) {
    let state = (seed + j) & MASK64;
    let x = 0n;
    let y = 0n;

    for (let step = 0n; step < steps; step++) {
      state = (state + 0x9e3779b97f4a7c15n) & MASK64;
      let z = state;
      z = ((z ^ (z >> 30n)) * 0xbf58476d1ce4e5b9n) & MASK64;
      z = ((z ^ (z >> 27n)) * 0x94d049bb133111ebn) & MASK64;

      switch (Number(z >> 62n)) {
        case 0:
          if (x === bound) {
            bumps++;
            continue;
          }
          x++;
          break;
        case 1:
          if (x === negativeBound) {
            bumps++;
            continue;
          }
          x--;
          break;
        case 2:
          if (y === bound) {
            bumps++;
            continue;
          }
          y++;
          break;
        default:
          if (y === negativeBound) {
            bumps++;
            continue;
          }
          y--;
          break;
      }

      if (x === 0n && y === 0n) returns++;
    }

    spread += x * x + y * y;
    const distance = (x < 0n ? -x : x) + (y < 0n ? -y : y);
    if (distance > farthestDistance) {
      farthestDistance = distance;
      farthestIndex = j;
    }
  }

  return { spread, bumps, returns, farthestIndex, farthestDistance };
}

function printResult(result) {
  process.stdout.write(
    `spread ${result.spread}\n` +
    `bumps ${result.bumps}\n` +
    `returns ${result.returns}\n` +
    `farthest ${result.farthestIndex} ${result.farthestDistance}\n`
  );
}

if (!isMainThread) {
  parentPort.postMessage(simulate(workerData));
} else {
  const fs = require('node:fs');
  const fields = fs.readFileSync(process.argv[2], 'utf8').trim().split(/\s+/);
  const walkers = BigInt(fields[0]);
  const steps = BigInt(fields[1]);
  const bound = BigInt(fields[2]);
  const seed = BigInt(fields[3]);
  const workers = Number(process.argv[3]);

  if (workers === 1) {
    printResult(simulate({ start: 0n, end: walkers, steps, bound, seed }));
  } else {
    const total = {
      spread: 0n,
      bumps: 0n,
      returns: 0n,
      farthestIndex: 0n,
      farthestDistance: -1n
    };
    let remaining = workers;
    const workerCount = BigInt(workers);

    for (let rank = 0; rank < workers; rank++) {
      const worker = new Worker(__filename, {
        workerData: {
          start: walkers * BigInt(rank) / workerCount,
          end: walkers * BigInt(rank + 1) / workerCount,
          steps,
          bound,
          seed
        }
      });

      worker.once('message', result => {
        total.spread += result.spread;
        total.bumps += result.bumps;
        total.returns += result.returns;

        if (
          result.farthestDistance > total.farthestDistance ||
          (
            result.farthestDistance === total.farthestDistance &&
            result.farthestIndex < total.farthestIndex
          )
        ) {
          total.farthestDistance = result.farthestDistance;
          total.farthestIndex = result.farthestIndex;
        }

        if (--remaining === 0) printResult(total);
      });
    }
  }
}
