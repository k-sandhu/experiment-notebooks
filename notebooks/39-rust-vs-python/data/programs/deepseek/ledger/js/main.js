"use strict";

const fs = require("fs");

let B = null;
let LEN = 0;
let P = 0;

const SAFE = 9007199254740991;

// ---------------------------------------------------------------------------
// Open addressing hash map keyed by spans of the input buffer.
// Values are Numbers while everything fits in a safe integer; if a value can
// exceed 2^53-1 the whole program switches to BigInt (see activateBig).
// ---------------------------------------------------------------------------
function hashSpan(s, n) {
    let h = 0x811c9dc5 | 0;
    for (let i = 0; i < n; i++) {
        h ^= B[s + i];
        h = Math.imul(h, 0x01000193);
    }
    return h >>> 0;
}

class SpanMap {
    constructor(c) {
        this.cap = c;
        this.cnt = 0;
        this.off = new Array(c).fill(0);
        this.klen = new Array(c).fill(-1);
        this.v1 = new Array(c).fill(0);
        this.v2 = new Array(c).fill(0);
    }

    grow() {
        const nc = this.cap * 2;
        const no = new Array(nc).fill(0);
        const nl = new Array(nc).fill(-1);
        const n1 = new Array(nc).fill(0);
        const n2 = new Array(nc).fill(0);
        const mask = nc - 1;
        for (let j = 0; j < this.cap; j++) {
            if (this.klen[j] < 0) continue;
            let i = hashSpan(this.off[j], this.klen[j]) & mask;
            while (nl[i] >= 0) i = (i + 1) & mask;
            no[i] = this.off[j];
            nl[i] = this.klen[j];
            n1[i] = this.v1[j];
            n2[i] = this.v2[j];
        }
        this.off = no;
        this.klen = nl;
        this.v1 = n1;
        this.v2 = n2;
        this.cap = nc;
    }

    find(s, n) {
        const mask = this.cap - 1;
        let i = hashSpan(s, n) & mask;
        while (this.klen[i] >= 0) {
            if (this.klen[i] === n && spanEqBytes(this.off[i], this.off[i] + n, s, s + n)) return i;
            i = (i + 1) & mask;
        }
        return -1;
    }

    getOrInsert(s, n) {
        if ((this.cnt + 1) * 10 > this.cap * 7) this.grow();
        const mask = this.cap - 1;
        let i = hashSpan(s, n) & mask;
        while (this.klen[i] >= 0) {
            if (this.klen[i] === n && spanEqBytes(this.off[i], this.off[i] + n, s, s + n)) return i;
            i = (i + 1) & mask;
        }
        this.off[i] = s;
        this.klen[i] = n;
        this.v1[i] = bigMode ? 0n : 0;
        this.v2[i] = bigMode ? 0n : 0;
        this.cnt++;
        return i;
    }
}

let rates, channels, accounts;
let totalNet = 0;
let totalCount = 0;
let bigMode = false;

function activateBig() {
    if (bigMode) return;
    bigMode = true;
    const maps = [rates, channels, accounts];
    for (let k = 0; k < maps.length; k++) {
        const m = maps[k];
        for (let i = 0; i < m.cap; i++) {
            if (typeof m.v1[i] === "number") m.v1[i] = BigInt(m.v1[i]);
            if (typeof m.v2[i] === "number") m.v2[i] = BigInt(m.v2[i]);
        }
    }
    if (typeof totalNet === "number") totalNet = BigInt(totalNet);
}

// ---------------------------------------------------------------------------
// Byte level JSON scanning
// ---------------------------------------------------------------------------
function skipWs() {
    while (P < LEN) {
        const c = B[P];
        if (c === 32 || c === 9 || c === 10 || c === 13) P++;
        else break;
    }
}

// Assumes B[P] === '"'. Leaves P just past the closing quote.
let strS = 0, strE = 0, strEsc = false;
function parseString() {
    P++;
    const s = P;
    let esc = false;
    for (;;) {
        const c = B[P];
        if (c === 34) {
            strS = s;
            strE = P;
            strEsc = esc;
            P++;
            return;
        }
        if (c === 92) {
            esc = true;
            P += 2;
        } else P++;
    }
}

function hex4(p) {
    let v = 0;
    for (let i = 0; i < 4; i++) {
        const c = B[p + i];
        let d;
        if (c >= 48 && c <= 57) d = c - 48;
        else if (c >= 97 && c <= 102) d = c - 97 + 10;
        else d = c - 65 + 10;
        v = (v << 4) | d;
    }
    return v;
}

