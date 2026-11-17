'use strict';
const fs = require('fs');

function step(n, dt, P, x, v, m, k, r, c) {
  const last = n - 1;
  const x0 = x[0];
  const fLast = k[last] * (((x0 + P) - x[last]) - r[last]);
  let fPrev = fLast;
  let xi = x0;
  for (let i = 0; i < last; i++) {
    const xn = x[i + 1];
    const fi = k[i] * ((xn - xi) - r[i]);
    const vi0 = v[i];
    const F = (fi - fPrev) - (c[i] * vi0);
    const vi = vi0 + dt * (F / m[i]);
    v[i] = vi;
    x[i] = xi + dt * vi;
    fPrev = fi;
    xi = xn;
  }
  {
    const vi0 = v[last];
    const F = (fLast - fPrev) - (c[last] * vi0);
    const vi = vi0 + dt * (F / m[last]);
    v[last] = vi;
    x[last] = xi + dt * vi;
  }
}

function fmt(val) {
  if (!Number.isFinite(val)) return String(val);
  const s = val.toExponential(16);
  const e = s.indexOf('e');
  if (e < 0) return s;
  const mant = s.substring(0, e);
  const sign = s.charAt(e + 1);
  let digits = s.substring(e + 2);
  if (digits.length < 2) digits = '0' + digits;
  return mant + 'e' + sign + digits;
}

function main() {
  const text = fs.readFileSync(process.argv[2], 'utf8');
  const tok = text.split(/\s+/);
  let p = 0;
  if (tok.length > 0 && tok[0] === '') p = 1;
  const n = parseInt(tok[p++], 10);
  const S = parseInt(tok[p++], 10);
  const dt = Number(tok[p++]);
  const P = Number(tok[p++]);

  const x = new Float64Array(n);
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

  for (let s = 0; s < S; s++) {
    step(n, dt, P, x, v, m, k, r, c);
  }

  let K = 0.0;
  let U = 0.0;
  let X = 0.0;
  let J = 0;
  let best = Math.abs(v[0]);
  for (let i = 0; i < n; i++) {
    const vi = v[i];
    K += ((0.5 * m[i]) * vi) * vi;
    let st;
    if (i < n - 1) {
      st = (x[i + 1] - x[i]) - r[i];
    } else {
      st = ((x[0] + P) - x[i]) - r[i];
    }
    U += ((0.5 * k[i]) * st) * st;
    X += x[i];
    const a = Math.abs(vi);
    if (a > best) {
      best = a;
      J = i;
    }
  }

  const out =
    'kinetic ' + fmt(K) + '\n' +
    'potential ' + fmt(U) + '\n' +
    'position ' + fmt(X) + '\n' +
    'fastest ' + J + '\n';
  fs.writeSync(1, out);
}

main();
