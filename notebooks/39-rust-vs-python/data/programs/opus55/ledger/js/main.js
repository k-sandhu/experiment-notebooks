"use strict";
// Ledger: streaming JSON Lines scanner with exact integer currency conversion.

const fs = require("fs");

const QUOTE = 0x22, BACKSLASH = 0x5c, COMMA = 0x2c, COLON = 0x3a;
const LBRACE = 0x7b, RBRACE = 0x7d, LBRACKET = 0x5b, RBRACKET = 0x5d, DOT = 0x2e, MINUS = 0x2d;

const WS = new Uint8Array(256);
WS[0x20] = WS[0x09] = WS[0x0a] = WS[0x0d] = 1;
// Bytes that matter while skipping a nested container.
const STRUCT = new Uint8Array(256);
STRUCT[QUOTE] = STRUCT[LBRACE] = STRUCT[RBRACE] = STRUCT[LBRACKET] = STRUCT[RBRACKET] = 1;
// Bytes that end a scalar (number, true, false, null).
const SCALAR_END = new Uint8Array(256);
SCALAR_END[COMMA] = SCALAR_END[RBRACE] = SCALAR_END[RBRACKET] = 1;
SCALAR_END[0x20] = SCALAR_END[0x09] = SCALAR_END[0x0a] = SCALAR_END[0x0d] = 1;

const lit = (s) => Buffer.from(s, "latin1");
const L_TYPE = lit("type"), L_TAGS = lit("tags"), L_META = lit("meta"), L_AMOUNT = lit("amount");
const L_ACCOUNT = lit("account"), L_CURRENCY = lit("currency"), L_CHANNEL = lit("channel"), L_RATES = lit("rates");
const L_CREDIT = lit("credit"), L_REFUND = lit("refund"), L_DEBIT = lit("debit"), L_TEST = lit("test");

/** Open-addressing table interning byte strings to dense indices, with per-entry totals. */
class Interner {
  constructor() {
    this.mask = 1023;
    this.slots = new Int32Array(1024); // index + 1, 0 = empty
    this.slotHash = new Int32Array(1024);
    this.keys = [];
    this.sum = [];
    this.count = [];
  }

  static hash(b, off, len) {
    let h = 0x811c9dc5 ^ len;
    for (let i = 0; i < len; i++) h = Math.imul(h ^ b[off + i], 0x01000193);
    return (h ^ (h >>> 15)) | 0;
  }

  static same(k, b, off, len) {
    if (k.length !== len) return false;
    for (let i = 0; i < len; i++) if (k[i] !== b[off + i]) return false;
    return true;
  }

  find(b, off, len) {
    const h = Interner.hash(b, off, len);
    const slots = this.slots, mask = this.mask;
    for (let i = h & mask; ; i = (i + 1) & mask) {
      const s = slots[i];
      if (s === 0) return -1;
      if (this.slotHash[i] === h && Interner.same(this.keys[s - 1], b, off, len)) return s - 1;
    }
  }

  intern(b, off, len) {
    const h = Interner.hash(b, off, len);
    const slots = this.slots, mask = this.mask;
    for (let i = h & mask; ; i = (i + 1) & mask) {
      const s = slots[i];
      if (s === 0) {
        this.keys.push(Uint8Array.prototype.slice.call(b, off, off + len));
        this.sum.push(0);
        this.count.push(0);
        const size = this.keys.length;
        slots[i] = size;
        this.slotHash[i] = h;
        if (size * 2 > slots.length) this.grow();
        return size - 1;
      }
      if (this.slotHash[i] === h && Interner.same(this.keys[s - 1], b, off, len)) return s - 1;
    }
  }

  grow() {
    const os = this.slots, oh = this.slotHash;
    this.slots = new Int32Array(os.length * 2);
    this.slotHash = new Int32Array(os.length * 2);
    const mask = (this.mask = this.slots.length - 1);
    for (let j = 0; j < os.length; j++) {
      if (os[j] === 0) continue;
      let i = oh[j] & mask;
      while (this.slots[i] !== 0) i = (i + 1) & mask;
      this.slots[i] = os[j];
      this.slotHash[i] = oh[j];
    }
  }
}

const currencies = new Interner();
const rates = []; // BigInt rate per currency index
const channels = new Interner();
const accounts = new Interner();
let counted = 0;
let net = 0n;
// Totals are kept as Numbers while exact (|x| < 2^53) and switch to BigInt otherwise.
const SAFE = Number.MAX_SAFE_INTEGER;

let buf = null;

// Result of the last parseStr: bytes [strOff, strOff + strLen) of strBuf.
let strBuf = null, strOff = 0, strLen = 0;

