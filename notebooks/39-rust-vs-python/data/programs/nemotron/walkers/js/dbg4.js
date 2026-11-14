"use strict";
const MASK = 0xffffffffn;
const MOD = 0xffffffffffffffffn + 1n;

const a = 7297201311842303532n, b = 12246979555848469589n;
const ref = (a * b) % MOD;
const a0 = Number(a & MASK), a1 = Number((a >> 32n) & MASK);
const b0 = Number(b & MASK), b1 = Number((b >> 32n) & MASK);
console.log("a0", a0, "a1", a1, "b0", b0, "b1", b1);

// new formula step by step
const a0l = a0 & 0xFFFF, a0h = a0 >>> 16;
const b0l = b0 & 0xFFFF, b0h = b0 >>> 16;
const p = Math.imul(a0l, b0l) >>> 0;
const t1u = Math.imul(a0l, b0h) >>> 0;
const t2u = Math.imul(a0h, b0l) >>> 0;
const t = t1u + t2u;
const q = ((t | 0) >>> 16) + (t >= 0x100000000 ? 0x10000 : 0);
const r = t & 0xFFFF;
const carry2 = p + (r << 16) >= 0x100000000 ? 1 : 0;
const u = Math.imul(a0h, b0h) >>> 0;
const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
const lo = (p + (r << 16)) | 0;
const h = (u + q + carry2 + mid) | 0;
const got = (BigInt(h >>> 0) << 32n) | BigInt(lo >>> 0);
console.log("p", p, "t1", t1u, "t2", t2u, "t", t, "q", q, "r", r, "carry2", carry2, "u", u);
console.log("mid", mid, "lo", lo, "h", h);
console.log("ref ", ref.toString());
console.log("got ", got.toString());

// direct high half of a0*b0
const pFull = BigInt(a0) * BigInt(b0);
console.log("a0*b0 =", pFull.toString(), "hi =", (pFull >> 32n).toString(), "lo =", (pFull & MASK).toString());
console.log("u + q + carry2 =", (u + q + carry2).toString());
console.log("q check: floor(t/2^16) =", (BigInt(t) >> 16n).toString());
