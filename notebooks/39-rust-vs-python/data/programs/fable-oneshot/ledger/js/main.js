'use strict';
const fs = require('fs');

const FNV = 0x811c9dc5 | 0;
const FNV_PRIME = 16777619;
const LIM = 4503599627370496; // 2^52
const B32 = 4294967296; // 2^32
const CHUNK = 1 << 20;

class Interner {
  constructor(bits) {
    const cap = 1 << bits;
    this.mask = cap - 1;
    this.table = new Int32Array(cap).fill(-1);
    this.count = 0;
    this.ecap = cap >> 1;
    this.hashes = new Int32Array(this.ecap);
    this.offs = new Int32Array(this.ecap);
    this.lens = new Int32Array(this.ecap);
    this.keys = Buffer.allocUnsafe(4096);
    this.keyUsed = 0;
  }
  find(buf, start, end, h) {
    const table = this.table, mask = this.mask, hashes = this.hashes, lens = this.lens;
    const len = end - start;
    let slot = (h ^ (h >>> 16)) & mask;
    for (;;) {
      const idx = table[slot];
      if (idx < 0) return ~slot;
      if (hashes[idx] === h && lens[idx] === len) {
        const keys = this.keys;
        let o = this.offs[idx], i = start;
        while (i < end && keys[o] === buf[i]) { i++; o++; }
        if (i === end) return idx;
      }
      slot = (slot + 1) & mask;
    }
  }
  get(buf, start, end, h) {
    const r = this.find(buf, start, end, h);
    if (r >= 0) return r;
    return this.add(buf, start, end, h, ~r);
  }
  add(buf, start, end, h, slot) {
    const len = end - start;
    const idx = this.count;
    if (idx === this.ecap) {
      const ne = this.ecap * 2;
      const nh = new Int32Array(ne); nh.set(this.hashes); this.hashes = nh;
      const no = new Int32Array(ne); no.set(this.offs); this.offs = no;
      const nl = new Int32Array(ne); nl.set(this.lens); this.lens = nl;
      this.ecap = ne;
    }
    if (this.keyUsed + len > this.keys.length) {
      let ns = this.keys.length * 2;
      if (ns < this.keyUsed + len) ns = this.keyUsed + len;
      const nk = Buffer.allocUnsafe(ns);
      this.keys.copy(nk, 0, 0, this.keyUsed);
      this.keys = nk;
    }
    const keys = this.keys;
    let o = this.keyUsed;
    this.offs[idx] = o;
    this.lens[idx] = len;
    this.hashes[idx] = h;
    for (let i = start; i < end; i++) keys[o++] = buf[i];
    this.keyUsed = o;
    this.table[slot] = idx;
    this.count = idx + 1;
    if (this.count * 2 > this.mask + 1) this.rehash();
    return idx;
  }
  rehash() {
    const cap = (this.mask + 1) * 2;
    const mask = cap - 1;
    const table = new Int32Array(cap).fill(-1);
    const hashes = this.hashes;
    const n = this.count;
    for (let i = 0; i < n; i++) {
      const h = hashes[i];
      let slot = (h ^ (h >>> 16)) & mask;
      while (table[slot] >= 0) slot = (slot + 1) & mask;
      table[slot] = i;
    }
    this.table = table;
    this.mask = mask;
  }
  name(i) {
    const o = this.offs[i];
    return this.keys.toString('utf8', o, o + this.lens[i]);
  }
}

const ACC = new Interner(16);
const CH = new Interner(6);
const CUR = new Interner(6);
let RATE_NUM = new Float64Array(0);
let RATE_BIG = [];

const S = {
  counted: 0,
  netLo: 0,
  netHi: 0,
  accLo: new Float64Array(1 << 15),
  accHi: new Float64Array(1 << 15),
  chCnt: new Float64Array(32),
  chLo: new Float64Array(32),
  chHi: new Float64Array(32),
};

function hashBytes(b) {
  let h = FNV;
  for (let i = 0; i < b.length; i++) h = Math.imul(h ^ b[i], FNV_PRIME);
  return h;
}

