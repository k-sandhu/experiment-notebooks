"use strict";

// Ledger: streams a JSON Lines file, parses only the fields it needs straight from bytes,
// and sums converted amounts per channel and per account with exact integer arithmetic.
// Values are plain Numbers while they are exact (|x| <= 2^53 - 1) and become BigInts only when they must.

const fs = require("fs");

const CHUNK = 1 << 22;
const SAFE = Number.MAX_SAFE_INTEGER;

const K_ACCOUNT = Buffer.from("account");
const K_TYPE = Buffer.from("type");
const K_CURRENCY = Buffer.from("currency");
const K_AMOUNT = Buffer.from("amount");
const K_TAGS = Buffer.from("tags");
const K_META = Buffer.from("meta");
const K_CHANNEL = Buffer.from("channel");
const K_RATES = Buffer.from("rates");
const V_TEST = Buffer.from("test");
const V_VOID = Buffer.from("void");
const V_DEBIT = Buffer.from("debit");

// Adds two exact integers, each a Number or a BigInt, keeping a Number while the result is safe.
function addAny(s, v) {
  if (typeof s === "number" && typeof v === "number") {
    const t = s + v;
    if (t <= SAFE && t >= -SAFE) return t;
  }
  return BigInt(s) + BigInt(v);
}

const SIMPLE_ESCAPES = { 98: "\b", 102: "\f", 110: "\n", 114: "\r", 116: "\t" };

// Decodes the JSON escapes in b[s, e) to a string. Surrogate pairs come out as two UTF-16 units, as JS wants.
function decodeEscapes(b, s, e) {
  let out = "";
  let start = s;
  for (let i = s; i < e; ) {
    if (b[i] !== 92) {
      i++;
      continue;
    }
    out += b.toString("utf8", start, i);
    const c = b[i + 1];
    i += 2;
    if (c === 117) {  // \uXXXX
      out += String.fromCharCode(parseInt(b.toString("latin1", i, i + 4), 16));
      i += 4;
    } else {
      out += SIMPLE_ESCAPES[c] ?? String.fromCharCode(c);  // \" \\ \/
    }
    start = i;
  }
  return out + b.toString("utf8", start, e);
}

function skipWs(b, p) {
  while (b[p] === 32 || b[p] === 9 || b[p] === 13 || b[p] === 10) p++;
  return p;
}

// Skips the ':' after a key, with whitespace around it.
function colon(b, p) {
  return skipWs(b, skipWs(b, p) + 1);
}

function skipString(b, p) {
  p++;
  while (b[p] !== 34) p += b[p] === 92 ? 2 : 1;
  return p + 1;
}

// Skips any JSON value starting at p and returns the position after it.
function skipValue(b, p) {
  if (b[p] === 34) return skipString(b, p);
  if (b[p] === 123 || b[p] === 91) {
    let depth = 0;
    for (;;) {
      const c = b[p];
      if (c === 34) {
        p = skipString(b, p);
        continue;
      }
      if (c === 123 || c === 91) depth++;
      else if (c === 125 || c === 93) {
        if (--depth === 0) return p + 1;
      }
      p++;
    }
  }
  while (b[p] !== 44 && b[p] !== 125 && b[p] !== 93 && b[p] !== 32 && b[p] !== 9 && b[p] !== 13 && b[p] !== 10) p++;
  return p;
}

// Maps string keys to dense slots, each holding a sum and a count.
class Index {
  constructor() {
    this.ids = new Map();
    this.keys = [];
    this.sums = [];
    this.counts = [];
  }

  find(k) {
    let i = this.ids.get(k);
    if (i === undefined) {
      i = this.keys.length;
      this.ids.set(k, i);
      this.keys.push(k);
      this.sums.push(0);
      this.counts.push(0);
    }
    return i;
  }
}

class Scan {
  constructor() {
    this.buf = null;
    this.haveRates = false;
    this.rates = new Map();
    this.counted = 0;
    this.net = 0;
    this.chan = new Index();
    this.acc = new Index();
    this.testFlag = false;
    this.metaChannel = null;
    // The last string read: raw bytes [s, e) of this.buf, or the decoded text when it had escapes.
    this.s = 0;
    this.e = 0;
    this.dec = null;
  }

  // p points at an opening quote. Sets the last-string fields and returns the position after the closing quote.
  readString(p) {
    const b = this.buf;
    let q = p + 1;
    let esc = false;
    while (b[q] !== 34) {
      if (b[q] === 92) {
        esc = true;
        q++;
      }
      q++;
    }
    this.s = p + 1;
    this.e = q;
    this.dec = esc ? decodeEscapes(b, p + 1, q) : null;
    return q + 1;
  }

