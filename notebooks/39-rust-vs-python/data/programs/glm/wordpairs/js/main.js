'use strict';
// Word pairs: count adjacent word pairs within sentences, report totals and top 20.
const fs = require('fs');

let buf; // lowercased input bytes

// Pair table: open addressing on Number keys (word ids fit in 26 bits each),
// keys in Float64Array (exact up to 2^53), counts in Int32Array; cnt 0 = empty.
let pKeys, pCnt, pMask, pFilled = 0;

// Word interning: words live inside the lowercased buffer.
let wTab, wOff, wLen, wHsh, wMask, wCount = 0;

let words = 0, pairs = 0;

function mix32(x) {
  // integer hash for a 53-bit key: fold to 32 bits exactly, then avalanche
  let h = (x % 4294967291) >>> 0;
  h ^= h >>> 16;
  h = Math.imul(h, 0x85EBCA6B);
  h ^= h >>> 13;
  h = Math.imul(h, 0xC2B2AE35);
  h ^= h >>> 16;
  return h >>> 0;
}

function addPair(key) {
  if ((pFilled + 1) * 4 > (pMask + 1) * 3) growPairs();
  let i = mix32(key) & pMask;
  for (;;) {
    if (pCnt[i] === 0) {
      pKeys[i] = key;
      pCnt[i] = 1;
      pFilled++;
      return;
    }
    if (pKeys[i] === key) {
      pCnt[i]++;
      return;
    }
    i = (i + 1) & pMask;
  }
}

function growPairs() {
  const ok = pKeys, oc = pCnt;
  const ns = pMask * 2 + 2;
  pKeys = new Float64Array(ns);
  pCnt = new Int32Array(ns);
  pMask = ns - 1;
  for (let j = 0; j < ok.length; j++) {
    const c = oc[j];
    if (c !== 0) {
      const key = ok[j];
      let i = mix32(key) & pMask;
      while (pCnt[i] !== 0) i = (i + 1) & pMask;
      pKeys[i] = key;
      pCnt[i] = c;
    }
  }
}

function intern(o, l, h) {
  if ((wCount + 1) * 2 > wMask + 1) growWords();
  let i = h & wMask;
  for (;;) {
    const slot = wTab[i];
    if (slot === 0) {
      const id = wCount++;
      wOff[id] = o;
      wLen[id] = l;
      wHsh[id] = h;
      wTab[i] = id + 1;
      return id;
    }
    const id = slot - 1;
    if (wHsh[id] === h && wLen[id] === l && eqBytes(wOff[id], o, l)) return id;
    i = (i + 1) & wMask;
  }
}

function eqBytes(a, b, l) {
  for (let k = 0; k < l; k++) if (buf[a + k] !== buf[b + k]) return false;
  return true;
}

function growWords() {
  const ot = wTab;
  const ns = wMask * 2 + 2;
  wTab = new Int32Array(ns);
  wMask = ns - 1;
  for (let j = 0; j < ot.length; j++) {
    const slot = ot[j];
    if (slot !== 0) {
      const id = slot - 1;
      let i = wHsh[id] & wMask;
      while (wTab[i] !== 0) i = (i + 1) & wMask;
      wTab[i] = id + 1;
    }
  }
}

function cmpWord(a, b) {
  const o1 = wOff[a], l1 = wLen[a], o2 = wOff[b], l2 = wLen[b];
  const m = Math.min(l1, l2);
  for (let k = 0; k < m; k++) {
    const d = buf[o1 + k] - buf[o2 + k];
    if (d !== 0) return d;
  }
  return l1 - l2;
}

function cmpWords(a, b) {
  const a1 = Math.floor(a / 67108864), a2 = a - a1 * 67108864;
  const b1 = Math.floor(b / 67108864), b2 = b - b1 * 67108864;
  const c = cmpWord(a1, b1);
  if (c !== 0) return c;
  return cmpWord(a2, b2);
}

function worse(ka, ca, kb, cb) {
  if (ca !== cb) return ca < cb;
  return cmpWords(ka, kb) > 0;
}

