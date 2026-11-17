'use strict';
const fs = require('fs');

function main() {
  const buf = fs.readFileSync(process.argv[2]);
  let pos = 0;

  function nextInt() {
    let c = buf[pos];
    while (c < 48) c = buf[++pos];
    let x = 0;
    while (c >= 48) {
      x = x * 10 + (c - 48);
      c = buf[++pos];
    }
    return x;
  }

  const N = nextInt();
  const M = nextInt();
  const Q = nextInt();

  const eu = new Int32Array(M);
  const ev = new Int32Array(M);
  const ew = new Int32Array(M);
  const off = new Int32Array(N + 2);

  for (let i = 0; i < M; i++) {
    let c = buf[pos];
    while (c < 48) c = buf[++pos];
    let u = 0;
    while (c >= 48) {
      u = u * 10 + (c - 48);
      c = buf[++pos];
    }
    while (c < 48) c = buf[++pos];
    let v = 0;
    while (c >= 48) {
      v = v * 10 + (c - 48);
      c = buf[++pos];
    }
    while (c < 48) c = buf[++pos];
    let w = 0;
    while (c >= 48) {
      w = w * 10 + (c - 48);
      c = buf[++pos];
    }
    eu[i] = u;
    ev[i] = v;
    ew[i] = w;
    if (u !== v) {
      off[u + 1] += 2;
      off[v + 1] += 2;
    }
  }

  // prefix sums (offsets in units of Int32 slots; each arc uses 2 slots)
  for (let i = 0; i < N; i++) off[i + 1] += off[i];
  const totalSlots = N > 0 ? off[N] : 0;
  const adj = new Int32Array(totalSlots);
  const fillPos = new Int32Array(N + 1);
  for (let i = 0; i < N; i++) fillPos[i] = off[i];
  for (let i = 0; i < M; i++) {
    const u = eu[i];
    const v = ev[i];
    if (u !== v) {
      const w = ew[i];
      let p = fillPos[u];
      adj[p] = v;
      adj[p + 1] = w;
      fillPos[u] = p + 2;
      p = fillPos[v];
      adj[p] = u;
      adj[p + 1] = w;
      fillPos[v] = p + 2;
    }
  }

  const useFloat = (N - 1) * 1000 >= 0x7fffffff;
  const dist = useFloat ? new Float64Array(N) : new Int32Array(N);
  const INF = useFloat ? Infinity : 0x7fffffff;

  // entry pool: [node, next] pairs; at most one entry per arc plus the source
  const pool = new Int32Array(totalSlots + 2);
  const head = new Int32Array(1024);
  const bits = new Int32Array(32);

  const out = [];

  for (let qi = 0; qi < Q; qi++) {
    const s = nextInt();
    dist.fill(INF);
    head.fill(-1);
    bits.fill(0);

    dist[s] = 0;
    pool[0] = s;
    pool[1] = -1;
    head[0] = 0;
    bits[0] = 1;
    let cnt = 2; // next free slot index in pool
    let pending = 1;
    let cur = 0;

    let R = 0;
    let total = 0;
    let hi = 0;
    let far = -1;
    let node = s;

    while (pending > 0) {
      const c = cur & 1023;
      let w = c >>> 5;
      let m = bits[w] & (-1 << (c & 31));
      while (m === 0) {
        w = (w + 1) & 31;
        m = bits[w];
      }
      const bitIdx = 31 - Math.clz32(m & -m);
      const b = (w << 5) + bitIdx;
      cur += (b - c) & 1023;
      bits[w] &= ~(1 << bitIdx);
      let e = head[b];
      head[b] = -1;

      while (e >= 0) {
        const v = pool[e];
        e = pool[e + 1];
        pending--;
        if (dist[v] === cur) {
          R++;
          total += cur;
          if (total >= 1e15) {
            total -= 1e15;
            hi++;
          }
          if (cur > far) {
            far = cur;
            node = v;
          } else if (v < node) {
            node = v;
          }
          const end = off[v + 1];
          for (let i = off[v]; i < end; i += 2) {
            const u = adj[i];
            const nd = cur + adj[i + 1];
            if (nd < dist[u]) {
              dist[u] = nd;
              const nb = nd & 1023;
              pool[cnt] = u;
              pool[cnt + 1] = head[nb];
              head[nb] = cnt;
              cnt += 2;
              bits[nb >>> 5] |= 1 << (nb & 31);
              pending++;
            }
          }
        }
      }
    }

    let totalStr;
    if (hi === 0) {
      totalStr = String(total);
    } else {
      totalStr = (BigInt(hi) * 1000000000000000n + BigInt(total)).toString();
    }
    out.push(s + ' ' + R + ' ' + totalStr + ' ' + far + ' ' + node + '\n');
  }

  if (out.length > 0) process.stdout.write(out.join(''));
}

main();
