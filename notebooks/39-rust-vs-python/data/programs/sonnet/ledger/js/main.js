"use strict";

const fs = require("fs");

const TWO32 = 4294967296;
const TWO52 = 4503599627370496;

// ---- byte-keyed aggregation table; sums kept as hi * 2^32 + lo in doubles ----
class Table {
  constructor() {
    this.index = new Int32Array(1 << 12).fill(-1);
    this.mask = (1 << 12) - 1;
    this.n = 0;
    this.hashes = new Int32Array(1024);
    this.keyOff = new Int32Array(1024);
    this.keyLen = new Int32Array(1024);
    this.hi = new Float64Array(1024);
    this.lo = new Float64Array(1024);
    this.counts = new Float64Array(1024);
    this.arena = new Uint8Array(1 << 14);
    this.arenaLen = 0;
  }

  add(k, off, len, vh, vl) {
    let hash = 0x811c9dc5 | 0;
    for (let i = 0; i < len; i++) hash = Math.imul(hash ^ k[off + i], 16777619);
    hash ^= hash >>> 15;
    let h = hash & this.mask;
    const index = this.index, hashes = this.hashes, keyLen = this.keyLen, keyOff = this.keyOff, arena = this.arena;
    for (;;) {
      const ix = index[h];
      if (ix < 0) break;
      if (hashes[ix] === hash && keyLen[ix] === len) {
        const o = keyOff[ix];
        let i = 0;
        while (i < len && arena[o + i] === k[off + i]) i++;
        if (i === len) {
          this.hi[ix] += vh;
          let l = this.lo[ix] + vl;
          if (l >= TWO52 || l <= -TWO52) {
            const c = Math.floor(l / TWO32);
            this.hi[ix] += c;
            l -= c * TWO32;
          }
          this.lo[ix] = l;
          this.counts[ix]++;
          return;
        }
      }
      h = (h + 1) & this.mask;
    }
    if (this.n === this.hashes.length) this.growArrays();
    if (this.arenaLen + len > this.arena.length) {
      const na = new Uint8Array(Math.max(this.arena.length * 2, this.arenaLen + len));
      na.set(this.arena);
      this.arena = na;
    }
    for (let i = 0; i < len; i++) this.arena[this.arenaLen + i] = k[off + i];
    const id = this.n++;
    this.hashes[id] = hash;
    this.keyOff[id] = this.arenaLen;
    this.keyLen[id] = len;
    this.arenaLen += len;
    this.hi[id] = vh;
    this.lo[id] = vl;
    this.counts[id] = 1;
    this.index[h] = id;
    if (this.n * 2 > this.index.length) this.growIndex();
  }

  growArrays() {
    const c = this.n * 2;
    const g = (a, T) => {
      const b = new T(c);
      b.set(a);
      return b;
    };
    this.hashes = g(this.hashes, Int32Array);
    this.keyOff = g(this.keyOff, Int32Array);
    this.keyLen = g(this.keyLen, Int32Array);
    this.hi = g(this.hi, Float64Array);
    this.lo = g(this.lo, Float64Array);
    this.counts = g(this.counts, Float64Array);
  }

  growIndex() {
    const cap = this.index.length * 2;
    this.index = new Int32Array(cap).fill(-1);
    this.mask = cap - 1;
    for (let i = 0; i < this.n; i++) {
      let h = this.hashes[i] & this.mask;
      while (this.index[h] >= 0) h = (h + 1) & this.mask;
      this.index[h] = i;
    }
  }

  key(i) {
    return Buffer.from(this.arena.buffer, this.arena.byteOffset + this.keyOff[i], this.keyLen[i]).toString("latin1");
  }

  // normalise lo into [0, 2^32) so (hi, lo) compares lexicographically
  normalise(i) {
    const c = Math.floor(this.lo[i] / TWO32);
    this.hi[i] += c;
    this.lo[i] -= c * TWO32;
  }

  value(i) {
    return BigInt(this.hi[i]) * 4294967296n + BigInt(this.lo[i]);
  }
}

const accounts = new Table();
const channels = new Table();
let totHi = 0, totLo = 0, totalCount = 0;

let buf = null;
let p = 0;
let sArr = null, sOff = 0, sLen = 0;
let rateKeys = [];
let rateVals = [];
let ratesDone = false;