function main() {
  const file = fs.readFileSync(process.argv[2]);
  buf = Buffer.from(file); // mutable copy
  const n = buf.length;
  for (let i = 0; i < n; i++) {
    const c = buf[i];
    if (c >= 65 && c <= 90) buf[i] = c + 32;
  }

  let ps = 1 << 20;
  while (ps < n / 8) ps <<= 1; // distinct pairs scale with input size; avoid rehashing
  pKeys = new Float64Array(ps);
  pCnt = new Int32Array(ps);
  pMask = ps - 1;

  wTab = new Int32Array(1 << 16);
  wMask = (1 << 16) - 1;
  wOff = new Int32Array(1 << 16);
  wLen = new Int32Array(1 << 16);
  wHsh = new Uint32Array(1 << 16);

  const TWO26 = 67108864;
  let prev = -1; // no previous word in current sentence
  let i = 0;
  while (i < n) {
    const c = buf[i];
    if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122)) {
      const start = i;
      let h = 0x811C9DC5;
      do {
        h = Math.imul(h ^ buf[i], 0x01000193);
        i++;
      } while (i < n && ((buf[i] >= 65 && buf[i] <= 90) || (buf[i] >= 97 && buf[i] <= 122)));
      const id = intern(start, i - start, h >>> 0);
      words++;
      if (prev >= 0) {
        addPair(prev * TWO26 + id);
        pairs++;
      }
      prev = id;
    } else {
      if (c === 46 || c === 33 || c === 63) prev = -1;
      i++;
    }
  }

  // Keep the 20 best pairs in a min-heap while scanning the pair table.
  const hKey = new Float64Array(20);
  const hCnt = new Int32Array(20);
  let hn = 0;
  for (let j = 0; j <= pMask; j++) {
    const cnt = pCnt[j];
    if (cnt === 0) continue;
    const key = pKeys[j];
    if (hn < 20) {
      let k = hn++;
      hKey[k] = key;
      hCnt[k] = cnt;
      while (k > 0) {
        const p = (k - 1) >> 1;
        if (worse(key, cnt, hKey[p], hCnt[p])) {
          const tk = hKey[p]; hKey[p] = hKey[k]; hKey[k] = tk;
          const tc = hCnt[p]; hCnt[p] = hCnt[k]; hCnt[k] = tc;
          k = p;
        } else break;
      }
    } else if (worse(hKey[0], hCnt[0], key, cnt)) {
      hKey[0] = key;
      hCnt[0] = cnt;
      let k = 0;
      for (;;) {
        const l = 2 * k + 1, r = l + 1;
        let m = k;
        if (l < hn && worse(hKey[l], hCnt[l], hKey[m], hCnt[m])) m = l;
        if (r < hn && worse(hKey[r], hCnt[r], hKey[m], hCnt[m])) m = r;
        if (m === k) break;
        const tk = hKey[m]; hKey[m] = hKey[k]; hKey[k] = tk;
        const tc = hCnt[m]; hCnt[m] = hCnt[k]; hCnt[k] = tc;
        k = m;
      }
    }
  }
  for (let a = 0; a < hn; a++) {
    let best = a;
    for (let b = a + 1; b < hn; b++) {
      if (hCnt[b] > hCnt[best] ||
          (hCnt[b] === hCnt[best] && cmpWords(hKey[b], hKey[best]) < 0)) best = b;
    }
    if (best !== a) {
      const tk = hKey[a]; hKey[a] = hKey[best]; hKey[best] = tk;
      const tc = hCnt[a]; hCnt[a] = hCnt[best]; hCnt[best] = tc;
    }
  }

  let out = Buffer.allocUnsafe(4096);
  let o = 0;
  const ensure = (k) => {
    if (o + k > out.length) {
      let nu = Buffer.allocUnsafe(Math.max(out.length * 2, o + k));
      out.copy(nu, 0, 0, o);
      out = nu;
    }
  };
  const writeNum = (v, suffix) => {
    ensure(24);
    let k = 24;
    do {
      out[o + --k] = 48 + (v % 10);
      v = (v - (v % 10)) / 10;
    } while (v > 0);
    out.copy(out, o, o + k, o + 24);
    o += 24 - k;
    out[o++] = suffix;
  };
  const writeWord = (id, suffix) => {
    ensure(wLen[id] + 1);
    buf.copy(out, o, wOff[id], wOff[id] + wLen[id]);
    o += wLen[id];
    out[o++] = suffix;
  };

  const writeStr = (s) => {
    ensure(s.length);
    out.write(s, o, 'latin1');
    o += s.length;
  };
  writeStr('words ');
  writeNum(words, 10);
  writeStr('pairs ');
  writeNum(pairs, 10);
  writeStr('distinct ');
  writeNum(pFilled, 10);
  for (let k = 0; k < hn; k++) {
    writeNum(hCnt[k], 32);
    writeWord(Math.floor(hKey[k] / TWO26), 32);
    writeWord(hKey[k] % TWO26, 10);
  }
  fs.writeSync(1, out.subarray(0, o));
}

main();
