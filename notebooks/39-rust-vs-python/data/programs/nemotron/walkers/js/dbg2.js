"use strict";
const MASK = 0xffffffffn;
function mul64(a0, a1, b0, b1, out) {
    const m0u = Math.imul(a0, b0) >>> 0;
    const h1 = m0u >>> 16;
    const a0l = a0 & 0xFFFF, a0h = a0 >>> 16;
    const b0l = b0 & 0xFFFF, b0h = b0 >>> 16;
    const s = (Math.imul(a0l, b0h) >>> 0) + (Math.imul(a0h, b0l) >>> 0);
    const q = ((s | 0) >>> 16) + (s >= 0x100000000 ? 0x10000 : 0);
    const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
    out[0] = m0u;
    out[1] = (Math.imul(a0h, b0h) + h1 + q + mid) | 0;
    return { m0u, h1, s, q, mid };
}
// state = 0xFFFFFFFFFFFFFFFF * 0xBF58476D1CE4E5B9 mod 2^64
const a = 0xFFFFFFFFFFFFFFFFn;
const b = 0xBF58476D1CE4E5B9n;
const ref = (a * b) % (0xffffffffffffffffn + 1n);
const a0 = Number(a & MASK), a1 = Number((a >> 32n) & MASK);
const b0 = Number(b & MASK), b1 = Number((b >> 32n) & MASK);
const out = [0, 0];
const info = mul64(a0, a1, b0, b1, out);
const got = (BigInt(out[1] >>> 0) << 32n) | BigInt(out[0] >>> 0);
console.log("ref", ref.toString());
console.log("got", got.toString());
console.log("info", info);
console.log("match", got === ref);

// also test the old (buggy) formula for comparison
function mul64Old(a0, a1, b0, b1, out) {
    const m0u = Math.imul(a0, b0) >>> 0;
    const a0l = a0 & 0xFFFF, a0h = a0 >>> 16;
    const b0l = b0 & 0xFFFF, b0h = b0 >>> 16;
    const s = (Math.imul(a0l, b0h) >>> 0) + (Math.imul(a0h, b0l) >>> 0) + (m0u >>> 16);
    const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
    out[0] = m0u;
    out[1] = (Math.imul(a0h, b0h) + ((s | 0) >>> 16) + (s >= 0x100000000 ? 0x10000 : 0) + mid) | 0;
}
const out2 = [0, 0];
mul64Old(a0, a1, b0, b1, out2);
const got2 = (BigInt(out2[1] >>> 0) << 32n) | BigInt(out2[0] >>> 0);
console.log("old got", got2.toString(), "old match", got2 === ref);