  // Whether the last string read equals the literal, given as bytes and as text.
  is(bytes, text) {
    if (this.dec !== null) return this.dec === text;
    if (this.e - this.s !== bytes.length) return false;
    const b = this.buf;
    for (let i = 0; i < bytes.length; i++) if (b[this.s + i] !== bytes[i]) return false;
    return true;
  }

  text() {
    return this.dec !== null ? this.dec : this.buf.toString("utf8", this.s, this.e);
  }

  // Converts the last string (an amount such as "12", "12.5" or "12.05") to hundredths.
  hundredths() {
    let src = this.buf;
    let s = this.s;
    let e = this.e;
    if (this.dec !== null) {
      src = Buffer.from(this.dec, "utf8");
      s = 0;
      e = src.length;
    }
    if (e - s > 13) {  // too many digits for an exact Number
      const [ip, fp = ""] = src.toString("latin1", s, e).split(".");
      return BigInt(ip) * 100n + BigInt((fp + "00").slice(0, 2));
    }
    let v = 0;
    let i = s;
    for (; i < e && src[i] !== 46; i++) v = v * 10 + (src[i] - 48);
    v *= 100;
    if (i < e) {
      i++;
      let frac = 0;
      let digits = 0;
      for (; digits < 2 && i < e; i++, digits++) frac = frac * 10 + (src[i] - 48);
      if (digits === 1) frac *= 10;
      v += frac;
    }
    return v;
  }

  processLines(stop) {
    const b = this.buf;
    let p = 0;
    while (p < stop) {
      let e = b.indexOf(10, p);
      if (e === -1 || e > stop) e = stop;
      let q = p;
      while (q < e && (b[q] === 32 || b[q] === 9 || b[q] === 13)) q++;
      if (q < e) {
        if (this.haveRates) {
          this.parseTxn(q);
        } else {
          this.parseRates(q);
          this.haveRates = true;
        }
      }
      p = e + 1;
    }
  }

  parseRates(p) {
    const b = this.buf;
    p = skipWs(b, p + 1);  // '{'
    if (b[p] === 125) return;
    for (;;) {
      p = this.readString(skipWs(b, p));
      const isRates = this.is(K_RATES, "rates");
      p = colon(b, p);
      p = isRates ? this.parseRateObject(p) : skipValue(b, p);
      p = skipWs(b, p);
      if (b[p] === 125) return;
      p++;  // ','
    }
  }

  parseRateObject(p) {
    const b = this.buf;
    p = skipWs(b, p + 1);  // '{'
    if (b[p] === 125) return p + 1;
    for (;;) {
      p = this.readString(skipWs(b, p));
      const name = this.text();
      p = colon(b, p);
      const s = p;
      if (b[p] === 45) p++;  // '-'
      while (b[p] >= 48 && b[p] <= 57) p++;
      const digits = b.toString("latin1", s, p);
      const r = Number(digits);
      this.rates.set(name, Number.isSafeInteger(r) ? r : BigInt(digits));
      p = skipWs(b, p);
      if (b[p] === 125) return p + 1;
      p++;  // ','
    }
  }

  parseTxn(p) {
    const b = this.buf;
    let isVoid = false;
    let isDebit = false;
    let account = "";
    let channel = "";
    let currency = "";
    let amount = 0;
    this.testFlag = false;

    p = skipWs(b, p + 1);  // '{'
    if (b[p] === 125) return;
    for (;;) {
      p = this.readString(skipWs(b, p));
      p = colon(b, p);
      if (this.is(K_ACCOUNT, "account")) {
        p = this.readString(p);
        account = this.text();
      } else if (this.is(K_TYPE, "type")) {
        p = this.readString(p);
        isVoid = this.is(V_VOID, "void");
        isDebit = this.is(V_DEBIT, "debit");
      } else if (this.is(K_CURRENCY, "currency")) {
        p = this.readString(p);
        currency = this.text();
      } else if (this.is(K_AMOUNT, "amount")) {
        if (b[p] === 34) {
          p = this.readString(p);
        } else {
          const e = skipValue(b, p);
          this.s = p;
          this.e = e;
          this.dec = null;
          p = e;
        }
        amount = this.hundredths();
      } else if (this.is(K_TAGS, "tags")) {
        p = this.parseTags(p);
      } else if (this.is(K_META, "meta")) {
        p = this.parseMeta(p);
        if (this.metaChannel !== null) channel = this.metaChannel;
      } else {
        p = skipValue(b, p);
      }
      p = skipWs(b, p);
      if (b[p] === 125) break;
      p++;  // ','
    }

    if (isVoid || this.testFlag) return;
    const rate = this.rates.get(currency);
    if (rate === undefined) return;

    // usd = hundredths * rate / 1000000, rounded down. The product is exact when it is at most SAFE.
    let usd;
    const prod = typeof amount === "number" && typeof rate === "number" ? amount * rate : Infinity;
    if (prod <= SAFE) {
      const r = prod % 1000000;
      usd = (prod - r) / 1000000;
    } else {
      usd = (BigInt(amount) * BigInt(rate)) / 1000000n;
    }
    const value = isDebit ? -usd : usd;

    this.counted++;
    this.net = addAny(this.net, value);
    const c = this.chan.find(channel);
    this.chan.counts[c]++;
    this.chan.sums[c] = addAny(this.chan.sums[c], value);
    const a = this.acc.find(account);
    this.acc.sums[a] = addAny(this.acc.sums[a], value);
  }

