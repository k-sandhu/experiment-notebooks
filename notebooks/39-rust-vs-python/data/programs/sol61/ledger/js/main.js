"use strict";
const fs = require("node:fs");
const { StringDecoder } = require("node:string_decoder");

const rates = new Map();
const accounts = new Map();
const channels = new Map();
let counted = 0, net = 0;
let first = true;

// Preserve numeric lexemes before native JSON parsing of the small rates header.
function integerLiteral(s) {
    const m = /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(s);
    const fraction = m[3] || "";
    let digits = m[2] + fraction;
    const scale = Number(m[4] || 0) - fraction.length;
    // Low 64 bits suffice: every amount*rate product is guaranteed to fit int64.
    if (scale >= 64) return 0n;
    if (scale < 0) {
        const keep = digits.length + scale;
        if (keep <= 0) return 0n;
        digits = digits.slice(0, keep);
    }
    let n = BigInt(m[1] + digits);
    if (scale > 0) n *= 10n ** BigInt(scale);
    return BigInt.asIntN(64, n);
}
function header(line) {
    const exact = line.replace(/"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g,
        token => token.charCodeAt(0) === 34 ? token : '"' + token + '"');
    const values = JSON.parse(exact).rates;
    for (const currency of Object.keys(values)) {
        const big = integerLiteral(values[currency]);
        rates.set(currency, { big, number: Number(big) });
    }
}
function hundredths(s) {
    let n = 0, i = 0;
    while (i < s.length && s.charCodeAt(i) !== 46) n = n * 10 + s.charCodeAt(i++) - 48;
    n *= 100;
    if (i < s.length) {
        ++i; n += (s.charCodeAt(i++) - 48) * 10;
        if (i < s.length) n += s.charCodeAt(i) - 48;
    }
    return n;
}
function bigHundredths(s) {
    const dot = s.indexOf(".");
    if (dot < 0) return BigInt(s) * 100n;
    const fraction = s.slice(dot + 1);
    return BigInt(s.slice(0, dot)) * 100n + BigInt(fraction) * (fraction.length === 1 ? 10n : 1n);
}
function add(total, value) {
    if (typeof total === "number") {
        const result = total + value;
        if (Number.isSafeInteger(result)) return result;
        return BigInt(total) + BigInt(value);
    }
    return total + BigInt(value);
}
// The parser visits only fields used by the ledger. Native JSON.parse decodes
// the uncommon escaped strings; ignored values are scanned without allocating.
let text = "", pos = 0;
function whitespace() {
    while (text.charCodeAt(pos) <= 32) ++pos;
}
function take() { whitespace(); ++pos; }
function more(end) {
    whitespace();
    if (text.charCodeAt(pos) === 44) { ++pos; whitespace(); }
    if (text.charCodeAt(pos) === end) { ++pos; return false; }
    return true;
}
function string() {
    whitespace();
    const start = ++pos;
    const end = text.indexOf('"', start);
    const slash = text.indexOf("\\", start);
    if (slash < 0 || slash > end) { pos = end + 1; return text.slice(start, end); }
    pos = start - 1;
    skipString();
    return JSON.parse(text.slice(start - 1, pos));
}
function field() {
    whitespace();
    const start = ++pos, end = text.indexOf('"', start);
    pos = end + 1;
    switch (end - start) {
        case 4:
            if (text.startsWith("type", start)) return 2;
            if (text.startsWith("tags", start)) return 5;
            if (text.startsWith("meta", start)) return 6;
            break;
        case 6: if (text.startsWith("amount", start)) return 3; break;
        case 7:
            if (text.startsWith("account", start)) return 1;
            if (text.startsWith("channel", start)) return 7;
            break;
        case 8: if (text.startsWith("currency", start)) return 4; break;
    }
    const slash = text.indexOf("\\", start);
    if (slash >= 0 && slash < end) {
        pos = start - 1;
        switch (string()) {
            case "account": return 1;
            case "type": return 2;
            case "amount": return 3;
            case "currency": return 4;
            case "tags": return 5;
            case "meta": return 6;
            case "channel": return 7;
        }
    }
    return 0;
}
function label() {
    whitespace();
    const start = ++pos, end = text.indexOf('"', start);
    pos = end + 1;
    if (end - start === 4) {
        if (text.startsWith("void", start)) return 1;
        if (text.startsWith("test", start)) return 3;
    } else if (end - start === 5 && text.startsWith("debit", start)) return 2;
    const slash = text.indexOf("\\", start);
    if (slash >= 0 && slash < end) {
        pos = start - 1;
        const value = string();
        return value === "void" ? 1 : value === "debit" ? 2 : value === "test" ? 3 : 0;
    }
    return 0;
}
function skipString() {
    let end = text.indexOf('"', pos + 1);
    for (;;) {
        let slashes = 0, i = end - 1;
        while (text.charCodeAt(i--) === 92) ++slashes;
        if ((slashes & 1) === 0) { pos = end + 1; return; }
        end = text.indexOf('"', end + 1);
    }
}
function skip() {
    whitespace();
    let c = text.charCodeAt(pos);
    if (c === 34) { skipString(); return; }
    if (c === 123 || c === 91) {
        let depth = 1;
        ++pos;
        while (depth !== 0) {
            c = text.charCodeAt(pos);
            if (c === 34) { skipString(); continue; }
            ++pos;
            if (c === 123 || c === 91) ++depth;
            else if (c === 125 || c === 93) --depth;
        }
    } else {
        while ((c = text.charCodeAt(pos)) > 32 && c !== 44 && c !== 125 && c !== 93) ++pos;
    }
}
function copyString(s) {
    // Long V8 substrings can otherwise keep an entire input block alive.
    return s.length <= 12 ? s : Buffer.from(s, "utf8").toString("utf8");
}
function transaction(line) {
    text = line; pos = 0; take();
    let account, channelName, currency, amountText, debit = false;
    while (more(125)) {
        const key = field(); take();
        switch (key) {
            case 1: account = string(); break;
            case 4: currency = string(); break;
            case 3: amountText = string(); break;
            case 2: {
                const type = label();
                if (type === 1) return;
                debit = type === 2;
                break;
            }
            case 5:
                take();
                while (more(93)) if (label() === 3) return;
                break;
            case 6:
                take();
                while (more(125)) {
                    const key = field(); take();
                    if (key === 7) channelName = string();
                    else skip();
                }
                break;
            default: skip();
        }
    }
    const rate = rates.get(currency);
    const amount = hundredths(amountText);
    const product = amount * rate.number;
    let value;
    if (Number.isSafeInteger(amount) && Number.isSafeInteger(rate.number) && Number.isSafeInteger(product)) {
        value = Math.floor(product / 1000000);
    } else {
        const exact = bigHundredths(amountText) * rate.big;
        let usd = exact / 1000000n;
        if (exact < 0n && exact % 1000000n !== 0n) --usd;
        // The product fits int64, so its quotient fits an exact Number.
        value = Number(usd);
    }
    if (debit) value = -value;
    ++counted;
    net = add(net, value);
    const old = accounts.get(account);
    if (old === undefined) accounts.set(copyString(account), { net: value });
    else old.net = add(old.net, value);
    const channel = channels.get(channelName);
    if (channel === undefined) channels.set(copyString(channelName), { count: 1, net: value });
    else { ++channel.count; channel.net = add(channel.net, value); }
}
function consume(line) {
    if (first) { header(line); first = false; }
    else transaction(line);
}

