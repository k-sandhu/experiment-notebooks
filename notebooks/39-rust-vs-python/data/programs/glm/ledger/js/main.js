"use strict";

// Ledger: fast single-pass JSON Lines aggregator.
// Hand-rolled byte scanner over the whole input Buffer (no DOM), plain Maps.
const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const u8 = new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
const n = u8.length;
let i = 0;

let sStart = 0;
let sEnd = 0;
let sEsc = false;

// scratch for decoded strings
let decBuf = new Uint8Array(256);
let decLen = 0;
function decNeed(k) {
  if (decBuf.length < k) {
    let cap = decBuf.length * 2;
    while (cap < k) cap *= 2;
    const nb = new Uint8Array(cap);
    nb.set(decBuf.subarray(0, decLen));
    decBuf = nb;
  }
}

function decode(from, to) {
  decNeed(to - from);
  let o = 0;
  let j = from;
  while (j < to) {
    const c = u8[j];
    if (c !== 0x5c) {
      decBuf[o++] = c;
      j++;
      continue;
    }
    const e = u8[j + 1];
    j += 2;
    switch (e) {
      case 0x22: decBuf[o++] = 0x22; break;
      case 0x5c: decBuf[o++] = 0x5c; break;
      case 0x2f: decBuf[o++] = 0x2f; break;
      case 0x62: decBuf[o++] = 8; break;
      case 0x66: decBuf[o++] = 12; break;
      case 0x6e: decBuf[o++] = 10; break;
      case 0x72: decBuf[o++] = 13; break;
      case 0x74: decBuf[o++] = 9; break;
      case 0x75: {
        let cp = hex4(j);
        j += 4;
        if (cp >= 0xd800 && cp <= 0xdbff && j + 1 < to && u8[j] === 0x5c && u8[j + 1] === 0x75) {
          const lo = hex4(j + 2);
          if (lo >= 0xdc00 && lo <= 0xdfff) {
            cp = 0x10000 + ((cp - 0xd800) << 10) + (lo - 0xdc00);
            j += 6;
          }
        }
        // UTF-8 encode
        if (cp < 0x80) {
          decBuf[o++] = cp;
        } else if (cp < 0x800) {
          decBuf[o++] = 0xc0 | (cp >> 6);
          decBuf[o++] = 0x80 | (cp & 0x3f);
        } else if (cp < 0x10000) {
          decBuf[o++] = 0xe0 | (cp >> 12);
          decBuf[o++] = 0x80 | ((cp >> 6) & 0x3f);
          decBuf[o++] = 0x80 | (cp & 0x3f);
        } else {
          decBuf[o++] = 0xf0 | (cp >> 18);
          decBuf[o++] = 0x80 | ((cp >> 12) & 0x3f);
          decBuf[o++] = 0x80 | ((cp >> 6) & 0x3f);
          decBuf[o++] = 0x80 | (cp & 0x3f);
        }
        break;
      }
      default: decBuf[o++] = e; break;
    }
  }
  decLen = o;
  return o;
}

function hex4(at) {
  let v = 0;
  for (let k = 0; k < 4; k++) {
    const c = u8[at + k];
    v <<= 4;
    if (c <= 0x39) v += c - 0x30;
    else if (c <= 0x46) v += c - 0x41 + 10;
    else v += c - 0x61 + 10;
  }
  return v;
}

function decString(from, to) {
  const o = decode(from, to);
  return scratchString(decBuf, o);
}

// Fast string build from ASCII/Latin1 bytes
function scratchString(bytes, len) {
  let s = "";
  const chunk = 4096;
  for (let j = 0; j < len; j += chunk) {
    const end = Math.min(j + chunk, len);
    s += String.fromCharCode.apply(null, bytes.subarray(j, end));
  }
  return s;
}

function skipWs() {
  while (i < n) {
    const c = u8[i];
    if (c === 0x20 || c === 0x09 || c === 0x0d || c === 0x0a) i++;
    else break;
  }
}

