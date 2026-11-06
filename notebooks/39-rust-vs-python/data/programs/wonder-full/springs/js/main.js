'use strict';
const fs = require('fs');

const data = fs.readFileSync(process.argv[2], 'utf8');
const toks = data.trim().split(/\s+/);
let t = 0;
const N = (toks[t++] | 0);
const S = Number(toks[t++]);
const dt = Number(toks[t++]);
const P = Number(toks[t++]);

if (!(N > 0)) {
  process.stdout.write('kinetic 0.000000000000e+00\npotential 0.000000000000e+00\nposition 0.000000000000e+00\nfastest 0\n');
  process.exit(0);
}

const x = new Float64Array(N);
const v = new Float64Array(N);
const m = new Float64Array(N);
const k = new Float64Array(N);
const r = new Float64Array(N);
const c = new Float64Array(N);
const a = new Float64Array(N); // dt / m

for (let i = 0; i < N; i++) {
  x[i] = Number(toks[t++]);
  v[i] = Number(toks[t++]);
  const mi = Number(toks[t++]);
  m[i] = mi;
  k[i] = Number(toks[t++]);
  r[i] = Number(toks[t++]);
  c[i] = Number(toks[t++]);
  a[i] = dt / mi;
}

const nm1 = N - 1;
const kn = k[nm1], rn = r[nm1];
for (let step = 0; step < S; step++) {
  const fLast = kn * (((x[0] + P) - x[nm1]) - rn);
  let fPrev = fLast;
  let xcur = x[0];
  for (let i = 0; i < nm1; i++) {
    const xnext = x[i + 1];
    const fi = k[i] * ((xnext - xcur) - r[i]);
    const vi = v[i];
    const nv = vi + a[i] * ((fi - fPrev) - c[i] * vi);
    v[i] = nv;
    x[i] = xcur + dt * nv;
    fPrev = fi;
    xcur = xnext;
  }
  // last mass (also correct for N==1)
  const nv = v[nm1] + a[nm1] * ((fLast - fPrev) - c[nm1] * v[nm1]);
  v[nm1] = nv;
  x[nm1] = x[nm1] + dt * nv;
}

let K = 0, U = 0, X = 0;
let J = 0;
let best = Math.abs(v[0]);
for (let i = 0; i < N; i++) {
  const vi = v[i];
  K += ((0.5 * m[i]) * vi) * vi;
  X += x[i];
  const av = vi < 0 ? -vi : vi;
  if (av > best) { best = av; J = i; }
}
for (let i = 0; i < nm1; i++) {
  const s = (x[i + 1] - x[i]) - r[i];
  U += ((0.5 * k[i]) * s) * s;
}
{
  const s = ((x[0] + P) - x[nm1]) - rn;
  U += ((0.5 * kn) * s) * s;
}

process.stdout.write(
  'kinetic ' + K.toExponential(12) + '\n' +
  'potential ' + U.toExponential(12) + '\n' +
  'position ' + X.toExponential(12) + '\n' +
  'fastest ' + J + '\n');