function decode(s, e) {
    let w = s, r = s;
    while (r < e) {
        const c = B[r++];
        if (c !== 92) {
            B[w++] = c;
            continue;
        }
        const x = B[r++];
        switch (x) {
            case 34: B[w++] = 34; break;
            case 92: B[w++] = 92; break;
            case 47: B[w++] = 47; break;
            case 98: B[w++] = 8; break;
            case 102: B[w++] = 12; break;
            case 110: B[w++] = 10; break;
            case 114: B[w++] = 13; break;
            case 116: B[w++] = 9; break;
            case 117: {
                let cp = hex4(r);
                r += 4;
                if (cp >= 0xD800 && cp <= 0xDBFF && r + 6 <= e &&
                    B[r] === 92 && B[r + 1] === 117) {
                    const lo = hex4(r + 2);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        r += 6;
                    }
                }
                if (cp < 0x80) {
                    B[w++] = cp;
                } else if (cp < 0x800) {
                    B[w++] = 0xC0 | (cp >> 6);
                    B[w++] = 0x80 | (cp & 0x3F);
                } else if (cp < 0x10000) {
                    B[w++] = 0xE0 | (cp >> 12);
                    B[w++] = 0x80 | ((cp >> 6) & 0x3F);
                    B[w++] = 0x80 | (cp & 0x3F);
                } else {
                    B[w++] = 0xF0 | (cp >> 18);
                    B[w++] = 0x80 | ((cp >> 12) & 0x3F);
                    B[w++] = 0x80 | ((cp >> 6) & 0x3F);
                    B[w++] = 0x80 | (cp & 0x3F);
                }
                break;
            }
            default: B[w++] = x; break;
        }
    }
    return w;
}

// Decodes escapes when present; result in strS/strE.
function parseStringValue() {
    parseString();
    if (strEsc) strE = decode(strS, strE);
}

function spanEq(s, e, lit) {
    const n = e - s;
    if (n !== lit.length) return false;
    for (let i = 0; i < n; i++)
        if (B[s + i] !== lit.charCodeAt(i)) return false;
    return true;
}

function spanEqBytes(s1, e1, s2, e2) {
    const n = e1 - s1;
    if (n !== e2 - s2) return false;
    for (let i = 0; i < n; i++)
        if (B[s1 + i] !== B[s2 + i]) return false;
    return true;
}

function spanCompare(o1, l1, o2, l2) {
    const n = l1 < l2 ? l1 : l2;
    for (let i = 0; i < n; i++) {
        const d = B[o1 + i] - B[o2 + i];
        if (d !== 0) return d;
    }
    return l1 - l2;
}

function skipValue() {
    skipWs();
    let c = B[P];
    if (c === 34) {
        parseString();
        return;
    }
    if (c === 123 || c === 91) {
        let depth = 0;
        for (;;) {
            c = B[P];
            if (c === 34) {
                parseString();
            } else {
                P++;
                if (c === 123 || c === 91) depth++;
                else if (c === 125 || c === 93) {
                    if (--depth === 0) return;
                }
            }
        }
    }
    while (P < LEN) {
        c = B[P];
        if (c === 44 || c === 125 || c === 93 || c === 32 || c === 9 || c === 10 || c === 13)
            return;
        P++;
    }
}

function parseAmountBig(s, e) {
    let ip = 0n;
    let i = s;
    while (i < e && B[i] !== 46) {
        ip = ip * 10n + BigInt(B[i] - 48);
        i++;
    }
    let frac = 0n;
    if (i < e) {
        i++;
        let digits = 0;
        while (i < e) {
            frac = frac * 10n + BigInt(B[i] - 48);
            i++;
            digits++;
        }
        if (digits === 1) frac *= 10n;
    }
    return ip * 100n + frac;
}

function parseAmount(s, e) {
    if (e - s > 13) return parseAmountBig(s, e);
    let ip = 0;
    let i = s;
    while (i < e && B[i] !== 46) {
        ip = ip * 10 + (B[i] - 48);
        i++;
    }
    let frac = 0;
    if (i < e) {
        i++;
        let digits = 0;
        while (i < e) {
            frac = frac * 10 + (B[i] - 48);
            i++;
            digits++;
        }
        if (digits === 1) frac *= 10;
    }
    return ip * 100 + frac;
}

