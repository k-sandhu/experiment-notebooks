"use strict";

const fs = require("fs");
const { Worker, isMainThread, parentPort, workerData } = require("worker_threads");

// SplitMix64 constants, split into 32-bit halves; all arithmetic is done on
// (lo, hi) pairs of unsigned 32-bit values to keep everything exact in doubles.
const G_LO = 0x7F4A7C15, G_HI = 0x9E3779B9;
const C1_LO = 0x1CE4E5B9, C1_HI = 0xBF58476D;
const C2_LO = 0x133111EB, C2_HI = 0x94D049BB;
const TWO32 = 4294967296;

const C1_LO0 = C1_LO & 0xffff, C1_LO1 = C1_LO >>> 16;
const C2_LO0 = C2_LO & 0xffff, C2_LO1 = C2_LO >>> 16;

function runWalker(stateLo, stateHi, L, B) {
    let lo = stateLo, hi = stateHi;
    let x = 0, y = 0;
    let bumps = 0, returns = 0;
    const nb = -B;

    for (let k = 0; k < L; ++k) {
        const nlo = lo + G_LO;
        lo = nlo >>> 0;
        hi = (hi + G_HI + (nlo > 0xFFFFFFFF ? 1 : 0)) >>> 0;

        let zlo = lo, zhi = hi;

        // z = (z ^ (z >>> 30)) * C1
        let slo = ((zlo >>> 30) | (zhi << 2)) >>> 0;
        let shi = zhi >>> 30;
        zlo = (zlo ^ slo) >>> 0;
        zhi = (zhi ^ shi) >>> 0;
        {
            const a0 = zlo & 0xffff, a1 = zlo >>> 16;
            const p0 = a0 * C1_LO0;
            const p1 = a0 * C1_LO1 + a1 * C1_LO0;
            const p2 = a1 * C1_LO1;
            const q = p0 + p1 * 65536;
            const mlo = q >>> 0;
            const mhi = (p2 + Math.floor(q / TWO32) +
                ((Math.imul(zlo, C1_HI) + Math.imul(zhi, C1_LO)) >>> 0)) >>> 0;
            zlo = mlo;
            zhi = mhi;
        }

        // z = (z ^ (z >>> 27)) * C2
        slo = ((zlo >>> 27) | (zhi << 5)) >>> 0;
        shi = zhi >>> 27;
        zlo = (zlo ^ slo) >>> 0;
        zhi = (zhi ^ shi) >>> 0;
        {
            const a0 = zlo & 0xffff, a1 = zlo >>> 16;
            const p0 = a0 * C2_LO0;
            const p1 = a0 * C2_LO1 + a1 * C2_LO0;
            const p2 = a1 * C2_LO1;
            const q = p0 + p1 * 65536;
            const mlo = q >>> 0;
            const mhi = (p2 + Math.floor(q / TWO32) +
                ((Math.imul(zlo, C2_HI) + Math.imul(zhi, C2_LO)) >>> 0)) >>> 0;
            zlo = mlo;
            zhi = mhi;
        }

        // d = top two bits of (z ^ (z >>> 31))
        const d = ((zhi ^ (zhi >>> 31)) >>> 30);

        const dir = 1 - 2 * (d & 1);
        const mx = (d < 2) ? -1 : 0;
        const nx0 = x + (dir & mx);
        const ny0 = y + (dir & ~mx);
        const ox = (nx0 > B ? 1 : 0) - (nx0 < nb ? 1 : 0);
        const oy = (ny0 > B ? 1 : 0) - (ny0 < nb ? 1 : 0);
        const nx = nx0 - ox;
        const ny = ny0 - oy;
        bumps += ((ox | oy) !== 0) ? 1 : 0;
        returns += ((nx | ny) === 0) ? 1 : 0;
        x = nx;
        y = ny;
    }

    const bx = BigInt(x), by = BigInt(y);
    return { spread: bx * bx + by * by, bumps: bumps, returns: returns, x: x, y: y };
}

