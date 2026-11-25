"use strict";
const fs = require("fs");
const { Worker, isMainThread, parentPort, workerData } = require("worker_threads");

const GOLD_LO_U = 0x7F4A7C15;
const GOLD_HI = 0x9E3779B9 | 0;
const C1_HI = 0xBF58476D | 0, C1_LO = 0x1CE4E5B9 | 0;
const C2_HI = 0x94D049BB | 0, C2_LO = 0x133111EB | 0;
// 16-bit halves of multiplier low words
const C1_LO16 = 0xE5B9, C1_HI16 = 0x1CE4;
const C2_LO16 = 0x11EB, C2_HI16 = 0x1331;

function compute(start, end, L, B, seedHi, seedLo) {
    let spread = 0, bumps = 0, returns = 0;
    let bestD = -1, bestJ = start;
    const DX = [1, -1, 0, 0];
    const DY = [0, 0, 1, -1];
    for (let j = start; j < end; j++) {
        // state = seed + j (unsigned 64)
        let loU0 = (seedLo >>> 0) + j;
        let carry0 = loU0 >= 4294967296 ? 1 : 0;
        let stateLo = loU0 | 0;
        let stateHi = (seedHi + carry0) | 0;
        let x = 0, y = 0;
        let b = 0, r = 0;
        for (let i = 0; i < L; i++) {
            // state += GOLD
            let loU = (stateLo >>> 0) + GOLD_LO_U;
            let carry = loU >= 4294967296 ? 1 : 0;
            stateLo = loU | 0;
            stateHi = (stateHi + GOLD_HI + carry) | 0;
            let zHi = stateHi, zLo = stateLo;
            // z ^= z >> 30
            zHi ^= zHi >>> 30;
            zLo ^= (stateHi << 2) | (stateLo >>> 30); // careful: use original z values
            // Actually above used state (=z before xor). Since zHi already xored for hi, lo shift uses original hi.
            // Recompute correctly: we already mutated zHi, but (stateHi) is original, ok.
            // multiply by C1
            {
                const aLo = zLo;
                const aLo16 = aLo & 0xffff;
                const aHi16 = aLo >>> 16;
                const mid = aHi16 * C1_LO16 + aLo16 * C1_HI16;
                const umulhi = aHi16 * C1_HI16 + Math.floor((mid * 65536 + aLo16 * C1_LO16) / 4294967296);
                const nh = (umulhi + Math.imul(zHi, C1_LO) + Math.imul(aLo, C1_HI)) | 0;
                const nl = Math.imul(aLo, C1_LO);
                zHi = nh; zLo = nl;
            }
            // z ^= z >> 27
            {
                const oh = zHi, ol = zLo;
                zHi = oh ^ (oh >>> 27);
                zLo = ol ^ ((oh << 5) | (ol >>> 27));
            }
            // multiply by C2
            {
                const aLo = zLo;
                const aLo16 = aLo & 0xffff;
                const aHi16 = aLo >>> 16;
                const mid = aHi16 * C2_LO16 + aLo16 * C2_HI16;
                const umulhi = aHi16 * C2_HI16 + Math.floor((mid * 65536 + aLo16 * C2_LO16) / 4294967296);
                const nh = (umulhi + Math.imul(zHi, C2_LO) + Math.imul(aLo, C2_HI)) | 0;
                const nl = Math.imul(aLo, C2_LO);
                zHi = nh; zLo = nl;
            }
            const rHi = zHi ^ (zHi >>> 31);
            const d = rHi >>> 30;
            const nx = x + DX[d];
            const ny = y + DY[d];
            if (nx > B || nx < -B || ny > B || ny < -B) {
                b++;
            } else {
                x = nx; y = ny;
                if (x === 0 && y === 0) r++;
            }
        }
        bumps += b; returns += r;
        spread += x * x + y * y;
        const dist = Math.abs(x) + Math.abs(y);
        if (dist > bestD) { bestD = dist; bestJ = j; }
    }
    return { spread, bumps, returns, bestD, bestJ };
}

if (!isMainThread) {
    const wd = workerData;
    const res = compute(wd.start, wd.end, wd.L, wd.B, wd.seedHi, wd.seedLo);
    parentPort.postMessage(res);
} else {
    main().catch(e => { console.error(e); process.exit(1); });
}

async function main() {
    const inputPath = process.argv[2];
    let workers = 1;
    if (process.argv[3] !== undefined) workers = parseInt(process.argv[3], 10) || 1;
    if (workers < 1) workers = 1;
    if (workers > 32) workers = 32;
    const text = fs.readFileSync(inputPath, "utf8").trim().split(/\s+/);
    const J = Number(text[0]);
    const L = Number(text[1]);
    const B = Number(text[2]);
    const seedBig = BigInt(text[3]);
    const seedHi = Number((seedBig >> 32n) & 0xffffffffn) | 0;
    const seedLo = Number(seedBig & 0xffffffffn) | 0;

    if (!(J > 0)) {
        process.stdout.write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
        return;
    }
    if (workers > J) workers = J;
    let parts;
    if (workers === 1) {
        parts = [compute(0, J, L, B, seedHi, seedLo)];
    } else {
        const base = Math.floor(J / workers), rem = J % workers;
        let s = 0;
        const promises = [];
        for (let w = 0; w < workers; w++) {
            const cnt = base + (w < rem ? 1 : 0);
            const st = s, en = s + cnt; s = en;
            promises.push(new Promise((resolve, reject) => {
                const wk = new Worker(__filename, { workerData: { start: st, end: en, L, B, seedHi, seedLo } });
                wk.once("message", resolve);
                wk.once("error", reject);
                wk.once("exit", code => { if (code !== 0) reject(new Error("worker exit " + code)); });
            }));
        }
        parts = await Promise.all(promises);
    }
    let spread = 0, bumps = 0, returns = 0, bestD = -1, bestJ = 0;
    for (const p of parts) {
        spread += p.spread; bumps += p.bumps; returns += p.returns;
        if (p.bestD > bestD) { bestD = p.bestD; bestJ = p.bestJ; }
    }
    if (bestD < 0) bestD = 0;
    process.stdout.write(`spread ${spread}\nbumps ${bumps}\nreturns ${returns}\nfarthest ${bestJ} ${bestD}\n`);
}
