'use strict';
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

// Fast path: positions fit comfortably in int32 (B <= 2^29), n <= 2^30.
// out = [x, y, bumps, returns, stateHi, stateLo]
function walk(out, n, B) {
  n = n | 0;
  B = B | 0;
  let x = out[0] | 0, y = out[1] | 0;
  let sh = out[4] | 0, sl = out[5] | 0;
  let bumps = 0, returns = 0;
  for (let i = 0; i < n; i++) {
    // state += 0x9E3779B97F4A7C15
    const nl = (sl + 0x7F4A7C15) | 0;
    sh = (sh + -1640531527 + ((sl & ~nl) >>> 31)) | 0;
    sl = nl;
    // z ^= z >>> 30
    let h = sh ^ (sh >>> 30);
    let l = sl ^ ((sl >>> 30) | (sh << 2));
    // z *= 0xBF58476D1CE4E5B9
    let a0 = l & 0xffff, a1 = l >>> 16;
    let p00 = Math.imul(a0, 0xE5B9), p01 = Math.imul(a0, 0x1CE4);
    let p10 = Math.imul(a1, 0xE5B9), p11 = Math.imul(a1, 0x1CE4);
    let mid = (p00 >>> 16) + (p01 & 0xffff) + (p10 & 0xffff);
    const th = (p11 + (p01 >>> 16) + (p10 >>> 16) + (mid >>> 16) +
      Math.imul(l, 0xBF58476D) + Math.imul(h, 0x1CE4E5B9)) | 0;
    const tl = Math.imul(l, 0x1CE4E5B9);
    // z ^= z >>> 27
    h = th ^ (th >>> 27);
    l = tl ^ ((tl >>> 27) | (th << 5));
    // high word of z * 0x94D049BB133111EB ; only top 2 bits needed
    a0 = l & 0xffff; a1 = l >>> 16;
    p00 = Math.imul(a0, 0x11EB); p01 = Math.imul(a0, 0x1331);
    p10 = Math.imul(a1, 0x11EB); p11 = Math.imul(a1, 0x1331);
    mid = (p00 >>> 16) + (p01 & 0xffff) + (p10 & 0xffff);
    const d = ((p11 + (p01 >>> 16) + (p10 >>> 16) + (mid >>> 16) +
      Math.imul(l, 0x94D049BB) + Math.imul(h, 0x133111EB)) | 0) >>> 30;

    const s = 1 - ((d & 1) << 1);
    const m = (d >>> 1) - 1;
    const nx = (x + (s & m)) | 0;
    const ny = (y + (s & ~m)) | 0;
    if (((B - nx) | (nx + B) | (B - ny) | (ny + B)) < 0) {
      bumps = (bumps + 1) | 0;
    } else {
      x = nx; y = ny;
      if ((nx | ny) === 0) returns = (returns + 1) | 0;
    }
  }
  out[0] = x; out[1] = y; out[2] = bumps; out[3] = returns; out[4] = sh; out[5] = sl;
}

// Slow path for enormous boxes (positions may exceed int32).
function walkBig(out, n, B) {
  n = n | 0;
  let x = out[0], y = out[1];
  let sh = out[4] | 0, sl = out[5] | 0;
  let bumps = 0, returns = 0;
  const nB = -B;
  for (let i = 0; i < n; i++) {
    const nl = (sl + 0x7F4A7C15) | 0;
    sh = (sh + -1640531527 + ((sl & ~nl) >>> 31)) | 0;
    sl = nl;
    let h = sh ^ (sh >>> 30);
    let l = sl ^ ((sl >>> 30) | (sh << 2));
    let a0 = l & 0xffff, a1 = l >>> 16;
    let p00 = Math.imul(a0, 0xE5B9), p01 = Math.imul(a0, 0x1CE4);
    let p10 = Math.imul(a1, 0xE5B9), p11 = Math.imul(a1, 0x1CE4);
    let mid = (p00 >>> 16) + (p01 & 0xffff) + (p10 & 0xffff);
    const th = (p11 + (p01 >>> 16) + (p10 >>> 16) + (mid >>> 16) +
      Math.imul(l, 0xBF58476D) + Math.imul(h, 0x1CE4E5B9)) | 0;
    const tl = Math.imul(l, 0x1CE4E5B9);
    h = th ^ (th >>> 27);
    l = tl ^ ((tl >>> 27) | (th << 5));
    a0 = l & 0xffff; a1 = l >>> 16;
    p00 = Math.imul(a0, 0x11EB); p01 = Math.imul(a0, 0x1331);
    p10 = Math.imul(a1, 0x11EB); p11 = Math.imul(a1, 0x1331);
    mid = (p00 >>> 16) + (p01 & 0xffff) + (p10 & 0xffff);
    const d = ((p11 + (p01 >>> 16) + (p10 >>> 16) + (mid >>> 16) +
      Math.imul(l, 0x94D049BB) + Math.imul(h, 0x133111EB)) | 0) >>> 30;

    const s = 1 - ((d & 1) << 1);
    const m = (d >>> 1) - 1;
    const nx = x + (s & m);
    const ny = y + (s & ~m);
    if (nx > B || nx < nB || ny > B || ny < nB) {
      bumps = (bumps + 1) | 0;
    } else {
      x = nx; y = ny;
      if (nx === 0 && ny === 0) returns = (returns + 1) | 0;
    }
  }
  out[0] = x; out[1] = y; out[2] = bumps; out[3] = returns; out[4] = sh; out[5] = sl;
}

