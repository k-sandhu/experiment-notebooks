"use strict";

const { parentPort, workerData } = require("worker_threads");

const MASK = 0xffffffffffffffffn;
const C1 = 0x9E3779B97F4A7C15n;
const C2 = 0xBF58476D1CE4E5B9n;
const C3 = 0x94D049BB133111EBn;

// Simulate walkers [start, end). Integer sums and the (distance, index)
// order are reduction-order independent, so this does not depend on how
// walkers are split across workers.
function runRange(start, end, L, B, seed) {
    let spread = 0n;
    let bumps = 0n;
    let returns = 0n;
    let farDist = 0n;
    let farWalker = start;
    const negB = -B;
    for (let j = start; j < end; j++) {
        let state = (seed + BigInt(j)) & MASK;
        let x = 0;
        let y = 0;
        let b = 0;
        let r = 0;
        for (let t = 0; t < L; t++) {
            state = (state + C1) & MASK;
            let z = state;
            z = ((z ^ (z >> 30n)) * C2) & MASK;
            z = ((z ^ (z >> 27n)) * C3) & MASK;
            const rnd = z ^ (z >> 31n);
            const d = Number(rnd >> 62n);
            let nx = x;
            let ny = y;
            if (d === 0) nx = x + 1;
            else if (d === 1) nx = x - 1;
            else if (d === 2) ny = y + 1;
            else ny = y - 1;
            if (nx >= negB && nx <= B && ny >= negB && ny <= B) {
                x = nx;
                y = ny;
                if (x === 0 && y === 0) r++;
            } else {
                b++;
            }
        }
        spread += BigInt(x * x + y * y);
        bumps += BigInt(b);
        returns += BigInt(r);
        const dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
        if (dist > Number(farDist)) {
            farDist = BigInt(dist);
            farWalker = j;
        }
    }
    return { spread, bumps, returns, farDist, farWalker };
}

const res = runRange(workerData.start, workerData.end, workerData.L, workerData.B, BigInt(workerData.seed));
parentPort.postMessage(res);
