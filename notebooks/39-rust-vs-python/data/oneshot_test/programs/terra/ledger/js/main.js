'use strict';

const fs = require('fs');
const { StringDecoder } = require('string_decoder');

function parseInteger(source) {
  let s = source;
  let sign = 1n;
  if (s[0] === '-') {
    sign = -1n;
    s = s.slice(1);
  }

  let exponent = 0;
  const e = s.search(/[eE]/);
  if (e !== -1) {
    exponent = Number(s.slice(e + 1));
    s = s.slice(0, e);
  }

  const dot = s.indexOf('.');
  if (dot !== -1) {
    exponent -= s.length - dot - 1;
    s = s.slice(0, dot) + s.slice(dot + 1);
  }

  let value = BigInt(s);
  if (value === 0n) return 0n;
  if (exponent > 0) value *= 10n ** BigInt(exponent);
  else if (exponent < 0) value /= 10n ** BigInt(-exponent);
  return sign * value;
}

function amountInHundredths(amount) {
  const dot = amount.indexOf('.');
  if (dot === -1) return BigInt(amount) * 100n;
  const digits = amount.slice(0, dot) + amount.slice(dot + 1);
  const value = BigInt(digits);
  return amount.length - dot === 2 ? value * 10n : value;
}

const rates = new Map();
const accounts = new Map();
const channels = new Map();
let counted = 0;
let net = 0n;
let firstLine = true;

function processLine(line) {
  if (firstLine) {
    firstLine = false;
    const header = JSON.parse(line, (key, value, context) => {
      return typeof value === 'number' ? context.source : value;
    });
    for (const [currency, source] of Object.entries(header.rates)) {
      rates.set(currency, parseInteger(source));
    }
    return;
  }

  const transaction = JSON.parse(line);
  if (transaction.type === 'void' || transaction.tags.includes('test')) return;

  const product = amountInHundredths(transaction.amount) * rates.get(transaction.currency);
  let usd = product / 1000000n;
  if (product < 0n && product % 1000000n !== 0n) usd--;

  const value = transaction.type === 'debit' ? -usd : usd;
  counted++;
  net += value;

  const channel = transaction.meta.channel;
  let channelData = channels.get(channel);
  if (channelData === undefined) {
    channelData = { count: 0, net: 0n };
    channels.set(channel, channelData);
  }
  channelData.count++;
  channelData.net += value;

  const account = transaction.account;
  const previous = accounts.get(account);
  accounts.set(account, previous === undefined ? value : previous + value);
}

const fd = fs.openSync(process.argv[2], 'r');
const buffer = Buffer.allocUnsafe(4 * 1024 * 1024);
const decoder = new StringDecoder('utf8');
let remainder = '';

while (true) {
  const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, null);
  if (bytesRead === 0) break;

  const text = remainder + decoder.write(buffer.subarray(0, bytesRead));
  let start = 0;
  let end;
  while ((end = text.indexOf('\n', start)) !== -1) {
    processLine(text.slice(start, end));
    start = end + 1;
  }
  remainder = text.slice(start);
}

remainder += decoder.end();
if (remainder.length !== 0) processLine(remainder);
fs.closeSync(fd);

const output = [`counted ${counted}`, `net ${net}`];

const channelNames = Array.from(channels.keys()).sort();
for (const name of channelNames) {
  const data = channels.get(name);
  output.push(`channel ${name} ${data.count} ${data.net}`);
}

const top = [];
for (const [id, value] of accounts) {
  let position = 0;
  while (position < top.length) {
    const entry = top[position];
    if (value > entry.value || (value === entry.value && id < entry.id)) break;
    position++;
  }
  if (position < 10) {
    top.splice(position, 0, { id, value });
    if (top.length > 10) top.pop();
  }
}

for (const entry of top) {
  output.push(`account ${entry.id} ${entry.value}`);
}

process.stdout.write(output.join('\n') + '\n');
