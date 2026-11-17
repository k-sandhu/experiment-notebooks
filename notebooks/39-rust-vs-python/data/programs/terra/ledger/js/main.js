"use strict";
const fs = require('fs');
const { StringDecoder } = require('string_decoder');
const fd = fs.openSync(process.argv[2], 'r');
const buffer = Buffer.allocUnsafe(1 << 20), decoder = new StringDecoder('utf8');
let pending = '', rates, count = 0, net = 0n;
const accounts = new Map(), channels = new Map();
function processLine(line) {
  if (rates === undefined) {
    const raw = JSON.parse(line, (key, value, context) => typeof value === 'number' ? context.source : value).rates;
    rates = new Map(Object.entries(raw).map(([key, value]) => [key, BigInt(value)]));
    return;
  }
  const t = JSON.parse(line);
  if (t.type === 'void' || t.tags.includes('test')) return;
  const dot = t.amount.indexOf('.');
  let cents;
  if (dot < 0) cents = BigInt(t.amount) * 100n;
  else { const frac = t.amount.slice(dot + 1); cents = BigInt(t.amount.slice(0, dot)) * 100n + BigInt(frac) * (frac.length === 1 ? 10n : 1n); }
  const product = cents * rates.get(t.currency);
  let value = product / 1000000n; if (product < 0n && product % 1000000n !== 0n) value--;
  if (t.type === 'debit') value = -value;
  count++; net += value; accounts.set(t.account, (accounts.get(t.account) || 0n) + value);
  let s = channels.get(t.meta.channel); if (s === undefined) { s = {count: 0, net: 0n}; channels.set(t.meta.channel, s); }
  s.count++; s.net += value;
}
for (;;) {
  const n = fs.readSync(fd, buffer, 0, buffer.length, null); if (!n) break;
  pending += decoder.write(buffer.subarray(0, n));
  let start = 0, end;
  while ((end = pending.indexOf('\n', start)) !== -1) { processLine(pending.slice(start, end)); start = end + 1; }
  pending = pending.slice(start);
}
pending += decoder.end(); if (pending.length) processLine(pending);
fs.closeSync(fd);
let out = `counted ${count}\nnet ${net}\n`;
const cmp = (a,b) => a < b ? -1 : a > b ? 1 : 0;
for (const [name,s] of [...channels].sort((a,b)=>cmp(a[0],b[0]))) out += `channel ${name} ${s.count} ${s.net}\n`;
for (const [name,value] of [...accounts].sort((a,b)=>a[1]===b[1]?cmp(a[0],b[0]):a[1]>b[1]?-1:1).slice(0,10)) out += `account ${name} ${value}\n`;
process.stdout.write(out);
