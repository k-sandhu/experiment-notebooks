'use strict';
const { isMainThread, parentPort, workerData, Worker } = require('worker_threads');
const fs = require('fs');

const GOLD_LO = 0x7F4A7C15; // 0x9E3779B97F4A7C15
const GOLD_HI = 0x9E3779B9;
const C1_LO = 0x1CE4E5B9;   // 0xBF58476D1CE4E5B9
const C1_HI = 0xBF58476D;
const C2_LO = 0x133111EB;   // 0x94D049BB133111EB
const C2_HI = 0x94D049BB;

// 64x64 -> 64 multiply, operands/results as [lo, hi] unsigned 32-bit halves.
// result = aLo*bLo + (aLo*bHi + aHi*bLo)*2^32 (mod 2^64): the high halves of the
// cross products land at bit 64+ and are dropped, so only their low halves are needed.
let _lo = 0, _hi = 0;
function mul64(aLo, aHi, bLo, bHi) {
  // t = aLo*bLo (full 64 bits)
  let aL = aLo & 0xFFFF, aH = aLo >>> 16, bL = bLo & 0xFFFF, bH = bLo >>> 16;
  let p0 = aL * bL, p1 = aL * bH + aH * bL, p2 = aH * bH;
  let u = p0 + ((p1 & 0xFFFF) * 0x10000);
  const tLo = u >>> 0;
  const tHi = (Math.floor(u / 0x100000000) + ((p1 / 0x10000) | 0) + p2) >>> 0;
  // low 32 bits of aLo*bHi
  bL = bHi & 0xFFFF; bH = bHi >>> 16;
  p0 = aL * bL; p1 = aL * bH + aH * bL;
  const m1Lo = (p0 + (p1 & 0xFFFF) * 0x10000) >>> 0;
  // low 32 bits of aHi*bLo
  aL = aHi & 0xFFFF; aH = aHi >>> 16; bL = bLo & 0xFFFF; bH = bLo >>> 16;
  p0 = aL * bL; p1 = aL * bH + aH * bL;
  const m2Lo = (p0 + (p1 & 0xFFFF) * 0x10000) >>> 0;
  const sLo = (m1Lo + m2Lo) >>> 0;
  _lo = tLo;
  _hi = (tHi + sLo) >>> 0;
}

