"use strict";
const fs = require("fs");

const d = fs.readFileSync(process.argv[2]);
const n = d.length;
let pos = 0;
let hi = 0; // shared cursor for hex4

// ---------- open-addressing map byte-string -> {net: i64, cnt}; keys in an arena ----------
class StrMap {
  constructor(capHint) {
    let c = 16;
    while (c < capHint) c <<= 1;
    this.hash = new Uint32Array(c);
    this.off = new Int32Array(c);
    this.klen = new Int32Array(c);
    this.net = new BigInt64Array(c);
    this.cnt = new Float64Array(c);
    this.used = new Uint8Array(c);
    this.arena = Buffer.alloc(1 << 16);
    this.arenaLen = 0;
    this.mask = c - 1;
    this.usedCnt = 0;
  }
  grow() {
    const oh = this.hash, oo = this.off, ol = this.klen, on = this.net, oc = this.cnt, ou = this.used;
    const c = oh.length * 2;
    this.hash = new Uint32Array(c); this.off = new Int32Array(c); this.klen = new Int32Array(c);
    this.net = new BigInt64Array(c); this.cnt = new Float64Array(c); this.used = new Uint8Array(c);
    this.mask = c - 1;
    for (let i = 0; i < oh.length; i++) if (ou[i]) {
      let j = oh[i] & this.mask;
      while (this.used[j]) j = (j + 1) & this.mask;
      this.used[j] = 1; this.hash[j] = oh[i]; this.off[j] = oo[i]; this.klen[j] = ol[i];
      this.net[j] = on[i]; this.cnt[j] = oc[i];
    }
  }
  findOrInsert(a, o, len) {
    if ((this.usedCnt + 1) * 10 > this.hash.length * 7) this.grow();
    const h = hashBytes(a, o, len);
    let i = h & this.mask;
    const arena = this.arena;
    while (true) {
      if (!this.used[i]) {
        this.used[i] = 1; this.hash[i] = h;
        if (this.arenaLen + len > this.arena.length) {
          let nc = this.arena.length;
          while (nc < this.arenaLen + len) nc <<= 1;
          const na = Buffer.alloc(nc);
          na.set(this.arena.subarray(0, this.arenaLen));
          this.arena = na;
        }
        this.off[i] = this.arenaLen; this.klen[i] = len;
        this.arena.set(a.subarray(o, o + len), this.arenaLen);
        this.arenaLen += len;
        this.net[i] = 0n; this.cnt[i] = 0; this.usedCnt++;
        return i;
      }
      if (this.hash[i] === h && this.klen[i] === len && bytesEq(this.arena, this.off[i], a, o, len)) return i;
      i = (i + 1) & this.mask;
    }
  }
  find(a, o, len) {
    const h = hashBytes(a, o, len);
    let i = h & this.mask;
    while (true) {
      if (!this.used[i]) return -1;
      if (this.hash[i] === h && this.klen[i] === len && bytesEq(this.arena, this.off[i], a, o, len)) return i;
      i = (i + 1) & this.mask;
    }
  }
}

function hashBytes(a, o, len) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < len; i++) {
    h ^= a[o + i];
    h = Math.imul(h, 16777619);
  }
  h ^= h >>> 16; h = Math.imul(h, 0x45d9f3b); h ^= h >>> 16;
  return h >>> 0;
}

function bytesEq(a, ao, b, bo, len) {
  for (let i = 0; i < len; i++) if (a[ao + i] !== b[bo + i]) return false;
  return true;
}

function cmpKey(m, x, y) {
  const a = m.arena, ao = m.off[x], al = m.klen[x], bo = m.off[y], bl = m.klen[y];
  const mm = al < bl ? al : bl;
  for (let i = 0; i < mm; i++) {
    const diff = a[ao + i] - a[bo + i];
    if (diff !== 0) return diff;
  }
  return al - bl;
}

// ---------- parser ----------
function makeBuf() { return { dec: new Uint8Array(64), a: null, off: 0, len: 0 }; }
const keyS = makeBuf(), acctS = makeBuf(), chanS = makeBuf(), miscS = makeBuf();

const K_ACCOUNT = Buffer.from("account"), K_TYPE = Buffer.from("type"),
  K_AMOUNT = Buffer.from("amount"), K_CURRENCY = Buffer.from("currency"),
  K_TAGS = Buffer.from("tags"), K_META = Buffer.from("meta"),
  K_RATES = Buffer.from("rates"), K_CHANNEL = Buffer.from("channel"),
  V_VOID = Buffer.from("void"), V_DEBIT = Buffer.from("debit"), V_TEST = Buffer.from("test");

function eq(s, lit) {
  if (s.len !== lit.length) return false;
  const a = s.a, o = s.off;
  for (let i = 0; i < lit.length; i++) if (a[o + i] !== lit[i]) return false;
  return true;
}

function skipWs() {
  while (pos < n) {
    const c = d[pos];
    if (c === 32 || c === 9 || c === 10 || c === 13) pos++; else break;
  }
}

