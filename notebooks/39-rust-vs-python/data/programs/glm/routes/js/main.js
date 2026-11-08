'use strict';
const fs = require('fs');

const buf = fs.readFileSync(process.argv[2]);
let pos = 0;

function readInt() {
  while (pos < buf.length && (buf[pos] < 48 || buf[pos] > 57)) pos++;
  let x = 0;
  while (pos < buf.length && buf[pos] >= 48 && buf[pos] <= 57) {
    x = x * 10 + buf[pos++] - 48;
  }
  return x;
}

const n = readInt(), m = readInt(), q = readInt();

const eu = new Int32Array(m), ev = new Int32Array(m), ew = new Int32Array(m);
const start = new Int32Array(n + 1);
for (let i = 0; i < m; i++) {
  const u = readInt(), v = readInt(), w = readInt();
  eu[i] = u; ev[i] = v; ew[i] = w;
  start[u + 1]++; start[v + 1]++;
}
for (let i = 0; i < n; i++) start[i + 1] += start[i];
const e2 = start[n];
const adjV = new Int32Array(e2), adjW = new Int32Array(e2);
const posArr = new Int32Array(n);
posArr.set(start.subarray(0, n));
for (let i = 0; i < m; i++) {
  const u = eu[i], v = ev[i], w = ew[i];
  adjV[posArr[u]] = v; adjW[posArr[u]] = w; posArr[u]++;
  adjV[posArr[v]] = u; adjW[posArr[v]] = w; posArr[v]++;
}

// Dial's bucket queue: weights are 1..1000, so a circular array of 1001
// buckets (singly linked lists through the arena array) holds all pending
// distances. Stale entries are skipped via the dist check.
const NB = 1001;
const arena = new Int32Array(2 * m + 2);
const nextIn = new Int32Array(2 * m + 2);
const head = new Int32Array(NB);

const dist = new Int32Array(n);
const settled = new Uint8Array(n);
const lines = new Array(q);

for (let qi = 0; qi < q; qi++) {
  const s = readInt();
  dist.fill(-1);
  settled.fill(0);
  head.fill(-1);
  let cnt = 0;
  dist[s] = 0;
  arena[cnt] = s; nextIn[cnt] = -1; head[0] = cnt; cnt++;
  let remaining = 1;
  let idx = 0;
  let d = 0;
  while (remaining > 0) {
    let e = head[idx];
    if (e < 0) { idx = idx + 1 === NB ? 0 : idx + 1; d++; continue; }
    head[idx] = nextIn[e];
    remaining--;
    const v = arena[e];
    if (settled[v] || dist[v] !== d) continue;
    settled[v] = 1;
    const end = start[v + 1];
    for (let i = start[v]; i < end; i++) {
      const u = adjV[i];
      if (settled[u]) continue;
      const nd = d + adjW[i];
      const du = dist[u];
      if (du < 0 || nd < du) {
        dist[u] = nd;
        const b = nd % NB;
        arena[cnt] = u; nextIn[cnt] = head[b]; head[b] = cnt; cnt++;
        remaining++;
      }
    }
  }
  let total = 0, far = 0, farNode = s, r = 0;
  for (let v = 0; v < n; v++) {
    const dd = dist[v];
    if (dd >= 0) {
      r++;
      total += dd;
      if (dd > far || (dd === far && v < farNode)) { far = dd; farNode = v; }
    }
  }
  lines[qi] = `${s} ${r} ${total} ${far} ${farNode}`;
}
process.stdout.write(lines.join('\n') + '\n');