// Walk walkers [j0, j1); returns aggregate for the chunk.
// The 64-bit state is kept as two SIGNED 32-bit halves (bitwise ops are exact on
// these, and |0 stores wrap mod 2^32), with the multiply expanded inline:
// result = aLo*bLo + (aLo*bHi + aHi*bLo)*2^32 (mod 2^64); the high halves of the
// cross products land at bit 64+ and are dropped, so only their low halves are needed.
function walkRange(j0, j1, L, B, seedBig) {
  let spread = 0n;
  let bumps = 0, rets = 0;
  let bestD = -1, bestJ = -1;
  const negB = -B;
  for (let j = j0; j < j1; j++) {
    const st = (seedBig + BigInt(j)) & 0xFFFFFFFFFFFFFFFFn;
    let lo = Number(st & 0xFFFFFFFFn) | 0;
    let hi = Number(st >> 32n) | 0;
    let x = 0, y = 0, b = 0, r = 0;
    for (let s = 0; s < L; s++) {
      // state += GOLDEN. With signed halves, the carry out of the low add happens
      // exactly when t = lo + GOLD_LO lands in [0, GOLD_LO).
      const t = lo + 0x7F4A7C15;
      lo = t | 0;
      hi = (hi + 0x9E3779B9 + (t >= 0 && t < 0x7F4A7C15 ? 1 : 0)) | 0;
      // z = state ^ (state >>> 30)
      let zLo = (lo ^ ((lo >>> 30) | ((hi << 2) >>> 0))) | 0;
      let zHi = (hi ^ (hi >>> 30)) | 0;
      // z *= 0xBF58476D1CE4E5B9
      let aL = zLo & 0xFFFF, aH = zLo >>> 16;
      let p0 = aL * 0xE5B9, p1 = aL * 0x1CE4 + aH * 0xE5B9, p2 = aH * 0x1CE4;
      let u = p0 + (p1 & 0xFFFF) * 0x10000;
      let rLo = u >>> 0;
      let rHi = ((u >= 0x100000000 ? 1 : 0) + ((p1 / 0x10000) | 0) + p2) >>> 0;
      p0 = aL * 0x476D; p1 = aL * 0xBF58 + aH * 0x476D;
      const m1Lo = (p0 + (p1 & 0xFFFF) * 0x10000) >>> 0;
      aL = zHi & 0xFFFF; aH = zHi >>> 16;
      p0 = aL * 0xE5B9; p1 = aL * 0x1CE4 + aH * 0xE5B9;
      const m2Lo = (p0 + (p1 & 0xFFFF) * 0x10000) >>> 0;
      zLo = rLo | 0;
      zHi = (rHi + ((m1Lo + m2Lo) >>> 0)) | 0;
      // z ^= z >>> 27
      zLo = (zLo ^ ((zLo >>> 27) | ((zHi << 5) >>> 0))) | 0;
      zHi = (zHi ^ (zHi >>> 27)) | 0;
      // z *= 0x94D049BB133111EB
      aL = zLo & 0xFFFF; aH = zLo >>> 16;
      p0 = aL * 0x11EB, p1 = aL * 0x1331 + aH * 0x11EB, p2 = aH * 0x1331;
      u = p0 + (p1 & 0xFFFF) * 0x10000;
      rLo = u >>> 0;
      rHi = ((u >= 0x100000000 ? 1 : 0) + ((p1 / 0x10000) | 0) + p2) >>> 0;
      p0 = aL * 0x49BB; p1 = aL * 0x94D0 + aH * 0x49BB;
      const m3Lo = (p0 + (p1 & 0xFFFF) * 0x10000) >>> 0;
      aL = zHi & 0xFFFF; aH = zHi >>> 16;
      p0 = aL * 0x11EB; p1 = aL * 0x1331 + aH * 0x11EB;
      const m4Lo = (p0 + (p1 & 0xFFFF) * 0x10000) >>> 0;
      zLo = rLo | 0;
      zHi = (rHi + ((m3Lo + m4Lo) >>> 0)) | 0;
      // z ^= z >>> 31; only the high half feeds the final d = z >>> 62
      zHi = (zHi ^ (zHi >>> 31)) | 0;
      const d = zHi >>> 30;
      let dx = 0, dy = 0;
      if (d === 0) dx = 1; else if (d === 1) dx = -1; else if (d === 2) dy = 1; else dy = -1;
      const nx = x + dx, ny = y + dy;
      if (nx > B || nx < negB || ny > B || ny < negB) {
        b++;
      } else {
        x = nx; y = ny;
        if (nx === 0 && ny === 0) r++;
      }
    }
    spread += BigInt(x) * BigInt(x) + BigInt(y) * BigInt(y);
    bumps += b;
    rets += r;
    const D = Math.abs(x) + Math.abs(y);
    if (D > bestD) { bestD = D; bestJ = j; }
  }
  return { spread: spread.toString(), bumps, rets, bestD, bestJ };
}

function aggregate(parts) {
  let spread = 0n, bumps = 0, rets = 0, bestD = -1, bestJ = -1;
  for (const p of parts) {
    spread += BigInt(p.spread);
    bumps += p.bumps;
    rets += p.rets;
    if (p.bestJ >= 0 && (bestJ < 0 || p.bestD > bestD)) {
      bestD = p.bestD;
      bestJ = p.bestJ;
    }
  }
  return { spread, bumps, rets, bestD, bestJ };
}

if (!isMainThread) {
  const { j0, j1, L, B, seed } = workerData;
  const res = walkRange(j0, j1, L, B, BigInt(seed));
  parentPort.postMessage(res);
} else {
  if (process.argv.length < 4) process.exit(1);
  const text = fs.readFileSync(process.argv[2], 'utf8');
  const parts = text.trim().split(/\s+/);
  const J = Number(parts[0]);
  const L = Number(parts[1]);
  const B = Number(parts[2]);
  const seed = parts[3];
  let workers = parseInt(process.argv[3], 10);
  if (!(workers >= 1)) workers = 1;
  if (workers > J) workers = J;

  const chunk = Math.ceil(J / workers);
  let pending = workers;
  const results = new Array(workers);
  if (workers === 1) {
    results[0] = walkRange(0, J, L, B, BigInt(seed));
    finish(results);
  } else {
    for (let w = 0; w < workers; w++) {
      const j0 = w * chunk;
      const j1 = Math.min(j0 + chunk, J);
      if (j0 >= j1) { done(w); continue; }
      const wk = new Worker(__filename, {
        workerData: { j0, j1, L, B, seed },
      });
      wk.on('message', (msg) => { results[w] = msg; done(w); });
      wk.on('error', (e) => { console.error(e); process.exit(1); });
    }
  }

  function done(w) {
    if (--pending === 0) finish(results);
  }

  function finish(results) {
    const r = aggregate(results.filter(Boolean));
    process.stdout.write(
      'spread ' + r.spread.toString() + '\n' +
      'bumps ' + r.bumps + '\n' +
      'returns ' + r.rets + '\n' +
      'farthest ' + r.bestJ + ' ' + r.bestD + '\n'
    );
  }
}
