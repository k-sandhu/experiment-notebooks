"use strict";
const fs = require("fs");

function main() {
  const path = process.argv[2];
  if (!path) return;
  const d = fs.readFileSync(path);
  const n = d.length;
  let p = 0;
  function nextInt() {
    while (p < n && d[p] <= 32) p++;
    if (p >= n) return 0;
    let neg = false;
    if (d[p] === 45) { neg = true; p++; }
    let v = 0;
    while (p < n && d[p] >= 48 && d[p] <= 57) {
      v = v * 10 + (d[p] - 48);
      p++;
    }
    return neg ? -v : v;
  }

  let N = nextInt();
  let M = nextInt();
  let Q = nextInt();
  if (N < 0) N = 0;
  if (M < 0) M = 0;
  if (Q < 0) Q = 0;

  const eu = new Int32Array(M);
  const ev = new Int32Array(M);
  const ew = new Int32Array(M);
  const deg = new Int32Array(N);
  let mStored = 0;
  let wmax = 0;
  for (let i = 0; i < M; i++) {
    const u = nextInt(), v = nextInt(), w = nextInt();
    if (u === v) continue;
    if (u < 0 || u >= N || v < 0 || v >= N) continue;
    eu[mStored] = u; ev[mStored] = v; ew[mStored] = w;
    mStored++;
    deg[u]++; deg[v]++;
    if (w > wmax) wmax = w;
  }
  const sources = new Int32Array(Q);
  for (let i = 0; i < Q; i++) sources[i] = nextInt();

  const off = new Int32Array(N + 1);
  for (let i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
  const E = off[N];
  const adjTo = new Int32Array(E);
  const adjW = new Int32Array(E);
  const cursor = new Int32Array(N);
  cursor.set(off.subarray(0, N));
  for (let i = 0; i < mStored; i++) {
    const u = eu[i], v = ev[i], w = ew[i];
    let a = cursor[u]++; adjTo[a] = v; adjW[a] = w;
    let b = cursor[v]++; adjTo[b] = u; adjW[b] = w;
  }

  const B = wmax > 0 ? wmax + 1 : 1;
  const WORDS = (B + 31) >> 5;
  const dist = new Float64Array(N);
  const head = new Int32Array(B);
  const bits = new Uint32Array(WORDS);
  let cap = Math.max(1024, N * 2);
  let eNode = new Int32Array(cap);
  let eNext = new Int32Array(cap);

  function tz32(x) {
    // x !== 0, 32-bit
    return 31 - Math.clz32(x & -x);
  }

  const doneSrc = [];
  const doneLine = [];
  let out = "";

  for (let qi = 0; qi < Q; qi++) {
    const s = sources[qi];
    let dup = false;
    for (let k = 0; k < doneSrc.length; k++) {
      if (doneSrc[k] === s) { out += doneLine[k]; dup = true; break; }
    }
    if (dup) continue;

    let R = 0, total = 0, far = 0, farNode = s;

    if (s >= 0 && s < N) {
      dist.fill(Infinity);
      head.fill(-1);
      bits.fill(0);
      let poolSize = 0;
      let nonEmpty = 0;
      dist[s] = 0;
      {
        if (poolSize === eNode.length) {
          const nn = new Int32Array(eNode.length * 2); nn.set(eNode); eNode = nn;
          const nx = new Int32Array(eNext.length * 2); nx.set(eNext); eNext = nx;
        }
        const idx = poolSize++;
        eNode[idx] = s;
        eNext[idx] = head[0];
        if (head[0] === -1) { bits[0] |= 1; nonEmpty++; }
        head[0] = idx;
      }
      let curBucket = 0;
      let curDist = 0;
      while (true) {
        if (head[curBucket] === -1) {
          if (nonEmpty === 0) break;
          const wi = curBucket >> 5;
          const bi = curBucket & 31;
          let posB = -1;
          let w = 0;
          if (bi < 31) w = bits[wi] & (~0 << (bi + 1));
          if (w !== 0) {
            posB = (wi << 5) + tz32(w);
          } else {
            for (let step = 1; step <= WORDS; step++) {
              let idxw = wi + step;
              if (idxw >= WORDS) idxw -= WORDS;
              const ww = bits[idxw];
              if (ww !== 0) { posB = (idxw << 5) + tz32(ww); break; }
            }
          }
          if (posB < 0) break;
          const delta = posB > curBucket ? (posB - curBucket) : (posB - curBucket + B);
          curDist += delta;
          curBucket = posB;
        }
        const eidx = head[curBucket];
        const u = eNode[eidx];
        const nxt = eNext[eidx];
        head[curBucket] = nxt;
        if (nxt === -1) {
          bits[curBucket >> 5] &= ~(1 << (curBucket & 31));
          nonEmpty--;
        }
        if (dist[u] !== curDist) continue;
        R++;
        total += curDist;
        if (curDist > far) { far = curDist; farNode = u; }
        else if (curDist === far && u < farNode) farNode = u;

        const begin = off[u];
        const end = off[u + 1];
        for (let ei = begin; ei < end; ei++) {
          const to = adjTo[ei];
          const wgt = adjW[ei];
          const nd = curDist + wgt;
          if (nd < dist[to]) {
            dist[to] = nd;
            let b = curBucket + wgt;
            if (b >= B) b -= B;
            if (poolSize === eNode.length) {
              const nn = new Int32Array(eNode.length * 2); nn.set(eNode); eNode = nn;
              const nx = new Int32Array(eNext.length * 2); nx.set(eNext); eNext = nx;
            }
            const idx = poolSize++;
            eNode[idx] = to;
            const h = head[b];
            eNext[idx] = h;
            if (h === -1) { bits[b >> 5] |= (1 << (b & 31)); nonEmpty++; }
            head[b] = idx;
          }
        }
      }
    }
    const line = s + " " + R + " " + total + " " + far + " " + farNode + "\n";
    out += line;
    doneSrc.push(s);
    doneLine.push(line);
  }
  process.stdout.write(out);
}
main();