// Decode JSON string content (range excludes the quotes).
function decodeStr(buf, start, end) {
  const raw = buf.toString('utf8', start, end);
  try {
    const v = JSON.parse('"' + raw + '"');
    return typeof v === 'string' ? v : raw;
  } catch (e) {
    return raw;
  }
}

function slowKeyId(buf, start, end) {
  const s = decodeStr(buf, start, end);
  switch (s) {
    case 'type': return 1;
    case 'amount': return 2;
    case 'currency': return 3;
    case 'account': return 4;
    case 'tags': return 5;
    case 'meta': return 6;
    default: return 0;
  }
}

function slowType(buf, start, end) {
  const s = decodeStr(buf, start, end);
  switch (s) {
    case 'credit': return 1;
    case 'debit': return 2;
    case 'refund': return 3;
    case 'void': return 4;
    default: return 0;
  }
}

function slowFind(interner, buf, start, end) {
  const b = Buffer.from(decodeStr(buf, start, end), 'utf8');
  return interner.find(b, 0, b.length, hashBytes(b));
}

function slowGet(interner, buf, start, end) {
  const b = Buffer.from(decodeStr(buf, start, end), 'utf8');
  return interner.get(b, 0, b.length, hashBytes(b));
}

function parseAmountBig(s) {
  const m = /^(\d+)(?:\.(\d{0,2}))?/.exec(s.trim());
  if (!m) return 0n;
  const frac = (m[2] || '').padEnd(2, '0');
  return BigInt(m[1] + frac);
}

function bigUsd(buf, amtOk, amt, amtStart, amtEnd, cur) {
  if (cur < 0 || cur >= RATE_BIG.length) return 0n;
  let h;
  if (amtOk) h = BigInt(amt);
  else if (amtStart < 0) return 0n;
  else h = parseAmountBig(decodeStr(buf, amtStart + 1, amtEnd - 1));
  return (h * RATE_BIG[cur]) / 1000000n;
}

function skipValue(buf, pos) {
  let c = buf[pos];
  if (c === 34) {
    pos++;
    for (;;) {
      c = buf[pos];
      if (c === 34) break;
      if (c === 92) pos += 2; else pos++;
    }
    return pos + 1;
  }
  if (c === 123 || c === 91) {
    let depth = 1;
    pos++;
    for (;;) {
      c = buf[pos];
      if (c === 34) {
        pos++;
        for (;;) {
          c = buf[pos];
          if (c === 34) break;
          if (c === 92) pos += 2; else pos++;
        }
        pos++;
      } else if (c === 123 || c === 91) {
        depth++;
        pos++;
      } else if (c === 125 || c === 93) {
        pos++;
        if (--depth === 0) return pos;
      } else {
        pos++;
      }
    }
  }
  pos++;
  for (;;) {
    c = buf[pos];
    if (!(c > 32) || c === 44 || c === 125 || c === 93) return pos;
    pos++;
  }
}

