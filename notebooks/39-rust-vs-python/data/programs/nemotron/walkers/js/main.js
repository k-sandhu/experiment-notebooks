"use strict";

const fs = require("fs");
const { isMainThread, workerData, parentPort, Worker } = require("worker_threads");

// SplitMix64 constants, split into little-endian uint32 limbs (stored as JS
// numbers, which represent every 32-bit pattern exactly).
const C_LO = 0x7F4A7C15;
const C_HI = 0x9E3779B9;
const M1_LO = 0x1CE4E5B9;
const M1_HI = 0xBF58476D;
const M2_LO = 0x133111EB;
const M2_HI = 0x94D049BB;

function parseU64(s) {
    const bi = BigInt(s);
    return { lo: Number(bi & 0xffffffffn), hi: Number((bi >> 32n) & 0xffffffffn) };
}

// Multiply 64x64 -> 64 (mod 2^64). All operands/results are little-endian
// uint32 limbs held as numbers with int32 bit patterns. Writes into `out`
// (reused across calls) to avoid allocations in the hot loop.
function mul64(a0, a1, b0, b1, out) {
    const a0l = a0 & 0xFFFF;
    const a0h = a0 >>> 16;
    const b0l = b0 & 0xFFFF;
    const b0h = b0 >>> 16;
    const p = Math.imul(a0l, b0l) >>> 0;
    const t = (Math.imul(a0l, b0h) >>> 0) + (Math.imul(a0h, b0l) >>> 0);
    const q = ((t | 0) >>> 16) + (t >= 0x100000000 ? 0x10000 : 0);
    const r = t & 0xFFFF;
    const r16 = r * 0x10000;  // exact double, < 2^32 (r << 16 would overflow int32)
    const carry2 = p + r16 >= 0x100000000 ? 1 : 0;
    const u = Math.imul(a0h, b0h) >>> 0;
    const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
    out[0] = (p + r16) | 0;
    out[1] = (u + q + carry2 + mid) | 0;
}

// Simulate walkers [start, end) and return partial results. All counters use
// 32-bit limb pairs so totals above 2^53 stay exact.
function runChunk(start, end, L, B, seedLo, seedHi) {
    const mulOut = [0, 0];
    let spreadLo = 0, spreadHi = 0;
    let bLo = 0, bHi = 0;
    let rLo = 0, rHi = 0;
    let farDist = 0, farIdx = start;
    const cLo = C_LO, cHi = C_HI;
    const m1Lo = M1_LO, m1Hi = M1_HI;
    const m2Lo = M2_LO, m2Hi = M2_HI;
    for (let j = start; j < end; ++j) {
        // state = seed + j (mod 2^64)
        let sLo = (seedLo + j) | 0;
        let carry = ((seedLo >>> 0) + (j >>> 0) >= 0x100000000) ? 1 : 0;
        let sHi = (seedHi + carry) | 0;

        let x = 0, y = 0;
        for (let s = 0; s < L; ++s) {
            // state += C
            let t = sLo + cLo;
            carry = ((sLo >>> 0) + (cLo >>> 0) >= 0x100000000) ? 1 : 0;
            sLo = t | 0;
            sHi = (sHi + cHi + carry) | 0;

            // z = state; z ^= z >> 30
            let z0 = sLo, z1 = sHi;
            let t0 = (z0 >>> 30) | ((z1 << 2) | 0);
            let t1 = z1 >>> 30;
            z0 ^= t0;
            z1 ^= t1;

            // z *= M1
            mul64(z0, z1, m1Lo, m1Hi, mulOut);
            z0 = mulOut[0]; z1 = mulOut[1];

            // z ^= z >> 27
            t0 = (z0 >>> 27) | ((z1 << 5) | 0);
            t1 = z1 >>> 27;
            z0 ^= t0;
            z1 ^= t1;

            // z *= M2
            mul64(z0, z1, m2Lo, m2Hi, mulOut);
            z0 = mulOut[0]; z1 = mulOut[1];

            // r = z ^ (z >> 31); d = top two bits
            t0 = (z0 >>> 31) | ((z1 << 1) | 0);
            const r1 = z1 ^ (z1 >>> 31);
            const r0 = z0 ^ t0;
            const d = (r1 >>> 30) & 3;

            let bumped;
            if (d === 0) { if (x < B) { ++x; bumped = false; } else bumped = true; }
            else if (d === 1) { if (x > -B) { --x; bumped = false; } else bumped = true; }
            else if (d === 2) { if (y < B) { ++y; bumped = false; } else bumped = true; }
            else { if (y > -B) { --y; bumped = false; } else bumped = true; }

            if (bumped) {
                bLo = (bLo + 1) | 0;
                if (bLo === 0) ++bHi;
            } else if (x === 0 && y === 0) {
                rLo = (rLo + 1) | 0;
                if (rLo === 0) ++rHi;
            }
        }

        // spread += x*x + y*y (exact via BigInt, once per walker)
        const cb = BigInt(x) * BigInt(x) + BigInt(y) * BigInt(y);
        const clo = Number(cb & 0xffffffffn);
        const chi = Number((cb >> 32n) & 0xffffffffn);
        let tt = spreadLo + clo;
        carry = ((spreadLo >>> 0) + (clo >>> 0) >= 0x100000000) ? 1 : 0;
        spreadLo = tt | 0;
        spreadHi = (spreadHi + chi + carry) | 0;

        const dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
        if (dist > farDist) {
            farDist = dist;
            farIdx = j;
        }
    }
    return { spreadLo, spreadHi, bLo, bHi, rLo, rHi, farDist, farIdx };
}

