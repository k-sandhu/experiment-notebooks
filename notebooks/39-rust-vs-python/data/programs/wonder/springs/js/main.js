"use strict";
const fs = require("fs");
const data = fs.readFileSync(process.argv[2], "utf8");
const toks = data.split(/\s+/);
// remove possible empty tokens
let ti = 0;
if (toks[0] === "") ti = 1;
// If trailing empty doesn't matter
const N = parseInt(toks[ti++], 10);
const S = parseInt(toks[ti++], 10);
const dt = Number(toks[ti++]);
const P = Number(toks[ti++]);
const x = new Float64Array(N), v = new Float64Array(N), m = new Float64Array(N),
      k = new Float64Array(N), r = new Float64Array(N), c = new Float64Array(N), dtm = new Float64Array(N);
for (let i = 0; i < N; i++) {
  x[i] = Number(toks[ti++]); v[i] = Number(toks[ti++]); m[i] = Number(toks[ti++]);
  k[i] = Number(toks[ti++]); r[i] = Number(toks[ti++]); c[i] = Number(toks[ti++]); dtm[i] = dt / m[i];
}
for (let step = 0; step < S; step++) {
  const fLast = k[N-1] * (((x[0] + P) - x[N-1]) - r[N-1]);
  let prevF = fLast;
  const last = N - 1;
  for (let i = 0; i < last; i++) {
    const fi = k[i] * ((x[i+1] - x[i]) - r[i]);
    const F = (fi - prevF) - (c[i] * v[i]);
    const nv = v[i] + dtm[i] * F;
    v[i] = nv;
    x[i] = x[i] + dt * nv;
    prevF = fi;
  }
  {
    const i = last;
    const F = (fLast - prevF) - (c[i] * v[i]);
    const nv = v[i] + dtm[i] * F;
    v[i] = nv;
    x[i] = x[i] + dt * nv;
  }
}
let K = 0, U = 0, X = 0;
for (let i = 0; i < N; i++) { K += ((0.5 * m[i]) * v[i]) * v[i]; X += x[i]; }
for (let i = 0; i < N-1; i++) { const s = (x[i+1]-x[i])-r[i]; U += ((0.5*k[i])*s)*s; }
{ const s = ((x[0]+P)-x[N-1])-r[N-1]; U += ((0.5*k[N-1])*s)*s; }
let J = 0, best = Math.abs(v[0]);
for (let i = 1; i < N; i++) { const a = Math.abs(v[i]); if (a > best) { best = a; J = i; } }
process.stdout.write(`kinetic ${K.toExponential(17)}\npotential ${U.toExponential(17)}\nposition ${X.toExponential(17)}\nfastest ${J}\n`);
