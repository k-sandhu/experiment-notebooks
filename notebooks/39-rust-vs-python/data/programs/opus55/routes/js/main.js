"use strict";

// Routes: Dijkstra from each source with a monotone radix heap on a CSR graph.
const fs = require("fs");

const buf = fs.readFileSync(process.argv[2]);
let pos = 0;

function next() {
  let c = buf[pos];
  while (c < 48 || c > 57) c = buf[++pos];
  let x = c - 48;
  c = buf[++pos];
  while (c >= 48 && c <= 57) {
    x = x * 10 + (c - 48);
    c = buf[++pos];
  }
  return x;
}

const n = next();
const m = next();
const q = next();

const eu = new Int32Array(m);
const ev = new Int32Array(m);
const ew = new Int32Array(m);
const start = new Int32Array(n + 1);
let weightSum = 0;
for (let i = 0; i < m; i++) {
  const u = next();
  const v = next();
  const w = next();
  eu[i] = u;
  ev[i] = v;
  ew[i] = w;
  weightSum += w;
  if (u !== v) {
    // self-loops never shorten a path
    start[u + 1]++;
    start[v + 1]++;
  }
}
for (let i = 0; i < n; i++) start[i + 1] += start[i];
// Neighbours of u: adj[2k] (node), adj[2k+1] (length) for k in start[u]..start[u+1).
const adj = new Int32Array(2 * start[n]);
const fill = start.slice(0, n);
for (let i = 0; i < m; i++) {
  const u = eu[i];
  const v = ev[i];
  const w = ew[i];
  if (u === v) continue;
  const pu = fill[u]++ << 1;
  adj[pu] = v;
  adj[pu + 1] = w;
  const pv = fill[v]++ << 1;
  adj[pv] = u;
  adj[pv + 1] = w;
}

// Radix heap: entries (dist, node) live in bucket 0 if dist equals the last popped minimum, otherwise in
// the bucket given by the highest bit where dist differs from it. When every distance fits in 31 bits
// (no shortest path is longer than the sum of all road lengths), distances are kept as small integers;
// otherwise as doubles, which are exact below 2^53.
const small = Math.min(weightSum, 1000 * Math.max(n - 1, 0)) < 0x7fffffff;
const DistArray = small ? Int32Array : Float64Array;
const INF = small ? 0x7fffffff : Infinity;
const NB = 66;
const bDist = [];
const bNode = [];
const bSize = new Int32Array(NB);
for (let i = 0; i < NB; i++) {
  bDist.push(new DistArray(1024));
  bNode.push(new Int32Array(1024));
}
const TWO32 = 4294967296;

function bucketOfSmall(d, last) {
  return 32 - Math.clz32(d ^ last);
}

function bucketOfBig(d, last) {
  if (d === last) return 0;
  const hi = (d / TWO32) ^ (last / TWO32);
  return hi !== 0 ? 64 - Math.clz32(hi) : 32 - Math.clz32(d ^ last);
}

const bucketOf = small ? bucketOfSmall : bucketOfBig;

function bpush(b, d, v) {
  const s = bSize[b];
  let da = bDist[b];
  if (s === da.length) {
    const nd = new DistArray(s * 2);
    nd.set(da);
    bDist[b] = da = nd;
    const nn = new Int32Array(s * 2);
    nn.set(bNode[b]);
    bNode[b] = nn;
  }
  da[s] = d;
  bNode[b][s] = v;
  bSize[b] = s + 1;
}

const dist = new DistArray(n);

function solve(s) {
  dist.fill(INF);
  bSize.fill(0);
  let last = 0;
  let heapSize = 1;
  dist[s] = 0;
  bpush(0, 0, s);
  let reach = 0;
  let total = 0n;
  let far = 0;
  let farNode = s;
  let sum = 0; // partial sum kept below 2^53, flushed into the BigInt total
  while (heapSize > 0) {
    if (bSize[0] === 0) {
      let i = 1;
      while (bSize[i] === 0) i++;
      const da = bDist[i];
      const na = bNode[i];
      const cnt = bSize[i];
      let mn = INF;
      for (let j = 0; j < cnt; j++) if (da[j] < mn) mn = da[j];
      last = mn;
      bSize[i] = 0;
      for (let j = 0; j < cnt; j++) {
        const d = da[j];
        bpush(bucketOf(d, last), d, na[j]);
      }
    }
    heapSize--;
    const top = --bSize[0];
    const d = bDist[0][top];
    const u = bNode[0][top];
    if (d !== dist[u]) continue;
    reach++;
    sum += d;
    if (sum > 4e15) {
      total += BigInt(sum);
      sum = 0;
    }
    if (d > far) {
      far = d;
      farNode = u;
    } else if (d === far && u < farNode) {
      farNode = u;
    }
    for (let k = start[u] << 1, end = start[u + 1] << 1; k < end; k += 2) {
      const v = adj[k];
      const nd = d + adj[k + 1];
      if (nd < dist[v]) {
        dist[v] = nd;
        bpush(bucketOf(nd, last), nd, v);
        heapSize++;
      }
    }
  }
  total += BigInt(sum);
  return s + " " + reach + " " + total + " " + far + " " + farNode + "\n";
}

let out = "";
for (let i = 0; i < q; i++) out += solve(next());
fs.writeSync(1, out);