function skipString() { // i at opening quote; leaves i past closing quote
  i++;
  while (true) {
    const c = u8[i];
    if (c === 0x5c) {
      i += 2; // hex digits after \u contain no '"' or '\\'
      continue;
    }
    if (c === 0x22) {
      i++;
      return;
    }
    i++;
  }
}

function scanString() { // i at opening quote; leaves i past closing quote
  i++;
  sStart = i;
  sEsc = false;
  while (true) {
    const c = u8[i];
    if (c === 0x5c) {
      sEsc = true;
      i += 2;
      continue;
    }
    if (c === 0x22) {
      sEnd = i;
      i++;
      return;
    }
    i++;
  }
}

function skipValue() {
  const c = u8[i];
  if (c === 0x22) {
    skipString();
    return;
  }
  if (c === 0x7b || c === 0x5b) {
    let depth = 0;
    while (i < n) {
      const d = u8[i];
      if (d === 0x22) {
        skipString();
        continue;
      }
      if (d === 0x7b || d === 0x5b) depth++;
      else if (d === 0x7d || d === 0x5d) {
        depth--;
        if (depth === 0) {
          i++;
          return;
        }
      }
      i++;
    }
    return;
  }
  while (i < n) {
    const d = u8[i];
    if (d === 0x2c || d === 0x7d || d === 0x5d || d === 0x20 || d === 0x09 || d === 0x0d || d === 0x0a) return;
    i++;
  }
}

function eqBytes(a, b, lit) {
  if (b - a !== lit.length) return false;
  for (let j = 0; j < lit.length; j++) {
    if (u8[a + j] !== lit.charCodeAt(j)) return false;
  }
  return true;
}

function decEq(lit) {
  const o = decode(sStart, sEnd);
  if (o !== lit.length) return false;
  for (let j = 0; j < o; j++) {
    if (decBuf[j] !== lit.charCodeAt(j)) return false;
  }
  return true;
}

// value string at sStart..sEnd (sEsc set)
function strValue() {
  if (!sEsc) return data.toString("latin1", sStart, sEnd);
  return decString(sStart, sEnd);
}

function parseAmount(from, to, esc) {
  if (esc) {
    const o = decode(from, to);
    return parseAmountDigits(decBuf, 0, o);
  }
  return parseAmountDigits(u8, from, to);
}

function parseAmountDigits(b, from, to) {
  let ip = 0;
  let j = from;
  while (j < to && b[j] >= 0x30 && b[j] <= 0x39) {
    if (ip > 900719925474098) return parseAmountBig(b, from, to); // next step would exceed 2^53
    ip = ip * 10 + (b[j] - 0x30);
    j++;
  }
  let frac = 0;
  let fd = 0;
  if (j < to && b[j] === 0x2e) {
    j++;
    while (j < to && fd < 2 && b[j] >= 0x30 && b[j] <= 0x39) {
      frac = frac * 10 + (b[j] - 0x30);
      fd++;
      j++;
    }
  }
  while (fd < 2) {
    frac *= 10;
    fd++;
  }
  return ip * 100 + frac;
}

function parseAmountBig(b, from, to) {
  let ip = 0n;
  let j = from;
  while (j < to && b[j] >= 0x30 && b[j] <= 0x39) {
    ip = ip * 10n + BigInt(b[j] - 0x30);
    j++;
  }
  let frac = 0n;
  let fd = 0;
  if (j < to && b[j] === 0x2e) {
    j++;
    while (j < to && fd < 2 && b[j] >= 0x30 && b[j] <= 0x39) {
      frac = frac * 10n + BigInt(b[j] - 0x30);
      fd++;
      j++;
    }
  }
  while (fd < 2) {
    frac *= 10n;
    fd++;
  }
  return ip * 100n + frac;
}