function typeKind(s, e) {
    const n = e - s;
    if (n === 6) {
        if (spanEq(s, e, "credit")) return 0;
        if (spanEq(s, e, "refund")) return 2;
    } else if (n === 5) {
        if (spanEq(s, e, "debit")) return 1;
    } else if (n === 4) {
        if (spanEq(s, e, "void")) return 3;
    }
    return -1;
}

function parseTags() {
    P++;
    let hasTest = false;
    for (;;) {
        skipWs();
        if (B[P] === 93) { P++; return hasTest; }
        parseStringValue();
        if (strE - strS === 4 && spanEq(strS, strE, "test")) hasTest = true;
        skipWs();
        if (B[P] === 44) { P++; continue; }
        if (B[P] === 93) { P++; return hasTest; }
    }
}

let metaS = 0, metaE = 0;
function parseMeta() {
    P++;
    metaS = 0;
    metaE = 0;
    for (;;) {
        skipWs();
        if (B[P] === 125) { P++; return; }
        parseString();
        let ks = strS, ke = strE;
        if (strEsc) ke = decode(ks, ke);
        skipWs();
        P++;
        skipWs();
        if (spanEq(ks, ke, "channel")) {
            parseStringValue();
            metaS = strS;
            metaE = strE;
        } else {
            skipValue();
        }
        skipWs();
        if (B[P] === 44) { P++; continue; }
        if (B[P] === 125) { P++; return; }
    }
}

function parseRatesObject() {
    P++;
    for (;;) {
        skipWs();
        if (B[P] === 125) { P++; return; }
        parseString();
        let ks = strS, ke = strE;
        if (strEsc) ke = decode(ks, ke);
        skipWs();
        P++;
        skipWs();
        let neg = false;
        if (B[P] === 45) { neg = true; P++; }
        // count digits first
        const ds = P;
        while (P < LEN) {
            const c = B[P];
            if (c < 48 || c > 57) break;
            P++;
        }
        const digits = P - ds;
        let v;
        if (digits > 15) {
            let bv = 0n;
            for (let i = ds; i < P; i++) bv = bv * 10n + BigInt(B[i] - 48);
            v = neg ? -bv : bv;
        } else {
            let nv = 0;
            for (let i = ds; i < P; i++) nv = nv * 10 + (B[i] - 48);
            v = neg ? -nv : nv;
        }
        const idx = rates.getOrInsert(ks, ke - ks);
        rates.v1[idx] = v;
        skipWs();
        if (B[P] === 44) { P++; continue; }
        if (B[P] === 125) { P++; return; }
    }
}

function addNet(d) {
    if (bigMode) {
        totalNet += typeof d === "bigint" ? d : BigInt(d);
        return;
    }
    if (Math.abs(totalNet) + Math.abs(d) <= SAFE) {
        totalNet += d;
    } else {
        activateBig();
        totalNet += BigInt(d);
    }
}

function addV1(m, i, d) {
    if (bigMode) {
        const cur = typeof m.v1[i] === "bigint" ? m.v1[i] : BigInt(m.v1[i]);
        m.v1[i] = cur + (typeof d === "bigint" ? d : BigInt(d));
        return;
    }
    const cur = m.v1[i];
    if (Math.abs(cur) + Math.abs(d) <= SAFE) m.v1[i] = cur + d;
    else {
        activateBig();
        m.v1[i] += BigInt(d);
    }
}

function addV2(m, i, d) {
    if (bigMode) {
        const cur = typeof m.v2[i] === "bigint" ? m.v2[i] : BigInt(m.v2[i]);
        m.v2[i] = cur + (typeof d === "bigint" ? d : BigInt(d));
        return;
    }
    const cur = m.v2[i];
    if (Math.abs(cur) + Math.abs(d) <= SAFE) m.v2[i] = cur + d;
    else {
        activateBig();
        m.v2[i] += BigInt(d);
    }
}

