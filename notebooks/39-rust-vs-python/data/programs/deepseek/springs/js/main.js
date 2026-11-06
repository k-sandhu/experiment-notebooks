"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2], "utf8");
const len = data.length;
let pos = 0;

function isWs(c) {
    return c === 32 || c === 10 || c === 13 || c === 9;
}

function nextToken() {
    while (pos < len && isWs(data.charCodeAt(pos))) pos++;
    const start = pos;
    while (pos < len && !isWs(data.charCodeAt(pos))) pos++;
    return data.substring(start, pos);
}

function nextNumber() {
    while (pos < len && isWs(data.charCodeAt(pos))) pos++;
    const start = pos;
    while (pos < len && !isWs(data.charCodeAt(pos))) pos++;
    return Number(data.substring(start, pos));
}

const n = nextNumber();
const steps = nextNumber();
const dt = nextNumber();
const P = nextNumber();

const x = new Float64Array(n);
const v = new Float64Array(n);
const m = new Float64Array(n);
const k = new Float64Array(n);
const r = new Float64Array(n);
const c = new Float64Array(n);

for (let i = 0; i < n; i++) {
    x[i] = nextNumber();
    v[i] = nextNumber();
    m[i] = nextNumber();
    k[i] = nextNumber();
    r[i] = nextNumber();
    c[i] = nextNumber();
}

const last = n - 1;
for (let t = 0; t < steps; t++) {
    const x0 = x[0];
    const xl = x[last];
    const sLast = ((x0 + P) - xl) - r[last];
    const fLast = k[last] * sLast;
    let fprev = fLast;

    for (let i = 0; i < last; i++) {
        const s = (x[i + 1] - x[i]) - r[i];
        const f = k[i] * s;
        const F = (f - fprev) - c[i] * v[i];
        const nv = v[i] + dt * (F / m[i]);
        v[i] = nv;
        x[i] = x[i] + dt * nv;
        fprev = f;
    }

    const Fl = (fLast - fprev) - c[last] * v[last];
    const nvl = v[last] + dt * (Fl / m[last]);
    v[last] = nvl;
    x[last] = x[last] + dt * nvl;
}

let K = 0.0, U = 0.0, X = 0.0;
for (let i = 0; i < n; i++) {
    K += ((0.5 * m[i]) * v[i]) * v[i];
    X += x[i];
}
for (let i = 0; i < last; i++) {
    const s = (x[i + 1] - x[i]) - r[i];
    U += ((0.5 * k[i]) * s) * s;
}
{
    const s = ((x[0] + P) - x[last]) - r[last];
    U += ((0.5 * k[last]) * s) * s;
}

let fastest = 0;
let best = -1.0;
for (let i = 0; i < n; i++) {
    const a = v[i] < 0 ? -v[i] : v[i];
    if (a > best) { best = a; fastest = i; }
}

let out = "kinetic " + K.toExponential(12) + "\n" +
          "potential " + U.toExponential(12) + "\n" +
          "position " + X.toExponential(12) + "\n" +
          "fastest " + fastest + "\n";
process.stdout.write(out);
