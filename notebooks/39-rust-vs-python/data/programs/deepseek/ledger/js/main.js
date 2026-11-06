"use strict";

const fs = require("fs");

const buf = fs.readFileSync(process.argv[2]);
const end = buf.length;
let pos = 0;

let sBeg = 0, sLen = 0, sEsc = false;
let rArr = buf, rOff = 0, rLen = 0;
let scratch = new Uint8Array(256);
let scratchLen = 0;

function enc(s) {
    const a = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
    return a;
}

const K_ACCOUNT = enc("account");
const K_AMOUNT = enc("amount");
const K_TYPE = enc("type");
const K_TAGS = enc("tags");
const K_META = enc("meta");
const K_CHANNEL = enc("channel");
const K_CURRENCY = enc("currency");
const K_RATES = enc("rates");
const K_TEST = enc("test");
const K_VOID = enc("void");
const K_DEBIT = enc("debit");

function skipWs() {
    const b = buf;
    let i = pos;
    while (i < end) {
        const c = b[i];
        if (c === 32 || c === 9 || c === 13 || c === 10) i++;
        else break;
    }
    pos = i;
}

function scanString() {
    const b = buf;
    let i = pos + 1;
    const s = i;
    let esc = false;
    while (b[i] !== 34) {
        if (b[i] === 92) {
            esc = true;
            i++;
            if (b[i] === 117) i += 5;
            else i++;
        } else {
            i++;
        }
    }
    sBeg = s;
    sLen = i - s;
    sEsc = esc;
    pos = i + 1;
}

function skipString() {
    const b = buf;
    let i = pos + 1;
    while (b[i] !== 34) {
        if (b[i] === 92) {
            i++;
            if (b[i] === 117) i += 5;
            else i++;
        } else {
            i++;
        }
    }
    pos = i + 1;
}

function hex4(b, q) {
    let v = 0;
    for (let i = 0; i < 4; i++) {
        const c = b[q + i];
        let d;
        if (c >= 48 && c <= 57) d = c - 48;
        else if (c >= 97 && c <= 102) d = c - 87;
        else d = c - 55;
        v = (v << 4) | d;
    }
    return v;
}

function ensureScratch(n) {
    if (n <= scratch.length) return;
    let cap = scratch.length;
    while (cap < n) cap *= 2;
    const ns = new Uint8Array(cap);
    ns.set(scratch.subarray(0, scratchLen));
    scratch = ns;
}

function unescape() {
    ensureScratch(sLen + 4);
    const b = buf;
    let q = sBeg;
    const e = sBeg + sLen;
    let n = 0;
    while (q < e) {
        let c = b[q++];
        if (c !== 92) {
            scratch[n++] = c;
            continue;
        }
        const esc = b[q++];
        switch (esc) {
            case 34: scratch[n++] = 34; break;
            case 92: scratch[n++] = 92; break;
            case 47: scratch[n++] = 47; break;
            case 98: scratch[n++] = 8; break;
            case 102: scratch[n++] = 12; break;
            case 110: scratch[n++] = 10; break;
            case 114: scratch[n++] = 13; break;
            case 116: scratch[n++] = 9; break;
            case 117: {
                let cp = hex4(b, q);
                q += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && q + 6 <= e && b[q] === 92 && b[q + 1] === 117) {
                    const lo = hex4(b, q + 2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        q += 6;
                    }
                }
                if (cp < 0x80) {
                    scratch[n++] = cp;
                } else if (cp < 0x800) {
                    scratch[n++] = 0xC0 | (cp >> 6);
                    scratch[n++] = 0x80 | (cp & 0x3F);
                } else if (cp < 0x10000) {
                    scratch[n++] = 0xE0 | (cp >> 12);
                    scratch[n++] = 0x80 | ((cp >> 6) & 0x3F);
                    scratch[n++] = 0x80 | (cp & 0x3F);
                } else {
                    scratch[n++] = 0xF0 | (cp >> 18);
                    scratch[n++] = 0x80 | ((cp >> 12) & 0x3F);
                    scratch[n++] = 0x80 | ((cp >> 6) & 0x3F);
                    scratch[n++] = 0x80 | (cp & 0x3F);
                }
                break;
            }
            default: scratch[n++] = esc; break;
        }
    }
    rArr = scratch;
    rOff = 0;
    rLen = n;
    scratchLen = n;
}

