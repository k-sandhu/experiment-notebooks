'use strict';

const fs = require('fs');

const input = fs.readFileSync(process.argv[2], 'utf8');
const tokens = input.split(/\s+/).filter(Boolean);
let t = 0;
const nextInt = () => parseInt(tokens[t++], 10);
const nextFloat = () => parseFloat(tokens[t++]);

const N = nextInt();
const S = nextInt();
const dt = nextFloat();
const P = nextFloat();

const x = new Array(N);
const v = new Array(N);
const m = new Array(N);
const k = new Array(N);
const r = new Array(N);
const c = new Array(N);
const f = new Array(N);
for (let i = 0; i < N; ++i) {
    x[i] = nextFloat();
    v[i] = nextFloat();
    m[i] = nextFloat();
    k[i] = nextFloat();
    r[i] = nextFloat();
    c[i] = nextFloat();
}

const nm1 = N - 1;
for (let step = 0; step < S; ++step) {
    // Stretches and spring forces from the old positions (read-only).
    for (let i = 0; i < nm1; ++i) {
        f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
    }
    f[nm1] = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1]);

    // Forces, then velocities, then positions. f is read-only here.
    let F = (f[0] - f[nm1]) - (c[0] * v[0]);
    v[0] = v[0] + dt * (F / m[0]);
    x[0] = x[0] + dt * v[0];
    for (let i = 1; i < N; ++i) {
        F = (f[i] - f[i - 1]) - (c[i] * v[i]);
        v[i] = v[i] + dt * (F / m[i]);
        x[i] = x[i] + dt * v[i];
    }
}

let K = 0.0;
let U = 0.0;
let X = 0.0;
let J = 0;
let best = -1.0;
for (let i = 0; i < N; ++i) {
    const xnext = (i + 1 < N) ? x[i + 1] : x[0] + P;
    const s = (xnext - x[i]) - r[i];
    U += ((0.5 * k[i]) * s) * s;
    K += ((0.5 * m[i]) * v[i]) * v[i];
    X += x[i];
    const av = v[i] < 0 ? -v[i] : v[i];
    if (av > best) { // strict: on a tie the smallest index wins
        best = av;
        J = i;
    }
}

process.stdout.write(
    'kinetic ' + K.toExponential(12) + '\n' +
    'potential ' + U.toExponential(12) + '\n' +
    'position ' + X.toExponential(12) + '\n' +
    'fastest ' + J + '\n');