  parseTags(p) {
    const b = this.buf;
    p = skipWs(b, p + 1);  // '['
    if (b[p] === 93) return p + 1;
    for (;;) {
      p = skipWs(b, p);
      if (b[p] === 34) {
        p = this.readString(p);
        if (this.is(V_TEST, "test")) this.testFlag = true;
      } else {
        p = skipValue(b, p);
      }
      p = skipWs(b, p);
      if (b[p] === 93) return p + 1;
      p++;  // ','
    }
  }

  // Stores the meta channel, if present, in this.metaChannel.
  parseMeta(p) {
    const b = this.buf;
    this.metaChannel = null;
    p = skipWs(b, p + 1);  // '{'
    if (b[p] === 125) return p + 1;
    for (;;) {
      p = this.readString(skipWs(b, p));
      p = colon(b, p);
      if (b[p] === 34 && this.is(K_CHANNEL, "channel")) {
        p = this.readString(p);
        this.metaChannel = this.text();
      } else {
        p = skipValue(b, p);
      }
      p = skipWs(b, p);
      if (b[p] === 125) return p + 1;
      p++;  // ','
    }
  }

  output() {
    const lines = [`counted ${this.counted}`, `net ${this.net}`];

    const ch = this.chan;
    const chanOrder = ch.keys.map((_, i) => i);
    chanOrder.sort((x, y) => (ch.keys[x] < ch.keys[y] ? -1 : ch.keys[x] > ch.keys[y] ? 1 : 0));
    for (const i of chanOrder) lines.push(`channel ${ch.keys[i]} ${ch.counts[i]} ${ch.sums[i]}`);

    // Mixed Number/BigInt comparisons with < and > are exact, so they are used instead of ===.
    const ac = this.acc;
    const accOrder = ac.keys.map((_, i) => i);
    accOrder.sort((x, y) => {
      if (ac.sums[x] > ac.sums[y]) return -1;
      if (ac.sums[x] < ac.sums[y]) return 1;
      return ac.keys[x] < ac.keys[y] ? -1 : ac.keys[x] > ac.keys[y] ? 1 : 0;
    });
    for (let k = 0; k < accOrder.length && k < 10; k++) {
      const i = accOrder[k];
      lines.push(`account ${ac.keys[i]} ${ac.sums[i]}`);
    }
    return lines.join("\n") + "\n";
  }
}

// Reads the whole file in chunks, feeding complete lines to the scanner.
function scanFile(fd, scan) {
  let buf = Buffer.allocUnsafe(CHUNK);
  let carry = 0;
  let pos = 0;
  for (;;) {
    if (carry === buf.length) {
      const bigger = Buffer.allocUnsafe(buf.length * 2);
      buf.copy(bigger, 0, 0, carry);
      buf = bigger;
    }
    const got = fs.readSync(fd, buf, carry, buf.length - carry, pos);
    pos += got;
    const end = carry + got;
    const eof = got === 0;
    let stop = end;
    if (!eof) stop = end === 0 ? 0 : buf.lastIndexOf(10, end - 1) + 1;
    scan.buf = buf;
    scan.processLines(stop);
    buf.copyWithin(0, stop, end);
    carry = end - stop;
    if (eof) return;
  }
}

function main() {
  const path = process.argv[2];
  if (path === undefined) {
    console.error("usage: node main.js INPUT_PATH");
    process.exit(2);
  }
  const fd = fs.openSync(path, "r");
  const scan = new Scan();
  try {
    scanFile(fd, scan);
  } finally {
    fs.closeSync(fd);
  }
  process.stdout.write(scan.output());
}

main();