function resolve() {
    if (sEsc) {
        unescape();
    } else {
        rArr = buf;
        rOff = sBeg;
        rLen = sLen;
    }
}

function eq(lit) {
    if (rLen !== lit.length) return false;
    const a = rArr, o = rOff;
    for (let i = 0; i < lit.length; i++) {
        if (a[o + i] !== lit[i]) return false;
    }
    return true;
}

function skipValue() {
    skipWs();
    const b = buf;
    let i = pos;
    const c = b[i];
    if (c === 34) {
        i++;
        while (b[i] !== 34) {
            if (b[i] === 92) { i++; if (b[i] === 117) i += 5; else i++; }
            else i++;
        }
        pos = i + 1;
        return;
    }
    if (c === 123 || c === 91) {
        let depth = 0;
        while (true) {
            const d = b[i];
            if (d === 34) {
                i++;
                while (b[i] !== 34) {
                    if (b[i] === 92) { i++; if (b[i] === 117) i += 5; else i++; }
                    else i++;
                }
                i++;
            } else if (d === 123 || d === 91) { depth++; i++; }
            else if (d === 125 || d === 93) { i++; if (--depth === 0) { pos = i; return; } }
            else i++;
        }
    }
    while (i < end) {
        const d = b[i];
        if (d === 44 || d === 125 || d === 93 || d === 32 || d === 9 || d === 13 || d === 10) break;
        i++;
    }
    pos = i;
}

// ---------------- rates
let rateKeys = [];
let rateVals = [];

function lookupRate() {
    const a = rArr, o = rOff, len = rLen;
    for (let i = 0; i < rateKeys.length; i++) {
        const k = rateKeys[i];
        if (k.length !== len) continue;
        let same = true;
        for (let j = 0; j < len; j++) {
            if (k[j] !== a[o + j]) { same = false; break; }
        }
        if (same) return rateVals[i];
    }
    return 0;
}

// ---------------- accounts: custom open-addressing map
let accSlots = new Int32Array(1 << 14);
let accStart = new Int32Array(1 << 13);
let accLen = new Int32Array(1 << 13);
let accSum = new Float64Array(1 << 13);
let accCnt = new Int32Array(1 << 13);
let accN = 0;
let arena = new Uint8Array(1 << 16);
let arenaLen = 0;

function bytesEqArr(A, ao, B, bo, len) {
    for (let i = 0; i < len; i++) {
        if (A[ao + i] !== B[bo + i]) return false;
    }
    return true;
}

function growAccounts() {
    const cap = accStart.length * 2;
    const s = new Int32Array(cap); s.set(accStart); accStart = s;
    const l = new Int32Array(cap); l.set(accLen); accLen = l;
    const v = new Float64Array(cap); v.set(accSum); accSum = v;
    const c = new Int32Array(cap); c.set(accCnt); accCnt = c;
}

function rehash() {
    const ns = new Int32Array(accSlots.length * 2);
    const mask = ns.length - 1;
    for (let idx = 0; idx < accN; idx++) {
        const len = accLen[idx];
        const st = accStart[idx];
        let h = 0x811c9dc5 | 0;
        for (let i = 0; i < len; i++) {
            h = Math.imul(h ^ arena[st + i], 0x01000193);
        }
        let slot = (h >>> 0) & mask;
        while (ns[slot] !== 0) slot = (slot + 1) & mask;
        ns[slot] = idx + 1;
    }
    accSlots = ns;
}

function internAccount() {
    const a = rArr, off = rOff, len = rLen;
    let h = 0x811c9dc5 | 0;
    for (let i = 0; i < len; i++) {
        h = Math.imul(h ^ a[off + i], 0x01000193);
    }
    let mask = accSlots.length - 1;
    let slot = (h >>> 0) & mask;
    while (true) {
        const e = accSlots[slot];
        if (e === 0) break;
        const idx = e - 1;
        if (accLen[idx] === len && bytesEqArr(arena, accStart[idx], a, off, len)) return idx;
        slot = (slot + 1) & mask;
    }
    if (accN === accStart.length) growAccounts();
    if (arenaLen + len > arena.length) {
        let cap = arena.length;
        while (cap < arenaLen + len) cap *= 2;
        const na = new Uint8Array(cap);
        na.set(arena.subarray(0, arenaLen));
        arena = na;
    }
    const idx = accN++;
    const st = arenaLen;
    arena.set(a.subarray(off, off + len), st);
    arenaLen += len;
    accStart[idx] = st;
    accLen[idx] = len;
    accSum[idx] = 0;
    accCnt[idx] = 0;
    accSlots[slot] = idx + 1;
    if (accN * 2 > accSlots.length) rehash();
    return idx;
}

