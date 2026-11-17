"use strict";

// Shortest paths from each source with Dial's bucket queue. Edge weights are 1..1000, so a ring of
// 1024 buckets replaces a heap: the bucket of distance d is d & 1023.
const fs = require("fs");

const BUCKETS = 1024; // greater than the largest weight (1000)
const NIL = -1;

const data = fs.readFileSync(process.argv[2]);
const len = data.length;
let pos = 0;

function nextInt() {
  let p = pos;
  while (p < len && (data[p] < 48 || data[p] > 57)) p++;
  let x = 0;
  while (p < len) {
    const c = data[p];
    if (c < 48 || c > 57) break;
    x = x * 10 + (c - 48);
    p++;
  }
  pos = p;
  return x;
}

const n = nextInt();
const m = nextInt();
const q = nextInt();

// Two passes over the edge lines: the first counts degrees, the second fills the adjacency arrays.
const edgesAt = pos;
const start = new Int32Array(n + 1);
for (let i = 0; i < m; i++) {
  start[nextInt() + 1]++;
  start[nextInt() + 1]++;
  nextInt();
}
for (let v = 0; v < n; v++) start[v + 1] += start[v];

const arcTo = new Int32Array(2 * m);
const arcW = new Int32Array(2 * m);
const fill = start.slice(0, n);
pos = edgesAt;
for (let i = 0; i < m; i++) {
  const u = nextInt();
  const v = nextInt();
  const w = nextInt();
  let a = fill[u]++;
  arcTo[a] = v;
  arcW[a] = w;
  a = fill[v]++;
  arcTo[a] = u;
  arcW[a] = w;
}

const dist = new Float64Array(n);
const head = new Int32Array(BUCKETS);
const entNode = new Int32Array(2 * m + 1);
const entNext = new Int32Array(2 * m + 1);
const lines = [];
for (let k = 0; k < q; k++) {
  const s = nextInt();
  dist.fill(Infinity);
  head.fill(NIL);

  let used = 0;
  let pending = 0;
  dist[s] = 0;
  entNode[used] = s;
  entNext[used] = NIL;
  head[0] = used++;
  pending++;

  let reached = 0;
  let total = 0;
  let far = 0;
  let node = s;
  for (let cur = 0; pending > 0; cur++) {
    const b = cur & (BUCKETS - 1);
    let e = head[b];
    head[b] = NIL;
    while (e !== NIL) {
      const v = entNode[e];
      e = entNext[e];
      pending--;
      if (dist[v] !== cur) continue;

      reached++;
      total += cur;
      if (cur > far || (cur === far && v < node)) {
        far = cur;
        node = v;
      }
      const end = start[v + 1];
      for (let i = start[v]; i < end; i++) {
        const to = arcTo[i];
        const nd = cur + arcW[i];
        if (nd < dist[to]) {
          dist[to] = nd;
          const nb = nd & (BUCKETS - 1);
          entNode[used] = to;
          entNext[used] = head[nb];
          head[nb] = used++;
          pending++;
        }
      }
    }
  }
  lines.push(`${s} ${reached} ${total} ${far} ${node}\n`);
}
process.stdout.write(lines.join(""));