if (process.argv.length < 3) process.exit(1);
const fd = fs.openSync(process.argv[2], "r");
const buffer = Buffer.allocUnsafe(1 << 20);
const decoder = new StringDecoder("utf8");
let pending = "";
for (;;) {
    const n = fs.readSync(fd, buffer, 0, buffer.length, null);
    if (n === 0) break;
    const block = decoder.write(buffer.subarray(0, n));
    let start = 0;
    for (;;) {
        const end = block.indexOf("\n", start);
        if (end < 0) break;
        const part = block.slice(start, end);
        if (pending.length === 0) consume(part);
        else { consume(pending + part); pending = ""; }
        start = end + 1;
    }
    if (start < block.length) pending += block.slice(start);
}
pending += decoder.end();
if (pending.length !== 0) consume(pending);
fs.closeSync(fd);

const output = ["counted " + counted + "\nnet " + net + "\n"];
for (const name of Array.from(channels.keys()).sort()) {
    const c = channels.get(name);
    output.push("channel " + name + " " + c.count + " " + c.net + "\n");
}
function better(a, b) {
    if (a[1].net > b[1].net) return true;
    if (a[1].net < b[1].net) return false;
    return a[0] < b[0];
}
const top = [];
for (const entry of accounts) {
    let pos = 0;
    while (pos < top.length && !better(entry, top[pos])) ++pos;
    if (pos < 10) {
        top.splice(pos, 0, entry);
        if (top.length > 10) top.pop();
    }
}
for (const [account, total] of top) output.push("account " + account + " " + total.net + "\n");
process.stdout.write(output.join(""));
