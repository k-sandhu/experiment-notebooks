"use strict";
const fs = require("fs");

const d = fs.readFileSync(process.argv[2]);
const N = d.length;
let pos = 0;

const charIdx = new Int32Array(256).fill(-1);
let A = 0;
while (pos < N && d[pos] !== 10) {
  const c = d[pos++];
  if (c >= 65 && c <= 90) charIdx[c] = A++;
}
if (pos < N) pos++;

function skipWs() {
  while (pos < N) {
    const c = d[pos];
    if (c === 32 || c === 10 || c === 13 || c === 9) pos++;
    else break;
  }
}
function parseInt() {
  skipWs();
  let v = 0;
  while (pos < N && d[pos] >= 48 && d[pos] <= 57) v = v * 10 + (d[pos++] - 48);
  return v;
}

const ins = new Int32Array(A), del = new Int32Array(A), sub = new Int32Array(A * A);
for (let i = 0; i < A; i++) ins[i] = parseInt();
for (let i = 0; i < A; i++) del[i] = parseInt();
for (let i = 0; i < A * A; i++) sub[i] = parseInt();
const P = parseInt();

const strs = new Array(2 * P);
let maxLen = 0;
for (let k = 0; k < 2 * P; k++) {
  skipWs();
  const start = pos;
  while (pos < N) {
    const c = d[pos];
    if (c === 32 || c === 10 || c === 13 || c === 9) break;
    pos++;
  }
  const len = pos - start;
  const s = new Uint8Array(len);
  for (let i = 0; i < len; i++) s[i] = charIdx[d[start + i]];
  if (len > maxLen) maxLen = len;
  strs[k] = s;
}

let prev = new Int32Array(maxLen + 1), cur = new Int32Array(maxLen + 1);
const insT = new Int32Array(maxLen);
const parts = [];
let total = 0;

for (let p = 0; p < P; p++) {
  const s = strs[2 * p], t = strs[2 * p + 1];
  const n = s.length, m = t.length;
  for (let j = 0; j < m; j++) insT[j] = ins[t[j]];
  prev[0] = 0;
  for (let j = 0; j < m; j++) prev[j + 1] = prev[j] + insT[j];
  for (let i = 0; i < n; i++) {
    const si = s[i];
    const dcost = del[si];
    const subBase = si * A;
    let diag = prev[0];
    let left = diag + dcost;
    cur[0] = left;
    for (let j = 0; j < m; j++) {
      const up = prev[j + 1];
      const a = up + dcost;
      const b = left + insT[j];
      const c = diag + sub[subBase + t[j]];
      let v = a < b ? a : b;
      if (c < v) v = c;
      diag = up;
      left = v;
      cur[j + 1] = v;
    }
    const tmp = prev; prev = cur; cur = tmp;
  }
  const ans = prev[m];
  total += ans;
  parts.push(ans);
}
parts.push("total " + total);
process.stdout.write(parts.join("\n") + "\n");