function hex4(b, q) {
  let v = 0;
  for (let i = 0; i < 4; i++) {
    const c = b[q + i];
    v <<= 4;
    if (c >= 48 && c <= 57) v |= c - 48;
    else if (c >= 97 && c <= 102) v |= c - 87;
    else v |= c - 55;
  }
  return v;
}

function pushUtf8(out, cp) {
  if (cp < 0x80) out.push(cp);
  else if (cp < 0x800) out.push(0xc0 | (cp >> 6), 0x80 | (cp & 0x3f));
  else if (cp < 0x10000) out.push(0xe0 | (cp >> 12), 0x80 | ((cp >> 6) & 0x3f), 0x80 | (cp & 0x3f));
  else out.push(0xf0 | (cp >> 18), 0x80 | ((cp >> 12) & 0x3f), 0x80 | ((cp >> 6) & 0x3f), 0x80 | (cp & 0x3f));
}

// p at opening quote; leaves p after closing quote
function parseStr() {
  const b = buf;
  let q = p + 1;
  const s = q;
  for (;;) {
    const c = b[q];
    if (c === 34) {
      sArr = b;
      sOff = s;
      sLen = q - s;
      p = q + 1;
      return;
    }
    if (c === 92) break;
    q++;
  }
  parseStrSlow(s, q);
}

function parseStrSlow(s, q) {
  const b = buf;
  const out = [];
  for (let i = s; i < q; i++) out.push(b[i]);
  for (;;) {
    const c = b[q];
    if (c === 34) {
      q++;
      break;
    }
    if (c === 92) {
      const e = b[q + 1];
      q += 2;
      switch (e) {
        case 110: out.push(10); break;
        case 116: out.push(9); break;
        case 114: out.push(13); break;
        case 98: out.push(8); break;
        case 102: out.push(12); break;
        case 117: {
          let cp = hex4(b, q);
          q += 4;
          if (cp >= 0xd800 && cp < 0xdc00 && b[q] === 92 && b[q + 1] === 117) {
            const lo = hex4(b, q + 2);
            if (lo >= 0xdc00 && lo < 0xe000) {
              cp = 0x10000 + ((cp - 0xd800) << 10) + (lo - 0xdc00);
              q += 6;
            }
          }
          pushUtf8(out, cp);
          break;
        }
        default: out.push(e);
      }
    } else {
      out.push(c);
      q++;
    }
  }
  sArr = Uint8Array.from(out);
  sOff = 0;
  sLen = out.length;
  p = q;
}

function skipWs() {
  const b = buf;
  let q = p;
  for (;;) {
    const c = b[q];
    if (c === 32 || c === 10 || c === 9 || c === 13) q++;
    else break;
  }
  p = q;
}

function skipString(q) {
  const b = buf;
  q++;
  for (;;) {
    const c = b[q];
    if (c === 34) break;
    if (c === 92) q++;
    q++;
  }
  return q + 1;
}

function skipValue() {
  const b = buf;
  let q = p;
  let c = b[q];
  if (c === 34) {
    p = skipString(q);
    return;
  }
  if (c === 123 || c === 91) {
    let depth = 0;
    for (;;) {
      c = b[q];
      if (c === 34) {
        q = skipString(q);
        continue;
      }
      q++;
      if (c === 123 || c === 91) depth++;
      else if (c === 125 || c === 93) {
        if (--depth === 0) break;
      }
    }
    p = q;
    return;
  }
  while (c !== 44 && c !== 125 && c !== 93 && c !== 32 && c !== 10 && c !== 13 && c !== 9) c = b[++q];
  p = q;
}

function parseInt10() {
  let v = 0;
  const b = buf;
  let q = p;
  while (b[q] >= 48 && b[q] <= 57) v = v * 10 + (b[q++] - 48);
  p = q;
  return v;
}

function litEq(a, off, len, lit) {
  if (len !== lit.length) return false;
  for (let i = 0; i < len; i++) if (a[off + i] !== lit.charCodeAt(i)) return false;
  return true;
}

function parseRates() {
  p++;
  for (;;) {
    skipWs();
    parseStr();
    const isRates = litEq(sArr, sOff, sLen, "rates");
    skipWs();
    p++;
    skipWs();
    if (isRates) {
      p++;
      for (;;) {
        skipWs();
        if (buf[p] === 125) {
          p++;
          break;
        }
        parseStr();
        rateKeys.push(Uint8Array.from(sArr.subarray(sOff, sOff + sLen)));
        skipWs();
        p++;
        skipWs();
        rateVals.push(parseInt10());
        skipWs();
        if (buf[p] === 44) p++;
      }
    } else {
      skipValue();
    }
    skipWs();
    if (buf[p] === 44) {
      p++;
      continue;
    }
    p++;
    break;
  }
}