function run(cfg) {
  const J = cfg.J, L = cfg.L, B = cfg.B, chunk = cfg.chunk;
  const seedHi = cfg.seedHi, seedLo = cfg.seedLo;
  const ctr = new Int32Array(cfg.sab);
  const out = new Float64Array(6);
  const fast = B <= 536870912;
  const smallSq = B <= 33554432;
  const CH = 1073741824;
  let accS = 0, bigS = 0n, accB = 0, bigB = 0n, accR = 0, bigR = 0n;
  let bestD = -1, bestJ = -1;
  for (;;) {
    const start = Atomics.add(ctr, 0, chunk);
    if (start >= J || start < 0) break;
    const end = Math.min(J, start + chunk);
    for (let j = start; j < end; j++) {
      const t = seedLo + j;
      out[0] = 0; out[1] = 0;
      out[4] = (seedHi + Math.floor(t / 4294967296)) | 0;
      out[5] = t | 0;
      let rem = L, b = 0, r = 0;
      while (rem > 0) {
        const n = rem > CH ? CH : rem;
        if (fast) walk(out, n, B); else walkBig(out, n, B);
        b += out[2]; r += out[3];
        rem -= n;
      }
      const x = out[0], y = out[1];
      if (smallSq) {
        accS += x * x + y * y;
        if (accS >= 1e15) { bigS += BigInt(accS); accS = 0; }
      } else {
        const bx = BigInt(x), by = BigInt(y);
        bigS += bx * bx + by * by;
      }
      accB += b;
      if (accB >= 1e15) { bigB += BigInt(accB); accB = 0; }
      accR += r;
      if (accR >= 1e15) { bigR += BigInt(accR); accR = 0; }
      const D = Math.abs(x) + Math.abs(y);
      if (D > bestD || (D === bestD && j < bestJ)) { bestD = D; bestJ = j; }
    }
  }
  return {
    s: (bigS + BigInt(accS)).toString(),
    b: (bigB + BigInt(accB)).toString(),
    r: (bigR + BigInt(accR)).toString(),
    d: bestD,
    j: bestJ
  };
}

if (isMainThread) {
  const fs = require('fs');
  const parts = fs.readFileSync(process.argv[2], 'utf8').trim().split(/\s+/);
  const J = Number(parts[0]);
  const L = Number(parts[1]);
  const Bbig = BigInt(parts[2]);
  const seed = BigInt.asUintN(64, BigInt(parts[3]));
  let W = parseInt(process.argv[3], 10);
  if (!(W >= 1)) W = 1;
  if (W > 32) W = 32;
  const B = Bbig > BigInt(L) ? L : Number(Bbig);
  const T = Math.max(1, Math.min(W, J));
  const chunk = Math.max(1, Math.floor(J / (T * 8)));
  const cfg = {
    J, L, B, chunk,
    seedHi: Number(seed >> 32n),
    seedLo: Number(seed & 0xFFFFFFFFn),
    sab: new SharedArrayBuffer(4)
  };

  const results = [];
  let pending = T - 1;
  let mainDone = false;

  const finish = () => {
    let S = 0n, Bm = 0n, R = 0n, bestD = -1, bestJ = -1;
    for (let i = 0; i < results.length; i++) {
      const res = results[i];
      S += BigInt(res.s); Bm += BigInt(res.b); R += BigInt(res.r);
      if (res.j >= 0 && (res.d > bestD || (res.d === bestD && res.j < bestJ))) {
        bestD = res.d; bestJ = res.j;
      }
    }
    process.stdout.write('spread ' + S.toString() + '\nbumps ' + Bm.toString() +
      '\nreturns ' + R.toString() + '\nfarthest ' + bestJ + ' ' + bestD + '\n');
  };

  for (let i = 0; i < T - 1; i++) {
    const w = new Worker(__filename, { workerData: cfg });
    w.on('message', (msg) => {
      results.push(msg);
      pending--;
      if (pending === 0 && mainDone) finish();
    });
    w.on('error', (e) => { throw e; });
  }

  results.push(run(cfg));
  mainDone = true;
  if (pending === 0) finish();
} else {
  parentPort.postMessage(run(workerData));
}
