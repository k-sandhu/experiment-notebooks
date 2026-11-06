"use strict";

// Log scan: summarise an access log by status class and path-template latency
// percentiles. Node 22, built-in modules only.

const fs = require("fs");

function isDigit(c) { return c >= 0x30 && c <= 0x39; }
function isUpper(c) { return c >= 0x41 && c <= 0x5A; }
function isLower(c) { return c >= 0x61 && c <= 0x7A; }

class Stats {
    constructor() {
        this.count = 0;
        this.maxT = 0; // max latency in tenths of a ms
        this.lats = [];
    }
    add(t) {
        this.count++;
        if (t > this.maxT) this.maxT = t;
        this.lats.push(t);
    }
}

// Strictly validates one line (Buffer slice without trailing \n). Returns
// [statusClass, latencyT, template, ok].
function parseLine(line) {
    let i = 0;
    const n = line.length;

    // 1. timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<space>
    if (n - i < 25) return null;
    if (!isDigit(line[i]) || !isDigit(line[i + 1]) || !isDigit(line[i + 2]) || !isDigit(line[i + 3])) return null;
    if (line[i + 4] !== 0x2D) return null; // '-'
    if (!isDigit(line[i + 5]) || !isDigit(line[i + 6])) return null;
    if (line[i + 7] !== 0x2D) return null;
    if (!isDigit(line[i + 8]) || !isDigit(line[i + 9])) return null;
    if (line[i + 10] !== 0x54) return null; // 'T'
    if (!isDigit(line[i + 11]) || !isDigit(line[i + 12])) return null;
    if (line[i + 13] !== 0x3A) return null; // ':'
    if (!isDigit(line[i + 14]) || !isDigit(line[i + 15])) return null;
    if (line[i + 16] !== 0x3A) return null;
    if (!isDigit(line[i + 17]) || !isDigit(line[i + 18])) return null;
    if (line[i + 19] !== 0x2E) return null; // '.'
    if (!isDigit(line[i + 20]) || !isDigit(line[i + 21]) || !isDigit(line[i + 22])) return null;
    if (line[i + 23] !== 0x5A || line[i + 24] !== 0x20) return null; // 'Z' ' '
    i += 25;

    // 2. host: [a-z]+-\d+<space>
    if (i >= n || !isLower(line[i])) return null;
    while (i < n && isLower(line[i])) i++;
    if (i >= n || line[i] !== 0x2D) return null; // '-'
    i++;
    if (i >= n || !isDigit(line[i])) return null;
    while (i < n && isDigit(line[i])) i++;
    if (i >= n || line[i] !== 0x20) return null;
    i++;

    // 3. method
    let ok = false;
    if (!ok && n - i > 3 && line[i] === 0x47 && line[i + 1] === 0x45 && line[i + 2] === 0x54 && line[i + 3] === 0x20) { i += 4; ok = true; } // GET
    if (!ok && n - i > 4 && line[i] === 0x50 && line[i + 1] === 0x4F && line[i + 2] === 0x53 && line[i + 3] === 0x54 && line[i + 4] === 0x20) { i += 5; ok = true; } // POST
    if (!ok && n - i > 3 && line[i] === 0x50 && line[i + 1] === 0x55 && line[i + 2] === 0x54 && line[i + 3] === 0x20) { i += 4; ok = true; } // PUT
    if (!ok && n - i > 6 && line[i] === 0x44 && line[i + 1] === 0x45 && line[i + 2] === 0x4C && line[i + 3] === 0x45 && line[i + 4] === 0x54 && line[i + 5] === 0x45 && line[i + 6] === 0x20) { i += 7; ok = true; } // DELETE
    if (!ok && n - i > 5 && line[i] === 0x50 && line[i + 1] === 0x41 && line[i + 2] === 0x54 && line[i + 3] === 0x43 && line[i + 4] === 0x48 && line[i + 5] === 0x20) { i += 6; ok = true; } // PATCH
    if (!ok) return null;

    // 4. path + template
    const tb = [];
    tb.push(0x2F); // '/'
    i++;
    let segStart = 1; // index in tb right after the leading '/'
    let segDigits = true;
    let segLen = 0;
    let done = false;
    for (;;) {
        if (i >= n) return null;
        const c = line[i];
        if (c === 0x2F) { // '/'
            if (segLen > 0 && segDigits) {
                tb.length = segStart;
                tb.push(0x7B, 0x69, 0x64, 0x7D); // '{id}'
            }
            tb.push(0x2F);
            i++;
            segStart = tb.length;
            segDigits = true;
            segLen = 0;
        } else if (c === 0x20) { // ' '
            if (segLen > 0 && segDigits) {
                tb.length = segStart;
                tb.push(0x7B, 0x69, 0x64, 0x7D);
            }
            i++;
            done = true;
            break;
        } else if (c === 0x3F) { // '?'
            if (segLen > 0 && segDigits) {
                tb.length = segStart;
                tb.push(0x7B, 0x69, 0x64, 0x7D);
            }
            i++;
            while (i < n && line[i] !== 0x20) i++;
            if (i >= n) return null;
            i++;
            done = true;
            break;
        } else {
            if (!isDigit(c) && !isUpper(c) && !isLower(c) && c !== 0x5F && c !== 0x2D) return null; // '_' '-'
            if (segLen === 0) segDigits = isDigit(c);
            else if (segDigits && !isDigit(c)) segDigits = false;
            segLen++;
            tb.push(c);
            i++;
        }
    }
    if (!done) return null;

    // 5. status: \d{3}<space>
    if (n - i < 4) return null;
    if (!isDigit(line[i]) || !isDigit(line[i + 1]) || !isDigit(line[i + 2])) return null;
    if (line[i + 3] !== 0x20) return null;
    const statusClass = line[i] - 0x30;
    i += 4;

    // 6. size: \d+B<space>
    if (i >= n || !isDigit(line[i])) return null;
    while (i < n && isDigit(line[i])) i++;
    if (i >= n || line[i] !== 0x42) return null; // 'B'
    i++;
    if (i >= n || line[i] !== 0x20) return null;
    i++;

    // 7. latency: \d+.\d ms<space>
    let ip = 0;
    const ls = i;
    while (i < n && isDigit(line[i])) { ip = ip * 10 + (line[i] - 0x30); i++; }
    if (i === ls || i >= n || line[i] !== 0x2E) return null; // '.'
    i++;
    if (i >= n || !isDigit(line[i])) return null;
    const frac = line[i] - 0x30;
    i++;
    if (n - i < 3 || line[i] !== 0x6D || line[i + 1] !== 0x73 || line[i + 2] !== 0x20) return null; // 'm' 's' ' '
    i += 3;
    const latencyT = ip * 10 + frac;

    // 8. "..." then end of line
    if (i >= n || line[i] !== 0x22) return null; // '"'
    i++;
    while (i < n && line[i] !== 0x22) i++;
    if (i >= n) return null;
    i++;
    if (i !== n) return null;

    return [statusClass, latencyT, Buffer.from(tb).toString("utf8"), true];
}