function processChunk(buf, pos, limit) {
  const accounts = ACC, channels = CH, currencies = CUR, rateNum = RATE_NUM;
  const nRates = rateNum.length;
  let counted = S.counted, netLo = S.netLo, netHi = S.netHi;
  let accLo = S.accLo, accHi = S.accHi, accCap = accLo.length;
  let chCnt = S.chCnt, chLo = S.chLo, chHi = S.chHi, chCap = chLo.length;
  let c = 0, p = 0, esc = false, hsh = 0;

  while (pos < limit) {
    c = buf[pos];
    if (c !== 123) {
      if (c <= 32) { pos++; continue; }
      while (pos < limit && buf[pos] !== 10) pos++;
      pos++;
      continue;
    }
    pos++;
    let type = 0, isTest = false, amtOk = false, amt = 0, amtStart = -1, amtEnd = -1, cur = -1;
    let accStart = 0, accEnd = 0, accHash = FNV, accEsc = false;
    let chStart = 0, chEnd = 0, chHash = FNV, chEsc = false;

    top: for (;;) {
      c = buf[pos];
      while (c !== 34) {
        if (c === 125 || pos >= limit) break top;
        pos++;
        c = buf[pos];
      }
      const ks = pos + 1;
      p = ks;
      esc = false;
      for (;;) {
        c = buf[p];
        if (c === 34) break;
        if (c === 92) { esc = true; p += 2; } else p++;
      }
      const klen = p - ks;
      pos = p + 1;
      c = buf[pos];
      while (c !== 58) { pos++; c = buf[pos]; }
      pos++;
      c = buf[pos];
      while (c <= 32) { pos++; c = buf[pos]; }

      let kid = 0;
      if (esc) {
        kid = slowKeyId(buf, ks, p);
      } else if (klen === 4) {
        const k0 = buf[ks];
        if (k0 === 116) {
          const k1 = buf[ks + 1];
          if (k1 === 121) {
            if (buf[ks + 2] === 112 && buf[ks + 3] === 101) kid = 1;
          } else if (k1 === 97) {
            if (buf[ks + 2] === 103 && buf[ks + 3] === 115) kid = 5;
          }
        } else if (k0 === 109) {
          if (buf[ks + 1] === 101 && buf[ks + 2] === 116 && buf[ks + 3] === 97) kid = 6;
        }
      } else if (klen === 6) {
        if (buf[ks] === 97 && buf[ks + 1] === 109 && buf[ks + 2] === 111 &&
            buf[ks + 3] === 117 && buf[ks + 4] === 110 && buf[ks + 5] === 116) kid = 2;
      } else if (klen === 7) {
        if (buf[ks] === 97 && buf[ks + 1] === 99 && buf[ks + 2] === 99 &&
            buf[ks + 3] === 111 && buf[ks + 4] === 117 && buf[ks + 5] === 110 &&
            buf[ks + 6] === 116) kid = 4;
      } else if (klen === 8) {
        if (buf[ks] === 99 && buf[ks + 1] === 117 && buf[ks + 2] === 114 &&
            buf[ks + 3] === 114 && buf[ks + 4] === 101 && buf[ks + 5] === 110 &&
            buf[ks + 6] === 99 && buf[ks + 7] === 121) kid = 3;
      }

      switch (kid) {
        case 1: { // type
          if (c === 34) {
            const t0 = buf[pos + 1];
            if (t0 === 99 && buf[pos + 7] === 34) { type = 1; pos += 8; }
            else if (t0 === 100 && buf[pos + 6] === 34) { type = 2; pos += 7; }
            else if (t0 === 114 && buf[pos + 7] === 34) { type = 3; pos += 8; }
            else if (t0 === 118 && buf[pos + 5] === 34) { type = 4; pos += 6; }
            else {
              p = pos + 1;
              for (;;) {
                c = buf[p];
                if (c === 34) break;
                if (c === 92) p += 2; else p++;
              }
              type = slowType(buf, pos + 1, p);
              pos = p + 1;
            }
          } else {
            type = 0;
            pos = skipValue(buf, pos);
          }
          break;
        }
        case 2: { // amount
          amtOk = false;
          if (c === 34) {
            p = pos + 1;
            const ds = p;
            let h = 0;
            let d = buf[p] - 48;
            while (d >= 0 && d <= 9) {
              h = h * 10 + d;
              p++;
              d = buf[p] - 48;
            }
            const nd = p - ds;
            c = buf[p];
            if (c === 46) {
              p++;
              d = buf[p] - 48;
              if (d >= 0 && d <= 9) {
                p++;
                const d2 = buf[p] - 48;
                if (d2 >= 0 && d2 <= 9) {
                  h = h * 100 + d * 10 + d2;
                  p++;
                } else {
                  h = h * 100 + d * 10;
                }
              } else {
                h = h * 100;
              }
              c = buf[p];
            } else {
              h = h * 100;
            }
            if (c === 34 && nd > 0 && nd <= 13) {
              amtOk = true;
              amt = h;
              pos = p + 1;
            } else {
              amtStart = pos;
              pos = skipValue(buf, pos);
              amtEnd = pos;
            }
          } else {
            amtStart = -1;
            pos = skipValue(buf, pos);
          }
          break;
        }
        case 3: { // currency
          if (c === 34) {
            p = pos + 1;
            hsh = FNV;
            esc = false;
            for (;;) {
              c = buf[p];
              if (c === 34) break;
              if (c === 92) { esc = true; p += 2; }
              else { hsh = Math.imul(hsh ^ c, FNV_PRIME); p++; }
            }
            cur = esc ? slowFind(currencies, buf, pos + 1, p) : currencies.find(buf, pos + 1, p, hsh);
            pos = p + 1;
          } else {
            cur = -1;
            pos = skipValue(buf, pos);
          }
          break;
        }
        case 4: { // account
          if (c === 34) {
            p = pos + 1;
            hsh = FNV;
            esc = false;
            for (;;) {
              c = buf[p];
              if (c === 34) break;
              if (c === 92) { esc = true; p += 2; }
              else { hsh = Math.imul(hsh ^ c, FNV_PRIME); p++; }
            }
            accStart = pos + 1;
            accEnd = p;
            accHash = hsh;
            accEsc = esc;
            pos = p + 1;
          } else {
            pos = skipValue(buf, pos);
          }
          break;
        }
        case 5: { // tags
          isTest = false;
          if (c === 91) {
            pos++;
            for (;;) {
              c = buf[pos];
              if (c === 93) { pos++; break; }
              if (c === 34) {
                if (buf[pos + 1] === 116 && buf[pos + 2] === 101 && buf[pos + 3] === 115 &&
                    buf[pos + 4] === 116 && buf[pos + 5] === 34) {
                  isTest = true;
                  pos += 6;
                } else {
                  p = pos + 1;
                  esc = false;
                  for (;;) {
                    c = buf[p];
                    if (c === 34) break;
                    if (c === 92) { esc = true; p += 2; } else p++;
                  }
                  if (esc && decodeStr(buf, pos + 1, p) === 'test') isTest = true;
                  pos = p + 1;
                }
              } else if (c <= 32 || c === 44) {
                pos++;
              } else {
                pos = skipValue(buf, pos);
              }
            }
          } else {
            pos = skipValue(buf, pos);
          }
          break;
        }
        case 6: { // meta
          if (c === 123) {
            chStart = 0; chEnd = 0; chHash = FNV; chEsc = false;
            pos++;
            meta: for (;;) {
              c = buf[pos];
              while (c !== 34) {
                if (c === 125 || pos >= limit) break meta;
                pos++;
                c = buf[pos];
              }
              const mks = pos + 1;
              p = mks;
              esc = false;
              for (;;) {
                c = buf[p];
                if (c === 34) break;
                if (c === 92) { esc = true; p += 2; } else p++;
              }
              const mklen = p - mks;
              pos = p + 1;
              c = buf[pos];
              while (c !== 58) { pos++; c = buf[pos]; }
              pos++;
              c = buf[pos];
              while (c <= 32) { pos++; c = buf[pos]; }
              let isCh = false;
              if (esc) {
                isCh = decodeStr(buf, mks, p) === 'channel';
              } else {
                isCh = mklen === 7 && buf[mks] === 99 && buf[mks + 1] === 104 &&
                  buf[mks + 2] === 97 && buf[mks + 3] === 110 && buf[mks + 4] === 110 &&
                  buf[mks + 5] === 101 && buf[mks + 6] === 108;
              }
              if (c === 34) {
                p = pos + 1;
                if (isCh) {
                  hsh = FNV;
                  esc = false;
                  for (;;) {
                    c = buf[p];
                    if (c === 34) break;
                    if (c === 92) { esc = true; p += 2; }
                    else { hsh = Math.imul(hsh ^ c, FNV_PRIME); p++; }
                  }
                  chStart = pos + 1;
                  chEnd = p;
                  chHash = hsh;
                  chEsc = esc;
                } else {
                  for (;;) {
                    c = buf[p];
                    if (c === 34) break;
                    if (c === 92) p += 2; else p++;
                  }
                }
                pos = p + 1;
              } else {
                pos = skipValue(buf, pos);
              }
            }
            pos++;
          } else {
            pos = skipValue(buf, pos);
          }
          break;
        }
        default: {
          if (c === 34) {
            p = pos + 1;
            for (;;) {
              c = buf[p];
              if (c === 34) break;
              if (c === 92) p += 2; else p++;
            }
            pos = p + 1;
          } else {
            pos = skipValue(buf, pos);
          }
        }
      }
    }

    pos++;
    while (pos < limit && buf[pos] !== 10) pos++;
    pos++;

    if (type !== 0 && type !== 4 && !isTest) {
      const ai = accEsc ? slowGet(accounts, buf, accStart, accEnd)
                        : accounts.get(buf, accStart, accEnd, accHash);
      if (ai >= accCap) {
        while (ai >= accCap) accCap *= 2;
        const nl = new Float64Array(accCap); nl.set(accLo); accLo = nl;
        const nh = new Float64Array(accCap); nh.set(accHi); accHi = nh;
      }
      const ci = chEsc ? slowGet(channels, buf, chStart, chEnd)
                       : channels.get(buf, chStart, chEnd, chHash);
      if (ci >= chCap) {
        while (ci >= chCap) chCap *= 2;
        const nc = new Float64Array(chCap); nc.set(chCnt); chCnt = nc;
        const nl = new Float64Array(chCap); nl.set(chLo); chLo = nl;
        const nh = new Float64Array(chCap); nh.set(chHi); chHi = nh;
      }

      let v = 0;
      let needBig = true;
      if (amtOk) {
        const rate = (cur >= 0 && cur < nRates) ? rateNum[cur] : 0;
        const pr = amt * rate;
        if (pr < LIM) {
          let q = Math.floor(pr / 1000000);
          const r = pr - q * 1000000;
          if (r < 0) q--; else if (r >= 1000000) q++;
          v = q;
          needBig = false;
        }
      }
      if (needBig) {
        const ub = bigUsd(buf, amtOk, amt, amtStart, amtEnd, cur);
        if (ub < 4503599627370496n) {
          v = Number(ub);
        } else {
          let vh = Number(ub / 4294967296n);
          v = Number(ub % 4294967296n);
          if (type === 2) vh = -vh;
          netHi += vh;
          chHi[ci] += vh;
          accHi[ai] += vh;
        }
      }
      if (type === 2) v = -v;

      counted++;
      let s = netLo + v;
      if (s >= LIM || s <= -LIM) {
        const r = s % B32;
        netHi += (s - r) / B32;
        s = r;
      }
      netLo = s;

      chCnt[ci]++;
      s = chLo[ci] + v;
      if (s >= LIM || s <= -LIM) {
        const r = s % B32;
        chHi[ci] += (s - r) / B32;
        s = r;
      }
      chLo[ci] = s;

      s = accLo[ai] + v;
      if (s >= LIM || s <= -LIM) {
        const r = s % B32;
        accHi[ai] += (s - r) / B32;
        s = r;
      }
      accLo[ai] = s;
    }
  }

  S.counted = counted;
  S.netLo = netLo;
  S.netHi = netHi;
  S.accLo = accLo;
  S.accHi = accHi;
  S.chCnt = chCnt;
  S.chLo = chLo;
  S.chHi = chHi;
}

