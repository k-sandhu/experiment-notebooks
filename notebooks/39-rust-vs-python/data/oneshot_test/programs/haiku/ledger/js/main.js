'use strict';
const fs = require('fs');

const LIM = 4503599627370496; // 2^52
const data = fs.readFileSync(process.argv[2]);
const len = data.length;

let nl = data.indexOf(10);
if (nl < 0) nl = len;
const header = JSON.parse(data.toString('utf8', 0, nl).trim());
const rateMap = new Map();
for (const k of Object.keys(header.rates)) rateMap.set(k, Number(header.rates[k]));

// Scanner state shared by helpers
let strS = 0, strE = 0, strEsc = false;
let tagTest = false;
let mHas = false, mChS = 0, mChE = 0, mChEsc = false;

function decodeAt(s, e) {
  // s = index after opening quote, e = index of closing quote
  return JSON.parse(data.toString('utf8', s - 1, e + 1));
}

function strOf(s, e, esc) {
  return esc ? decodeAt(s, e) : data.toString('utf8', s, e);
}

function keyIs(s, e, esc, str) {
  if (esc) return decodeAt(s, e) === str;
  if (e - s !== str.length) return false;
  for (let i = 0; i < str.length; i++) {
    if (data[s + i] !== str.charCodeAt(i)) return false;
  }
  return true;
}

// p points at opening quote. Sets strS/strE/strEsc, returns index after closing quote.
function readStr(p) {
  const s = p + 1;
  let i = s;
  let esc = false;
  for (;;) {
    const c = data[i];
    if (c === 34) break;
    if (c === 92) { esc = true; i += 2; } else i++;
  }
  strS = s;
  strE = i;
  strEsc = esc;
  return i + 1;
}

// Skips any JSON value starting at p (no leading whitespace). Returns index after it.
function skipValue(p) {
  let depth = 0;
  for (;;) {
    const c = data[p];
    if (c === 34) {
      p = readStr(p);
      if (depth === 0) return p;
      continue;
    }
    if (c === 123 || c === 91) {
      depth++;
    } else if (c === 125 || c === 93) {
      if (depth === 0) return p;
      if (--depth === 0) return p + 1;
    } else if (depth === 0 && (c === 44 || c <= 32)) {
      return p;
    }
    p++;
  }
}

// Parses the tags value; sets tagTest if any string equals "test".
function parseTags(p) {
  if (data[p] !== 91) return skipValue(p);
  p++;
  for (;;) {
    while (data[p] <= 32) p++;
    const c = data[p];
    if (c === 93) return p + 1;
    if (c === 44) { p++; continue; }
    if (c === 34) {
      p = readStr(p);
      if (strEsc) {
        if (decodeAt(strS, strE) === 'test') tagTest = true;
      } else if (strE - strS === 4 && data[strS] === 116 && data[strS + 1] === 101 &&
                 data[strS + 2] === 115 && data[strS + 3] === 116) {
        tagTest = true;
      }
    } else {
      p = skipValue(p);
    }
  }
}

// Parses the meta object; captures its top-level "channel" string.
function parseMeta(p) {
  if (data[p] !== 123) return skipValue(p);
  p++;
  for (;;) {
    while (data[p] <= 32) p++;
    const c = data[p];
    if (c === 125) return p + 1;
    if (c === 44) { p++; continue; }
    p = readStr(p);
    const ks = strS, ke = strE, kesc = strEsc;
    while (data[p] <= 32) p++;
    p++; // ':'
    while (data[p] <= 32) p++;
    if (data[p] === 34 && keyIs(ks, ke, kesc, 'channel')) {
      p = readStr(p);
      mHas = true;
      mChS = strS;
      mChE = strE;
      mChEsc = strEsc;
    } else {
      p = skipValue(p);
    }
  }
}

function typeOf(s, e, esc) {
  if (esc) {
    switch (decodeAt(s, e)) {
      case 'credit': return 1;
      case 'debit': return 2;
      case 'refund': return 3;
      case 'void': return 4;
      default: return 0;
    }
  }
  switch (data[s]) {
    case 99: return 1;  // c
    case 100: return 2; // d
    case 114: return 3; // r
    case 118: return 4; // v
    default: return 0;
  }
}

// Exact slow path for large amounts, using BigInt.
function slowUsd(s, e, rate) {
  const str = data.toString('latin1', s, e);
  const dot = str.indexOf('.');
  const ip = dot < 0 ? str : str.slice(0, dot);
  const fp = dot < 0 ? '00' : (str.slice(dot + 1) + '00').slice(0, 2);
  const hb = BigInt(ip || '0') * 100n + BigInt(fp);
  return hb * BigInt(rate) / 1000000n;
}

const accMap = new Map();
const accNames = [];
const accNum = [];
const accBig = [];

const chMap = new Map();
const chNames = [];
const chCnt = [];
const chNum = [];
const chBig = [];

let counted = 0;
let totNum = 0;
let totBig = 0n;

