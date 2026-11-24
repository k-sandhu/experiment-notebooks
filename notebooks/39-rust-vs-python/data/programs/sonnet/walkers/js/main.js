"use strict";
const { Worker, isMainThread, parentPort, workerData } = require("worker_threads");

const DX = new Int32Array([1, -1, 0, 0]);
const DY = new Int32Array([0, 0, 1, -1]);

// 64-bit SplitMix64 on (hi, lo) 32-bit halves; only the top two bits of the output are needed.
function mulhi(a, b) {
  const a0 = a & 0xffff, a1 = a >>> 16, b0 = b & 0xffff, b1 = b >>> 16;
  const t = a0 * b0;
  const m1 = a1 * b0 + (t >>> 16);
  const m2 = a0 * b1 + (m1 & 0xffff);
  return (a1 * b1 + (m1 >>> 16) + (m2 >>> 16)) | 0;
}

function walk(sh, sl, L, B, out, o) {
  let x = 0, y = 0, bumps = 0, returns = 0;
  const G_H = 0x9E3779B9 | 0, G_L = 0x7F4A7C15 | 0;
  const C1H = 0xBF58476D | 0, C1L = 0x1CE4E5B9 | 0;
  const C2H = 0x94D049BB | 0, C2L = 0x133111EB | 0;
  for (let i = 0; i < L; i++) {
    const nl = (sl + G_L) | 0;
    sh = (sh + G_H + ((nl >>> 0) < (sl >>> 0) ? 1 : 0)) | 0;
    sl = nl;
    // z ^= z >> 30
    let zl = sl ^ ((sl >>> 30) | (sh << 2));
    let zh = sh ^ (sh >>> 30);
    // z *= C1
    const ml = Math.imul(zl, C1L);
    const mh = (mulhi(zl, C1L) + Math.imul(zh, C1L) + Math.imul(zl, C1H)) | 0;
    // z ^= z >> 27
    zl = ml ^ ((ml >>> 27) | (mh << 5));
    zh = mh ^ (mh >>> 27);
    // z *= C2, high word only
    const hh = (mulhi(zl, C2L) + Math.imul(zh, C2L) + Math.imul(zl, C2H)) | 0;
    const d = hh >>> 30;
    const nx = x + DX[d], ny = y + DY[d];
    if (nx < -B || nx > B || ny < -B || ny > B) {
      bumps++;
    } else {
      x = nx; y = ny;
      if ((x | y) === 0) returns++;
    }
  }
  out[o] = x * x + y * y;
  out[o + 1] = bumps;
  out[o + 2] = returns;
  out[o + 3] = Math.abs(x) + Math.abs(y);
}

function runJobs(js, seed, L, B) {
  const out = new Float64Array(js.length * 4);
  for (let k = 0; k < js.length; k++) {
    const s = BigInt.asUintN(64, seed + BigInt(js[k]));
    walk(Number(s >> 32n) | 0, Number(s & 0xffffffffn) | 0, L, B, out, k * 4);
  }
  return out;
}

if (isMainThread) {
  const fs = require("fs");
  const p = fs.readFileSync(process.argv[2], "utf8").trim().split(/\s+/);
  const J = parseInt(p[0]), L = parseInt(p[1]), B = parseInt(p[2]);
  const seed = BigInt(p[3]);
  const W = Math.min(Math.max(1, parseInt(process.argv[3])), J);
  const lists = [];
  for (let w = 0; w < W; w++) {
    const l = [];
    for (let j = w; j < J; j += W) l.push(j);
    lists.push(l);
  }
  const res = new Array(J);
  let pending = 0;
  const finish = () => {
    let spread = 0, bumps = 0, returns = 0, bestD = -1, bestJ = 0;
    for (let j = 0; j < J; j++) {
      const r = res[j];
      spread += r[0]; bumps += r[1]; returns += r[2];
      if (r[3] > bestD) { bestD = r[3]; bestJ = j; }
    }
    process.stdout.write(`spread ${spread}\nbumps ${bumps}\nreturns ${returns}\nfarthest ${bestJ} ${bestD}\n`);
  };
  const store = (w, out) => {
    lists[w].forEach((j, k) => { res[j] = out.subarray(k * 4, k * 4 + 4); });
  };
  if (W === 1) {
    store(0, runJobs(lists[0], seed, L, B));
    finish();
  } else {
    for (let w = 1; w < W; w++) {
      pending++;
      const wk = new Worker(__filename, { workerData: { js: lists[w], seed: p[3], L, B } });
      wk.on("message", (out) => {
        store(w, out);
        if (--pending === 0) finish();
      });
      wk.on("error", (e) => { console.error(e); process.exit(1); });
    }
    store(0, runJobs(lists[0], seed, L, B));
    if (pending === 0) finish();
  }
} else {
  const { js, seed, L, B } = workerData;
  parentPort.postMessage(runJobs(js, BigInt(seed), L, B));
}
