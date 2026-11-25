"use strict";

const fs = require("fs");

// One fused pass per step. x has length n+1: x[n] is the ghost x[0] + P closing the ring.
function simulate(n, steps, dt, P, x, v, m, k, r, c) {
  for (let s = 0; s < steps; s++) {
    x[n] = x[0] + P;
    let fprev = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
    let xi = x[0];
    for (let i = 0; i < n; i++) {
      const xn = x[i + 1];
      const f = k[i] * ((xn - xi) - r[i]);
      let vi = v[i];
      const F = (f - fprev) - c[i] * vi;
      vi = vi + dt * (F / m[i]);
      v[i] = vi;
      x[i] = xi + dt * vi;
      fprev = f;
      xi = xn;
    }
  }
}

function main() {
  const text = fs.readFileSync(process.argv[2], "latin1");
  const tok = text.split(/\s+/);
  let p = 0;
  while (p < tok.length && tok[p] === "") p++;
  const n = parseInt(tok[p++], 10);
  const steps = parseInt(tok[p++], 10);
  const dt = Number(tok[p++]);
  const P = Number(tok[p++]);

  const x = new Float64Array(n + 1);
  const v = new Float64Array(n);
  const m = new Float64Array(n);
  const k = new Float64Array(n);
  const r = new Float64Array(n);
  const c = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    x[i] = Number(tok[p++]);
    v[i] = Number(tok[p++]);
    m[i] = Number(tok[p++]);
    k[i] = Number(tok[p++]);
    r[i] = Number(tok[p++]);
    c[i] = Number(tok[p++]);
  }

  simulate(n, steps, dt, P, x, v, m, k, r, c);

  let K = 0, U = 0, X = 0, best = -1, J = 0;
  x[n] = x[0] + P;
  for (let i = 0; i < n; i++) {
    K += ((0.5 * m[i]) * v[i]) * v[i];
    const st = (x[i + 1] - x[i]) - r[i];
    U += ((0.5 * k[i]) * st) * st;
    X += x[i];
    const a = Math.abs(v[i]);
    if (a > best) {
      best = a;
      J = i;
    }
  }
  process.stdout.write(`kinetic ${K}\npotential ${U}\nposition ${X}\nfastest ${J}\n`);
}

main();