// Scratch buffers for strings with escapes, one per field that must survive until the object ends.
const K_KEY = 0, K_ACC = 1, K_CHAN = 2, K_TYPE = 3, K_AMT = 4, K_CUR = 5, K_TAG = 6;
const scratch = [];
for (let k = 0; k < 7; k++) scratch.push(new Uint8Array(256));

function skipWs(i) {
  const b = buf;
  while (WS[b[i]] === 1) i++;
  return i;
}

function hexVal(c) {
  return c <= 0x39 ? c - 0x30 : (c | 0x20) - 0x61 + 10;
}

function hex4(b, i) {
  return (hexVal(b[i]) << 12) | (hexVal(b[i + 1]) << 8) | (hexVal(b[i + 2]) << 4) | hexVal(b[i + 3]);
}

/** Parses the string whose opening quote is at i; result in strBuf/strOff/strLen. */
function parseStr(i, slot) {
  const b = buf;
  const start = ++i;
  for (;;) {
    const c = b[i];
    if (c === QUOTE) {
      strBuf = b;
      strOff = start;
      strLen = i - start;
      return i + 1;
    }
    if (c === BACKSLASH) return decodeStr(start, i, slot);
    i++;
  }
}

function decodeStr(start, i, slot) {
  const b = buf;
  let out = scratch[slot];
  let n = i - start;
  if (out.length < n + 16) out = new Uint8Array((n + 16) * 2);
  out.set(b.subarray(start, i), 0);
  for (;;) {
    if (out.length < n + 8) {
      const o2 = new Uint8Array(out.length * 2);
      o2.set(out);
      out = o2;
    }
    const c = b[i];
    if (c === QUOTE) break;
    if (c !== BACKSLASH) {
      out[n++] = c;
      i++;
      continue;
    }
    const e = b[i + 1];
    i += 2;
    switch (e) {
      case 0x6e: out[n++] = 0x0a; break; // n
      case 0x74: out[n++] = 0x09; break; // t
      case 0x72: out[n++] = 0x0d; break; // r
      case 0x62: out[n++] = 0x08; break; // b
      case 0x66: out[n++] = 0x0c; break; // f
      case 0x75: { // u
        let cp = hex4(b, i);
        i += 4;
        if (cp >= 0xd800 && cp < 0xdc00 && b[i] === BACKSLASH && b[i + 1] === 0x75) {
          const lo = hex4(b, i + 2);
          if (lo >= 0xdc00 && lo < 0xe000) {
            cp = 0x10000 + ((cp - 0xd800) << 10) + (lo - 0xdc00);
            i += 6;
          }
        }
        if (cp < 0x80) {
          out[n++] = cp;
        } else if (cp < 0x800) {
          out[n++] = 0xc0 | (cp >> 6);
          out[n++] = 0x80 | (cp & 0x3f);
        } else if (cp < 0x10000) {
          out[n++] = 0xe0 | (cp >> 12);
          out[n++] = 0x80 | ((cp >> 6) & 0x3f);
          out[n++] = 0x80 | (cp & 0x3f);
        } else {
          out[n++] = 0xf0 | (cp >> 18);
          out[n++] = 0x80 | ((cp >> 12) & 0x3f);
          out[n++] = 0x80 | ((cp >> 6) & 0x3f);
          out[n++] = 0x80 | (cp & 0x3f);
        }
        break;
      }
      default: out[n++] = e; // \" \\ \/
    }
  }
  scratch[slot] = out;
  strBuf = out;
  strOff = 0;
  strLen = n;
  return i + 1;
}

function skipStrBody(i) {
  const b = buf;
  for (;;) {
    const c = b[i];
    if (c === QUOTE) return i + 1;
    i += c === BACKSLASH ? 2 : 1;
  }
}

function skipContainer(i) {
  const b = buf;
  let depth = 1;
  i++;
  for (;;) {
    while (STRUCT[b[i]] === 0) i++;
    const c = b[i++];
    if (c === QUOTE) {
      i = skipStrBody(i);
    } else if (c === LBRACE || c === LBRACKET) {
      depth++;
    } else if (--depth === 0) {
      return i;
    }
  }
}

function skipVal(i) {
  const b = buf;
  const c = b[i];
  if (c === QUOTE) return skipStrBody(i + 1);
  if (c === LBRACE || c === LBRACKET) return skipContainer(i);
  while (SCALAR_END[b[i]] === 0) i++;
  return i;
}

/** True if the last parsed string equals the literal bytes. */
function strIs(l) {
  const n = l.length;
  if (strLen !== n) return false;
  const s = strBuf, o = strOff;
  for (let k = 0; k < n; k++) if (s[o + k] !== l[k]) return false;
  return true;
}

