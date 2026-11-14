"use strict";

const { isMainThread, Worker, workerData, parentPort } = require("node:worker_threads");

// Compute only the top two SplitMix64 output bits. Each multiply uses exact
// 16-bit partial products for the carry and Math.imul for the low 32 bits.
// The final xor by (z >>> 31) cannot affect the direction bits.
function direction(lo, hi) {
    let a = lo ^ ((lo >>> 30) | (hi << 2));
    let b = hi ^ (hi >>> 30);
    let low16 = a & 65535;
    let high16 = a >>> 16;
    let carry = Math.floor((high16 * 0xE5B9 + low16 * 0x1CE4 +
        ((low16 * 0xE5B9) >>> 16)) / 65536);
    hi = (Math.imul(b, 0x1CE4E5B9) + Math.imul(a, 0xBF58476D) +
        high16 * 0x1CE4 + carry) | 0;
    lo = Math.imul(a, 0x1CE4E5B9);
    a = lo ^ ((lo >>> 27) | (hi << 5));
    b = hi ^ (hi >>> 27);
    low16 = a & 65535;
    high16 = a >>> 16;
    carry = Math.floor((high16 * 0x11EB + low16 * 0x1331 +
        ((low16 * 0x11EB) >>> 16)) / 65536);
    hi = (Math.imul(b, 0x133111EB) + Math.imul(a, 0x94D049BB) +
        high16 * 0x1331 + carry) | 0;
    return hi >>> 30;
}

function simulate(first, end, steps, bound, seed) {
    // Coordinates and per-walker counts are exact Numbers when steps is safe.
    // Convert at walker boundaries so squared distances and totals stay exact
    // even when they exceed Number.MAX_SAFE_INTEGER.
    if (steps > BigInt(Number.MAX_SAFE_INTEGER)) {
        return simulateBig(first, end, steps, bound, seed);
    }
    const length = Number(steps);
    const box = Number(bound < steps ? bound : steps);
    let spread = 0n, bumps = 0n, returns = 0n, walker = 0n, distance = -1;
    for (let j = first; j < end; ++j) {
        const initial = BigInt.asUintN(64, seed + j);
        let lo = Number(initial & 0xFFFFFFFFn) >>> 0;
        let hi = Number(initial >> 32n) | 0;
        let x = 0, y = 0, hits = 0, visits = 0;
        for (let k = 0; k < length; ++k) {
            const nextLo = (lo + 0x7F4A7C15) >>> 0;
            hi = (hi + 0x9E3779B9 + (nextLo < lo ? 1 : 0)) | 0;
            lo = nextLo;
            const d = direction(lo, hi);
            const axis = d >>> 1;
            const delta = 1 - 2 * (d & 1);
            const nx = x + (delta & (axis - 1));
            const ny = y + (delta & -axis);
            if (nx > box || nx < -box || ny > box || ny < -box) {
                ++hits;
            } else {
                x = nx;
                y = ny;
                if (x === 0 && y === 0) ++visits;
            }
        }
        const bx = BigInt(x), by = BigInt(y);
        spread += bx * bx + by * by;
        bumps += BigInt(hits);
        returns += BigInt(visits);
        const dist = Math.abs(x) + Math.abs(y);
        if (dist > distance) {
            distance = dist;
            walker = j;
        }
    }
    return { spread, bumps, returns, walker, distance: BigInt(distance) };
}

// Preserve integer semantics for inputs beyond the Number loop-counter range.
function simulateBig(first, end, steps, bound, seed) {
    let spread = 0n, bumps = 0n, returns = 0n, walker = 0n, distance = -1n;
    for (let j = first; j < end; ++j) {
        const initial = BigInt.asUintN(64, seed + j);
        let lo = Number(initial & 0xFFFFFFFFn) >>> 0;
        let hi = Number(initial >> 32n) | 0;
        let x = 0n, y = 0n;
        for (let k = 0n; k < steps; ++k) {
            const nextLo = (lo + 0x7F4A7C15) >>> 0;
            hi = (hi + 0x9E3779B9 + (nextLo < lo ? 1 : 0)) | 0;
            lo = nextLo;
            const d = direction(lo, hi);
            const delta = (d & 1) === 0 ? 1n : -1n;
            const wall = delta > 0n ? bound : -bound;
            if ((d < 2 ? x : y) === wall) {
                ++bumps;
            } else {
                if (d < 2) x += delta;
                else y += delta;
                if (x === 0n && y === 0n) ++returns;
            }
        }
        spread += x * x + y * y;
        const dist = (x < 0n ? -x : x) + (y < 0n ? -y : y);
        if (dist > distance) {
            distance = dist;
            walker = j;
        }
    }
    return { spread, bumps, returns, walker, distance };
}

if (!isMainThread) {
    const { first, end, steps, bound, seed } = workerData;
    parentPort.postMessage(simulate(first, end, steps, bound, seed));
} else {
    const fs = require("node:fs");
    const [walkers, steps, bound, seed] = fs.readFileSync(process.argv[2], "utf8")
        .trim().split(/\s+/).map(BigInt);
    const workers = Number(process.argv[3]);
    const count = BigInt(workers);
    const q = walkers / count, remainder = walkers % count;
    let pending = workers;
    const total = { spread: 0n, bumps: 0n, returns: 0n, walker: 0n, distance: -1n };
    function collect(result) {
        total.spread += result.spread;
        total.bumps += result.bumps;
        total.returns += result.returns;
        if (result.distance > total.distance ||
            (result.distance === total.distance && result.walker < total.walker)) {
            total.distance = result.distance;
            total.walker = result.walker;
        }
        if (--pending === 0) {
            if (total.distance < 0n) total.distance = 0n;
            process.stdout.write(`spread ${total.spread}\nbumps ${total.bumps}\n` +
                `returns ${total.returns}\nfarthest ${total.walker} ${total.distance}\n`);
        }
    }
    for (let w = 1; w < workers; ++w) {
        const index = BigInt(w);
        const first = q * index + (index < remainder ? index : remainder);
        const end = first + q + (index < remainder ? 1n : 0n);
        const worker = new Worker(__filename, {
            workerData: { first, end, steps, bound, seed }
        });
        worker.once("message", collect);
        worker.once("error", error => { throw error; });
    }
    collect(simulate(0n, q + (remainder > 0n ? 1n : 0n), steps, bound, seed));
}