function addInto(tLo, tHi, aLo, aHi) {
    let t = tLo + aLo;
    const carry = ((tLo >>> 0) + (aLo >>> 0) >= 0x100000000) ? 1 : 0;
    tLo = t | 0;
    tHi = (tHi + aHi + carry) | 0;
    return { lo: tLo, hi: tHi };
}

function finish(results) {
    let tSpreadLo = 0, tSpreadHi = 0;
    let tBLo = 0, tBHi = 0;
    let tRLo = 0, tRHi = 0;
    let farDist = 0, farIdx = 0;
    for (const res of results) {
        if (!res) continue;
        const s = addInto(tSpreadLo, tSpreadHi, res.spreadLo, res.spreadHi);
        tSpreadLo = s.lo; tSpreadHi = s.hi;
        const b = addInto(tBLo, tBHi, res.bLo, res.bHi);
        tBLo = b.lo; tBHi = b.hi;
        const rr = addInto(tRLo, tRHi, res.rLo, res.rHi);
        tRLo = rr.lo; tRHi = rr.hi;
        if (res.farDist > farDist || (res.farDist === farDist && res.farIdx < farIdx)) {
            farDist = res.farDist;
            farIdx = res.farIdx;
        }
    }
    const spread = (BigInt(tSpreadHi >>> 0) << 32n) | BigInt(tSpreadLo >>> 0);
    const bumps = (BigInt(tBHi >>> 0) << 32n) | BigInt(tBLo >>> 0);
    const returns = (BigInt(tRHi >>> 0) << 32n) | BigInt(tRLo >>> 0);
    console.log("spread " + spread.toString());
    console.log("bumps " + bumps.toString());
    console.log("returns " + returns.toString());
    console.log("farthest " + farIdx + " " + farDist);
}

if (isMainThread) {
    const args = process.argv.slice(2);
    const parts = fs.readFileSync(args[0], "utf8").trim().split(/\s+/);
    const J = parseInt(parts[0], 10);
    const L = parseInt(parts[1], 10);
    const B = parseInt(parts[2], 10);
    const seed = parseU64(parts[3]);

    const workers = parseInt(args[1], 10) || 1;
    const n = J > 0 ? Math.min(workers, J) : 0;
    const results = new Array(n);

    if (n === 0) {
        finish(results);
    } else if (n === 1) {
        results[0] = runChunk(0, J, L, B, seed.lo, seed.hi);
        finish(results);
    } else {
        const chunk = Math.ceil(J / n);
        results[0] = runChunk(0, Math.min(chunk, J), L, B, seed.lo, seed.hi);
        const workersToSpawn = [];
        for (let i = 1; i < n; ++i) {
            const start = i * chunk;
            const end = Math.min(start + chunk, J);
            if (end > start) workersToSpawn.push({ i, start, end });
        }
        let pending = workersToSpawn.length;
        let workerError = null;
        const done = () => {
            if (workerError) throw workerError;
            finish(results);
        };
        for (const { i, start, end } of workersToSpawn) {
            const w = new Worker(__filename, {
                workerData: { start, end, L, B, seedLo: seed.lo, seedHi: seed.hi }
            });
            w.on("message", (msg) => { results[i] = msg; if (--pending === 0) done(); });
            w.on("error", (err) => { workerError = err; if (--pending === 0) done(); });
        }
        if (pending === 0) done();
    }
} else {
    const res = runChunk(workerData.start, workerData.end, workerData.L, workerData.B,
                         workerData.seedLo, workerData.seedHi);
    parentPort.postMessage(res);
}