function parseRates(i) {
  const b = buf;
  i = skipWs(i + 1);
  if (b[i] === RBRACE) return i + 1;
  for (;;) {
    i = parseStr(i, K_KEY);
    const isRates = strIs(L_RATES);
    i = skipWs(skipWs(i) + 1);
    if (isRates && b[i] === LBRACE) {
      i = skipWs(i + 1);
      if (b[i] !== RBRACE) {
        for (;;) {
          i = parseStr(i, K_CUR);
          const id = currencies.intern(strBuf, strOff, strLen);
          i = skipWs(skipWs(i) + 1);
          let neg = false;
          if (b[i] === MINUS) {
            neg = true;
            i++;
          }
          let v = 0n;
          while (b[i] >= 0x30 && b[i] <= 0x39) v = v * 10n + BigInt(b[i++] - 0x30);
          i = skipVal(i);
          rates[id] = neg ? -v : v;
          i = skipWs(i);
          if (b[i] === COMMA) {
            i = skipWs(i + 1);
            continue;
          }
          break;
        }
      }
      i++;
    } else {
      i = skipVal(i);
    }
    i = skipWs(i);
    if (b[i] === COMMA) {
      i = skipWs(i + 1);
      continue;
    }
    return i + 1;
  }
}

// Number-or-BigInt addition that stays exact.
function addExact(a, v) {
  if (typeof a === "number") {
    const r = a + v;
    if (r <= SAFE && r >= -SAFE) return r;
    return BigInt(a) + BigInt(v);
  }
  return a + BigInt(v);
}

function parseTx(i) {
  const b = buf;
  let accB = null, chanB = null, curB = null, amtB = null;
  let accO = 0, accL = 0, chanO = 0, chanL = 0, curO = 0, curL = 0, amtO = 0, amtL = 0;
  let sign = 0;
  let test = false;

  i = skipWs(i + 1);
  if (b[i] === RBRACE) return i + 1;
  for (;;) {
    i = parseStr(i, K_KEY);
    const kl = strLen;
    let kind = 0; // 1 type, 2 tags, 3 meta, 4 amount, 5 account, 6 currency
    if (kl === 4) {
      if (strIs(L_TYPE)) kind = 1;
      else if (strIs(L_TAGS)) kind = 2;
      else if (strIs(L_META)) kind = 3;
    } else if (kl === 6) {
      if (strIs(L_AMOUNT)) kind = 4;
    } else if (kl === 7) {
      if (strIs(L_ACCOUNT)) kind = 5;
    } else if (kl === 8) {
      if (strIs(L_CURRENCY)) kind = 6;
    }
    i = skipWs(skipWs(i) + 1);
    switch (kind) {
      case 1:
        i = parseStr(i, K_TYPE);
        if (strIs(L_CREDIT) || strIs(L_REFUND)) sign = 1;
        else if (strIs(L_DEBIT)) sign = -1;
        else sign = 0;
        break;
      case 2:
        i = skipWs(i + 1);
        if (b[i] !== RBRACKET) {
          for (;;) {
            if (b[i] === QUOTE) {
              i = parseStr(i, K_TAG);
              if (strIs(L_TEST)) test = true;
            } else {
              i = skipVal(i);
            }
            i = skipWs(i);
            if (b[i] === COMMA) {
              i = skipWs(i + 1);
              continue;
            }
            break;
          }
        }
        i++;
        break;
      case 3:
        i = skipWs(i + 1);
        if (b[i] !== RBRACE) {
          for (;;) {
            i = parseStr(i, K_KEY);
            const isChan = strIs(L_CHANNEL);
            i = skipWs(skipWs(i) + 1);
            if (isChan && b[i] === QUOTE) {
              i = parseStr(i, K_CHAN);
              chanB = strBuf;
              chanO = strOff;
              chanL = strLen;
            } else {
              i = skipVal(i);
            }
            i = skipWs(i);
            if (b[i] === COMMA) {
              i = skipWs(i + 1);
              continue;
            }
            break;
          }
        }
        i++;
        break;
      case 4:
        i = parseStr(i, K_AMT);
        amtB = strBuf;
        amtO = strOff;
        amtL = strLen;
        break;
      case 5:
        i = parseStr(i, K_ACC);
        accB = strBuf;
        accO = strOff;
        accL = strLen;
        break;
      case 6:
        i = parseStr(i, K_CUR);
        curB = strBuf;
        curO = strOff;
        curL = strLen;
        break;
      default:
        i = skipVal(i);
    }
    i = skipWs(i);
    if (b[i] === COMMA) {
      i = skipWs(i + 1);
      continue;
    }
    i++;
    break;
  }

  if (sign === 0 || test) return i;

  // Integer part as a Number while exact; fall back to BigInt for very long amounts.
  let k = 0;
  let ip = 0;
  while (k < amtL && amtB[amtO + k] !== DOT) ip = ip * 10 + (amtB[amtO + k++] - 0x30);
  let frac = 0;
  if (k < amtL) {
    k++;
    if (k < amtL) frac += (amtB[amtO + k] - 0x30) * 10;
    if (k + 1 < amtL) frac += amtB[amtO + k + 1] - 0x30;
  }
  const cid = currencies.find(curB, curO, curL);
  const rate = cid < 0 ? 0n : rates[cid];
  let v;
  const rn = Number(rate);
  const hund = ip * 100 + frac;
  if (ip <= 9e13 && hund * rn <= SAFE) {
    // Exact in doubles: product below 2^53, floor of an exact non-negative quotient.
    v = Math.floor((hund * rn) / 1000000);
    // Guard against rounding of the division right below an integer boundary.
    if ((v + 1) * 1000000 <= hund * rn) v++;
    else if (v * 1000000 > hund * rn) v--;
  } else {
    let hb = 0n;
    for (let j = 0; j < amtL && amtB[amtO + j] !== DOT; j++) hb = hb * 10n + BigInt(amtB[amtO + j] - 0x30);
    const q = ((hb * 100n + BigInt(frac)) * rate) / 1000000n;
    v = q <= BigInt(SAFE) ? Number(q) : q;
  }
  if (sign < 0) v = -v;

  counted++;
  const ch = channels.intern(chanB, chanO, chanL);
  const ac = accounts.intern(accB, accO, accL);
  netAdd(v);
  channels.count[ch]++;
  channels.sum[ch] = typeof v === "number" ? addExact(channels.sum[ch], v) : toBig(channels.sum[ch]) + v;
  accounts.sum[ac] = typeof v === "number" ? addExact(accounts.sum[ac], v) : toBig(accounts.sum[ac]) + v;
  return i;
}

