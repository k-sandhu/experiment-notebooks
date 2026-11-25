"use strict";
const fs = require("fs");
const buf = fs.readFileSync(process.argv[2]);
let pos = 0;
const blen = buf.length;
function parseInt() {
  while (pos < blen && (buf[pos] < 48 || buf[pos] > 57)) pos++;
  let v = 0;
  while (pos < blen && buf[pos] >= 48 && buf[pos] <= 57) { v = v * 10 + (buf[pos] - 48); pos++; }
  return v;
}
if (blen === 0) process.exit(0);
const N = parseInt(), M = parseInt(), Q = parseInt();
const eu = new Int32Array(M), ev = new Int32Array(M), ew = new Int32Array(M);
const deg = new Int32Array(N);
let ecnt = 0;
for (let i = 0; i < M; i++) {
  const u = parseInt(), v = parseInt(), w = parseInt();
  if (u === v) continue;
  eu[ecnt] = u; ev[ecnt] = v; ew[ecnt] = w; ecnt++;
  deg[u]++; deg[v]++;
}
const sources = new Int32Array(Q);
for (let i = 0; i < Q; i++) sources[i] = parseInt();

const off = new Int32Array(N + 1);
for (let i = 0; i < N; i++) off[i + 1] = off[i] + deg[i];
const adj = new Int32Array(off[N]);
const curArr = new Int32Array(N);
curArr.set(off.subarray(0, N));
for (let i = 0; i < ecnt; i++) {
  const u = eu[i], v = ev[i], w = ew[i];
  adj[curArr[u]++] = (v << 10) | w;
  adj[curArr[v]++] = (u << 10) | w;
}

const INF = 0x3f3f3f3f;
const dist = new Int32Array(N);
const nxt = new Int32Array(N), prv = new Int32Array(N);
const done = new Uint8Array(N);
const head = new Int32Array(1024);
const words = new Uint32Array(32); // 1024 bits

function ctz32(x) { return 31 - Math.clz32(x & -x); }

let out = "";
const cache = [];
for (let qi = 0; qi < Q; qi++) {
  const s = sources[qi];
  let R, tot, far, farNode;
  let hit = null;
  for (const c of cache) if (c.s === s) { hit = c; break; }
  if (hit) { R = hit.R; tot = hit.tot; far = hit.far; farNode = hit.node; }
  else {
    dist.fill(INF); done.fill(0); head.fill(-1); words.fill(0);
    dist[s] = 0; head[0] = s; nxt[s] = -1; prv[s] = -1; words[0] = 1;
    let inq = 1;
    let curDist = 0, curB = 0;
    R = 0; tot = 0; far = 0; farNode = s;
    while (inq > 0) {
      let node = head[curB];
      head[curB] = -1;
      words[curB >> 5] &= ~(1 << (curB & 31));
      while (node !== -1) {
        const nn = nxt[node];
        done[node] = 1; inq--;
        R++; tot += curDist;
        if (curDist > far) { far = curDist; farNode = node; }
        else if (curDist === far && node < farNode) farNode = node;
        const a0 = off[node], a1 = off[node + 1];
        for (let ai = a0; ai < a1; ai++) {
          const pk = adj[ai];
          const v = pk >> 10;
          if (done[v]) continue;
          const nd = curDist + (pk & 1023);
          if (nd < dist[v]) {
            if (dist[v] !== INF) {
              const ob = dist[v] & 1023;
              const pv = prv[v], nv = nxt[v];
              if (pv !== -1) nxt[pv] = nv; else head[ob] = nv;
              if (nv !== -1) prv[nv] = pv;
              if (head[ob] === -1) words[ob >> 5] &= ~(1 << (ob & 31));
            } else inq++;
            dist[v] = nd;
            const nb = nd & 1023;
            const oh = head[nb];
            nxt[v] = oh; prv[v] = -1;
            if (oh !== -1) prv[oh] = v;
            else words[nb >> 5] |= (1 << (nb & 31));
            head[nb] = v;
          }
        }
        node = nn;
      }
      if (inq === 0) break;
      // find next bucket: words are 32x32 bits
      const wi = curB >> 5, bi = curB & 31;
      let nb = -1;
      let w0 = (bi === 31) ? 0 : (words[wi] & (~0 << (bi + 1)));
      if (w0 !== 0) nb = (wi << 5) + ctz32(w0);
      else {
        for (let k = 1; k < 32; k++) {
          const idx = (wi + k) & 31;
          const w = words[idx];
          if (w !== 0) { nb = (idx << 5) + ctz32(w); break; }
        }
        if (nb === -1) {
          const low = (bi === 31) ? -1 : ((1 << (bi + 1)) - 1);
          const w = words[wi] & low;
          if (w !== 0) nb = (wi << 5) + ctz32(w);
        }
      }
      let offd = nb - curB; if (offd <= 0) offd += 1024;
      curDist += offd; curB = nb;
    }
    if (cache.length < 64) cache.push({ s, R, tot, far, node: farNode });
  }
  out += s + " " + R + " " + tot + " " + far + " " + farNode + "\n";
}
process.stdout.write(out);