function parseTags() {
  i++; // '['
  let test = false;
  while (true) {
    skipWs();
    if (u8[i] === 0x5d) {
      i++;
      return test;
    }
    if (u8[i] === 0x22) {
      scanString();
      if (!test) {
        test = sEsc ? decEq("test") : sEnd - sStart === 4 && eqBytes(sStart, sEnd, "test");
      }
    } else {
      skipValue();
    }
    skipWs();
    if (u8[i] === 0x2c) i++;
  }
}

function parseMeta() {
  i++; // '{'
  let channel = null;
  while (true) {
    skipWs();
    if (u8[i] === 0x7d) {
      i++;
      return channel;
    }
    scanString();
    const ks = sStart, ke = sEnd, kesc = sEsc;
    skipWs();
    i++; // ':'
    skipWs();
    const isChannel = kesc ? decEq2(ks, ke, "channel") : ke - ks === 7 && eqBytes(ks, ke, "channel");
    if (isChannel) {
      scanString();
      channel = strValue();
    } else {
      skipValue();
    }
    skipWs();
    if (u8[i] === 0x2c) i++;
  }
}

function decEq2(from, to, lit) {
  const o = decode(from, to);
  if (o !== lit.length) return false;
  for (let j = 0; j < o; j++) {
    if (decBuf[j] !== lit.charCodeAt(j)) return false;
  }
  return true;
}

// ---- rates ----
const rates = new Map();
skipWs();
i++; // '{'
for (;;) {
  skipWs();
  scanString();
  const ks = sStart, ke = sEnd, kesc = sEsc;
  skipWs();
  i++; // ':'
  skipWs();
  if (!kesc && eqBytes(ks, ke, "rates")) {
    i++; // '{'
    for (;;) {
      skipWs();
      if (u8[i] === 0x7d) {
        i++;
        break;
      }
      scanString();
      const cur = strValue();
      skipWs();
      i++; // ':'
      skipWs();
      let r = 0;
      while (u8[i] >= 0x30 && u8[i] <= 0x39) {
        r = r * 10 + (u8[i] - 0x30);
        i++;
      }
      rates.set(cur, r);
      skipWs();
      if (u8[i] === 0x2c) i++;
    }
  } else {
    skipValue();
  }
  skipWs();
  if (u8[i] === 0x2c) {
    i++;
    continue;
  }
  i++;
  break;
}

// ---- transactions ----
let totalCount = 0;
let totalNet = 0;
const channels = new Map(); // name -> [count, net]
const accounts = new Map(); // id -> net

