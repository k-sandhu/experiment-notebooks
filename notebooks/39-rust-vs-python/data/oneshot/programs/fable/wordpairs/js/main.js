'use strict';
const fs = require('fs');

function eqWord(data, start, pool, off, len) {
  for (let k = 0; k < len; k++) {
    if (pool[off + k] !== (data[start + k] | 32)) return false;
  }
  return true;
}

function cmpW(a, b, pool, meta) {
  if (a === b) return 0;
  const oa = meta[2 * a], la = meta[2 * a + 1];
  const ob = meta[2 * b], lb = meta[2 * b + 1];
  const m = la < lb ? la : lb;
  for (let k = 0; k < m; k++) {
    const d = pool[oa + k] - pool[ob + k];
    if (d !== 0) return d;
  }
  return la - lb;
}

function cmpPair(a, b, a2, b2, pool, meta) {
  const d = cmpW(a, a2, pool, meta);
  if (d !== 0) return d;
  return cmpW(b, b2, pool, meta);
}

function wordStr(pool, meta, id) {
  const off = meta[2 * id], len = meta[2 * id + 1];
  let s = '';
  for (let k = 0; k < len; k++) s += String.fromCharCode(pool[off + k]);
  return s;
}

function main() {
  const path = process.argv[2];
  const fd = fs.openSync(path, 'r');
  const size = fs.fstatSync(fd).size;
  const buf = Buffer.allocUnsafeSlow(size + 1);
  let n = 0;
  while (n < size) {
    const r = fs.readSync(fd, buf, n, size - n, null);
    if (r <= 0) break;
    n += r;
  }
  fs.closeSync(fd);
  buf[n] = 10; // sentinel (non-letter)
  const data = new Uint8Array(buf.buffer, buf.byteOffset, n + 1);

  // Sequence of word ids; sign bit set => word starts a new sentence.
  const seqCap = (n >> 1) + 2;
  let seq;
  {
    const sb = Buffer.allocUnsafeSlow(seqCap * 4);
    if ((sb.byteOffset & 3) === 0) {
      seq = new Int32Array(sb.buffer, sb.byteOffset, seqCap);
    } else {
      seq = new Int32Array(seqCap);
    }
  }

  const MIN = -2147483648;
  const MULT = -1640531535; // 0x9E3779B1 as int32

  let tabBits = 17;
  let tabShift = 32 - tabBits;
  let tabCap = 1 << tabBits;
  let tab = new Int32Array(tabCap * 2); // [hash, id+1]
  let tabMask2 = tabCap * 2 - 1;

  let metaCap = 1 << 16;
  let meta = new Int32Array(metaCap * 2); // [off, len]
  let pool = new Uint8Array(1 << 20);
  let poolLen = 0;

  let V = 0, W = 0;
  let flag = MIN;
  let i = 0;

  while (i < n) {
    const c = data[i];
    let l = (c | 32) - 97;
    if ((l >>> 0) < 26) {
      const start = i;
      let h = l + 1;
      i++;
      for (;;) {
        l = (data[i] | 32) - 97;
        if ((l >>> 0) >= 26) break;
        h = ((h << 5) | (h >>> 27)) ^ (l + 1);
        i++;
      }
      const len = i - start;
      let s = (Math.imul(h, MULT) >>> tabShift) << 1;
      let id = 0;
      for (;;) {
        const e = tab[s + 1];
        if (e === 0) {
          // insert new word
          if (V === metaCap) {
            metaCap *= 2;
            const nm = new Int32Array(metaCap * 2);
            nm.set(meta);
            meta = nm;
          }
          if (poolLen + len > pool.length) {
            let ns = pool.length * 2;
            if (ns < poolLen + len) ns = poolLen + len;
            const np = new Uint8Array(ns);
            np.set(pool);
            pool = np;
          }
          meta[2 * V] = poolLen;
          meta[2 * V + 1] = len;
          for (let k = 0; k < len; k++) pool[poolLen + k] = data[start + k] | 32;
          poolLen += len;
          tab[s] = h;
          tab[s + 1] = V + 1;
          id = V++;
          if (V * 2 > tabCap) {
            tabBits++;
            tabShift = 32 - tabBits;
            tabCap = tabCap * 2;
            const nt = new Int32Array(tabCap * 2);
            const m = tabCap * 2 - 1;
            const oldLen = tab.length;
            for (let j = 0; j < oldLen; j += 2) {
              const e2 = tab[j + 1];
              if (e2 !== 0) {
                const hh = tab[j];
                let q = (Math.imul(hh, MULT) >>> tabShift) << 1;
                while (nt[q + 1] !== 0) q = (q + 2) & m;
                nt[q] = hh;
                nt[q + 1] = e2;
              }
            }
            tab = nt;
            tabMask2 = m;
          }
          break;
        }
        if (tab[s] === h) {
          id = e - 1;
          if (meta[2 * id + 1] === len &&
              (len <= 6 || eqWord(data, start, pool, meta[2 * id], len))) break;
        }
        s = (s + 2) & tabMask2;
      }
      seq[W++] = id | flag;
      flag = 0;
    } else {
      if (c === 46 || c === 33 || c === 63) flag = MIN;
      i++;
    }
  }

  // Pass 2: count pairs per first word
  const pos = new Int32Array(V + 1);
  let T = 0;
  let prev = 0;
  for (let k = 0; k < W; k++) {
    const v = seq[k];
    if (v >= 0) {
      pos[prev]++;
      T++;
      prev = v;
    } else {
      prev = v & 0x7fffffff;
    }
  }

  const bstart = new Int32Array(V + 1);
  {
    let acc = 0;
    for (let a = 0; a < V; a++) {
      const cnt = pos[a];
      bstart[a] = acc;
      pos[a] = acc;
      acc += cnt;
    }
    bstart[V] = acc;
  }

  // Pass 3: scatter second words into buckets by first word
  const second = new Int32Array(T);
  prev = 0;
  for (let k = 0; k < W; k++) {
    const v = seq[k];
    if (v >= 0) {
      second[pos[prev]++] = v;
      prev = v;
    } else {
      prev = v & 0x7fffffff;
    }
  }

  // Pass 4: count within each bucket
  const cnt = new Int32Array(V > 0 ? V : 1);
  const touched = new Int32Array(V > 0 ? V : 1);
  const topC = new Int32Array(20);
  const topA = new Int32Array(20);
  const topB = new Int32Array(20);
  let topN = 0;
  let thr = 0;
  let D = 0;

  for (let a = 0; a < V; a++) {
    const s = bstart[a], e = bstart[a + 1];
    if (s === e) continue;
    let nt = 0;
    for (let j = s; j < e; j++) {
      const b = second[j];
      const c0 = cnt[b];
      cnt[b] = c0 + 1;
      if (c0 === 0) touched[nt++] = b;
    }
    D += nt;
    for (let t = 0; t < nt; t++) {
      const b = touched[t];
      const c = cnt[b];
      cnt[b] = 0;
      if (c >= thr) {
        if (topN < 20 || c > thr ||
            cmpPair(a, b, topA[19], topB[19], pool, meta) < 0) {
          let p = topN < 20 ? topN : 19;
          while (p > 0) {
            const pc = topC[p - 1];
            if (pc > c) break;
            if (pc === c && cmpPair(a, b, topA[p - 1], topB[p - 1], pool, meta) > 0) break;
            topC[p] = pc;
            topA[p] = topA[p - 1];
            topB[p] = topB[p - 1];
            p--;
          }
          topC[p] = c;
          topA[p] = a;
          topB[p] = b;
          if (topN < 20) topN++;
          if (topN === 20) thr = topC[19];
        }
      }
    }
  }

  let out = 'words ' + W + '\npairs ' + T + '\ndistinct ' + D + '\n';
  for (let k = 0; k < topN; k++) {
    out += topC[k] + ' ' + wordStr(pool, meta, topA[k]) + ' ' + wordStr(pool, meta, topB[k]) + '\n';
  }
  process.stdout.write(out);
}

main();