function toBig(x) {
  return typeof x === "bigint" ? x : BigInt(x);
}

let netNum = 0;
function netAdd(v) {
  if (typeof v === "number") {
    const r = netNum + v;
    if (r <= SAFE && r >= -SAFE) {
      netNum = r;
      return;
    }
    net += BigInt(netNum) + BigInt(v);
    netNum = 0;
    return;
  }
  net += v;
}

/** Parses all complete objects in buf[0, lim); buf[lim] holds a 0 sentinel. */
function processChunk(lim, first) {
  let i = 0;
  for (;;) {
    i = skipWs(i);
    if (i >= lim) return first;
    if (first) {
      i = parseRates(i);
      first = false;
    } else {
      i = parseTx(i);
    }
  }
}

function compareBytes(a, b) {
  return Buffer.compare(a, b);
}

function main() {
  const path = process.argv[2];
  const fd = fs.openSync(path, "r");
  const slack = 64;
  let capacity = 8 << 20;
  buf = Buffer.allocUnsafe(capacity + slack);
  let n = 0;
  let first = true;
  for (;;) {
    if (n === capacity) {
      const nb = Buffer.allocUnsafe(capacity * 2 + slack);
      buf.copy(nb, 0, 0, n);
      buf = nb;
      capacity *= 2;
    }
    const got = fs.readSync(fd, buf, n, capacity - n, null);
    const eof = got === 0;
    n += got;
    let lim;
    if (eof) {
      if (n === 0) break;
      if (buf[n - 1] !== 0x0a) buf[n++] = 0x0a;
      lim = n;
    } else {
      lim = buf.lastIndexOf(0x0a, n - 1) + 1;
      if (lim === 0) continue;
    }
    const saved = buf[lim];
    buf[lim] = 0; // sentinel stops whitespace skipping
    first = processChunk(lim, first);
    buf[lim] = saved;
    buf.copy(buf, 0, lim, n);
    n -= lim;
    if (eof) break;
  }
  fs.closeSync(fd);

  const lines = [];
  lines.push("counted " + counted);
  lines.push("net " + (net + BigInt(netNum)).toString());
  const ch = channels.keys.map((_, idx) => idx);
  ch.sort((x, y) => compareBytes(channels.keys[x], channels.keys[y]));
  const latin1 = (k) => Buffer.from(k.buffer, k.byteOffset, k.length).toString("latin1");
  for (const c of ch) {
    lines.push("channel " + latin1(channels.keys[c]) + " " + channels.count[c] + " " + channels.sum[c].toString());
  }
  const ac = accounts.keys.map((_, idx) => idx);
  ac.sort((x, y) => {
    const sx = accounts.sum[x], sy = accounts.sum[y]; // Number or BigInt; relational ops mix fine
    if (sx > sy) return -1;
    if (sx < sy) return 1;
    return compareBytes(accounts.keys[x], accounts.keys[y]);
  });
  for (let k = 0; k < Math.min(10, ac.length); k++) {
    const a = ac[k];
    lines.push("account " + latin1(accounts.keys[a]) + " " + accounts.sum[a].toString());
  }
  fs.writeSync(1, lines.join("\n") + "\n");
}

main();
