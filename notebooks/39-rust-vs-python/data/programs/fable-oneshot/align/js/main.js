'use strict';
const fs = require('fs');

function main() {
  const data = fs.readFileSync(process.argv[2], 'latin1');
  const tok = data.split(/\s+/);
  let pos = 0;
  if (tok.length > 0 && tok[0] === '') pos = 1;

  const alphabet = tok[pos++];
  const A = alphabet.length;
  const map = new Uint8Array(256);
  for (let i = 0; i < A; i++) map[alphabet.charCodeAt(i) & 255] = i;

  const ins = new Int32Array(A);
  const del = new Int32Array(A);
  const sub = new Int32Array(A * A);
  for (let i = 0; i < A; i++) ins[i] = parseInt(tok[pos++], 10);
  for (let i = 0; i < A; i++) del[i] = parseInt(tok[pos++], 10);
  for (let i = 0; i < A * A; i++) sub[i] = parseInt(tok[pos++], 10);

  const P = parseInt(tok[pos++], 10);

  let capM = 1024;
  let capN = 1024;
  let row = new Int32Array(capM + 1);
  let insT = new Int32Array(capM);
  let tc = new Uint8Array(capM);
  let prof = new Int32Array(A * capM);
  let sc = new Uint8Array(capN);

  const out = new Array(P + 1);
  let total = 0;

  for (let p = 0; p < P; p++) {
    const s = tok[pos++];
    const t = tok[pos++];
    const n = s.length;
    const m = t.length;

    if (m > capM) {
      capM = m * 2;
      row = new Int32Array(capM + 1);
      insT = new Int32Array(capM);
      tc = new Uint8Array(capM);
      prof = new Int32Array(A * capM);
    }
    if (n > capN) {
      capN = n * 2;
      sc = new Uint8Array(capN);
    }

    for (let i = 0; i < n; i++) sc[i] = map[s.charCodeAt(i) & 255];

    // first row and per-column insertion costs
    row[0] = 0;
    let acc = 0;
    for (let j = 0; j < m; j++) {
      const c = map[t.charCodeAt(j) & 255];
      tc[j] = c;
      const ic = ins[c];
      insT[j] = ic;
      acc += ic;
      row[j + 1] = acc;
    }

    // query profile: prof[c*m + j] = sub[c][t_j]
    for (let c = 0; c < A; c++) {
      const base = c * A;
      const off = c * m;
      for (let j = 0; j < m; j++) {
        prof[off + j] = sub[base + tc[j]];
      }
    }

    for (let i = 0; i < n; i++) {
      const c = sc[i];
      const d = del[c];
      const off = c * m;
      let diag = row[0];
      let left = diag + d;
      row[0] = left;
      for (let j = 0; j < m; j++) {
        const up = row[j + 1];
        let v = diag + prof[off + j];
        const a = up + d;
        if (a < v) v = a;
        const b = left + insT[j];
        if (b < v) v = b;
        row[j + 1] = v;
        left = v;
        diag = up;
      }
    }

    const cost = row[m];
    total += cost;
    out[p] = cost;
  }

  out[P] = 'total ' + total;
  process.stdout.write(out.join('\n') + '\n');
}

main();