// Two independent walkers interleaved so the CPU can overlap their serial
// SplitMix64 dependency chains.
function runWalker2(lo0, hi0, lo1, hi1, L, B) {
    let a_lo = lo0, a_hi = hi0;
    let b_lo = lo1, b_hi = hi1;
    let x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    let b0 = 0, r0 = 0, b1 = 0, r1 = 0;
    const nb = -B;

    for (let k = 0; k < L; ++k) {
        // ---- walker 0 ----
        let nlo = a_lo + G_LO;
        a_lo = nlo >>> 0;
        a_hi = (a_hi + G_HI + (nlo > 0xFFFFFFFF ? 1 : 0)) >>> 0;
        let zlo = a_lo, zhi = a_hi;
        let slo = ((zlo >>> 30) | (zhi << 2)) >>> 0;
        let shi = zhi >>> 30;
        zlo = (zlo ^ slo) >>> 0;
        zhi = (zhi ^ shi) >>> 0;
        {
            const a0 = zlo & 0xffff, a1 = zlo >>> 16;
            const p0 = a0 * C1_LO0;
            const p1 = a0 * C1_LO1 + a1 * C1_LO0;
            const p2 = a1 * C1_LO1;
            const q = p0 + p1 * 65536;
            const mlo = q >>> 0;
            const mhi = (p2 + Math.floor(q / TWO32) +
                ((Math.imul(zlo, C1_HI) + Math.imul(zhi, C1_LO)) >>> 0)) >>> 0;
            zlo = mlo;
            zhi = mhi;
        }
        slo = ((zlo >>> 27) | (zhi << 5)) >>> 0;
        shi = zhi >>> 27;
        zlo = (zlo ^ slo) >>> 0;
        zhi = (zhi ^ shi) >>> 0;
        {
            const a0 = zlo & 0xffff, a1 = zlo >>> 16;
            const p0 = a0 * C2_LO0;
            const p1 = a0 * C2_LO1 + a1 * C2_LO0;
            const p2 = a1 * C2_LO1;
            const q = p0 + p1 * 65536;
            const mlo = q >>> 0;
            const mhi = (p2 + Math.floor(q / TWO32) +
                ((Math.imul(zlo, C2_HI) + Math.imul(zhi, C2_LO)) >>> 0)) >>> 0;
            zlo = mlo;
            zhi = mhi;
        }
        let d = ((zhi ^ (zhi >>> 31)) >>> 30);
        let dir = 1 - 2 * (d & 1);
        let mx = (d < 2) ? -1 : 0;
        let nx0 = x0 + (dir & mx);
        let ny0 = y0 + (dir & ~mx);
        let ox = (nx0 > B ? 1 : 0) - (nx0 < nb ? 1 : 0);
        let oy = (ny0 > B ? 1 : 0) - (ny0 < nb ? 1 : 0);
        let nx = nx0 - ox;
        let ny = ny0 - oy;
        b0 += ((ox | oy) !== 0) ? 1 : 0;
        r0 += ((nx | ny) === 0) ? 1 : 0;
        x0 = nx;
        y0 = ny;

        // ---- walker 1 ----
        nlo = b_lo + G_LO;
        b_lo = nlo >>> 0;
        b_hi = (b_hi + G_HI + (nlo > 0xFFFFFFFF ? 1 : 0)) >>> 0;
        zlo = b_lo;
        zhi = b_hi;
        slo = ((zlo >>> 30) | (zhi << 2)) >>> 0;
        shi = zhi >>> 30;
        zlo = (zlo ^ slo) >>> 0;
        zhi = (zhi ^ shi) >>> 0;
        {
            const a0 = zlo & 0xffff, a1 = zlo >>> 16;
            const p0 = a0 * C1_LO0;
            const p1 = a0 * C1_LO1 + a1 * C1_LO0;
            const p2 = a1 * C1_LO1;
            const q = p0 + p1 * 65536;
            const mlo = q >>> 0;
            const mhi = (p2 + Math.floor(q / TWO32) +
                ((Math.imul(zlo, C1_HI) + Math.imul(zhi, C1_LO)) >>> 0)) >>> 0;
            zlo = mlo;
            zhi = mhi;
        }
        slo = ((zlo >>> 27) | (zhi << 5)) >>> 0;
        shi = zhi >>> 27;
        zlo = (zlo ^ slo) >>> 0;
        zhi = (zhi ^ shi) >>> 0;
        {
            const a0 = zlo & 0xffff, a1 = zlo >>> 16;
            const p0 = a0 * C2_LO0;
            const p1 = a0 * C2_LO1 + a1 * C2_LO0;
            const p2 = a1 * C2_LO1;
            const q = p0 + p1 * 65536;
            const mlo = q >>> 0;
            const mhi = (p2 + Math.floor(q / TWO32) +
                ((Math.imul(zlo, C2_HI) + Math.imul(zhi, C2_LO)) >>> 0)) >>> 0;
            zlo = mlo;
            zhi = mhi;
        }
        d = ((zhi ^ (zhi >>> 31)) >>> 30);
        dir = 1 - 2 * (d & 1);
        mx = (d < 2) ? -1 : 0;
        nx0 = x1 + (dir & mx);
        ny0 = y1 + (dir & ~mx);
        ox = (nx0 > B ? 1 : 0) - (nx0 < nb ? 1 : 0);
        oy = (ny0 > B ? 1 : 0) - (ny0 < nb ? 1 : 0);
        nx = nx0 - ox;
        ny = ny0 - oy;
        b1 += ((ox | oy) !== 0) ? 1 : 0;
        r1 += ((nx | ny) === 0) ? 1 : 0;
        x1 = nx;
        y1 = ny;
    }

    const bx0 = BigInt(x0), by0 = BigInt(y0);
    const bx1 = BigInt(x1), by1 = BigInt(y1);
    return [
        { spread: bx0 * bx0 + by0 * by0, bumps: b0, returns: r0, x: x0, y: y0 },
        { spread: bx1 * bx1 + by1 * by1, bumps: b1, returns: r1, x: x1, y: y1 }
    ];
}

