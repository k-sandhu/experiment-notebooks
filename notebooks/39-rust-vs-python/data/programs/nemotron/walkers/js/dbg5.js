"use strict";
const MASK = 0xffffffffn;
const MOD = 0xffffffffffffffffn + 1n;

const a = 14972417095725547289n, b = 1653310713498880480n;
const ref = (a * b) % MOD;
const a0 = Number(a & MASK), a1 = Number((a >> 32n) & MASK);
const b0 = Number(b & MASK), b1 = Number((b >> 32n) & MASK);
console.log("ref", ref.toString());
console.log("a0", a0, "a1", a1, "b0", b0, "b1", b1);

const pFull = BigInt(a0) * BigInt(b0);
console.log("a0*b0", pFull.toString(), "floor/2^32", (pFull >> 32n).toString(), "lo", (pFull & MASK).toString());

const midExact = (BigInt(a0) * BigInt(b1) + BigInt(a1) * BigInt(b0)) % MOD;
console.log("mid exact mod 2^32:", (midExact & 0xffffffffn).toString());

const a0l = a0 & 0xFFFF, a0h = a0 >>> 16;
const b0l = b0 & 0xFFFF, b0h = b0 >>> 16;
const p = Math.imul(a0l, b0l) >>> 0;
const t = (Math.imul(a0l, b0h) >>> 0) + (Math.imul(a0h, b0l) >>> 0);
const q = ((t | 0) >>> 16) + (t >= 0x100000000 ? 0x10000 : 0);
const r = t & 0xFFFF;
const r16 = r * 0x10000;
const carry2 = p + r16 >= 0x100000000 ? 1 : 0;
const u = Math.imul(a0h, b0h) >>> 0;
const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
console.log("p", p, "t", t, "q", q, "r", r, "carry2", carry2, "u", u, "mid", mid);
console.log("check p + r16 =", (p + r16).toString(), "mod 2^32:", ((p + r16) | 0).toString(), "vs imul(a0,b0)", (Math.imul(a0, b0) >>> 0).toString());
console.log("u+q+carry2 =", (u + q + carry2).toString(), "vs floor/2^32 mod 2^32:", Number((pFull >> 32n) & MASK).toString());
