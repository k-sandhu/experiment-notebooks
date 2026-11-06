"use strict";

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
let ppos = 0;

function next() {
  const n = data.length;
  let i = ppos;
  while (i < n && (data[i] < 48 || data[i] > 57)) i++;
  let v = 0;
  while (i < n && data[i] >= 48 && data[i] <= 57) {
    v = v * 10 + (data[i] - 48);
    i++;
  }
  ppos = i;
  return v;
}

const N = next(), M = next(), Q = next();

const eu = new Int32Array(M), ev = new Int32Array(M), ew = new Int32Array(M);
for (let i = 0; i < M; i++) {
  eu[i] = next(); ev[i] = next(); ew[i] = next();
}
const src = new Int32Array(Q);
for (let i = 0; i < Q; i++) src[i] = next();

// CSR adjacency (skip self-loops)
const off = new Int32Array(N + 1);
for (let i = 0; i < M; i++) {
  if (eu[i] !== ev[i]) { off[eu[i]]++; off[ev[i]]++; }
}
let run = 0;
for (let v = 0; v < N; v++) { const d = off[v]; off[v] = run; run += d; }
off[N] = run;
const adj = new Int32Array(run), wt = new Int32Array(run);
const pos = new Int32Array(N);
pos.set(off.subarray(0, N));
for (let i = 0; i < M; i++) {
  const u = eu[i], v = ev[i], w = ew[i];
  if (u === v) continue;
  adj[pos[u]] = v; wt[pos[u]] = w; pos[u]++;
  adj[pos[v]] = u; wt[pos[v]] = w; pos[v]++;
}

const INF = Infinity;
const dist = new Float64Array(N);
const hcap = 2 * M + 16;
const hd = new Float64Array(hcap);
const hn = new Int32Array(hcap);

const outChunks = [];

for (let qi = 0; qi < Q; qi++) {
  const s = src[qi];
  dist.fill(INF);
  let hsize = 0;
  dist[s] = 0;
  hd[0] = 0; hn[0] = s; hsize = 1;
  let total = 0, far = -1, cnt = 0, farNode = s;

  while (hsize > 0) {
    const d = hd[0];
    const v = hn[0];
    hsize--;
    hd[0] = hd[hsize]; hn[0] = hn[hsize];
    // sift down (hole method, 4-ary); reinsert moved last element
    const d0 = hd[hsize], v0 = hn[hsize];
    let i = 0;
    while (hsize > 0) {
      const c = 4 * i + 1;
      let m = i, mv = d0;
      let e = c + 4;
      if (e > hsize) e = hsize;
      for (let j = c; j < e; j++) {
        if (hd[j] < mv) { mv = hd[j]; m = j; }
      }
      if (m === i) break;
      hd[i] = mv; hn[i] = hn[m];
      i = m;
    }
    if (hsize > 0) { hd[i] = d0; hn[i] = v0; }
    if (d !== dist[v]) continue;
    cnt++;
    total += d;
    if (d > far || (d === far && v < farNode)) { far = d; farNode = v; }
    const e1 = off[v + 1];
    for (let e = off[v]; e < e1; e++) {
      const to = adj[e];
      const nd = d + wt[e];
      if (nd < dist[to]) {
        dist[to] = nd;
        // push
        let j = hsize;
        hd[j] = nd; hn[j] = to; hsize++;
        while (j > 0) {
          const par = (j - 1) >> 2;
          if (hd[par] <= nd) break;
          hd[j] = hd[par]; hn[j] = hn[par];
          j = par;
        }
        hd[j] = nd; hn[j] = to;
      }
    }
  }

  outChunks.push(`${s} ${cnt} ${total} ${far} ${farNode}\n`);
}

process.stdout.write(outChunks.join(""));
