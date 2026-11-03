"use strict";
const fs = require("fs");

const t = fs.readFileSync(process.argv[2], "latin1").split(/\s+/).filter((s) => s.length > 0);
let p = 0;
const n = Number(t[p++]);
const steps = Number(t[p++]);
const dt = Number(t[p++]);
const P = Number(t[p++]);
const x = new Float64Array(n), v = new Float64Array(n), m = new Float64Array(n),
  k = new Float64Array(n), r = new Float64Array(n), c = new Float64Array(n);
for (let i = 0; i < n; i++) {
  x[i] = Number(t[p++]);
  v[i] = Number(t[p++]);
  m[i] = Number(t[p++]);
  k[i] = Number(t[p++]);
  r[i] = Number(t[p++]);
  c[i] = Number(t[p++]);
}
const n1 = n - 1;
for (let s = 0; s < steps; s++) {
  const flast = k[n1] * (((x[0] + P) - x[n1]) - r[n1]);
  let fprev = flast;
  for (let i = 0; i < n1; i++) {
    const f = k[i] * ((x[i + 1] - x[i]) - r[i]);
    const F = (f - fprev) - (c[i] * v[i]);
    const nv = v[i] + dt * (F / m[i]);
    v[i] = nv;
    x[i] = x[i] + dt * nv;
    fprev = f;
  }
  const F = (flast - fprev) - (c[n1] * v[n1]);
  const nv = v[n1] + dt * (F / m[n1]);
  v[n1] = nv;
  x[n1] = x[n1] + dt * nv;
}
let kin = 0, pot = 0, pos = 0, best = -1, bi = 0;
for (let i = 0; i < n; i++) {
  kin += ((0.5 * m[i]) * v[i]) * v[i];
  const st = i < n1 ? ((x[i + 1] - x[i]) - r[i]) : (((x[0] + P) - x[n1]) - r[n1]);
  pot += ((0.5 * k[i]) * st) * st;
  pos += x[i];
  const a = Math.abs(v[i]);
  if (a > best) { best = a; bi = i; }
}
process.stdout.write(`kinetic ${kin.toExponential(12)}\npotential ${pot.toExponential(12)}\nposition ${pos.toExponential(12)}\nfastest ${bi}\n`);
