'use strict';
const fs = require('fs');

class Interner {
  constructor() {
    this.cap = 1024;
    this.mask = this.cap - 1;
    this.tab = new Int32Array(this.cap);
    this.n = 0;
    this.off = new Int32Array(256);
    this.len = new Int32Array(256);
    this.hash = new Int32Array(256);
    this.store = Buffer.allocUnsafe(1 << 16);
    this.used = 0;
  }
  intern(src, s, e) {
    let h = 0x811c9dc5 | 0;
    for (let i = s; i < e; i++) h = Math.imul(h ^ src[i], 16777619);
    const len = e - s;
    const tab = this.tab, store = this.store, mask = this.mask;
    let slot = h & mask;
    for (;;) {
      const v = tab[slot];
      if (v === 0) break;
      const id = v - 1;
      if (this.hash[id] === h && this.len[id] === len) {
        const o = this.off[id];
        let i = 0;
        while (i < len && store[o + i] === src[s + i]) i++;
        if (i === len) return id;
      }
      slot = (slot + 1) & mask;
    }
    const id = this.n;
    if (id === this.off.length) {
      const m = id * 2;
      let t = new Int32Array(m); t.set(this.off); this.off = t;
      t = new Int32Array(m); t.set(this.len); this.len = t;
      t = new Int32Array(m); t.set(this.hash); this.hash = t;
    }
    if (this.used + len > this.store.length) {
      const ns = Buffer.allocUnsafe(Math.max(this.store.length * 2, this.used + len));
      this.store.copy(ns, 0, 0, this.used);
      this.store = ns;
    }
    src.copy(this.store, this.used, s, e);
    this.off[id] = this.used;
    this.len[id] = len;
    this.hash[id] = h;
    this.used += len;
    this.n = id + 1;
    tab[slot] = id + 1;
    if (this.n * 2 > this.cap) {
      const nc = this.cap * 2;
      const nt = new Int32Array(nc);
      const nm = nc - 1;
      for (let k = 0; k < this.n; k++) {
        let sl = this.hash[k] & nm;
        while (nt[sl] !== 0) sl = (sl + 1) & nm;
        nt[sl] = k + 1;
      }
      this.tab = nt; this.cap = nc; this.mask = nm;
    }
    return id;
  }
  name(i) {
    return this.store.subarray(this.off[i], this.off[i] + this.len[i]);
  }
}

const accI = new Interner();
const chI = new Interner();

let accLo = new Float64Array(1 << 16);
let chLo = new Float64Array(256);
let chCnt = new Float64Array(256);
const accHi = new Map();
const chHi = new Map();
let count = 0;
let totLo = 0;
let totHi = 0n;

const strMap = new Map();
const packedMap = new Map();
let ratesDone = false;

let b = null;
let p = 0;
let strS = 0, strE = 0, strEsc = false;

// per-transaction state
let acc = -1, typ = 0, hund = 0, amStr = null, rate = 0, chan = -1, isTest = false;

function decode(s, e) {
  return JSON.parse('"' + b.toString('utf8', s, e) + '"');
}

function scanStr() {
  let i = p + 1;
  let esc = false;
  for (;;) {
    const c = b[i];
    if (c === 34) break;
    if (c === 92) { esc = true; i += 2; } else i++;
  }
  strS = p + 1; strE = i; strEsc = esc; p = i + 1;
}

function skipValue() {
  const c = b[p];
  if (c === 34) { scanStr(); return; }
  if (c === 123 || c === 91) {
    let depth = 0;
    for (;;) {
      const ch = b[p];
      if (ch === 34) {
        p++;
        for (;;) {
          const d = b[p];
          if (d === 34) break;
          p += d === 92 ? 2 : 1;
        }
        p++;
      } else if (ch === 123 || ch === 91) { depth++; p++; }
      else if (ch === 125 || ch === 93) { depth--; p++; if (depth === 0) return; }
      else p++;
    }
  }
  for (;;) {
    const d = b[p];
    if (d === 44 || d === 125 || d === 93 || d === 32 || d === 10 || d === 13 || d === 9) return;
    p++;
  }
}

