'use strict';
// Ledger: sum JSON-lines transactions with exact integer currency conversion.
// Single pass over the raw bytes; only the needed fields are extracted.
const fs = require('fs');

function main() {
  const data = fs.readFileSync(process.argv[2]);
  const n = data.length;
  const rates = new Table(16);
  const channels = new Table(16);
  const accounts = new Table(1 << 12);
  const scratch = Buffer.allocUnsafe(1024);

  // Open-addressing hash table keyed by byte ranges in `data`.
  // Keys are copied into a private pool; doubles for the values.
  function Table(cap0) {
    let cap = 1 << 10;
    while (cap < cap0) cap <<= 1;
    this.mask = cap - 1;
    this.slot = new Int32Array(cap); // entry idx + 1
    this.keyOff = new Int32Array(cap);
    this.keyLen = new Int32Array(cap);
    this.a = new Float64Array(cap); // count
    this.b = new Float64Array(cap); // net
    this.size = 0;
    this.pool = Buffer.allocUnsafe(1 << 16);
    this.poolLen = 0;
    this.entries = []; // [off, len, a, b] filled on finish()
  }

  Table.prototype.find = function (s, e, src) {
    if (src === undefined) src = data;
    let i = this.hashRange(src, s, e) & this.mask;
    const slot = this.slot;
    while (slot[i] !== 0) {
      const t = slot[i] - 1;
      const kl = this.keyLen[t];
      if (kl === e - s) {
        const p = this.pool;
        let po = this.keyOff[t];
        let k = 0;
        while (k < kl && p[po + k] === src[s + k]) k++;
        if (k === kl) return t;
      }
      i = (i + 1) & this.mask;
    }
    return -1;
  };

  Table.prototype.findOrInsert = function (s, e, src) {
    if (src === undefined) src = data;
    if (this.size * 10 >= this.mask * 7) this.grow();
    let i = this.hashRange(src, s, e) & this.mask;
    const slot = this.slot;
    while (slot[i] !== 0) {
      const t = slot[i] - 1;
      const kl = this.keyLen[t];
      if (kl === e - s) {
        const p = this.pool;
        let po = this.keyOff[t];
        let k = 0;
        while (k < kl && p[po + k] === src[s + k]) k++;
        if (k === kl) return t;
      }
      i = (i + 1) & this.mask;
    }
    const t = this.size++;
    const len = e - s;
    if (this.poolLen + len > this.pool.length) {
      const np = Buffer.allocUnsafe(Math.max(this.pool.length * 2, this.poolLen + len));
      this.pool.copy(np, 0, 0, this.poolLen);
      this.pool = np;
    }
    src.copy(this.pool, this.poolLen, s, e);
    this.keyOff[t] = this.poolLen;
    this.keyLen[t] = len;
    this.poolLen += len;
    this.a[t] = 0;
    this.b[t] = 0;
    slot[i] = t + 1;
    return t;
  };

  Table.prototype.hashRange = function (src, s, e) {
    let h = 0xcbf29ce4;
    for (let i = s; i < e; i++) {
      h ^= src[i];
      h = (h * 0x1000193) | 0;
    }
    return h & 0x7fffffff;
  };

  Table.prototype.grow = function () {
    const cap = (this.mask + 1) << 1;
    this.mask = cap - 1;
    const nslot = new Int32Array(cap);
    const nKeyOff = new Int32Array(cap);
    const nKeyLen = new Int32Array(cap);
    const na = new Float64Array(cap);
    const nb = new Float64Array(cap);
    for (let t = 0; t < this.size; t++) {
      // re-hash from the pool
      const off = this.keyOff[t], len = this.keyLen[t];
      let h = 0xcbf29ce4;
      for (let k = 0; k < len; k++) {
        h ^= this.pool[off + k];
        h = (h * 0x1000193) | 0;
      }
      let i = (h & 0x7fffffff) & this.mask;
      while (nslot[i] !== 0) i = (i + 1) & this.mask;
      nslot[i] = t + 1;
      nKeyOff[t] = off;
      nKeyLen[t] = len;
      na[t] = this.a[t];
      nb[t] = this.b[t];
    }
    this.slot = nslot;
    this.keyOff = nKeyOff;
    this.keyLen = nKeyLen;
    this.a = na;
    this.b = nb;
  };

  Table.prototype.decodedKey = function (t) {
    return this.pool.toString('utf8', this.keyOff[t], this.keyOff[t] + this.keyLen[t]);
  };

  const isWS = (c) => c === 32 || c === 9 || c === 13 || c === 10;

  function skipWS(i) {
    while (i < n && isWS(data[i])) i++;
    return i;
  }

  // parses string starting at '"'; sets sV (start), eV (end), sN (next index)
  let sV = 0, eV = 0, sN = 0, escV = false;

  function parseString(i) {
    i++;
    sV = i;
    let esc = false;
    while (i < n) {
      const c = data[i];
      if (c === 34) break; // '"'
      if (c === 92) { // '\\'
        esc = true;
        i++;
        if (data[i] === 117) i += 4; // 'u'
      }
      i++;
    }
    eV = i;
    escV = esc;
    sN = i + 1;
  }

  function skipValue(i) {
    if (i < n && data[i] === 34) {
      parseString(i);
      return sN;
    }
    if (i < n && (data[i] === 123 || data[i] === 91)) { // '{' '['
      let depth = 0;
      while (i < n) {
        const c = data[i];
        if (c === 34) {
          parseString(i);
          i = sN;
          continue;
        }
        if (c === 123 || c === 91) depth++;
        else if (c === 125 || c === 93) { // '}' ']'
          if (--depth === 0) return i + 1;
        }
        i++;
      }
      return i;
    }
    while (i < n) {
      const c = data[i];
      if (c === 44 || c === 125 || c === 93) break; // ',' '}' ']'
      i++;
    }
    return i;
  }

  function decodeInto(s, e) {
    // decode JSON string escapes into scratch; returns byte length
    let k = 0;
    for (let i = s; i < e; i++) {
      let c = data[i];
      if (c !== 92) { scratch[k++] = c; continue; }
      i++;
      const x = data[i];
      if (x === 117) { // 'u'
        let cp = hex4(i + 1);
        i += 4;
        if (cp >= 0xd800 && cp <= 0xdbff && data[i + 1] === 92 && data[i + 2] === 117) {
          const lo = hex4(i + 3);
          if (lo >= 0xdc00 && lo <= 0xdfff) {
            cp = 0x10000 + ((cp - 0xd800) << 10) + (lo - 0xdc00);
            i += 6;
          }
        }
        // UTF-8 encode
        if (cp < 0x80) scratch[k++] = cp;
        else if (cp < 0x800) {
          scratch[k++] = 0xc0 | (cp >> 6);
          scratch[k++] = 0x80 | (cp & 0x3f);
        } else if (cp < 0x10000) {
          scratch[k++] = 0xe0 | (cp >> 12);
          scratch[k++] = 0x80 | ((cp >> 6) & 0x3f);
          scratch[k++] = 0x80 | (cp & 0x3f);
        } else {
          scratch[k++] = 0xf0 | (cp >> 18);
          scratch[k++] = 0x80 | ((cp >> 12) & 0x3f);
          scratch[k++] = 0x80 | ((cp >> 6) & 0x3f);
          scratch[k++] = 0x80 | (cp & 0x3f);
        }
      } else {
        scratch[k++] =
          x === 114 ? 13 :   // \r
          x === 110 ? 10 :   // \n
          x === 116 ? 9 :    // \t
          x === 98 ? 8 :     // \b
          x === 102 ? 12 :   // \f
          x;                 // " \ / \\
      }
    }
    return k;
  }

  function hex4(i) {
    let v = 0;
    for (let k = 0; k < 4; k++) {
      const c = data[i + k];
      v = v * 16 + (c <= 57 ? c - 48 : (c | 32) - 87);
    }
    return v;
  }

  // compares string value (raw, maybe escaped) to ASCII literal
  function strEq(s, e, esc, lit) {
    if (!esc) {
      const len = e - s;
      if (len !== lit.length) return false;
      for (let k = 0; k < len; k++) if (data[s + k] !== lit.charCodeAt(k)) return false;
      return true;
    }
    const len = decodeInto(s, e);
    if (len !== lit.length) return false;
    for (let k = 0; k < len; k++) if (scratch[k] !== lit.charCodeAt(k)) return false;
    return true;
  }

  // "12", "12.5", "12.05" -> integer hundredths
  function parseAmount(s, e) {
    let whole = 0;
    let i = s;
    while (i < e) {
      const c = data[i] - 48;
      if (c < 0 || c > 9) break;
      whole = whole * 10 + c;
      i++;
    }
    let frac = 0;
    if (i < e && data[i] === 46) { // '.'
      i++;
      frac = (data[i] - 48) * 10;
      i++;
      if (i < e) frac += data[i] - 48;
    }
    return whole * 100 + frac;
  }

  function makeKey(s, e, esc) {
    if (!esc) return data.toString('latin1', s, e);
    const len = decodeInto(s, e);
    return scratch.toString('utf8', 0, len);
  }

  // First line: rates.
  let i = skipWS(0);
  let eol = data.indexOf(10, i);
  if (eol < 0) eol = n;
  {
    let p = skipWS(i);
    if (p < n && data[p] === 123) { // '{'
      p++;
      while (p < n) {
        p = skipWS(p);
        if (p >= n || data[p] === 125) break; // '}'
        if (data[p] === 44) { p++; continue; } // ','
        parseString(p);
        const ks = sV, ke = eV, kesc = escV;
        p = skipWS(sN);
        p++; // ':'
        p = skipWS(p);
        if (strEq(ks, ke, kesc, 'rates')) {
          p = skipWS(p);
          p++; // '{'
          while (p < n) {
            p = skipWS(p);
            if (p >= n || data[p] === 125) break;
            if (data[p] === 44) { p++; continue; }
            parseString(p);
            const cs = sV, ce = eV, cesc = escV;
            p = skipWS(sN);
            p++; // ':'
            p = skipWS(p);
            let neg = false;
            if (data[p] === 45) { neg = true; p++; } // '-'
            let rate = 0;
            while (p < n) {
              const c = data[p] - 48;
              if (c < 0 || c > 9) break;
              rate = rate * 10 + c;
              p++;
            }
            if (neg) rate = -rate;
            let kS = cs, kE = ce, kSrc = data;
            if (cesc) { kE = decodeInto(cs, ce); kS = 0; kSrc = scratch; }
            rates.b[rates.findOrInsert(kS, kE, kSrc)] = rate;
          }
          p++; // '}'
        } else {
          p = skipValue(p);
        }
      }
    }
  }
  i = eol < n ? eol + 1 : n;

  let totalCount = 0, totalNet = 0;
  while (i < n) {
    let q = skipWS(i);
    eol = data.indexOf(10, i);
    if (eol < 0) eol = n;
    if (q < eol && data[q] === 123) { // '{'
      q++;
      let sign = 0, rate = 0, amount = 0, hasRate = false;
      let accS = -1, accE = 0, accEsc = false;
      let chanS = -1, chanE = 0, chanEsc = false;
      let isTest = false;
      while (true) {
        q = skipWS(q);
        if (q >= n || data[q] === 125) { q++; break; } // '}'
        if (data[q] === 44) { q++; continue; } // ','
        parseString(q);
        const ks = sV, ke = eV, kesc = escV;
        q = skipWS(sN);
        q++; // ':'
        q = skipWS(q);
        if (!kesc) {
          const kl = ke - ks;
          const k0 = kl > 0 ? data[ks] : 0;
          if (k0 === 116 && kl === 4) { // 't' -> type/tags
            if (data[ks + 1] === 121) { // 'y' -> "type"
              parseString(q);
              const vs = sV, ve = eV, vesc = escV;
              q = sN;
              if (strEq(vs, ve, vesc, 'credit') || strEq(vs, ve, vesc, 'refund')) sign = 1;
              else if (strEq(vs, ve, vesc, 'debit')) sign = -1;
              continue;
            } else if (data[ks + 1] === 97) { // 'a' -> "tags"
              q++; // '['
              while (true) {
                q = skipWS(q);
                if (q >= n || data[q] === 93) { q++; break; } // ']'
                if (data[q] === 44) { q++; continue; } // ','
                if (data[q] === 34) { // '"'
                  parseString(q);
                  const vs = sV, ve = eV, vesc = escV;
                  q = sN;
                  if (!isTest && strEq(vs, ve, vesc, 'test')) isTest = true;
                } else {
                  q = skipValue(q);
                }
              }
              continue;
            }
          } else if (k0 === 97 && kl === 6 && data[ks + 1] === 109) { // 'a' "amount"
            parseString(q);
            const vs = sV, ve = eV;
            q = sN;
            amount = parseAmount(vs, ve);
            continue;
          } else if (k0 === 97 && kl === 7 && data[ks + 1] === 99) { // 'a' "account"
            parseString(q);
            accS = sV; accE = eV; accEsc = escV;
            q = sN;
            continue;
          } else if (k0 === 99 && kl === 8) { // 'c' "currency"
            parseString(q);
            const vs = sV, ve = eV, vesc = escV;
            q = sN;
            let kS = vs, kE = ve, kSrc = data;
            if (vesc) { kE = decodeInto(vs, ve); kS = 0; kSrc = scratch; }
            const ri = rates.find(kS, kE, kSrc);
            hasRate = ri >= 0;
            if (hasRate) rate = rates.b[ri];
            continue;
          } else if (k0 === 109 && kl === 4) { // 'm' "meta"
            q++; // '{'
            while (true) {
              q = skipWS(q);
              if (q >= n || data[q] === 125) { q++; break; } // '}'
              if (data[q] === 44) { q++; continue; } // ','
              parseString(q);
              const mks = sV, mke = eV, mkesc = escV;
              q = skipWS(sN);
              q++; // ':'
              q = skipWS(q);
              if (strEq(mks, mke, mkesc, 'channel')) {
                parseString(q);
                chanS = sV; chanE = eV; chanEsc = escV;
                q = sN;
              } else {
                q = skipValue(q);
              }
            }
            continue;
          }
        }
        q = skipValue(q);
      }
      if (sign !== 0 && !isTest && hasRate && accS >= 0 && chanS >= 0) {
        const val = sign * Math.trunc((amount * rate) / 1000000);
        totalCount++;
        totalNet += val;
        let cS = chanS, cE = chanE, cSrc = data;
        if (chanEsc) { cE = decodeInto(chanS, chanE); cS = 0; cSrc = scratch; }
        let ci = channels.find(cS, cE, cSrc);
        if (ci < 0) {
          ci = channels.findOrInsert(cS, cE, cSrc);
          channels.a[ci] = 1;
          channels.b[ci] = val;
        } else {
          channels.a[ci]++;
          channels.b[ci] += val;
        }
        let aS = accS, aE = accE, aSrc = data;
        if (accEsc) { aE = decodeInto(accS, accE); aS = 0; aSrc = scratch; }
        let ai = accounts.find(aS, aE, aSrc);
        if (ai < 0) {
          ai = accounts.findOrInsert(aS, aE, aSrc);
          accounts.b[ai] = val;
        } else {
          accounts.b[ai] += val;
        }
      }
    }
    i = eol < n ? eol + 1 : n;
  }

  const out = [];
  out.push('counted ' + totalCount);
  out.push('net ' + totalNet);

  // channel lines sorted by name ascending (byte order)
  const chanIdx = [];
  for (let t = 0; t < channels.size; t++) chanIdx.push(t);
  const byteCmp = (tbl, x, y) => {
    const ox = tbl.keyOff[x], oy = tbl.keyOff[y];
    const lx = tbl.keyLen[x], ly = tbl.keyLen[y];
    const m = Math.min(lx, ly);
    for (let k = 0; k < m; k++) {
      const d = tbl.pool[ox + k] - tbl.pool[oy + k];
      if (d !== 0) return d;
    }
    return lx - ly;
  };
  chanIdx.sort((x, y) => byteCmp(channels, x, y));
  for (const t of chanIdx) {
    out.push('channel ' + channels.decodedKey(t) + ' ' + channels.a[t] + ' ' + channels.b[t]);
  }

  // top 10 accounts by net desc, then id asc
  const best = [];
  const accBetter = (x, y) => {
    if (accounts.b[x] !== accounts.b[y]) return accounts.b[x] > accounts.b[y];
    return byteCmp(accounts, x, y) < 0;
  };
  for (let t = 0; t < accounts.size; t++) {
    if (best.length < 10) {
      best.push(t);
      continue;
    }
    let worst = 0;
    for (let j = 1; j < best.length; j++) if (accBetter(best[worst], best[j])) worst = j;
    if (accBetter(t, best[worst])) best[worst] = t;
  }
  best.sort((x, y) => (accBetter(x, y) ? -1 : accBetter(y, x) ? 1 : 0));
  for (const t of best) out.push('account ' + accounts.decodedKey(t) + ' ' + accounts.b[t]);

  process.stdout.write(out.join('\n') + '\n');
}

main();
