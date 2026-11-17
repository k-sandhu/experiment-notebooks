"use strict";

const fs = require("node:fs");
const stamp = Buffer.from("0000-00-00T00:00:00.000Z ", "ascii");
const pathChars = new Uint8Array(256);
function digit(c) { return c >= 48 && c <= 57; }
for (let c = 0; c < 256; ++c)
    pathChars[c] = digit(c) || c >= 65 && c <= 90 || c >= 97 && c <= 122 || c === 95 || c === 47 || c === 45;

function method(b, start, length, name) {
    if (length !== name.length) return false;
    for (let j = 0; j < length; ++j) if (b[start+j] !== name.charCodeAt(j)) return false;
    return true;
}

class Group {
    constructor(key, next) {
        this.key = key;
        this.next = next;
        this.values = null;
        this.size = 0;
        this.large = null;
    }
    add(value) {
        if (this.values === null) this.values = new Float64Array(4);
        else if (this.size === this.values.length) {
            const grown = new Float64Array(this.size * 2);
            grown.set(this.values);
            this.values = grown;
        }
        this.values[this.size++] = value;
    }
    get count() { return this.size + (this.large === null ? 0 : this.large.length); }
}

class Scanner {
    constructor() {
        // Numeric hashes and reusable bytes avoid allocating a path string per line.
        // A collision chain still compares every byte, so hash collisions are harmless.
        this.groups = new Map();
        this.key = Buffer.allocUnsafe(256);
        this.statuses = new Float64Array(10);
        this.lines = 0;
        this.malformed = 0;
    }
    parse(b, from, end) {
        if (end-from < 50) return false;
        for (let j = 0; j < stamp.length; ++j)
            if (stamp[j] === 48 ? !digit(b[from+j]) : b[from+j] !== stamp[j]) return false;
        let i = from+25, start = i;
        while (i < end && b[i] >= 97 && b[i] <= 122) ++i;
        if (i === start || i === end || b[i++] !== 45) return false;
        start = i;
        while (i < end && digit(b[i])) ++i;
        if (i === start || i === end || b[i++] !== 32) return false;
        start = i;
        while (i < end && b[i] !== 32) ++i;
        const length = i-start;
        if (i === end || !(method(b,start,length,"GET") || method(b,start,length,"POST") ||
            method(b,start,length,"PUT") || method(b,start,length,"DELETE") || method(b,start,length,"PATCH"))) return false;
        ++i;
        if (i === end || b[i] !== 47) return false;
        const pathStart = i;
        while (i < end && pathChars[b[i]]) ++i;
        const pathEnd = i;
        if (i < end && b[i] === 63) while (i < end && b[i] !== 32) ++i;
        if (i === end || b[i++] !== 32) return false;
        if (end-i < 4 || !digit(b[i]) || !digit(b[i+1]) || !digit(b[i+2]) || b[i+3] !== 32) return false;
        const status = b[i]-48;
        i += 4;
        start = i;
        while (i < end && digit(b[i])) ++i;
        if (i === start || end-i < 2 || b[i] !== 66 || b[i+1] !== 32) return false;
        i += 2;
        start = i;
        while (i < end && b[i] === 48) ++i;
        const significant = i;
        while (i < end && digit(b[i])) ++i;
        const decimal = i;
        if (i === start || end-i < 7 || b[i] !== 46 || !digit(b[i+1]) || b[i+2] !== 109 ||
            b[i+3] !== 115 || b[i+4] !== 32 || b[i+5] !== 34 || b[end-1] !== 34 ||
            b.indexOf(34, i+6) !== end-1) return false;

        const needed = (pathEnd-pathStart)*3;
        if (this.key.length < needed) this.key = Buffer.allocUnsafe(Math.max(needed, this.key.length*2));
        const key = this.key;
        let p = pathStart, used = 0;
        while (p < pathEnd) {
            key[used++] = 47;
            start = ++p;
            let numeric = true;
            while (p < pathEnd && b[p] !== 47) { if (!digit(b[p])) numeric = false; ++p; }
            if (p !== start && numeric) {
                key[used++] = 123; key[used++] = 105; key[used++] = 100; key[used++] = 125;
            } else {
                for (let j = start; j < p; ++j) key[used++] = b[j];
            }
        }
        let hash = 2166136261;
        for (let j = 0; j < used; ++j) hash = Math.imul(hash ^ key[j], 16777619);
        const head = this.groups.get(hash);
        let g = head;
        while (g !== undefined) {
            if (g.key.length === used) {
                let j = 0;
                while (j < used && key[j] === g.key[j]) ++j;
                if (j === used) break;
            }
            g = g.next;
        }
        if (g === undefined) {
            const stored = Buffer.allocUnsafe(used);
            key.copy(stored, 0, 0, used);
            g = new Group(stored, head);
            this.groups.set(hash, g);
        }
        if (decimal-significant <= 14) {
            let value = 0;
            for (let j = significant; j < decimal; ++j) value = value*10 + b[j]-48;
            g.add(value*10 + b[decimal+1]-48);
        } else {
            if (g.large === null) g.large = [];
            g.large.push(b.toString("ascii", significant, decimal) + String.fromCharCode(b[decimal+1]));
        }
        ++this.statuses[status];
        return true;
    }
    read(path) {
        const fd = fs.openSync(path, "r");
        let buffer = Buffer.allocUnsafe(1 << 20), used = 0;
        try {
            for (;;) {
                const got = fs.readSync(fd, buffer, used, buffer.length-used, null);
                if (got === 0) break;
                const end = used+got;
                let begin = 0;
                while (begin < end) {
                    const next = buffer.indexOf(10, begin);
                    if (next < 0 || next >= end) break;
                    ++this.lines;
                    if (!this.parse(buffer, begin, next)) ++this.malformed;
                    begin = next+1;
                }
                used = end-begin;
                if (used) buffer.copy(buffer, 0, begin, end);
                if (used === buffer.length) {
                    const grown = Buffer.allocUnsafe(buffer.length*2);
                    buffer.copy(grown, 0, 0, used);
                    buffer = grown;
                }
            }
        } finally { fs.closeSync(fd); }
    }
    output() {
        const out = [`lines ${this.lines}\nmalformed ${this.malformed}\n`];
        for (let c = 0; c < 10; ++c)
            if (this.statuses[c]) out.push(`status ${c}xx ${this.statuses[c]}\n`);
        const top = [];
        for (const head of this.groups.values()) {
            for (let g = head; g !== undefined; g = g.next) {
                let pos = top.length;
                while (pos > 0 && better(g, top[pos-1])) --pos;
                if (pos >= 10) continue;
                top.splice(pos, 0, g);
                if (top.length > 10) top.pop();
            }
        }
        for (const g of top) {
            // Typed-array sorting is numeric and runs in Node's native implementation.
            if (g.size > 1) g.values.subarray(0, g.size).sort();
            if (g.large !== null) g.large.sort((a,b) => a.length-b.length || (a < b ? -1 : a > b ? 1 : 0));
            const count = g.count;
            out.push(`path ${g.key.toString("ascii")} ${count} ${at(g,Math.floor((count-1)/2))} ` +
                `${at(g,count-1-Math.floor(count/20))} ${at(g,count-1)}\n`);
        }
        process.stdout.write(out.join(""));
    }
}
function better(a, b) { return a.count !== b.count ? a.count > b.count : Buffer.compare(a.key,b.key) < 0; }
function at(g, rank) {
    if (rank < g.size) {
        const v = g.values[rank];
        return `${Math.floor(v/10)}.${v%10}`;
    }
    const s = g.large[rank-g.size];
    return s.slice(0,-1) + "." + s.slice(-1);
}

if (process.argv.length < 3) process.exit(1);
const scanner = new Scanner();
scanner.read(process.argv[2]);
scanner.output();