function keyId(ks, ke) {
  const n = ke - ks;
  const c = b[ks];
  switch (n) {
    case 7:
      return (c === 97 && b[ks + 1] === 99 && b[ks + 2] === 99 && b[ks + 3] === 111 &&
        b[ks + 4] === 117 && b[ks + 5] === 110 && b[ks + 6] === 116) ? 1 : 0;
    case 4:
      if (c === 116) {
        const d = b[ks + 1];
        if (d === 121 && b[ks + 2] === 112 && b[ks + 3] === 101) return 2;
        if (d === 97 && b[ks + 2] === 103 && b[ks + 3] === 115) return 5;
      } else if (c === 109 && b[ks + 1] === 101 && b[ks + 2] === 116 && b[ks + 3] === 97) return 6;
      return 0;
    case 6:
      return (c === 97 && b[ks + 1] === 109 && b[ks + 2] === 111 && b[ks + 3] === 117 &&
        b[ks + 4] === 110 && b[ks + 5] === 116) ? 3 : 0;
    case 8:
      return (c === 99 && b[ks + 1] === 117 && b[ks + 2] === 114 && b[ks + 3] === 114 &&
        b[ks + 4] === 101 && b[ks + 5] === 110 && b[ks + 6] === 99 && b[ks + 7] === 121) ? 4 : 0;
  }
  return 0;
}

function keyIdStr(s) {
  switch (s) {
    case 'account': return 1;
    case 'type': return 2;
    case 'amount': return 3;
    case 'currency': return 4;
    case 'tags': return 5;
    case 'meta': return 6;
  }
  return 0;
}

function typeCodeStr(s) {
  switch (s) {
    case 'credit': return 1;
    case 'debit': return 2;
    case 'refund': return 3;
    case 'void': return 4;
  }
  return 0;
}

function parseAmount(src, s, e) {
  let i = s, ip = 0;
  while (i < e) {
    const c = src[i];
    if (c === 46) break;
    ip = ip * 10 + (c - 48);
    i++;
  }
  const nd = i - s;
  if (nd > 13 || nd === 0) {
    hund = -1;
    amStr = src.toString('latin1', s, e);
    return;
  }
  let fr = 0;
  if (i < e) {
    i++;
    if (i < e) {
      fr = (src[i] - 48) * 10;
      i++;
      if (i < e) fr += src[i] - 48;
    }
  }
  hund = ip * 100 + fr;
}

function slowAmount(str, r) {
  const dot = str.indexOf('.');
  const ipS = dot < 0 ? str : str.slice(0, dot);
  let fs2 = dot < 0 ? '' : str.slice(dot + 1);
  fs2 = (fs2 + '00').slice(0, 2);
  const h = BigInt(ipS || '0') * 100n + BigInt(fs2);
  return h * BigInt(r) / 1000000n;
}

function lookupRate(src, s, e, esc) {
  if (!esc) {
    const n = e - s;
    if (n > 0 && n <= 3) {
      let key = 0;
      for (let i = s; i < e; i++) key = key * 256 + src[i];
      const r = packedMap.get(key);
      if (r !== undefined) return r;
    }
    const r2 = strMap.get(src.toString('utf8', s, e));
    return r2 === undefined ? 0 : r2;
  }
  const r3 = strMap.get(decode(s, e));
  return r3 === undefined ? 0 : r3;
}

function growAcc() {
  const n = new Float64Array(accLo.length * 2);
  n.set(accLo);
  accLo = n;
}
function growCh() {
  let n = new Float64Array(chLo.length * 2);
  n.set(chLo); chLo = n;
  n = new Float64Array(chCnt.length * 2);
  n.set(chCnt); chCnt = n;
}