function parseRates(text) {
  if (text.length > 0 && text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  const srcs = new WeakMap();
  const obj = JSON.parse(text, function (k, v, ctx) {
    if (typeof v === 'number' && ctx !== undefined && ctx !== null && typeof ctx.source === 'string') {
      let m = srcs.get(this);
      if (!m) { m = new Map(); srcs.set(this, m); }
      m.set(k, ctx.source);
    }
    return v;
  });
  const rates = (obj && obj.rates) || {};
  const keys = Object.keys(rates);
  const nums = new Float64Array(keys.length);
  const bigs = new Array(keys.length);
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    const v = Number(rates[k]);
    let big;
    if (Number.isSafeInteger(v)) {
      big = BigInt(v);
    } else {
      const m = srcs.get(rates);
      const s = m ? m.get(k) : undefined;
      if (typeof s === 'string' && /^-?\d+$/.test(s)) big = BigInt(s);
      else if (Number.isFinite(v)) big = BigInt(Math.trunc(v));
      else big = 0n;
    }
    const b = Buffer.from(k, 'utf8');
    const idx = CUR.get(b, 0, b.length, hashBytes(b));
    nums[idx] = Number(big);
    bigs[idx] = big;
  }
  RATE_NUM = nums;
  RATE_BIG = bigs;
}

