"use strict";

const fs = require("fs");

function main() {
  const text = fs.readFileSync(process.argv[2], "latin1");
  const tokens = text.split(/[\s]+/);
  let ti = 0;
  const nextd = () => parseFloat(tokens[ti++]);

  const n = nextd() | 0;
  const s = nextd() | 0;
  const dt = nextd();
  const P = nextd();

  const x = new Float64Array(n), v = new Float64Array(n), m = new Float64Array(n);
  const k = new Float64Array(n), r = new Float64Array(n), c = new Float64Array(n);
  const f = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    x[i] = nextd();
    v[i] = nextd();
    m[i] = nextd();
    k[i] = nextd();
    r[i] = nextd();
    c[i] = nextd();
  }

  for (let step = 0; step < s; step++) {
    for (let i = 0; i < n - 1; i++) {
      f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
    }
    f[n - 1] = k[n - 1] * (((x[0] + P) - x[n - 1]) - r[n - 1]);

    {
      const F = (f[0] - f[n - 1]) - (c[0] * v[0]);
      const nv = v[0] + dt * (F / m[0]);
      x[0] = x[0] + dt * nv;
      v[0] = nv;
    }
    for (let i = 1; i < n; i++) {
      const F = (f[i] - f[i - 1]) - (c[i] * v[i]);
      const nv = v[i] + dt * (F / m[i]);
      x[i] = x[i] + dt * nv;
      v[i] = nv;
    }
  }

  let K = 0, U = 0, X = 0;
  let J = 0, best = 0;
  for (let i = 0; i < n; i++) {
    K += ((0.5 * m[i]) * v[i]) * v[i];
    X += x[i];
    const av = v[i] < 0 ? -v[i] : v[i];
    if (av > best) { best = av; J = i; }
  }
  for (let i = 0; i < n - 1; i++) {
    const sp = (x[i + 1] - x[i]) - r[i];
    U += ((0.5 * k[i]) * sp) * sp;
  }
  {
    const sp = ((x[0] + P) - x[n - 1]) - r[n - 1];
    U += ((0.5 * k[n - 1]) * sp) * sp;
  }

  process.stdout.write(
    "kinetic " + K.toExponential(17) +
    "\npotential " + U.toExponential(17) +
    "\nposition " + X.toExponential(17) +
    "\nfastest " + J + "\n"
  );
}

main();