function stateOf(seedLo, seedHi, j) {
    const sumLo = seedLo + j;
    return [sumLo >>> 0, (seedHi + (sumLo > 0xFFFFFFFF ? 1 : 0)) >>> 0];
}

function workerMain() {
    const { j0, j1, L, B, seedLo, seedHi } = workerData;
    let spread = 0n, bumps = 0, returns = 0;
    let bestDist = -1, bestJ = j0;

    const account = (r, j) => {
        spread += r.spread;
        bumps += r.bumps;
        returns += r.returns;
        const d = Math.abs(r.x) + Math.abs(r.y);
        if (d > bestDist) { bestDist = d; bestJ = j; }
    };

    let j = j0;
    for (; j + 1 < j1; j += 2) {
        const s0 = stateOf(seedLo, seedHi, j);
        const s1 = stateOf(seedLo, seedHi, j + 1);
        const rs = runWalker2(s0[0], s0[1], s1[0], s1[1], L, B);
        account(rs[0], j);
        account(rs[1], j + 1);
    }
    if (j < j1) {
        const s = stateOf(seedLo, seedHi, j);
        account(runWalker(s[0], s[1], L, B), j);
    }

    parentPort.postMessage({
        spread: spread,
        bumps: bumps,
        returns: returns,
        bestDist: bestDist,
        bestJ: bestJ
    });
}

function main() {
    const inputPath = process.argv[2];
    let workersArg = parseInt(process.argv[3], 10);
    if (!(workersArg >= 1)) workersArg = 1;

    const tok = fs.readFileSync(inputPath, "utf8").trim().split(/\s+/);
    const J = parseInt(tok[0], 10);
    const L = parseInt(tok[1], 10);
    const B = parseInt(tok[2], 10);
    const seed = BigInt(tok[3]);
    const seedLo = Number(seed & 0xFFFFFFFFn);
    const seedHi = Number((seed >> 32n) & 0xFFFFFFFFn);

    let workers = workersArg;
    if (workers > J) workers = J;
    if (workers < 1) workers = 1;

    if (J <= 0) {
        process.stdout.write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
        return;
    }

    if (workers === 1) {
        let spread = 0n, bumps = 0, returns = 0;
        let bestDist = -1, bestJ = 0;
        const account = (r, j) => {
            spread += r.spread;
            bumps += r.bumps;
            returns += r.returns;
            const d = Math.abs(r.x) + Math.abs(r.y);
            if (d > bestDist) { bestDist = d; bestJ = j; }
        };
        let j = 0;
        for (; j + 1 < J; j += 2) {
            const s0 = stateOf(seedLo, seedHi, j);
            const s1 = stateOf(seedLo, seedHi, j + 1);
            const rs = runWalker2(s0[0], s0[1], s1[0], s1[1], L, B);
            account(rs[0], j);
            account(rs[1], j + 1);
        }
        if (j < J) {
            const s = stateOf(seedLo, seedHi, j);
            account(runWalker(s[0], s[1], L, B), j);
        }
        process.stdout.write(
            "spread " + spread + "\nbumps " + bumps + "\nreturns " + returns +
            "\nfarthest " + bestJ + " " + bestDist + "\n");
        return;
    }

    const jobs = [];
    const baseCount = Math.floor(J / workers);
    const rem = J % workers;
    let start = 0;
    for (let t = 0; t < workers; ++t) {
        const cnt = baseCount + (t < rem ? 1 : 0);
        const j0 = start;
        const j1 = start + cnt;
        start = j1;
        jobs.push({ j0: j0, j1: j1, L: L, B: B, seedLo: seedLo, seedHi: seedHi });
    }

    let remaining = jobs.length;
    let spread = 0n, bumps = 0, returns = 0;
    let bestDist = -1, bestJ = 0;

    for (let t = 0; t < jobs.length; ++t) {
        const w = new Worker(__filename, { workerData: jobs[t] });
        w.on("message", (msg) => {
            spread += msg.spread;
            bumps += msg.bumps;
            returns += msg.returns;
            if (msg.bestDist > bestDist ||
                (msg.bestDist === bestDist && msg.bestJ < bestJ)) {
                bestDist = msg.bestDist;
                bestJ = msg.bestJ;
            }
            if (--remaining === 0) {
                process.stdout.write(
                    "spread " + spread + "\nbumps " + bumps + "\nreturns " + returns +
                    "\nfarthest " + bestJ + " " + bestDist + "\n");
            }
        });
        w.on("error", (err) => { throw err; });
    }
}

if (isMainThread) {
    main();
} else {
    workerMain();
}
