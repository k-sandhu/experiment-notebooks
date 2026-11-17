"use strict";

// Springs on a ring: explicit time stepping of N masses joined by N springs (see SPEC.md).
//
// State lives in Float64Array buffers, so V8 keeps the hot loops on unboxed doubles. Each step
// runs in two passes. The arithmetic keeps the spec's operation order, so the results match the
// reference bit for bit, apart from summation order in the final sums.

const fs = require("fs");

function readRing(path) {
  const tokens = fs.readFileSync(path, "latin1").trim().split(/\s+/);
  let pos = 0;
  const n = Number(tokens[pos++]);
  const steps = Number(tokens[pos++]);
  const dt = Number(tokens[pos++]);
  const circumference = Number(tokens[pos++]);

  const x = new Float64Array(n);
  const v = new Float64Array(n);
  const m = new Float64Array(n);
  const k = new Float64Array(n);
  const r = new Float64Array(n);
  const c = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    x[i] = Number(tokens[pos++]);
    v[i] = Number(tokens[pos++]);
    m[i] = Number(tokens[pos++]);
    k[i] = Number(tokens[pos++]);
    r[i] = Number(tokens[pos++]);
    c[i] = Number(tokens[pos++]);
  }
  return { n, steps, dt, circumference, x, v, m, k, r, c, f: new Float64Array(n) };
}

// One time step (SPEC.md, "One time step").
function step(ring) {
  const { n, dt, circumference: p, x, v, m, k, r, c, f } = ring;

  // Pass 1: spring forces from the old positions. Spring n-1 wraps around to mass 0.
  for (let i = 0; i + 1 < n; i++) {
    f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
  }
  f[n - 1] = k[n - 1] * (((x[0] + p) - x[n - 1]) - r[n - 1]);

  // Pass 2: velocity from the forces (old velocity), then position from the new velocity.
  // Mass 0 uses the force of spring n-1 as its left neighbour.
  v[0] = v[0] + dt * (((f[0] - f[n - 1]) - (c[0] * v[0])) / m[0]);
  for (let i = 1; i < n; i++) {
    v[i] = v[i] + dt * (((f[i] - f[i - 1]) - (c[i] * v[i])) / m[i]);
  }
  for (let i = 0; i < n; i++) {
    x[i] = x[i] + dt * v[i];
  }
}

function main() {
  if (process.argv.length < 3) {
    console.error("usage: node main.js INPUT_PATH");
    process.exit(1);
  }
  const ring = readRing(process.argv[2]);
  const { n, x, v, m, k, r, circumference: p } = ring;

  for (let s = 0; s < ring.steps; s++) {
    step(ring);
  }

  let kinetic = 0;
  for (let i = 0; i < n; i++) {
    kinetic += ((0.5 * m[i]) * v[i]) * v[i];
  }

  let potential = 0;
  for (let i = 0; i + 1 < n; i++) {
    const s = (x[i + 1] - x[i]) - r[i];
    potential += ((0.5 * k[i]) * s) * s;
  }
  const sLast = ((x[0] + p) - x[n - 1]) - r[n - 1];
  potential += ((0.5 * k[n - 1]) * sLast) * sLast;

  let position = 0;
  for (let i = 0; i < n; i++) {
    position += x[i];
  }

  let fastest = 0;
  for (let i = 1; i < n; i++) {
    if (Math.abs(v[i]) > Math.abs(v[fastest])) {
      fastest = i;
    }
  }

  process.stdout.write(
    `kinetic ${kinetic.toExponential(16)}\n` +
      `potential ${potential.toExponential(16)}\n` +
      `position ${position.toExponential(16)}\n` +
      `fastest ${fastest}\n`
  );
}

main();
