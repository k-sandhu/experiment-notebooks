"use strict";

const fs = require("node:fs");

// Pack two 16-bit IDs into one word. Larger vocabularies use two words, avoiding
// BigInt overhead and the precision limit of packing 64 bits into a Number.
class PairList {
    constructor(estimate) {
        this.keys = new Uint32Array(Math.max(16, estimate));
        this.high = null;
        this.size = 0;
    }
    grow() {
        const keys = new Uint32Array(this.keys.length * 2);
        keys.set(this.keys); this.keys = keys;
        if (this.high !== null) {
            const high = new Uint32Array(keys.length);
            high.set(this.high); this.high = high;
        }
    }
    add(a, b) {
        if (this.high === null && (a > 65535 || b > 65535)) {
            this.high = new Uint32Array(this.keys.length);
            for (let i = 0; i < this.size; ++i) {
                this.high[i] = this.keys[i] >>> 16; this.keys[i] &= 65535;
            }
        }
        if (this.size === this.keys.length) this.grow();
        if (this.high === null) this.keys[this.size++] = (a << 16) | b;
        else { this.high[this.size] = a; this.keys[this.size++] = b; }
    }
    sort() {
        const size = this.size;
        if (size < 2) return;
        if (this.high === null && size < 2048) {
            this.keys.subarray(0, size).sort(); return;
        }
        let keys = this.keys, high = this.high;
        let variation = 0, highVariation = 0;
        const first = keys[0], firstHigh = high === null ? 0 : high[0];
        for (let i = 1; i < size; ++i) {
            variation |= keys[i] ^ first;
            if (high !== null) highVariation |= high[i] ^ firstHigh;
        }
        if (variation === 0 && highVariation === 0) return;
        let scratch = new Uint32Array(size);
        const offsets = new Uint32Array(2048);
        if (high === null) {
            for (let shift = 0; shift < 32; shift += 11) {
                if (((variation >>> shift) & 2047) === 0) continue;
                offsets.fill(0);
                for (let i = 0; i < size; ++i) ++offsets[(keys[i] >>> shift) & 2047];
                let total = 0;
                for (let j = 0; j < offsets.length; ++j) { const count = offsets[j]; offsets[j] = total; total += count; }
                for (let i = 0; i < size; ++i) scratch[offsets[(keys[i] >>> shift) & 2047]++] = keys[i];
                const swap = keys; keys = scratch; scratch = swap;
            }
        } else {
            let scratchHigh = new Uint32Array(size);
            for (let part = 0; part < 2; ++part) {
                const changes = part === 0 ? variation : highVariation;
                for (let shift = 0; shift < 32; shift += 11) {
                    if (((changes >>> shift) & 2047) === 0) continue;
                    offsets.fill(0);
                    const field = part === 0 ? keys : high;
                    for (let i = 0; i < size; ++i) ++offsets[(field[i] >>> shift) & 2047];
                    let total = 0;
                    for (let j = 0; j < offsets.length; ++j) { const count = offsets[j]; offsets[j] = total; total += count; }
                    for (let i = 0; i < size; ++i) {
                        const p = offsets[(field[i] >>> shift) & 2047]++;
                        scratch[p] = keys[i]; scratchHigh[p] = high[i];
                    }
                    const swap = keys; keys = scratch; scratch = swap;
                    const swapHigh = high; high = scratchHigh; scratchHigh = swapHigh;
                }
            }
        }
        this.keys = keys; this.high = high;
    }
}

class Vocabulary {
    constructor(data) {
        this.data = data;
        this.slots = new Uint32Array(1024);
        this.starts = [0]; this.lengths = [0]; this.hashes = [0];
    }
    intern(start, length, hash) {
        let mask = this.slots.length - 1, p = hash & mask;
        while (this.slots[p] !== 0) {
            const id = this.slots[p];
            if (this.hashes[id] === hash && this.lengths[id] === length) {
                const previous = this.starts[id];
                let j = 0;
                while (j < length && this.data[start + j] === this.data[previous + j]) ++j;
                if (j === length) return id;
            }
            p = (p + 1) & mask;
        }
        const id = this.starts.length;
        if (id >= this.slots.length - this.slots.length / 4) {
            this.slots = new Uint32Array(this.slots.length * 2); mask = this.slots.length - 1;
            for (let k = 1; k < id; ++k) {
                let q = this.hashes[k] & mask;
                while (this.slots[q] !== 0) q = (q + 1) & mask;
                this.slots[q] = k;
            }
            p = hash & mask; while (this.slots[p] !== 0) p = (p + 1) & mask;
        }
        this.starts.push(start); this.lengths.push(length); this.hashes.push(hash);
        this.slots[p] = id;
        return id;
    }
}

function main() {
    const data = fs.readFileSync(process.argv[2]);
    const vocabulary = new Vocabulary(data), pairs = new PairList(Math.floor(data.length / 6));
    let wordCount = 0, pairCount = 0, previous = 0, i = 0;
    while (i < data.length) {
        let c = data[i] | 32;
        if (c >= 97 && c <= 122) {
            const start = i;
            let hash = 0x811c9dc5;
            do {
                data[i++] = c;
                hash = Math.imul(hash ^ c, 16777619);
                if (i === data.length) break;
                c = data[i] | 32;
            } while (c >= 97 && c <= 122);
            const id = vocabulary.intern(start, i - start, hash >>> 0);
            ++wordCount;
            if (previous !== 0) { pairs.add(previous, id); ++pairCount; }
            previous = id;
        } else {
            const raw = data[i++];
            if (raw === 46 || raw === 33 || raw === 63) previous = 0;
        }
    }
    const words = new Array(vocabulary.starts.length), order = [];
    for (i = 1; i < words.length; ++i) {
        words[i] = data.toString("ascii", vocabulary.starts[i], vocabulary.starts[i] + vocabulary.lengths[i]);
        order.push(i);
    }
    order.sort((a, b) => words[a] < words[b] ? -1 : words[a] > words[b] ? 1 : 0);
    const rank = new Uint32Array(words.length);
    for (i = 0; i < order.length; ++i) rank[order[i]] = i;
    const topFirst = new Uint32Array(20), topSecond = new Uint32Array(20), topCounts = new Float64Array(20);
    let used = 0;
    function better(a, b, count, p) {
        if (count !== topCounts[p]) return count > topCounts[p];
        const ar = rank[a], br = rank[topFirst[p]];
        return ar !== br ? ar < br : rank[b] < rank[topSecond[p]];
    }
    pairs.sort();
    const keys = pairs.keys, high = pairs.high;
    let distinct = 0;
    for (i = 0; i < pairs.size;) {
        const start = i, key = keys[i];
        const a = high === null ? key >>> 16 : high[i];
        const b = high === null ? key & 65535 : key;
        ++i;
        while (i < pairs.size && keys[i] === key && (high === null || high[i] === a)) ++i;
        const count = i - start;
        ++distinct;
        if (used === 20 && !better(a, b, count, 19)) continue;
        let p = Math.min(used, 19);
        while (p > 0 && better(a, b, count, p - 1)) {
            topFirst[p] = topFirst[p - 1]; topSecond[p] = topSecond[p - 1]; topCounts[p] = topCounts[p - 1]; --p;
        }
        topFirst[p] = a; topSecond[p] = b; topCounts[p] = count;
        if (used < 20) ++used;
    }
    let output = `words ${wordCount}\npairs ${pairCount}\ndistinct ${distinct}\n`;
    for (i = 0; i < used; ++i) output += `${topCounts[i]} ${words[topFirst[i]]} ${words[topSecond[i]]}\n`;
    process.stdout.write(output);
}

main();