function parseTransaction() {
    P++;
    let accS = 0, accE = 0;
    let chS = 0, chE = 0;
    let hundredths = 0;
    let rate = 0;
    let type = -1;
    let hasTest = false;

    for (;;) {
        skipWs();
        if (B[P] === 125) { P++; break; }
        parseString();
        let ks = strS, ke = strE;
        if (strEsc) ke = decode(ks, ke);
        skipWs();
        P++;
        skipWs();

        if (spanEq(ks, ke, "account")) {
            parseStringValue();
            accS = strS;
            accE = strE;
        } else if (spanEq(ks, ke, "type")) {
            parseStringValue();
            type = typeKind(strS, strE);
        } else if (spanEq(ks, ke, "amount")) {
            parseStringValue();
            hundredths = parseAmount(strS, strE);
        } else if (spanEq(ks, ke, "currency")) {
            parseStringValue();
            const ri = rates.find(strS, strE - strS);
            rate = ri >= 0 ? rates.v1[ri] : 0;
        } else if (spanEq(ks, ke, "tags")) {
            hasTest = parseTags();
        } else if (spanEq(ks, ke, "meta")) {
            parseMeta();
            chS = metaS;
            chE = metaE;
        } else {
            skipValue();
        }

        skipWs();
        if (B[P] === 44) { P++; continue; }
        if (B[P] === 125) { P++; break; }
    }

    if (type === 3 || type === -1 || hasTest) return;

    if (!bigMode) {
        if (typeof hundredths === "bigint" || typeof rate === "bigint") {
            activateBig();
        } else if (hundredths !== 0 && hundredths * rate > SAFE) {
            activateBig();
        }
    }

    let usd;
    if (bigMode) {
        const h = typeof hundredths === "bigint" ? hundredths : BigInt(hundredths);
        const rr = typeof rate === "bigint" ? rate : BigInt(rate);
        usd = (h * rr) / 1000000n;
    } else {
        usd = Math.floor(hundredths * rate / 1000000);
    }

    const signed = type === 1 ? -usd : usd;
    addNet(signed);
    totalCount++;

    const ci = channels.getOrInsert(chS, chE - chS);
    addV1(channels, ci, 1);
    addV2(channels, ci, signed);

    const ai = accounts.getOrInsert(accS, accE - accS);
    addV1(accounts, ai, signed);
}

function main() {
    if (process.argv.length < 3) return;
    B = fs.readFileSync(process.argv[2]);
    LEN = B.length;

    rates = new SpanMap(64);
    channels = new SpanMap(64);
    accounts = new SpanMap(1 << 14);

    P = 0;
    skipWs();
    P++;
    for (;;) {
        skipWs();
        if (B[P] === 125) { P++; break; }
        parseString();
        let ks = strS, ke = strE;
        if (strEsc) ke = decode(ks, ke);
        skipWs();
        P++;
        skipWs();
        if (spanEq(ks, ke, "rates")) parseRatesObject();
        else skipValue();
        skipWs();
        if (B[P] === 44) { P++; continue; }
        if (B[P] === 125) { P++; break; }
    }

    for (;;) {
        skipWs();
        if (P >= LEN) break;
        parseTransaction();
    }

    // Channels sorted by name.
    const chIdx = [];
    for (let i = 0; i < channels.cap; i++)
        if (channels.klen[i] >= 0) chIdx.push(i);
    chIdx.sort((a, b) => spanCompare(channels.off[a], channels.klen[a],
                                     channels.off[b], channels.klen[b]));

    // Accounts: top 10 by net desc, then id asc.
    const accIdx = [];
    for (let i = 0; i < accounts.cap; i++)
        if (accounts.klen[i] >= 0) accIdx.push(i);
    accIdx.sort((a, b) => {
        const va = accounts.v1[a], vb = accounts.v1[b];
        if (va !== vb) return va > vb ? -1 : 1;
        return spanCompare(accounts.off[a], accounts.klen[a],
                           accounts.off[b], accounts.klen[b]);
    });
    const k = accIdx.length < 10 ? accIdx.length : 10;

    let out = "counted " + totalCount + "\nnet " + String(totalNet) + "\n";
    for (let j = 0; j < chIdx.length; j++) {
        const idx = chIdx[j];
        out += "channel " + B.toString("utf8", channels.off[idx], channels.off[idx] + channels.klen[idx]) +
            " " + String(channels.v1[idx]) + " " + String(channels.v2[idx]) + "\n";
    }
    for (let j = 0; j < k; j++) {
        const idx = accIdx[j];
        out += "account " + B.toString("utf8", accounts.off[idx], accounts.off[idx] + accounts.klen[idx]) +
            " " + String(accounts.v1[idx]) + "\n";
    }
    process.stdout.write(out);
}

main();