function skipStringRaw() {
  pos++;
  while (pos < n) {
    const c = d[pos];
    if (c === 34) { pos++; return; } // "
    pos += c === 92 ? 2 : 1; // backslash
  }
}

function hex4(end) {
  let v = 0;
  for (let k = 0; k < 4 && hi < end; k++, hi++) {
    const c = d[hi];
    v <<= 4;
    if (c >= 48 && c <= 57) v |= c - 48;
    else if (c >= 97 && c <= 102) v |= c - 87;
    else if (c >= 65 && c <= 70) v |= c - 55;
  }
  return v;
}

function appendUtf8(out, w, cp) {
  if (cp < 0x80) out[w++] = cp;
  else if (cp < 0x800) { out[w++] = 0xC0 | (cp >> 6); out[w++] = 0x80 | (cp & 0x3F); }
  else if (cp < 0x10000) {
    out[w++] = 0xE0 | (cp >> 12); out[w++] = 0x80 | ((cp >> 6) & 0x3F); out[w++] = 0x80 | (cp & 0x3F);
  } else {
    out[w++] = 0xF0 | (cp >> 18); out[w++] = 0x80 | ((cp >> 12) & 0x3F);
    out[w++] = 0x80 | ((cp >> 6) & 0x3F); out[w++] = 0x80 | (cp & 0x3F);
  }
  return w;
}

function parseString(out) {
  pos++;
  const start = pos;
  let esc = false;
  while (pos < n) {
    const c = d[pos];
    if (c === 34) break;
    if (c === 92) { esc = true; pos += 2; } else pos++;
  }
  const end = pos;
  if (pos < n) pos++;
  if (!esc) { out.a = d; out.off = start; out.len = end - start; return; }
  if (out.dec.length < end - start) {
    let nc = out.dec.length;
    while (nc < end - start) nc <<= 1;
    out.dec = new Uint8Array(nc);
  }
  const o = out.dec;
  let w = 0, i = start;
  while (i < end) {
    const c = d[i];
    if (c !== 92) { o[w++] = c; i++; continue; }
    i++;
    if (i >= end) break;
    const e = d[i++];
    if (e === 34) o[w++] = 34;
    else if (e === 92) o[w++] = 92;
    else if (e === 47) o[w++] = 47;
    else if (e === 98) o[w++] = 8;
    else if (e === 102) o[w++] = 12;
    else if (e === 110) o[w++] = 10;
    else if (e === 114) o[w++] = 13;
    else if (e === 116) o[w++] = 9;
    else if (e === 117) { // u
      hi = i; let cp = hex4(end); i = hi;
      if (cp >= 0xD800 && cp <= 0xDBFF && i + 1 < end && d[i] === 92 && d[i + 1] === 117) {
        i += 2; hi = i; const lo = hex4(end); i = hi;
        if (lo >= 0xDC00 && lo <= 0xDFFF) cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
        else { w = appendUtf8(o, w, cp); cp = lo; }
      }
      w = appendUtf8(o, w, cp);
    } else o[w++] = e;
  }
  out.a = o; out.off = 0; out.len = w;
}

function skipValue() {
  skipWs();
  if (pos >= n) return;
  const c = d[pos];
  if (c === 34) { skipStringRaw(); return; }
  if (c === 123 || c === 91) { // { [
    let depth = 0;
    while (pos < n) {
      const ch = d[pos];
      if (ch === 34) { skipStringRaw(); continue; }
      if (ch === 123 || ch === 91) { depth++; pos++; }
      else if (ch === 125 || ch === 93) { depth--; pos++; if (depth === 0) return; }
      else pos++;
    }
    return;
  }
  while (pos < n) {
    const ch = d[pos];
    if (ch === 44 || ch === 125 || ch === 93 || ch === 32 || ch === 9 || ch === 10 || ch === 13) break;
    pos++;
  }
}

function parseInt64() {
  skipWs();
  let neg = false;
  if (pos < n && d[pos] === 45) { neg = true; pos++; }
  let v = 0;
  while (pos < n && d[pos] >= 48 && d[pos] <= 57) v = v * 10 + (d[pos++] - 48);
  return neg ? -v : v;
}

// Returns hundredths as BigInt (exact even for very long digit strings).
function parseAmount(s) {
  const a = s.a;
  let i = s.off;
  const end = s.off + s.len;
  let ip = 0, digits = 0;
  while (i < end && a[i] !== 46) { ip = ip * 10 + (a[i] - 48); i++; digits++; }
  let h = ip * 100;
  if (i < end) {
    i++;
    if (i < end) { h += (a[i] - 48) * 10; i++; digits++; }
    if (i < end) { h += a[i] - 48; digits++; }
  }
  if (digits <= 15) return BigInt(h);
  // Slow exact path.
  let hb = 0n, frac = 0;
  i = s.off;
  while (i < end && a[i] !== 46) { hb = hb * 10n + BigInt(a[i] - 48); i++; }
  hb *= 100n;
  if (i < end) {
    i++;
    if (i < end) { frac += (a[i] - 48) * 10; i++; }
    if (i < end) frac += a[i] - 48;
  }
  return hb + BigInt(frac);
}

