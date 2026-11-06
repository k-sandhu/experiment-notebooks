'use strict';

const fs = require('fs');

const buf = fs.readFileSync(process.argv[2], 'utf8');
const lines = buf.split('\n');

const rates = Object.create(null);
let totalCount = 0;
let totalNet = 0;
const channels = Object.create(null);
const accounts = Object.create(null);

function parseAmount(s) {
    let j = 0, dollars = 0, n = s.length;
    while (j < n) {
        const c = s.charCodeAt(j);
        if (c < 48 || c > 57) break;
        dollars = dollars * 10 + (c - 48);
        j++;
    }
    let cents = 0;
    if (j < n && s.charCodeAt(j) === 46) {
        j++;
        let nd = 0;
        while (j < n) {
            const c = s.charCodeAt(j);
            if (c < 48 || c > 57 || nd >= 2) break;
            cents = cents * 10 + (c - 48);
            j++;
            nd++;
        }
        while (nd < 2) { cents *= 10; nd++; }
    }
    return dollars * 100 + cents;
}

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.length === 0) continue;
    let o;
    try { o = JSON.parse(line); } catch (e) { continue; }
    if (o.rates !== undefined) {
        const r = o.rates;
        for (const k in r) rates[k] = r[k];
        continue;
    }
    const typ = o.type;
    if (typ === 'void') continue;
    let skipped = false;
    const tags = o.tags;
    if (tags) {
        for (let t = 0; t < tags.length; t++) {
            if (tags[t] === 'test') { skipped = true; break; }
        }
    }
    if (skipped) continue;
    const hundredths = parseAmount(o.amount);
    const rate = rates[o.currency];
    if (rate === undefined) continue;
    let usd = (hundredths * rate / 1000000) | 0;
    if (typ === 'debit') usd = -usd;
    totalCount++;
    totalNet += usd;
    const ch = o.meta && o.meta.channel;
    let c = channels[ch];
    if (!c) { c = [0, 0]; channels[ch] = c; }
    c[0]++;
    c[1] += usd;
    accounts[o.account] = (accounts[o.account] || 0) + usd;
}

let out = 'counted ' + totalCount + '\n' + 'net ' + totalNet + '\n';

const chNames = Object.keys(channels);
chNames.sort();
for (let k = 0; k < chNames.length; k++) {
    const name = chNames[k];
    const c = channels[name];
    out += 'channel ' + name + ' ' + c[0] + ' ' + c[1] + '\n';
}

const accts = Object.keys(accounts).map(k => ({ k: k, v: accounts[k] }));
accts.sort((a, b) => b.v - a.v || (a.k < b.k ? -1 : a.k > b.k ? 1 : 0));
const lim = Math.min(10, accts.length);
for (let k = 0; k < lim; k++) {
    out += 'account ' + accts[k].k + ' ' + accts[k].v + '\n';
}

process.stdout.write(out);