function parseMeta() {
  p++;
  for (;;) {
    let c;
    while ((c = b[p]) === 32 || c === 10 || c === 13 || c === 9) p++;
    if (c === 125) { p++; return; }
    if (c === 44) { p++; continue; }
    scanStr();
    const ks = strS, ke = strE;
    let isChan;
    if (!strEsc) {
      isChan = (ke - ks === 7 && b[ks] === 99 && b[ks + 1] === 104 && b[ks + 2] === 97 &&
        b[ks + 3] === 110 && b[ks + 4] === 110 && b[ks + 5] === 101 && b[ks + 6] === 108);
    } else {
      isChan = decode(ks, ke) === 'channel';
    }
    while ((c = b[p]) !== 58) p++;
    p++;
    while ((c = b[p]) === 32 || c === 10 || c === 13 || c === 9) p++;
    if (isChan && c === 34) {
      scanStr();
      if (!strEsc) chan = chI.intern(b, strS, strE);
      else {
        const d = Buffer.from(decode(strS, strE), 'utf8');
        chan = chI.intern(d, 0, d.length);
      }
      if (chan >= chLo.length) growCh();
    } else skipValue();
  }
}

function parseTx() {
  p++;
  acc = -1; typ = 0; hund = 0; amStr = null; rate = 0; chan = -1; isTest = false;
  for (;;) {
    let c;
    while ((c = b[p]) === 32 || c === 10 || c === 13 || c === 9) p++;
    if (c === 125) { p++; break; }
    if (c === 44) { p++; continue; }
    scanStr();
    const kid = strEsc ? keyIdStr(decode(strS, strE)) : keyId(strS, strE);
    while ((c = b[p]) !== 58) p++;
    p++;
    while ((c = b[p]) === 32 || c === 10 || c === 13 || c === 9) p++;
    switch (kid) {
      case 1:
        if (c !== 34) { skipValue(); break; }
        scanStr();
        if (!strEsc) acc = accI.intern(b, strS, strE);
        else {
          const d = Buffer.from(decode(strS, strE), 'utf8');
          acc = accI.intern(d, 0, d.length);
        }
        if (acc >= accLo.length) growAcc();
        break;
      case 2:
        if (c !== 34) { skipValue(); break; }
        scanStr();
        if (!strEsc) {
          const n = strE - strS;
          const f = b[strS];
          if (n === 6) typ = f === 99 ? 1 : (f === 114 ? 3 : 0);
          else if (n === 5) typ = 2;
          else if (n === 4) typ = 4;
          else typ = 0;
        } else typ = typeCodeStr(decode(strS, strE));
        break;
      case 3:
        if (c !== 34) { skipValue(); break; }
        scanStr();
        if (!strEsc) parseAmount(b, strS, strE);
        else {
          const d = Buffer.from(decode(strS, strE), 'utf8');
          parseAmount(d, 0, d.length);
        }
        break;
      case 4:
        if (c !== 34) { skipValue(); break; }
        scanStr();
        rate = lookupRate(b, strS, strE, strEsc);
        break;
      case 5:
        if (c !== 91) { skipValue(); break; }
        p++;
        for (;;) {
          let d;
          while ((d = b[p]) === 32 || d === 10 || d === 13 || d === 9) p++;
          if (d === 93) { p++; break; }
          if (d === 44) { p++; continue; }
          if (d === 34) {
            scanStr();
            if (!strEsc) {
              if (strE - strS === 4 && b[strS] === 116 && b[strS + 1] === 101 &&
                b[strS + 2] === 115 && b[strS + 3] === 116) isTest = true;
            } else if (decode(strS, strE) === 'test') isTest = true;
          } else skipValue();
        }
        break;
      case 6:
        if (c !== 123) skipValue(); else parseMeta();
        break;
      default:
        skipValue();
    }
  }

  if (typ === 0 || typ === 4 || isTest || acc < 0 || chan < 0) return;

  let sv = 0, big = null;
  if (hund >= 0) {
    const pr = hund * rate;
    if (pr <= 9e15) {
      let q = Math.floor(pr / 1e6);
      const r = pr - q * 1e6;
      if (r < 0) q--; else if (r >= 1e6) q++;
      sv = typ === 2 ? -q : q;
    } else big = BigInt(hund) * BigInt(rate) / 1000000n;
  } else big = slowAmount(amStr, rate);

  count++;
  chCnt[chan]++;
  if (big !== null) {
    if (typ === 2) big = -big;
    totHi += big;
    accHi.set(acc, (accHi.get(acc) || 0n) + big);
    chHi.set(chan, (chHi.get(chan) || 0n) + big);
    return;
  }
  totLo += sv;
  if (totLo > 4e15 || totLo < -4e15) { totHi += BigInt(totLo); totLo = 0; }
  let x = accLo[acc] + sv;
  if (x > 4e15 || x < -4e15) { accHi.set(acc, (accHi.get(acc) || 0n) + BigInt(x)); x = 0; }
  accLo[acc] = x;
  x = chLo[chan] + sv;
  if (x > 4e15 || x < -4e15) { chHi.set(chan, (chHi.get(chan) || 0n) + BigInt(x)); x = 0; }
  chLo[chan] = x;
}

