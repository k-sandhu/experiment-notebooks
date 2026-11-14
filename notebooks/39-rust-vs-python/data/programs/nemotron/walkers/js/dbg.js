"use strict";
const MASK = 0xffffffffn;

function parseU64(s) {
    const bi = BigInt(s);
    return { lo: Number(bi & MASK), hi: Number((bi >> 32n) & MASK) };
}

const C_LO = 0x7F4A7C15;
const C_HI = 0x9E3779B9;

function mul64(a0, a1, b0, b1, out) {
    const a0l = a0 & 0xFFFF, a0h = a0 >>> 16;
    const b0l = b0 & 0xFFFF, b0h = b0 >>> 16;
    const p = Math.imul(a0l, b0l) >>> 0;
    const t = (Math.imul(a0l, b0h) >>> 0) + (Math.imul(a0h, b0l) >>> 0);
    const q = ((t | 0) >>> 16) + (t >= 0x100000000 ? 0x10000 : 0);
    const r = t & 0xFFFF;
    const r16 = r * 0x10000;  // exact double, < 2^32
    const carry2 = p + r16 >= 0x100000000 ? 1 : 0;
    const u = Math.imul(a0h, b0h) >>> 0;
    const mid = (Math.imul(a0, b1) >>> 0) + (Math.imul(a1, b0) >>> 0);
    out[0] = (p + r16) | 0;
    out[1] = (u + q + carry2 + mid) | 0;
}

function limbs(bi) {
    return { lo: Number(bi & MASK), hi: Number((bi >> 32n) & MASK) };
}
function combine(l) {
    return (BigInt(l.hi >>> 0) << 32n) | BigInt(l.lo >>> 0);
}

const seed = parseU64("18446744073709551615");
let rLo = seed.lo, rHi = seed.hi; // limb state
let bState = BigInt(seed.lo) | (BigInt(seed.hi) << 32n); // bigint state

const out = [0, 0];
let t0, t1;
for (let step = 0; step < 5; ++step) {
    // reference (BigInt)
    bState = (bState + BigInt(C_HI) * 0x100000000n + BigInt(C_LO)) % (0xffffffffffffffffn + 1n);
    let z = bState;
    z = ((z ^ (z >> 30n)) * 0xBF58476D1CE4E5B9n) % (0xffffffffffffffffn + 1n);
    z = ((z ^ (z >> 27n)) * 0x94D049BB133111EBn) % (0xffffffffffffffffn + 1n);
    const rRef = z ^ (z >> 31n);

    // limbs: state += C
    let t = rLo + C_LO;
    let carry = ((rLo >>> 0) + (C_LO >>> 0) >= 0x100000000) ? 1 : 0;
    rLo = t | 0;
    rHi = (rHi + C_HI + carry) | 0;
    const cur = combine({ lo: rLo, hi: rHi });
    if (cur !== bState) { console.log("STATE MISMATCH step", step, cur.toString(), bState.toString()); process.exit(1); }

    let z0 = rLo, z1 = rHi;
    t0 = (z0 >>> 30) | ((z1 << 2) | 0);
    t1 = z1 >>> 30;
    z0 ^= t0; z1 ^= t1;
    mul64(z0, z1, 0x1CE4E5B9, 0xBF58476D, out);
    z0 = out[0]; z1 = out[1];
    t0 = (z0 >>> 27) | ((z1 << 5) | 0);
    t1 = z1 >>> 27;
    z0 ^= t0; z1 ^= t1;
    mul64(z0, z1, 0x133111EB, 0x94D049BB, out);
    z0 = out[0]; z1 = out[1];
    t0 = (z0 >>> 31) | ((z1 << 1) | 0);
    const r1 = z1 ^ (z1 >>> 31);
    const r0 = z0 ^ t0;
    const rLimb = (BigInt(r1 >>> 0) << 32n) | BigInt(r0 >>> 0);
    if (rLimb !== rRef) {
        console.log("R MISMATCH step", step, rLimb.toString(), rRef.toString());
        console.log(" z limbs:", combine({lo: z0, hi: z1}).toString(), "ref z:", z.toString());
        process.exit(1);
    }
    console.log("step", step, "OK r=", rLimb.toString(), "d=", Number(rRef >> 62n));
}
console.log("ALL OK");
