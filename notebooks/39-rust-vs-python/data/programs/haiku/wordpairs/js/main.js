"use strict";

// Counts adjacent word pairs within sentences and prints the 20 most frequent ones (see SPEC.md).
//
// One pass over the whole input Buffer: letters form words, which are looked up in an open-addressing
// vocabulary table; each pair of neighbouring words is counted in an open-addressing table held in
// one Int32Array (three ints per slot), which avoids a Map keyed by numbers or strings.

const fs = require("fs");

// Byte classes.
const SEPARATOR = 0;
const LETTER = 1;
const SENTENCE_END = 2;
const CLASS = new Uint8Array(256);
for (let c = 65; c <= 90; c++) {
  CLASS[c] = LETTER;
  CLASS[c + 32] = LETTER;
}
CLASS[46] = SENTENCE_END; // .
CLASS[33] = SENTENCE_END; // !
CLASS[63] = SENTENCE_END; // ?

const FNV_OFFSET = 0x811c9dc5;
const FNV_PRIME = 0x01000193;
const NO_WORD = -1;
const TOP = 20;

function mixPair(a, b) {
  let h = Math.imul(a, 0x9e3779b1) ^ b;
  h ^= h >>> 16;
  h = Math.imul(h, 0x85ebca6b);
  h ^= h >>> 13;
  return h;
}

// Maps lower-cased words to dense ids in first-seen order.
class Vocab {
  constructor() {
    this.table = new Int32Array(1 << 16); // id + 1, 0 = empty
    this.hashes = [];
    this.words = [];
  }

  // buf[start..start+len) holds letters in either case; h is the FNV-1a hash of their lower-case form.
  find(buf, start, len, h) {
    const table = this.table;
    const mask = table.length - 1;
    let idx = h & mask;
    let v;
    while ((v = table[idx]) !== 0) {
      const id = v - 1;
      if (this.hashes[id] === h && sameFolded(this.words[id], buf, start, len)) {
        return id;
      }
      idx = (idx + 1) & mask;
    }
    const id = this.words.length;
    this.words.push(buf.toString("latin1", start, start + len).toLowerCase());
    this.hashes.push(h);
    table[idx] = id + 1;
    if (this.words.length * 2 > table.length) {
      this.rehash();
    }
    return id;
  }

  rehash() {
    const bigger = new Int32Array(this.table.length * 2);
    const mask = bigger.length - 1;
    for (let id = 0; id < this.hashes.length; id++) {
      let idx = this.hashes[id] & mask;
      while (bigger[idx] !== 0) {
        idx = (idx + 1) & mask;
      }
      bigger[idx] = id + 1;
    }
    this.table = bigger;
  }
}

function sameFolded(w, buf, start, len) {
  if (w.length !== len) {
    return false;
  }
  for (let j = 0; j < len; j++) {
    if (w.charCodeAt(j) !== (buf[start + j] | 0x20)) {
      return false;
    }
  }
  return true;
}

// Counts ordered pairs of word ids. Slot k is slots[3k..3k+2] = (first, second, count); count 0 = empty.
class PairCounter {
  constructor() {
    this.slots = new Int32Array((1 << 20) * 3);
    this.mask = (1 << 20) - 1;
    this.distinct = 0;
  }

  add(a, b) {
    const s = this.slots;
    const mask = this.mask;
    let idx = mixPair(a, b) & mask;
    for (;;) {
      const p = idx * 3;
      if (s[p + 2] === 0) {
        s[p] = a;
        s[p + 1] = b;
        s[p + 2] = 1;
        if (++this.distinct * 4 > (mask + 1) * 3) {
          this.grow();
        }
        return;
      }
      if (s[p] === a && s[p + 1] === b) {
        s[p + 2]++;
        return;
      }
      idx = (idx + 1) & mask;
    }
  }

  grow() {
    const cap = (this.mask + 1) * 2;
    const m = cap - 1;
    const bigger = new Int32Array(cap * 3);
    const old = this.slots;
    for (let s = 0; s < old.length; s += 3) {
      if (old[s + 2] === 0) {
        continue;
      }
      let idx = mixPair(old[s], old[s + 1]) & m;
      while (bigger[idx * 3 + 2] !== 0) {
        idx = (idx + 1) & m;
      }
      bigger[idx * 3] = old[s];
      bigger[idx * 3 + 1] = old[s + 1];
      bigger[idx * 3 + 2] = old[s + 2];
    }
    this.slots = bigger;
    this.mask = m;
  }
}

// Entry k of a top list is t[3k..3k+2] = (count, first id, second id).
function better(t, x, y, rank) {
  const cx = t[3 * x];
  const cy = t[3 * y];
  if (cx !== cy) {
    return cx > cy;
  }
  const ax = rank[t[3 * x + 1]];
  const ay = rank[t[3 * y + 1]];
  if (ax !== ay) {
    return ax < ay;
  }
  return rank[t[3 * x + 2]] < rank[t[3 * y + 2]];
}

function swapEntries(t, x, y) {
  for (let k = 0; k < 3; k++) {
    const tmp = t[3 * x + k];
    t[3 * x + k] = t[3 * y + k];
    t[3 * y + k] = tmp;
  }
}

function main() {
  if (process.argv.length < 3) {
    process.stderr.write("usage: node main.js INPUT_PATH\n");
    process.exit(2);
  }
  const buf = fs.readFileSync(process.argv[2]);
  const vocab = new Vocab();
  const pairs = new PairCounter();
  let words = 0;
  let total = 0;
  let prev = NO_WORD;
  const n = buf.length;
  let i = 0;
  while (i < n) {
    const cls = CLASS[buf[i]];
    if (cls === LETTER) {
      const start = i;
      let h = FNV_OFFSET;
      do {
        h = Math.imul(h ^ (buf[i] | 0x20), FNV_PRIME);
        i++;
      } while (i < n && CLASS[buf[i]] === LETTER);
      const id = vocab.find(buf, start, i - start, h);
      words++;
      if (prev !== NO_WORD) {
        pairs.add(prev, id);
        total++;
      }
      prev = id;
    } else {
      if (cls === SENTENCE_END) {
        prev = NO_WORD;
      }
      i++;
    }
  }

  // Rank words by byte order so ties can be broken with integer comparisons.
  const names = vocab.words;
  const order = names.map((_, k) => k);
  order.sort((x, y) => (names[x] < names[y] ? -1 : names[x] > names[y] ? 1 : 0));
  const rank = new Int32Array(names.length);
  for (let r = 0; r < order.length; r++) {
    rank[order[r]] = r;
  }

  const top = new Int32Array(3 * (TOP + 1));
  let k = 0;
  const data = pairs.slots;
  for (let s = 0; s < data.length; s += 3) {
    const c = data[s + 2];
    if (c === 0) {
      continue;
    }
    let j = k;
    top[3 * j] = c;
    top[3 * j + 1] = data[s];
    top[3 * j + 2] = data[s + 1];
    if (k === TOP && !better(top, TOP, TOP - 1, rank)) {
      continue;
    }
    if (k < TOP) {
      k++;
    }
    while (j > 0 && better(top, j, j - 1, rank)) {
      swapEntries(top, j, j - 1);
      j--;
    }
  }

  let out = "";
  out += `words ${words}\npairs ${total}\ndistinct ${pairs.distinct}\n`;
  for (let r = 0; r < k; r++) {
    out += `${top[3 * r]} ${names[top[3 * r + 1]]} ${names[top[3 * r + 2]]}\n`;
  }
  process.stdout.write(out);
}

main();
