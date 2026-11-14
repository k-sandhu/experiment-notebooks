'use strict';

const fs = require('fs');

function main() {
  const tokens = fs.readFileSync(process.argv[2], 'utf8').trim().split(/\s+/);
  let p = 0;

  const n = Number(tokens[p++]);
  const steps = Number(tokens[p++]);
  const dt = Number(tokens[p++]);
  const circumference = Number(tokens[p++]);

  const x = new Float64Array(n);
  const v = new Float64Array(n);
  const m = new Float64Array(n);
  const k = new Float64Array(n);
  const r = new Float64Array(n);
  const c = new Float64Array(n);
  const force = new Float64Array(n);

  for (let i = 0; i < n; i++) {
    x[i] = Number(tokens[p++]);
    v[i] = Number(tokens[p++]);
    m[i] = Number(tokens[p++]);
    k[i] = Number(tokens[p++]);
    r[i] = Number(tokens[p++]);
    c[i] = Number(tokens[p++]);
  }

  const last = n - 1;

  for (let step = 0; step < steps; step++) {
    for (let i = 0; i < last; i++) {
      force[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
    }
    force[last] =
      k[last] * (((x[0] + circumference) - x[last]) - r[last]);

    let previousForce = force[last];
    for (let i = 0; i < n; i++) {
      const currentForce = force[i];
      const oldVelocity = v[i];
      const netForce =
        (currentForce - previousForce) - (c[i] * oldVelocity);
      const newVelocity = oldVelocity + dt * (netForce / m[i]);

      v[i] = newVelocity;
      x[i] = x[i] + dt * newVelocity;
      previousForce = currentForce;
    }
  }

  let kinetic = 0;
  let potential = 0;
  let position = 0;
  let fastest = 0;
  let greatestSpeed = -1;

  for (let i = 0; i < n; i++) {
    const velocity = v[i];
    kinetic += ((0.5 * m[i]) * velocity) * velocity;
    position += x[i];

    const speed = Math.abs(velocity);
    if (speed > greatestSpeed) {
      greatestSpeed = speed;
      fastest = i;
    }
  }

  for (let i = 0; i < last; i++) {
    const stretch = (x[i + 1] - x[i]) - r[i];
    potential += ((0.5 * k[i]) * stretch) * stretch;
  }

  const lastStretch =
    ((x[0] + circumference) - x[last]) - r[last];
  potential += ((0.5 * k[last]) * lastStretch) * lastStretch;

  process.stdout.write(
    `kinetic ${kinetic.toExponential(16)}\n` +
    `potential ${potential.toExponential(16)}\n` +
    `position ${position.toExponential(16)}\n` +
    `fastest ${fastest}\n`
  );
}

main();