while (true) {
  skipWs();
  if (i >= n) break;
  i++; // '{'

  let typeCode = 0; // 1 credit, 2 debit, 3 refund, 4 void
  let testTag = false;
  let hund = 0;
  let currency = null;
  let account = null;
  let channel = null;

  for (;;) {
    skipWs();
    scanString();
    const ks = sStart, ke = sEnd, kesc = sEsc;
    const klen = ke - ks;
    skipWs();
    i++; // ':'
    skipWs();
    if (!kesc) {
      const c0 = klen > 0 ? u8[ks] : 0;
      if (klen === 4 && c0 === 0x74 && eqBytes(ks, ke, "type")) {
        scanString();
        // typeCode
        if (!sEsc) {
          const l = sEnd - sStart;
          if (l === 6 && eqBytes(sStart, sEnd, "credit")) typeCode = 1;
          else if (l === 5 && eqBytes(sStart, sEnd, "debit")) typeCode = 2;
          else if (l === 6 && eqBytes(sStart, sEnd, "refund")) typeCode = 3;
          else if (l === 4 && eqBytes(sStart, sEnd, "void")) typeCode = 4;
        } else {
          const t = decString(sStart, sEnd);
          typeCode = t === "credit" ? 1 : t === "debit" ? 2 : t === "refund" ? 3 : t === "void" ? 4 : 0;
        }
      } else if (klen === 6 && eqBytes(ks, ke, "amount")) {
        scanString();
        hund = parseAmount(sStart, sEnd, sEsc);
      } else if (klen === 8 && eqBytes(ks, ke, "currency")) {
        scanString();
        currency = strValue();
      } else if (klen === 7 && eqBytes(ks, ke, "account")) {
        scanString();
        account = strValue();
      } else if (klen === 4 && c0 === 0x74 && eqBytes(ks, ke, "tags")) {
        testTag = parseTags();
      } else if (klen === 4 && c0 === 0x6d && eqBytes(ks, ke, "meta")) {
        channel = parseMeta();
      } else {
        skipValue();
      }
    } else {
      const o = decode(ks, ke);
      // compare decoded key
      let k;
      if (o === 4 && decBuf[0] === 0x74 && decBuf[1] === 0x79 && decBuf[2] === 0x70 && decBuf[3] === 0x65) k = "type";
      else if (o === 6 && decBuf[0] === 0x61) k = "amount";
      else if (o === 8 && decBuf[0] === 0x63) k = "currency";
      else if (o === 7 && decBuf[0] === 0x61) k = "account";
      else if (o === 4 && decBuf[0] === 0x74) k = "tags";
      else if (o === 4 && decBuf[0] === 0x6d) k = "meta";
      else k = null;
      if (k === "type") {
        scanString();
        if (!sEsc) {
          const l = sEnd - sStart;
          if (l === 6 && eqBytes(sStart, sEnd, "credit")) typeCode = 1;
          else if (l === 5 && eqBytes(sStart, sEnd, "debit")) typeCode = 2;
          else if (l === 6 && eqBytes(sStart, sEnd, "refund")) typeCode = 3;
          else if (l === 4 && eqBytes(sStart, sEnd, "void")) typeCode = 4;
        } else {
          const t = decString(sStart, sEnd);
          typeCode = t === "credit" ? 1 : t === "debit" ? 2 : t === "refund" ? 3 : t === "void" ? 4 : 0;
        }
      } else if (k === "amount") {
        scanString();
        hund = parseAmount(sStart, sEnd, sEsc);
      } else if (k === "currency") {
        scanString();
        currency = strValue();
      } else if (k === "account") {
        scanString();
        account = strValue();
      } else if (k === "tags") {
        testTag = parseTags();
      } else if (k === "meta") {
        channel = parseMeta();
      } else {
        skipValue();
      }
    }
    skipWs();
    if (u8[i] === 0x2c) {
      i++;
      continue;
    }
    i++; // '}'
    break;
  }

  if (typeCode === 4 || testTag) continue;
  const rate = rates.get(currency);
  if (rate === undefined) continue;

  // exact integer math: products beyond 2^53 go through BigInt
  let usd;
  if (typeof hund === "bigint") {
    usd = Number((hund * BigInt(rate)) / 1000000n);
  } else if (hund <= 9007199254740991 / rate) {
    const prod = hund * rate;
    usd = (prod - (prod % 1000000)) / 1000000;
  } else {
    usd = Number((BigInt(hund) * BigInt(rate)) / 1000000n);
  }
  const v = typeCode === 2 ? -usd : usd;

  totalCount++;
  totalNet += v;

  const c = channels.get(channel);
  if (c === undefined) channels.set(channel, [1, v]);
  else {
    c[0]++;
    c[1] += v;
  }
  const a = accounts.get(account);
  accounts.set(account, a === undefined ? v : a + v);
}

// ---- output ----
const out = [];
out.push("counted " + totalCount);
out.push("net " + totalNet);

const chRows = Array.from(channels).sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
for (const [name, agg] of chRows) {
  out.push("channel " + name + " " + agg[0] + " " + agg[1]);
}

const accRows = Array.from(accounts, ([name, net]) => [name, net]);
accRows.sort((a, b) => (a[1] !== b[1] ? (b[1] - a[1]) : (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)));
const lim = Math.min(10, accRows.length);
for (let k = 0; k < lim; k++) {
  out.push("account " + accRows[k][0] + " " + accRows[k][1]);
}
out.push("");
process.stdout.write(out.join("\n"));
