"use strict";
// Word pairs: count adjacent word pairs within sentences, report the top 20.
//
// 1. Scan the input bytes once. Words are hashed while scanned and interned to
//    dense ids by an open-addressing table in typed arrays. The scan records the
//    id sequence (negative id = word starts a sentence) and counts pairs per
//    first word.
// 2. Counting-sort the pairs by first word (second words only).
// 3. For each first word, count its second words in a dense counter array that
//    stays in cache, and keep the 20 best pairs. Ties are broken by each word's
//    lexicographic rank, so the selection compares integers only.

const fs = require("fs");

// 1 = letter, 2 = sentence end, 0 = other.
const CLASS = new Uint8Array(256);
for (let c = 97; c <= 122; c++) {
  CLASS[c] = 1;
  CLASS[c - 32] = 1;
}
CLASS[46] = CLASS[33] = CLASS[63] = 2;

function main() {
  const path = process.argv[2];
  if (!path) {
    process.stderr.write("usage: node main.js INPUT\n");
    process.exit(1);
  }
  const buf = fs.readFileSync(path);
  const n = buf.length;

  // Word table: slot i holds hash at 2i and id at 2i+1 (0 = empty).
  let bits = 16;
  let mask = (1 << bits) - 1;
  let slots = new Int32Array(2 << bits);
  let wOff = new Int32Array(1 << 16);
  let wLen = new Int32Array(1 << 16);
  let deg = new Int32Array(1 << 16); // pairs per first word
  let nextId = 1;

  function resize(b) {
    const old = slots;
    slots = new Int32Array(2 << b);
    bits = b;
    mask = (1 << b) - 1;
    for (let j = 0; j < old.length; j += 2) {
      if (old[j + 1] === 0) continue;
      let i = old[j] >>> (32 - b);
      while (slots[2 * i + 1] !== 0) i = (i + 1) & mask;
      slots[2 * i] = old[j];
      slots[2 * i + 1] = old[j + 1];
    }
  }

  function add(start, len, h, i) {
    const id = nextId++;
    for (let j = start; j < start + len; j++) buf[j] |= 0x20; // lower-case the stored copy
    if (id === wOff.length) {
      const o = new Int32Array(id * 2); o.set(wOff); wOff = o;
      const l = new Int32Array(id * 2); l.set(wLen); wLen = l;
      const d = new Int32Array(id * 2); d.set(deg); deg = d;
    }
    wOff[id] = start;
    wLen[id] = len;
    slots[2 * i] = h;
    slots[2 * i + 1] = id;
    if (id * 2 > mask + 1) resize(bits + 1);
    return id;
  }

  const seq = new Int32Array((n >>> 1) + 2); // at most one word per two bytes, plus one
  let nseq = 0;
  let totalPairs = 0;
  let prev = 0; // previous word id in the current sentence, 0 = none
  let i = 0;
  while (i < n) {
    let c = buf[i];
    const k = CLASS[c];
    if (k !== 1) {
      if (k === 2) prev = 0;
      i++;
      continue;
    }
    const start = i;
    let h = 0x811c9dc5;
    do {
      h = Math.imul(h ^ (c | 0x20), 0x01000193);
      i++;
    } while (i < n && CLASS[(c = buf[i])] === 1);
    const len = i - start;
    h ^= h >>> 15;
    h = Math.imul(h + len, 0x2c1b3c6d);
    h ^= h >>> 12;
    h = Math.imul(h, 0x297a2d39);
    h ^= h >>> 15;

    let s = h >>> (32 - bits);
    let id = 0;
    for (;;) {
      const sid = slots[2 * s + 1];
      if (sid === 0) break;
      if (slots[2 * s] === h && wLen[sid] === len) {
        const o = wOff[sid];
        let j = 0;
        while (j < len && buf[o + j] === (buf[start + j] | 0x20)) j++;
        if (j === len) {
          id = sid;
          break;
        }
      }
      s = (s + 1) & mask;
    }
    if (id === 0) id = add(start, len, h, s);

    if (prev !== 0) {
      deg[prev]++;
      totalPairs++;
      seq[nseq++] = id;
    } else {
      seq[nseq++] = -id;
    }
    prev = id;
  }
  const nw = nextId - 1;

  // Bucket the second word of every pair by its first word.
  const pos = new Int32Array(nw + 2);
  for (let id = 1; id <= nw; id++) pos[id + 1] = pos[id] + deg[id];
  const fill = pos.slice();
  const second = new Int32Array(totalPairs + 1);
  for (let j = 1; j < nseq; j++) {
    const x = seq[j];
    if (x > 0) {
      const p = seq[j - 1];
      second[fill[p < 0 ? -p : p]++] = x;
    }
  }

  // Lexicographic rank of each word id.
  const strs = new Array(nw + 1);
  strs[0] = "";
  for (let id = 1; id <= nw; id++) strs[id] = buf.latin1Slice(wOff[id], wOff[id] + wLen[id]);
  const order = new Int32Array(nw);
  for (let id = 0; id < nw; id++) order[id] = id + 1;
  order.sort((a, b) => (strs[a] < strs[b] ? -1 : strs[a] > strs[b] ? 1 : 0));
  const rank = new Int32Array(nw + 1);
  for (let r = 0; r < nw; r++) rank[order[r]] = r;

  // Count second words per first word; keep the 20 best pairs.
  const K = 20;
  const tc = new Int32Array(K), tr1 = new Int32Array(K), tr2 = new Int32Array(K);
  const ta = new Int32Array(K), tb = new Int32Array(K);
  let nt = 0;
  let distinct = 0;
  const cnt = new Int32Array(nw + 1);
  for (let a = 1; a <= nw; a++) {
    const lo = pos[a], hi = pos[a + 1];
    if (lo === hi) continue;
    for (let j = lo; j < hi; j++) cnt[second[j]]++;
    const ra = rank[a];
    for (let j = lo; j < hi; j++) {
      const b = second[j];
      const c = cnt[b];
      if (c === 0) continue;
      cnt[b] = 0;
      distinct++;
      if (nt === K && c < tc[K - 1]) continue;
      const rb = rank[b];
      if (nt === K && !(c > tc[K - 1] || (c === tc[K - 1] && (ra < tr1[K - 1] || (ra === tr1[K - 1] && rb < tr2[K - 1]))))) continue;
      let p = nt < K ? nt++ : K - 1;
      while (p > 0 && (c > tc[p - 1] || (c === tc[p - 1] && (ra < tr1[p - 1] || (ra === tr1[p - 1] && rb < tr2[p - 1]))))) {
        tc[p] = tc[p - 1];
        tr1[p] = tr1[p - 1];
        tr2[p] = tr2[p - 1];
        ta[p] = ta[p - 1];
        tb[p] = tb[p - 1];
        p--;
      }
      tc[p] = c;
      tr1[p] = ra;
      tr2[p] = rb;
      ta[p] = a;
      tb[p] = b;
    }
  }

  let out = `words ${nseq}\npairs ${totalPairs}\ndistinct ${distinct}\n`;
  for (let t = 0; t < nt; t++) out += `${tc[t]} ${strs[ta[t]]} ${strs[tb[t]]}\n`;
  process.stdout.write(out);
}

main();