// ---------------- channels
const chName = [];
const chCnt = [];
const chNet = [];
let chN = 0;

function internChannel() {
    const a = rArr, o = rOff, len = rLen;
    for (let i = 0; i < chN; i++) {
        const n = chName[i];
        if (n.length !== len) continue;
        let same = true;
        for (let j = 0; j < len; j++) {
            if (n[j] !== a[o + j]) { same = false; break; }
        }
        if (same) return i;
    }
    const n = new Uint8Array(len);
    for (let j = 0; j < len; j++) n[j] = a[o + j];
    chName.push(n);
    chCnt.push(0);
    chNet.push(0);
    return chN++;
}

function parseAmount() {
    const a = rArr;
    let i = rOff;
    const e = rOff + rLen;
    let whole = 0;
    while (i < e) {
        const c = a[i];
        if (c < 48 || c > 57) break;
        whole = whole * 10 + (c - 48);
        i++;
    }
    let f1 = 0, f2 = 0;
    if (i < e && a[i] === 46) {
        i++;
        if (i < e) { f1 = a[i] - 48; i++; }
        if (i < e) { f2 = a[i] - 48; }
    }
    return whole * 100 + f1 * 10 + f2;
}

// ---------------- transactions
let totalCount = 0;
let totalNet = 0;

function parseTags() {
    pos++;
    skipWs();
    const b = buf;
    if (b[pos] === 93) { pos++; return false; }
    let hasTest = false;
    while (true) {
        skipWs();
        if (b[pos] === 34) {
            scanString();
            if (!hasTest) {
                resolve();
                if (eq(K_TEST)) hasTest = true;
            }
        } else {
            skipValue();
        }
        skipWs();
        if (b[pos] === 44) { pos++; continue; }
        pos++;
        return hasTest;
    }
}

function parseMeta() {
    let chIdx = -1;
    pos++;
    skipWs();
    const b = buf;
    if (b[pos] === 125) { pos++; return chIdx; }
    while (true) {
        skipWs();
        scanString();
        resolve();
        const isChannel = eq(K_CHANNEL);
        skipWs();
        pos++;
        skipWs();
        if (isChannel) {
            scanString();
            resolve();
            chIdx = internChannel();
        } else {
            skipValue();
        }
        skipWs();
        if (b[pos] === 44) { pos++; continue; }
        pos++;
        return chIdx;
    }
}

function parseTransaction() {
    let acctIdx = -1;
    let chIdx = -1;
    let sign = 1;
    let hasTagTest = false;
    let hundredths = 0;
    let rate = 0;

    const b = buf;
    pos++;
    skipWs();
    if (b[pos] === 125) { pos++; return; }
    while (true) {
        skipWs();
        scanString();
        resolve();
        const first = rLen > 0 ? rArr[rOff] : 0;
        skipWs();
        pos++;
        skipWs();
        switch (first) {
            case 97: // 'a'
                if (eq(K_ACCOUNT)) {
                    scanString(); resolve();
                    acctIdx = internAccount();
                } else if (eq(K_AMOUNT)) {
                    scanString(); resolve();
                    hundredths = parseAmount();
                } else {
                    skipValue();
                }
                break;
            case 116: // 't'
                if (eq(K_TYPE)) {
                    scanString(); resolve();
                    if (eq(K_VOID)) sign = 0;
                    else if (eq(K_DEBIT)) sign = -1;
                    else sign = 1;
                } else if (eq(K_TAGS)) {
                    hasTagTest = parseTags();
                } else {
                    skipValue();
                }
                break;
            case 109: // 'm'
                if (eq(K_META)) chIdx = parseMeta();
                else skipValue();
                break;
            case 99: // 'c'
                if (eq(K_CURRENCY)) {
                    scanString(); resolve();
                    rate = lookupRate();
                } else {
                    skipValue();
                }
                break;
            default:
                skipValue();
                break;
        }
        skipWs();
        if (b[pos] === 44) { pos++; continue; }
        pos++;
        break;
    }

    if (sign === 0 || hasTagTest) return;

    const usd = Math.floor((hundredths * rate) / 1000000);
    const val = sign > 0 ? usd : -usd;

    totalCount++;
    totalNet += val;
    if (acctIdx >= 0) {
        accSum[acctIdx] += val;
        accCnt[acctIdx]++;
    }
    if (chIdx >= 0) {
        chCnt[chIdx]++;
        chNet[chIdx] += val;
    }
}