let pos = nl + 1;
for (;;) {
  while (data[pos] <= 32) pos++;
  if (pos >= len) break;
  pos++; // '{'

  let typ = 0;
  let amS = 0, amE = 0;
  let curS = 0, curE = 0, curEsc = false;
  let accS = 0, accE = 0, accEsc = false;
  tagTest = false;
  mHas = false;

  for (;;) {
    while (data[pos] <= 32) pos++;
    const c = data[pos];
    if (c === 125) { pos++; break; }
    if (c === 44) { pos++; continue; }

    pos = readStr(pos);
    const ks = strS, ke = strE, kesc = strEsc;
    while (data[pos] <= 32) pos++;
    pos++; // ':'
    while (data[pos] <= 32) pos++;

    if (keyIs(ks, ke, kesc, 'account')) {
      pos = readStr(pos);
      accS = strS; accE = strE; accEsc = strEsc;
    } else if (keyIs(ks, ke, kesc, 'amount')) {
      pos = readStr(pos);
      amS = strS; amE = strE;
    } else if (keyIs(ks, ke, kesc, 'type')) {
      pos = readStr(pos);
      typ = typeOf(strS, strE, strEsc);
    } else if (keyIs(ks, ke, kesc, 'currency')) {
      pos = readStr(pos);
      curS = strS; curE = strE; curEsc = strEsc;
    } else if (keyIs(ks, ke, kesc, 'tags')) {
      pos = parseTags(pos);
    } else if (keyIs(ks, ke, kesc, 'meta')) {
      pos = parseMeta(pos);
    } else {
      pos = skipValue(pos);
    }
  }

  if (typ === 0 || typ === 4 || tagTest) continue;

  const neg = typ === 2;
  const rate = rateMap.get(strOf(curS, curE, curEsc));

  let u = -1;
  let ub = 0n;
  if (amE - amS <= 13) {
    let h = 0, i = amS;
    while (i < amE) {
      const d = data[i];
      if (d === 46) break;
      h = h * 10 + (d - 48);
      i++;
    }
    h *= 100;
    if (i < amE) {
      i++;
      let f = 0, k = 0;
      while (i < amE) {
        f = f * 10 + (data[i] - 48);
        i++;
        k++;
      }
      if (k === 1) f *= 10;
      h += f;
    }
    const p = h * rate;
    if (p <= LIM) u = (p - p % 1000000) / 1000000;
  }
  if (u < 0) ub = slowUsd(amS, amE, rate);

  const ch = mHas ? strOf(mChS, mChE, mChEsc) : '';
  let ci = chMap.get(ch);
  if (ci === undefined) {
    ci = chNames.length;
    chMap.set(ch, ci);
    chNames.push(ch);
    chCnt.push(0);
    chNum.push(0);
    chBig.push(0n);
  }

  const acc = strOf(accS, accE, accEsc);
  let ai = accMap.get(acc);
  if (ai === undefined) {
    ai = accNames.length;
    accMap.set(acc, ai);
    accNames.push(acc);
    accNum.push(0);
    accBig.push(0n);
  }

  counted++;
  chCnt[ci]++;

  if (u >= 0) {
    const v = neg ? -u : u;
    let t = totNum + v;
    if (t > LIM || t < -LIM) { totBig += BigInt(t); t = 0; }
    totNum = t;

    let x = chNum[ci] + v;
    if (x > LIM || x < -LIM) { chBig[ci] += BigInt(x); x = 0; }
    chNum[ci] = x;

    let y = accNum[ai] + v;
    if (y > LIM || y < -LIM) { accBig[ai] += BigInt(y); y = 0; }
    accNum[ai] = y;
  } else {
    const v = neg ? -ub : ub;
    totBig += v;
    chBig[ci] += v;
    accBig[ai] += v;
  }
}

// Output
const out = [];
out.push('counted ' + counted);
out.push('net ' + (totBig + BigInt(totNum)));

const chSorted = chNames.slice().sort();
for (const name of chSorted) {
  const i = chMap.get(name);
  out.push('channel ' + name + ' ' + chCnt[i] + ' ' + (chBig[i] + BigInt(chNum[i])));
}

// Top 10 accounts: sum desc, then ID asc
const N = accNames.length;
const topI = [];
const topV = [];
for (let i = 0; i < N; i++) {
  const v = accBig[i] + BigInt(accNum[i]);
  let j;
  if (topI.length < 10) {
    j = topI.length;
    topI.push(i);
    topV.push(v);
  } else {
    const w = topV[9];
    if (v < w || (v === w && accNames[i] >= accNames[topI[9]])) continue;
    j = 9;
  }
  while (j > 0) {
    const pv = topV[j - 1];
    if (v > pv || (v === pv && accNames[i] < accNames[topI[j - 1]])) {
      topI[j] = topI[j - 1];
      topV[j] = pv;
      j--;
    } else {
      break;
    }
  }
  topI[j] = i;
  topV[j] = v;
}
for (let k = 0; k < topI.length; k++) {
  out.push('account ' + accNames[topI[k]] + ' ' + topV[k]);
}

process.stdout.write(out.join('\n') + '\n');