function parseTx() {
  p++;
  let accArr = null, accOff = 0, accLen = 0;
  let chanArr = null, chanOff = 0, chanLen = 0;
  let type = 0;
  let hund = 0, hundBig = null, rate = 0;
  let test = false;
  for (;;) {
    skipWs();
    if (buf[p] === 125) {
      p++;
      break;
    }
    parseStr();
    const ka = sArr, ko = sOff, kl = sLen;
    skipWs();
    p++;
    skipWs();
    let kind = 0;
    if (kl === 4) {
      const c0 = ka[ko], c1 = ka[ko + 1], c2 = ka[ko + 2], c3 = ka[ko + 3];
      if (c0 === 116 && c1 === 121 && c2 === 112 && c3 === 101) kind = 2;
      else if (c0 === 116 && c1 === 97 && c2 === 103 && c3 === 115) kind = 5;
      else if (c0 === 109 && c1 === 101 && c2 === 116 && c3 === 97) kind = 6;
    } else if (kl === 6) {
      if (litEq(ka, ko, kl, "amount")) kind = 3;
    } else if (kl === 7) {
      if (litEq(ka, ko, kl, "account")) kind = 1;
    } else if (kl === 8) {
      if (litEq(ka, ko, kl, "currency")) kind = 4;
    }
    switch (kind) {
      case 1:
        parseStr();
        accArr = sArr; accOff = sOff; accLen = sLen;
        break;
      case 2:
        parseStr();
        type = sLen > 0 ? sArr[sOff] : 0;
        break;
      case 3: {
        parseStr();
        const a = sArr;
        let q = sOff;
        const e = q + sLen;
        if (sLen > 15) {
          let ds = "";
          for (let i = q; i < e; i++) ds += String.fromCharCode(a[i]);
          const dot = ds.indexOf(".");
          let ipS = dot < 0 ? ds : ds.slice(0, dot);
          let frS = dot < 0 ? "" : ds.slice(dot + 1);
          frS = (frS + "00").slice(0, 2);
          hundBig = BigInt(ipS || "0") * 100n + BigInt(frS);
          hund = 0;
          break;
        }
        let ip = 0;
        while (q < e && a[q] !== 46) ip = ip * 10 + (a[q++] - 48);
        let fr = 0;
        if (q < e) {
          q++;
          if (q < e) {
            fr = (a[q++] - 48) * 10;
            if (q < e) fr += a[q] - 48;
          }
        }
        hund = ip * 100 + fr;
        break;
      }
      case 4: {
        parseStr();
        const n = rateKeys.length;
        for (let i = 0; i < n; i++) {
          const rk = rateKeys[i];
          if (rk.length !== sLen) continue;
          let j = 0;
          while (j < sLen && rk[j] === sArr[sOff + j]) j++;
          if (j === sLen) {
            rate = rateVals[i];
            break;
          }
        }
        break;
      }
      case 5: {
        p++;
        skipWs();
        if (buf[p] === 93) {
          p++;
          break;
        }
        for (;;) {
          skipWs();
          parseStr();
          if (sLen === 4 && sArr[sOff] === 116 && sArr[sOff + 1] === 101 && sArr[sOff + 2] === 115 && sArr[sOff + 3] === 116) test = true;
          skipWs();
          if (buf[p] === 44) {
            p++;
            continue;
          }
          p++;
          break;
        }
        break;
      }
      case 6: {
        p++;
        for (;;) {
          skipWs();
          if (buf[p] === 125) {
            p++;
            break;
          }
          parseStr();
          const isChannel = litEq(sArr, sOff, sLen, "channel");
          skipWs();
          p++;
          skipWs();
          if (isChannel && buf[p] === 34) {
            parseStr();
            chanArr = sArr; chanOff = sOff; chanLen = sLen;
          } else {
            skipValue();
          }
          skipWs();
          if (buf[p] === 44) {
            p++;
            continue;
          }
          p++;
          break;
        }
        break;
      }
      default:
        skipValue();
    }
    skipWs();
    if (buf[p] === 44) {
      p++;
      continue;
    }
    p++;
    break;
  }
  if (type === 118 || test) return;
  const sign = type === 100 ? -1 : 1;
  let vh, vl;
  let usd = -1;
  if (hundBig === null) {
    const prod = hund * rate;
    if (prod < 9e15) {
      const r = prod % 1000000;
      usd = (prod - r) / 1000000;
    }
  }
  if (usd >= 0) {
    const v = sign * usd;
    vh = Math.floor(v / TWO32);
    vl = v - vh * TWO32;
  } else {
    const h = hundBig === null ? BigInt(hund) : hundBig;
    let v = (h * BigInt(rate)) / 1000000n;
    if (sign < 0) v = -v;
    vh = Number(v >> 32n);
    vl = Number(v & 0xffffffffn);
  }
  totalCount++;
  totHi += vh;
  totLo += vl;
  if (totLo >= TWO52) {
    const c = Math.floor(totLo / TWO32);
    totHi += c;
    totLo -= c * TWO32;
  }
  accounts.add(accArr, accOff, accLen, vh, vl);
  channels.add(chanArr, chanOff, chanLen, vh, vl);
}