function cmpByteArrays(a, b) {
    const n = Math.min(a.length, b.length);
    for (let i = 0; i < n; i++) {
        if (a[i] !== b[i]) return a[i] - b[i];
    }
    return a.length - b.length;
}

function cmpArena(i, j) {
    const ni = accLen[i], nj = accLen[j];
    const si = accStart[i], sj = accStart[j];
    const n = Math.min(ni, nj);
    for (let k = 0; k < n; k++) {
        if (arena[si + k] !== arena[sj + k]) return arena[si + k] - arena[sj + k];
    }
    return ni - nj;
}

function decodeBytes(u8, off, len) {
    return Buffer.from(u8.buffer, u8.byteOffset + off, len).toString("utf8");
}

function main() {
    // first line {"rates": {...}}
    skipWs();
    pos++;
    skipWs();
    const b = buf;
    if (b[pos] !== 125) {
        while (true) {
            skipWs();
            scanString();
            resolve();
            const isRates = eq(K_RATES);
            skipWs();
            pos++;
            skipWs();
            if (isRates && b[pos] === 123) {
                pos++;
                skipWs();
                if (b[pos] !== 125) {
                    while (true) {
                        skipWs();
                        scanString();
                        resolve();
                        const cur = new Uint8Array(rLen);
                        cur.set(rArr.subarray(rOff, rOff + rLen));
                        skipWs();
                        pos++;
                        skipWs();
                        let neg = false;
                        if (b[pos] === 45) { neg = true; pos++; }
                        let v = 0;
                        while (b[pos] >= 48 && b[pos] <= 57) {
                            v = v * 10 + (b[pos] - 48);
                            pos++;
                        }
                        if (neg) v = -v;
                        rateKeys.push(cur);
                        rateVals.push(v);
                        skipWs();
                        if (b[pos] === 44) { pos++; continue; }
                        pos++;
                        break;
                    }
                } else {
                    pos++;
                }
            } else {
                skipValue();
            }
            skipWs();
            if (b[pos] === 44) { pos++; continue; }
            pos++;
            break;
        }
    } else {
        pos++;
    }

    while (true) {
        skipWs();
        if (pos >= end) break;
        if (b[pos] !== 123) { pos++; continue; }
        parseTransaction();
    }

    // sort channels by byte order
    const ci = [];
    for (let i = 0; i < chN; i++) ci.push(i);
    ci.sort((x, y) => cmpByteArrays(chName[x], chName[y]));

    // top ten accounts
    const best = new Array(10);
    let bn = 0;
    for (let i = 0; i < accN; i++) {
        if (accCnt[i] === 0) continue;
        const s = accSum[i];
        let p = bn;
        while (p > 0) {
            const o = best[p - 1];
            let better;
            if (s !== accSum[o]) better = s > accSum[o];
            else better = cmpArena(i, o) < 0;
            if (!better) break;
            p--;
        }
        if (p >= 10) continue;
        if (bn < 10) bn++;
        for (let j = bn - 1; j > p; j--) best[j] = best[j - 1];
        best[p] = i;
    }

    const lines = [];
    lines.push("counted " + totalCount);
    lines.push("net " + totalNet);
    for (let i = 0; i < chN; i++) {
        const c = ci[i];
        if (chCnt[c] === 0) continue;
        lines.push("channel " + decodeBytes(chName[c], 0, chName[c].length) + " " + chCnt[c] + " " + chNet[c]);
    }
    for (let i = 0; i < bn; i++) {
        const a = best[i];
        lines.push("account " + decodeBytes(arena, accStart[a], accLen[a]) + " " + accSum[a]);
    }
    process.stdout.write(lines.join("\n") + "\n");
}

main();