function pos(pct, nn) {
    return Math.floor((pct * nn + 99) / 100) - 1; // nearest-rank, 0-based index
}

function main() {
    const b = fs.readFileSync(process.argv[2]);
    const n = b.length;
    let p = 0;
    let lines = 0, malformed = 0;
    const statusCount = new Uint32Array(10);
    const map = new Map();

    const out = [];

    while (p < n) {
        let nl = p;
        while (nl < n && b[nl] !== 0x0A) nl++; // '\n'
        const line = b.subarray(p, nl);
        p = nl + 1;
        lines++;
        const r = parseLine(line);
        if (r === null) {
            malformed++;
            continue;
        }
        const sc = r[0], lat = r[1], tmpl = r[2];
        statusCount[sc]++;
        let s = map.get(tmpl);
        if (s === undefined) {
            s = new Stats();
            map.set(tmpl, s);
        }
        s.add(lat);
    }

    out.push("lines " + lines + "\n");
    out.push("malformed " + malformed + "\n");
    for (let d = 0; d < 10; d++) {
        if (statusCount[d] !== 0) {
            out.push("status " + String.fromCharCode(0x30 + d) + "xx " + statusCount[d] + "\n");
        }
    }

    const paths = [];
    for (const [key, s] of map) paths.push({ key, s });
    paths.sort((a, b) => {
        if (b.s.count !== a.s.count) return b.s.count - a.s.count;
        if (a.key < b.key) return -1;
        if (a.key > b.key) return 1;
        return 0;
    });
    const limit = Math.min(paths.length, 10);
    for (let i = 0; i < limit; i++) {
        const pe = paths[i];
        const s = pe.s;
        s.lats.sort((a, b) => a - b);
        const nn = s.lats.length;
        const p50 = s.lats[pos(50, nn)];
        const p95 = s.lats[pos(95, nn)];
        out.push("path " + pe.key + " " + s.count + " "
            + Math.floor(p50 / 10) + "." + (p50 % 10) + " "
            + Math.floor(p95 / 10) + "." + (p95 % 10) + " "
            + Math.floor(s.maxT / 10) + "." + (s.maxT % 10) + "\n");
    }

    process.stdout.write(Buffer.concat(out.map(s => Buffer.from(s, "utf8"))));
}

main();