// ---------- main ----------
const rates = new StrMap(64), channels = new StrMap(64), accounts = new StrMap(1 << 16);

skipWs();
if (pos < n && d[pos] === 123) {
  pos++; skipWs();
  if (pos < n && d[pos] === 125) pos++;
  else {
    outer: while (true) {
      skipWs(); parseString(keyS);
      skipWs(); pos++; skipWs();
      if (eq(keyS, K_RATES)) {
        pos++; skipWs();
        if (pos < n && d[pos] === 125) pos++;
        else while (true) {
          skipWs(); parseString(miscS);
          skipWs(); pos++;
          const rv = parseInt64();
          rates.net[rates.findOrInsert(miscS.a, miscS.off, miscS.len)] = BigInt(rv);
          skipWs();
          if (pos < n && d[pos] === 44) { pos++; continue; }
          if (pos < n && d[pos] === 125) pos++;
          break;
        }
      } else skipValue();
      skipWs();
      if (pos < n && d[pos] === 44) { pos++; continue; }
      if (pos < n && d[pos] === 125) pos++;
      break outer;
    }
  }
}

let counted = 0;
let net = 0n;
while (true) {
  skipWs();
  if (pos >= n) break;
  let sign = 1, isVoid = false, hasTest = false;
  let hundredths = 0n, rate = 0n;
  acctS.a = null; acctS.len = 0; chanS.a = null; chanS.len = 0;
  pos++; skipWs();
  if (pos < n && d[pos] === 125) pos++;
  else {
    tx: while (true) {
      skipWs(); parseString(keyS);
      skipWs(); pos++; skipWs();
      if (eq(keyS, K_ACCOUNT)) {
        parseString(acctS);
      } else if (eq(keyS, K_TYPE)) {
        parseString(miscS);
        if (eq(miscS, V_VOID)) isVoid = true;
        else if (eq(miscS, V_DEBIT)) sign = -1;
        else sign = 1;
      } else if (eq(keyS, K_AMOUNT)) {
        parseString(miscS);
        hundredths = parseAmount(miscS);
      } else if (eq(keyS, K_CURRENCY)) {
        parseString(miscS);
        const sl = rates.find(miscS.a, miscS.off, miscS.len);
        rate = sl >= 0 ? rates.net[sl] : 0n;
      } else if (eq(keyS, K_TAGS)) {
        pos++; skipWs();
        if (pos < n && d[pos] === 93) pos++;
        else while (true) {
          skipWs();
          if (pos < n && d[pos] === 34) {
            parseString(miscS);
            if (eq(miscS, V_TEST)) hasTest = true;
          } else skipValue();
          skipWs();
          if (pos < n && d[pos] === 44) { pos++; continue; }
          if (pos < n && d[pos] === 93) pos++;
          break;
        }
      } else if (eq(keyS, K_META)) {
        pos++; skipWs();
        if (pos < n && d[pos] === 125) pos++;
        else while (true) {
          skipWs(); parseString(keyS);
          skipWs(); pos++; skipWs();
          if (eq(keyS, K_CHANNEL)) parseString(chanS);
          else skipValue();
          skipWs();
          if (pos < n && d[pos] === 44) { pos++; continue; }
          if (pos < n && d[pos] === 125) pos++;
          break;
        }
      } else {
        skipValue();
      }
      skipWs();
      if (pos < n && d[pos] === 44) { pos++; continue; }
      if (pos < n && d[pos] === 125) pos++;
      break tx;
    }
  }
  if (isVoid || hasTest) continue;
  const usd = (hundredths * rate) / 1000000n;
  const signed = sign < 0 ? -usd : usd;
  counted++;
  net += signed;
  accounts.net[accounts.findOrInsert(acctS.a, acctS.off, acctS.len)] += signed;
  const cs = channels.findOrInsert(chanS.a, chanS.off, chanS.len);
  channels.net[cs] += signed;
  channels.cnt[cs]++;
}

function slots(m) {
  const r = new Array(m.usedCnt);
  let k = 0;
  for (let i = 0; i < m.used.length; i++) if (m.used[i]) r[k++] = i;
  return r;
}

const chans = slots(channels);
chans.sort((x, y) => cmpKey(channels, x, y));
const accts = slots(accounts);
accts.sort((x, y) => {
  const nx = accounts.net[x], ny = accounts.net[y];
  if (nx !== ny) return nx > ny ? -1 : 1;
  return cmpKey(accounts, x, y);
});

let out = "counted " + counted + "\nnet " + net.toString() + "\n";
for (const s of chans) {
  out += "channel " + channels.arena.subarray(channels.off[s], channels.off[s] + channels.klen[s]).toString("utf8")
    + " " + channels.cnt[s] + " " + channels.net[s].toString() + "\n";
}
const top = Math.min(10, accts.length);
for (let i = 0; i < top; i++) {
  const s = accts[i];
  out += "account " + accounts.arena.subarray(accounts.off[s], accounts.off[s] + accounts.klen[s]).toString("utf8")
    + " " + accounts.net[s].toString() + "\n";
}
process.stdout.write(out);