function processRange(buf, start, end) {
  b = buf;
  if (!ratesDone) {
    let e = buf.indexOf(10, start);
    if (e < 0 || e >= end) e = end;
    let line = buf.toString('utf8', start, e);
    if (line.charCodeAt(0) === 0xFEFF) line = line.slice(1);
    const rates = JSON.parse(line).rates;
    for (const k of Object.keys(rates)) {
      const v = Number(rates[k]);
      strMap.set(k, v);
      if (k.length >= 1 && k.length <= 3) {
        let ok = true, key = 0;
        for (let i = 0; i < k.length; i++) {
          const cc = k.charCodeAt(i);
          if (cc >= 128) { ok = false; break; }
          key = key * 256 + cc;
        }
        if (ok) packedMap.set(key, v);
      }
    }
    ratesDone = true;
    start = e + 1;
  }
  p = start;
  for (;;) {
    let c;
    while (p < end && ((c = b[p]) === 10 || c === 13 || c === 32 || c === 9)) p++;
    if (p >= end) break;
    parseTx();
  }
}

function main() {
  const fd = fs.openSync(process.argv[2], 'r');
  let cap = 1 << 22;
  let buf = Buffer.allocUnsafe(cap);
  let len = 0;
  for (;;) {
    const n = fs.readSync(fd, buf, len, cap - len, null);
    if (n === 0) {
      if (len > 0) processRange(buf, 0, len);
      break;
    }
    len += n;
    const nl = buf.lastIndexOf(10, len - 1);
    if (nl < 0) {
      if (len === cap) {
        cap *= 2;
        const nb = Buffer.allocUnsafe(cap);
        buf.copy(nb, 0, 0, len);
        buf = nb;
      }
      continue;
    }
    processRange(buf, 0, nl + 1);
    buf.copyWithin(0, nl + 1, len);
    len -= nl + 1;
  }
  fs.closeSync(fd);

  const out = [];
  out.push('counted ' + count);
  out.push('net ' + String(BigInt(totLo) + totHi));

  // channels
  const nch = chI.n;
  const cids = [];
  for (let i = 0; i < nch; i++) cids.push(i);
  cids.sort((x, y) => Buffer.compare(chI.name(x), chI.name(y)));
  for (const i of cids) {
    const net = BigInt(chLo[i]) + (chHi.get(i) || 0n);
    out.push('channel ' + chI.name(i).toString('utf8') + ' ' + chCnt[i] + ' ' + String(net));
  }

  // accounts
  const nacc = accI.n;
  let vals;
  if (accHi.size === 0) vals = accLo;
  else {
    vals = new Array(nacc);
    for (let i = 0; i < nacc; i++) vals[i] = BigInt(accLo[i]) + (accHi.get(i) || 0n);
  }
  const better = (i, j) => {
    const a = vals[i], c = vals[j];
    if (a > c) return true;
    if (a < c) return false;
    return Buffer.compare(accI.name(i), accI.name(j)) < 0;
  };
  const tops = [];
  for (let i = 0; i < nacc; i++) {
    if (tops.length === 10) {
      if (!better(i, tops[9])) continue;
      tops.pop();
    }
    let k = tops.length;
    tops.push(i);
    while (k > 0 && better(i, tops[k - 1])) { tops[k] = tops[k - 1]; k--; }
    tops[k] = i;
  }
  for (const i of tops) {
    const net = BigInt(accLo[i]) + (accHi.get(i) || 0n);
    out.push('account ' + accI.name(i).toString('utf8') + ' ' + String(net));
  }
  process.stdout.write(out.join('\n') + '\n');
}

main();
