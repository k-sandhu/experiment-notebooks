"use strict";
const fs = require("fs");

const buf = fs.readFileSync(process.argv[2]);
const len = buf.length;
let pos = 0;

function readInt() {
  while (pos < len && buf[pos] < 48) pos++;
  let x = 0;
  let c;
  while (pos < len && (c = buf[pos]) >= 48) { x = x * 10 + (c - 48); pos++; }
  return x;
}

const n = readInt(), m = readInt(), q = readInt();
const eu = new Int32Array(m), ev = new Int32Array(m), ew = new Int32Array(m);
const start = new Int32Array(n + 2);
for (let i = 0; i < m; i++) {
  const u = readInt(), v = readInt(), w = readInt();
  eu[i] = u; ev[i] = v; ew[i] = w;
  if (u !== v) { start[u + 2]++; start[v + 2]++; }
}
for (let i = 2; i <= n + 1; i++) start[i] += start[i - 1];
const adj = new Int32Array(start[n + 1]);
for (let i = 0; i < m; i++) {
  const u = eu[i], v = ev[i], w = ew[i];
  if (u === v) continue;
  adj[start[u + 1]++] = v * 1024 + w;
  adj[start[v + 1]++] = u * 1024 + w;
}
const INF = 1e18;
const dist = new Float64Array(n);
const h = new Float64Array(adj.length + 2);
const mul = n; // key = dist * n + node, exact below 2^53
const lines = [];
for (let qi = 0; qi < q; qi++) {
  const s = readInt();
  dist.fill(INF);
  dist[s] = 0;
  h[0] = s;
  let hs = 1;
  while (hs > 0) {
    const top = h[0];
    const last = h[--hs];
    if (hs > 0) {
      let i = 0;
      for (;;) {
        let c = 2 * i + 1;
        if (c >= hs) break;
        if (c + 1 < hs && h[c + 1] < h[c]) c++;
        if (h[c] >= last) break;
        h[i] = h[c];
        i = c;
      }
      h[i] = last;
    }
    const u = top % mul;
    const d = (top - u) / mul;
    if (d !== dist[u]) continue;
    for (let e = start[u], ee = start[u + 1]; e < ee; e++) {
      const x = adj[e];
      const v = x >> 10;
      const nd = d + (x & 1023);
      if (nd < dist[v]) {
        dist[v] = nd;
        const key = nd * mul + v;
        let i = hs++;
        while (i > 0) {
          const par = (i - 1) >> 1;
          if (h[par] <= key) break;
          h[i] = h[par];
          i = par;
        }
        h[i] = key;
      }
    }
  }
  let total = 0, far = 0, cnt = 0;
  for (let i = 0; i < n; i++) {
    const d = dist[i];
    if (d !== INF) {
      cnt++;
      total += d;
      if (d > far) far = d;
    }
  }
  let node = 0;
  for (let i = 0; i < n; i++) if (dist[i] === far) { node = i; break; }
  lines.push(s + " " + cnt + " " + total + " " + far + " " + node);
}
process.stdout.write(lines.join("\n") + "\n");
