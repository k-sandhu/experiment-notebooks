"use strict";

const fs = require("node:fs");

function simulate(n, steps, dt, p, x, v, m, k, r, c) {
    const last = n - 1;
    for (let step = 0; step < steps; ++step) {
        let current = x[0];
        const lastForce = k[last] * (((current + p) - x[last]) - r[last]);
        let previousForce = lastForce;
        // Keep old neighbors in scalars; no force buffer or second pass needed.
        for (let i = 0; i < last; ++i) {
            const next = x[i + 1];
            const force = k[i] * ((next - current) - r[i]);
            const net = (force - previousForce) - c[i] * v[i];
            const velocity = v[i] + dt * (net / m[i]);
            v[i] = velocity;
            x[i] = current + dt * velocity;
            current = next;
            previousForce = force;
        }
        const net = (lastForce - previousForce) - c[last] * v[last];
        const velocity = v[last] + dt * (net / m[last]);
        v[last] = velocity;
        x[last] = current + dt * velocity;
    }
}

function main() {
    const text = fs.readFileSync(process.argv[2], "utf8");
    let at = 0;
    function number() {
        while (at < text.length && text.charCodeAt(at) <= 32) ++at;
        const start = at;
        while (at < text.length && text.charCodeAt(at) > 32) ++at;
        return Number(text.slice(start, at));
    }
    const n = number(), steps = number(), dt = number(), p = number();
    const storage = new Float64Array(6 * n);
    const x = storage.subarray(0, n), v = storage.subarray(n, 2 * n);
    const m = storage.subarray(2 * n, 3 * n), k = storage.subarray(3 * n, 4 * n);
    const r = storage.subarray(4 * n, 5 * n), c = storage.subarray(5 * n, 6 * n);
    for (let i = 0; i < n; ++i) {
        x[i] = number(); v[i] = number(); m[i] = number();
        k[i] = number(); r[i] = number(); c[i] = number();
    }
    simulate(n, steps, dt, p, x, v, m, k, r, c);
    let kinetic = 0, potential = 0, position = 0;
    let fastest = 0, speed = Math.abs(v[0]);
    for (let i = 0; i < n; ++i) {
        kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        const stretch = i + 1 < n
            ? (x[i + 1] - x[i]) - r[i]
            : ((x[0] + p) - x[i]) - r[i];
        potential += ((0.5 * k[i]) * stretch) * stretch;
        position += x[i];
        if (Math.abs(v[i]) > speed) { speed = Math.abs(v[i]); fastest = i; }
    }
    process.stdout.write(`kinetic ${kinetic.toExponential(16)}\npotential ${potential.toExponential(16)}\nposition ${position.toExponential(16)}\nfastest ${fastest}\n`);
}

main();