function val(hi, lo) {
  return hi === 0 ? lo : BigInt(hi) * 4294967296n + BigInt(lo);
}

function main() {
  const path = process.argv[2];
  const fd = fs.openSync(path, 'r');
  let buf = Buffer.allocUnsafe(CHUNK);
  let have = 0;
  let first = true;

  for (;;) {
    if (have === buf.length) {
      const nb = Buffer.allocUnsafe(buf.length * 2);
      buf.copy(nb, 0, 0, have);
      buf = nb;
    }
    const n = fs.readSync(fd, buf, have, buf.length - have, null);
    if (n <= 0) break;
    const end = have + n;
    const lastNl = buf.lastIndexOf(10, end - 1);
    if (lastNl < 0) {
      have = end;
      continue;
    }
    let pos = 0;
    if (first) {
      const nl = buf.indexOf(10);
      parseRates(buf.toString('utf8', 0, nl));
      pos = nl + 1;
      first = false;
    }
    processChunk(buf, pos, lastNl + 1);
    buf.copyWithin(0, lastNl + 1, end);
    have = end - lastNl - 1;
  }
  fs.closeSync(fd);

  if (have > 0) {
    if (have === buf.length) {
      const nb = Buffer.allocUnsafe(buf.length + 16);
      buf.copy(nb, 0, 0, have);
      buf = nb;
    }
    buf[have] = 10;
    let pos = 0;
    if (first) {
      const text = buf.toString('utf8', 0, have);
      if (text.trim().length > 0) parseRates(text);
      pos = have + 1;
      first = false;
    }
    if (pos < have + 1) processChunk(buf, pos, have + 1);
  }

  const lines = [];
  lines.push('counted ' + String(S.counted));
  lines.push('net ' + String(val(S.netHi, S.netLo)));

  const nch = CH.count;
  const chs = [];
  for (let i = 0; i < nch; i++) chs.push({ name: CH.name(i), i: i });
  chs.sort(function (a, b) { return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0); });
  for (let k = 0; k < chs.length; k++) {
    const i = chs[k].i;
    lines.push('channel ' + chs[k].name + ' ' + String(S.chCnt[i]) + ' ' + String(val(S.chHi[i], S.chLo[i])));
  }

  const nacc = ACC.count;
  const accLo = S.accLo, accHi = S.accHi;
  let anyBig = false;
  for (let i = 0; i < nacc; i++) {
    if (accHi[i] !== 0) { anyBig = true; break; }
  }
  let vals;
  if (anyBig) {
    vals = new Array(nacc);
    for (let i = 0; i < nacc; i++) vals[i] = BigInt(accHi[i]) * 4294967296n + BigInt(accLo[i]);
  } else {
    vals = accLo;
  }
  const better = function (i, j) {
    const a = vals[i], b = vals[j];
    if (a > b) return true;
    if (a < b) return false;
    return ACC.name(i) < ACC.name(j);
  };
  const top = [];
  for (let i = 0; i < nacc; i++) {
    if (top.length < 10) {
      top.push(i);
    } else if (better(i, top[9])) {
      top[9] = i;
    } else {
      continue;
    }
    let k = top.length - 1;
    while (k > 0 && better(top[k], top[k - 1])) {
      const t = top[k]; top[k] = top[k - 1]; top[k - 1] = t;
      k--;
    }
  }
  for (let k = 0; k < top.length; k++) {
    const i = top[k];
    lines.push('account ' + ACC.name(i) + ' ' + String(vals[i]));
  }

  process.stdout.write(lines.join('\n') + '\n');
}

main();
