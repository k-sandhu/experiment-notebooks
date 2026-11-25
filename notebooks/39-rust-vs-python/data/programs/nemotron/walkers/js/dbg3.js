"use strict";
const MASK = 0xffffffffn;
const MOD = 0xffffffffffffffffn + 1n;

function rand64() {
    return (BigInt(Math.floor(Math.random() * 0x100000000)) << 32n) | BigInt(Math.floor(Math.random() * 0x100000000));
}
function limbs(bi) {
    return { lo: Number(bi & MASK), hi: Number((bi >> 32n) & MASK) };
}

// current (new) formula
function mul64New(a0, a1, b0, b1, out) {
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
    out[0] = (p + r16) | 0;
    out[1] = (u + q + carry2 + mid) | 0;
}

// old formula
function mul64Old(a0, a1, b0, b1, out) {
    const m0u = Math.imul(a0, b0) >>> 0;
    const h1 = m0u >>> 16;
    const a0l = a0 & 0xFFFF, a0h = a0 >>> 16;
    const b0l = b0 & 0xFFFF, b0h = b0 >>> 16;
    const s = (Math.imul(a0l, b0h) >>> 0) + (Math.imul(a0h, b0l) >>> 0) + h1;
    const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
    out[0] = m0u;
    out[1] = (Math.imul(a0h, b0h) + ((s | 0) >>> 16) + (s >= 0x100000000 ? 0x10000 : 0) + mid) | 0;
}

const out = [0, 0];
let failsNew = 0, failsOld = 0;
const N = 200000;
for (let i = 0; i < N; ++i) {
    const a = rand64(), b = rand64();
    const ref = (a * b) % MOD;
    const la = limbs(a), lb = limbs(b);
    mul64New(la.lo, la.hi, lb.lo, lb.hi, out);
    const gotNew = (BigInt(out[1] >>> 0) << 32n) | BigInt(out[0] >>> 0);
    if (gotNew !== ref) { if (failsNew < 5) console.log("NEW fail", a.toString(), b.toString(), ref.toString(), gotNew.toString()); ++failsNew; }
    mul64Old(la.lo, la.hi, lb.lo, lb.hi, out);
    const gotOld = (BigInt(out[1] >>> 0) << 32n) | BigInt(out[0] >>> 0);
    if (gotOld !== ref) { if (failsOld < 5) console.log("OLD fail", a.toString(), b.toString(), ref.toString(), gotOld.toString()); ++failsOld; }
}
console.log("done new fails:", failsNew, "old fails:", failsOld, "of", N);
