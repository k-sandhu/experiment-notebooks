"use strict";

const fs = require("fs");
const path = require("path");
const { Worker } = require("worker_threads");

const MASK = 0xffffffffffffffffn;
const C1 = 0x9E3779B97F4A7C15n;
const C2 = 0xBF58476D1CE4E5B9n;
const C3 = 0x94D049BB133111EBn;

function main() {
    const args = process.argv.slice(2);
    const text = fs.readFileSync(args[0], "utf8");
    const parts = text.trim().split(/\s+/);
    const J = Number(parts[0]);
    const L = Number(parts[1]);
    const B = Number(parts[2]);
    const seed = BigInt(parts[3]);
    const W = Number(args[1]);
    const workers = Math.max(1, Math.min(32, W));

    const results = [];
    let pending = workers;
    for (let i = 0; i < workers; i++) {
        const start = Math.floor((i * J) / workers);
        const end = Math.floor(((i + 1) * J) / workers);
        const w = new Worker(require("path").join(__dirname, "worker.js"), {
            workerData: { start, end, L, B, seed: seed.toString() },
        });
        w.on("message", (res) => {
            results[i] = res;
            if (--pending === 0) finish();
        });
        w.on("error", (err) => {
            console.error(err);
            process.exit(1);
        });
    }

    function finish() {
        let spread = results[0].spread;
        let bumps = results[0].bumps;
        let returns = results[0].returns;
        let farDist = results[0].farDist;
        let farWalker = results[0].farWalker;
        for (let i = 1; i < workers; i++) {
            const r = results[i];
            spread += r.spread;
            bumps += r.bumps;
            returns += r.returns;
            const d = Number(r.farDist);
            if (d > Number(farDist) || (d === Number(farDist) && r.farWalker < farWalker)) {
                farDist = r.farDist;
                farWalker = r.farWalker;
            }
        }
        process.stdout.write(
            "spread " + spread + "\n" +
            "bumps " + bumps + "\n" +
            "returns " + returns + "\n" +
            "farthest " + farWalker + " " + farDist + "\n",
        );
        process.exit(0);
    }
}

main();