function processChunk(end) {
  p = 0;
  for (;;) {
    skipWs();
    if (p >= end) break;
    if (!ratesDone) {
      parseRates();
      ratesDone = true;
    } else {
      parseTx();
    }
  }
}

function main() {
  const fd = fs.openSync(process.argv[2], "r");
  let cap = 1 << 22;
  buf = Buffer.allocUnsafe(cap + 16);
  let have = 0;
  let eof = false;
  while (!eof) {
    const n = fs.readSync(fd, buf, have, cap - have, null);
    if (n <= 0) eof = true;
    else have += n;
    let end;
    if (eof) {
      if (have > 0 && buf[have - 1] !== 10) buf[have++] = 10;
      end = have;
      buf[end] = 0;
    } else {
      let i = have;
      while (i > 0 && buf[i - 1] !== 10) i--;
      if (i === 0) {
        if (have === cap) {
          cap *= 2;
          const nb = Buffer.allocUnsafe(cap + 16);
          buf.copy(nb, 0, 0, have);
          buf = nb;
        }
        continue;
      }
      end = i;
    }
    processChunk(end);
    if (!eof) {
      buf.copyWithin(0, end, have);
      have -= end;
    }
  }
  fs.closeSync(fd);

  const net = BigInt(totHi) * 4294967296n + BigInt(totLo);
  const lines = [`counted ${totalCount}`, `net ${net}`];
  const order = [];
  for (let i = 0; i < channels.n; i++) order.push(i);
  const names = order.map((i) => channels.key(i));
  order.sort((a, b) => (names[a] < names[b] ? -1 : names[a] > names[b] ? 1 : 0));
  for (const i of order) lines.push(`channel ${names[i]} ${channels.counts[i]} ${channels.value(i)}`);

  const na = accounts.n;
  for (let i = 0; i < na; i++) accounts.normalise(i);
  const keyLess = (a, b) => {
    const ao = accounts.keyOff[a], bo = accounts.keyOff[b];
    const al = accounts.keyLen[a], bl = accounts.keyLen[b];
    const m = Math.min(al, bl);
    const ar = accounts.arena;
    for (let i = 0; i < m; i++) {
      const d = ar[ao + i] - ar[bo + i];
      if (d !== 0) return d < 0;
    }
    return al < bl;
  };
  const before = (a, b) => {
    if (accounts.hi[a] !== accounts.hi[b]) return accounts.hi[a] > accounts.hi[b];
    if (accounts.lo[a] !== accounts.lo[b]) return accounts.lo[a] > accounts.lo[b];
    return keyLess(a, b);
  };
  const topN = Math.min(10, na);
  const top = new Array(topN);
  let tn = 0;
  for (let i = 0; i < na; i++) {
    if (tn === topN && !before(i, top[tn - 1])) continue;
    let j;
    if (tn < topN) j = tn++;
    else j = tn - 1;
    while (j > 0 && before(i, top[j - 1])) {
      top[j] = top[j - 1];
      j--;
    }
    top[j] = i;
  }
  for (let i = 0; i < tn; i++) lines.push(`account ${accounts.key(top[i])} ${accounts.value(top[i])}`);
  fs.writeSync(1, Buffer.from(lines.join("\n") + "\n", "latin1"));
}

main();
