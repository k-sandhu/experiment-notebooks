'use strict';

const fs = require('fs');

// Convert amount string "12", "12.5", "12.05" to integer hundredths.
function parseAmount(s) {
    const dot = s.indexOf('.');
    if (dot === -1) {
        return parseInt(s, 10) * 100;
    }
    let h = 0;
    for (let i = 0; i < dot; i++) {
        h = h * 10 + (s.charCodeAt(i) - 48);
    }
    let f = 0;
    let fd = 0;
    for (let i = dot + 1; i < s.length; i++) {
        f = f * 10 + (s.charCodeAt(i) - 48);
        fd++;
    }
    if (fd === 1) return h * 100 + f * 10;
    return h * 100 + f;
}

function main() {
    const path = process.argv[2];
    const buf = fs.readFileSync(path, 'utf8');
    const lines = buf.split('\n');

    // First line: rates.
    const rates = JSON.parse(lines[0]).rates;

    const accounts = new Map(); // string -> bigint
    const channels = new Map(); // string -> {count:number, net:bigint}
    let counted = 0;
    let net = 0n;

    const HUNDRED = 1000000n;

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        if (line.length === 0) continue;
        const o = JSON.parse(line);
        if (o.type === 'void') continue;

        const tags = o.tags;
        let testTag = false;
        for (let t = 0; t < tags.length; t++) {
            if (tags[t] === 'test') {
                testTag = true;
                break;
            }
        }
        if (testTag) continue;

        const hundred = parseAmount(o.amount);
        const rate = rates[o.currency];
        // Exact integer arithmetic, rounding down (floor for non-negative values).
        const usd = (BigInt(hundred) * BigInt(rate)) / HUNDRED;
        const val = (o.type === 'credit' || o.type === 'refund') ? usd : -usd;

        counted++;
        net += val;

        const ch = o.meta.channel;
        let c = channels.get(ch);
        if (c === undefined) {
            c = { count: 0, net: 0n };
            channels.set(ch, c);
        }
        c.count++;
        c.net += val;

        accounts.set(o.account, (accounts.get(o.account) || 0n) + val);
    }

    const out = [];
    out.push('counted ' + counted);
    out.push('net ' + net.toString());

    const chNames = [...channels.keys()].sort();
    for (const name of chNames) {
        const c = channels.get(name);
        out.push('channel ' + name + ' ' + c.count + ' ' + c.net.toString());
    }

    const acs = [...accounts.entries()].sort((a, b) => {
        if (a[1] > b[1]) return -1;
        if (a[1] < b[1]) return 1;
        if (a[0] < b[0]) return -1;
        if (a[0] > b[0]) return 1;
        return 0;
    });
    const m = acs.length < 10 ? acs.length : 10;
    for (let i = 0; i < m; i++) {
        out.push('account ' + acs[i][0] + ' ' + acs[i][1].toString());
    }

    process.stdout.write(out.join('\n') + '\n');
}

main();
