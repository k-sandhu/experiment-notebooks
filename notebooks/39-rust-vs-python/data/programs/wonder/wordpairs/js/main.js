"use strict";
const fs = require("fs");

function main() {
  const buf = fs.readFileSync(process.argv[2]);
  const n = buf.length;

  // lookup: lowercase value if letter else 0
  const lowTab = new Uint8Array(256);
  for (let c = 0; c < 256; c++) {
    if (c >= 65 && c <= 90) lowTab[c] = c + 32;
    else if (c >= 97 && c <= 122) lowTab[c] = c;
  }

  let wcap = 1 << 17;
  let wmask = wcap - 1;
  let wtab = new Int32Array(wcap).fill(-1);
  let whash = new Int32Array(wcap);
  let arena = new Uint8Array(1 << 19);
  let arenaSize = 0;
  let woff = new Int32Array(45000);
  let wlen = new Int32Array(45000);
  let vocab = 0;

  let pcap = 1 << 21;
  let pmask = pcap - 1;
  let pfirst = new Int32Array(pcap).fill(-1);
  let psecond = new Int32Array(pcap);
  let pcounts = new Int32Array(pcap);
  let psize = 0;

  function hashPair(a, b) {
    let h = a | 0;
    h = Math.imul(h ^ (h >>> 16), 0x45d9f3b);
    h = (h ^ (b | 0)) | 0;
    h = Math.imul(h ^ (h >>> 16), 0x45d9f3b);
    h ^= h >>> 16;
    return h >>> 0;
  }
  function pairGrow() {
    const ncap = pcap * 2, nmask = ncap - 1;
    const nf = new Int32Array(ncap).fill(-1);
    const ns = new Int32Array(ncap);
    const nc = new Int32Array(ncap);
    for (let i2 = 0; i2 < pcap; i2++) {
      const a = pfirst[i2];
      if (a === -1) continue;
      const b = psecond[i2];
      let idx = hashPair(a, b) & nmask;
      while (nf[idx] !== -1) idx = (idx + 1) & nmask;
      nf[idx] = a; ns[idx] = b; nc[idx] = pcounts[i2];
    }
    pfirst = nf; psecond = ns; pcounts = nc; pcap = ncap; pmask = nmask;
  }
  function wordGrow() {
    const ncap = wcap * 2, nmask = ncap - 1;
    const nt = new Int32Array(ncap).fill(-1);
    const nh = new Int32Array(ncap);
    for (let i2 = 0; i2 < wcap; i2++) {
      const id = wtab[i2];
      if (id < 0) continue;
      let idx = whash[i2] & nmask;
      while (nt[idx] !== -1) idx = (idx + 1) & nmask;
      nt[idx] = id; nh[idx] = whash[i2];
    }
    wtab = nt; whash = nh; wcap = ncap; wmask = nmask;
  }
  function wordCmp(a, b) {
    if (a === b) return 0;
    const oa = woff[a], ob = woff[b];
    const la = wlen[a], lb = wlen[b];
    const m = la < lb ? la : lb;
    for (let j = 0; j < m; j++) {
      const d = arena[oa + j] - arena[ob + j];
      if (d !== 0) return d;
    }
    return la - lb;
  }

  let W = 0, T = 0;
  let prev = -1;
  let i = 0;
  while (i < n) {
    const c0 = buf[i];
    if (lowTab[c0] !== 0) {
      const start = i;
      let h = 0x811c9dc5 | 0;
      while (i < n) {
        const lc = lowTab[buf[i]];
        if (lc === 0) break;
        h ^= lc;
        h = Math.imul(h, 0x01000193);
        i++;
      }
      const len = i - start;
      let id;
      let idx = h & wmask;
      while (true) {
        const cur = wtab[idx];
        if (cur < 0) {
          id = vocab++;
          if (vocab > woff.length) {
            const no = new Int32Array(woff.length * 2); no.set(woff); woff = no;
            const nl = new Int32Array(wlen.length * 2); nl.set(wlen); wlen = nl;
          }
          if (arenaSize + len > arena.length) {
            let ncap = arena.length;
            while (ncap < arenaSize + len) ncap *= 2;
            const na = new Uint8Array(ncap); na.set(arena); arena = na;
          }
          const off = arenaSize;
          for (let j = 0; j < len; j++) arena[arenaSize++] = lowTab[buf[start + j]];
          woff[id] = off; wlen[id] = len;
          wtab[idx] = id; whash[idx] = h;
          if (vocab * 2 > wcap) wordGrow();
          break;
        }
        if (whash[idx] === h && wlen[cur] === len) {
          const off = woff[cur];
          let eq = true;
          for (let j = 0; j < len; j++) {
            if (arena[off + j] !== lowTab[buf[start + j]]) { eq = false; break; }
          }
          if (eq) { id = cur; break; }
        }
        idx = (idx + 1) & wmask;
      }
      W++;
      if (prev >= 0) {
        T++;
        let pi = hashPair(prev, id) & pmask;
        while (true) {
          const a = pfirst[pi];
          if (a === -1) {
            pfirst[pi] = prev; psecond[pi] = id; pcounts[pi] = 1; psize++;
            if (psize * 10 > pcap * 7) pairGrow();
            break;
          }
          if (a === prev && psecond[pi] === id) { pcounts[pi]++; break; }
          pi = (pi + 1) & pmask;
        }
      }
      prev = id;
    } else {
      if (c0 === 46 || c0 === 33 || c0 === 63) prev = -1;
      i++;
    }
  }

  const tc = new Int32Array(20), ta = new Int32Array(20), tb = new Int32Array(20);
  let tsz = 0;
  function better(c1, a1, b1, c2, a2, b2) {
    if (c1 !== c2) return c1 > c2;
    const cmp = wordCmp(a1, a2);
    if (cmp !== 0) return cmp < 0;
    return wordCmp(b1, b2) < 0;
  }
  for (let k = 0; k < pcap; k++) {
    const a = pfirst[k];
    if (a === -1) continue;
    const cnt = pcounts[k];
    const b = psecond[k];
    if (tsz === 20) {
      if (!better(cnt, a, b, tc[19], ta[19], tb[19])) continue;
      let pos = 19;
      while (pos > 0 && better(cnt, a, b, tc[pos - 1], ta[pos - 1], tb[pos - 1])) {
        tc[pos] = tc[pos - 1]; ta[pos] = ta[pos - 1]; tb[pos] = tb[pos - 1]; pos--;
      }
      tc[pos] = cnt; ta[pos] = a; tb[pos] = b;
    } else {
      let pos = tsz++;
      while (pos > 0 && better(cnt, a, b, tc[pos - 1], ta[pos - 1], tb[pos - 1])) {
        tc[pos] = tc[pos - 1]; ta[pos] = ta[pos - 1]; tb[pos] = tb[pos - 1]; pos--;
      }
      tc[pos] = cnt; ta[pos] = a; tb[pos] = b;
    }
  }

  let out = "words " + W + "\n" + "pairs " + T + "\n" + "distinct " + psize + "\n";
  for (let k = 0; k < tsz; k++) {
    const oa = woff[ta[k]], la = wlen[ta[k]];
    const ob = woff[tb[k]], lb = wlen[tb[k]];
    out += tc[k] + " " + Buffer.from(arena.buffer, oa, la).toString("ascii") + " " + Buffer.from(arena.buffer, ob, lb).toString("ascii") + "\n";
  }
  process.stdout.write(out);
}
main();
