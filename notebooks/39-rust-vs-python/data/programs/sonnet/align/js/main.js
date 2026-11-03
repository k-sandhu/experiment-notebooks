"use strict";
const fs = require("fs");

const b = fs.readFileSync(process.argv[2]);
const len = b.length;
let p = 0;

function skipWs() {
  while (p < len && b[p] <= 32) p++;
}
function nextInt() {
  skipWs();
  let v = 0;
  while (p < len && b[p] >= 48 && b[p] <= 57) v = v * 10 + (b[p++] - 48);
  return v;
}

skipWs();
const code = new Int32Array(256);
let A = 0;
while (p < len && b[p] > 32) code[b[p++]] = A++;
const ins = new Int32Array(A), del = new Int32Array(A), sub = new Int32Array(A * A);
for (let i = 0; i < A; i++) ins[i] = nextInt();
for (let i = 0; i < A; i++) del[i] = nextInt();
for (let i = 0; i < A * A; i++) sub[i] = nextInt();
const P = nextInt();

let cap = 16;
let prev = new Int32Array(cap), cur = new Int32Array(cap), tc = new Int32Array(cap), insT = new Int32Array(cap);
const out = [];
let total = 0;
for (let q = 0; q < P; q++) {
  skipWs();
  const s = p;
  while (p < len && b[p] > 32) p++;
  const n = p - s;
  skipWs();
  const t = p;
  while (p < len && b[p] > 32) p++;
  const m = p - t;
  if (cap < m + 1) {
    cap = m + 1;
    prev = new Int32Array(cap); cur = new Int32Array(cap);
    tc = new Int32Array(cap); insT = new Int32Array(cap);
  }
  for (let j = 1; j <= m; j++) {
    const c = code[b[t + j - 1]];
    tc[j] = c;
    insT[j] = ins[c];
  }
  let pv = prev, cu = cur;
  pv[0] = 0;
  for (let j = 1; j <= m; j++) pv[j] = pv[j - 1] + insT[j];
  for (let i = 1; i <= n; i++) {
    const a = code[b[s + i - 1]];
    const d = del[a];
    const base = a * A;
    let left = pv[0] + d;
    cu[0] = left;
    for (let j = 1; j <= m; j++) {
      let v = pv[j] + d;
      const w = pv[j - 1] + sub[base + tc[j]];
      if (w < v) v = w;
      const l = left + insT[j];
      if (l < v) v = l;
      left = v;
      cu[j] = v;
    }
    const tmp = pv; pv = cu; cu = tmp;
  }
  const r = pv[m];
  total += r;
  out.push(r);
}
out.push("total " + total);
process.stdout.write(out.join("\n") + "\n");
