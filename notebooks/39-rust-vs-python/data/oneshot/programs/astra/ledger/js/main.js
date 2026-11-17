'use strict';

const fs = require('fs');

let source = '';
let pos = 0;

function whitespace() {
  while (source.charCodeAt(pos) <= 32) pos++;
}

function skipString() {
  const start = pos + 1;
  let end = source.indexOf('"', start);

  while (source.charCodeAt(end - 1) === 92) {
    let k = end - 1;
    while (k >= start && source.charCodeAt(k) === 92) k--;
    if (((end - 1 - k) & 1) === 0) break;
    end = source.indexOf('"', end + 1);
  }

  pos = end + 1;
}

function readString() {
  const start = pos;
  skipString();
  const value = source.slice(start + 1, pos - 1);
  return value.indexOf('\\') === -1
    ? value
    : JSON.parse(source.slice(start, pos));
}

function skipValue() {
  const first = source.charCodeAt(pos);

  if (first === 34) {
    skipString();
    return;
  }

  if (first === 123 || first === 91) {
    let depth = 1;
    pos++;

    while (depth !== 0) {
      const c = source.charCodeAt(pos);
      if (c === 34) {
        skipString();
      } else {
        pos++;
        if (c === 123 || c === 91) depth++;
        else if (c === 125 || c === 93) depth--;
      }
    }
    return;
  }

  while (pos < source.length) {
    const c = source.charCodeAt(pos);
    if (c <= 32 || c === 44 || c === 125 || c === 93) return;
    pos++;
  }
}

function exactInteger(token) {
  if (
    token.indexOf('.') === -1 &&
    token.indexOf('e') === -1 &&
    token.indexOf('E') === -1
  ) {
    return BigInt(token);
  }

  const match = /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(token);
  const fraction = match[3] || '';
  let value = BigInt(match[2] + fraction);

  if (value === 0n) return 0n;

  const scale = BigInt(match[4] || '0') - BigInt(fraction.length);
  if (scale >= 0n) value *= 10n ** scale;
  else value /= 10n ** (-scale);

  return match[1] ? -value : value;
}

function readRates() {
  const result = new Map();
  pos++;
  whitespace();

  while (source.charCodeAt(pos) !== 125) {
    const currency = readString();
    whitespace();
    pos++;
    whitespace();

    const start = pos;
    skipValue();
    const token = source.slice(start, pos);
    const integer = exactInteger(token);
    const numeric = Number(integer);

    result.set(currency, {
      integer,
      numeric,
      safe: Number.isSafeInteger(numeric)
    });

    whitespace();
    if (source.charCodeAt(pos) !== 44) break;
    pos++;
    whitespace();
  }

  pos++;
  return result;
}

let rates;

function parseHeader(line) {
  source = line;
  pos = 0;
  whitespace();
  pos++;
  whitespace();

  while (source.charCodeAt(pos) !== 125) {
    const key = readString();
    whitespace();
    pos++;
    whitespace();

    if (key === 'rates') rates = readRates();
    else skipValue();

    whitespace();
    if (source.charCodeAt(pos) !== 44) break;
    pos++;
    whitespace();
  }
}

function readTags() {
  let test = false;
  pos++;
  whitespace();

  while (source.charCodeAt(pos) !== 93) {
    if (readString() === 'test') test = true;
    whitespace();
    if (source.charCodeAt(pos) !== 44) break;
    pos++;
    whitespace();
  }

  pos++;
  return test;
}

function readChannel() {
  let channel;
  pos++;
  whitespace();

  while (source.charCodeAt(pos) !== 125) {
    const key = readString();
    whitespace();
    pos++;
    whitespace();

    if (key === 'channel') channel = readString();
    else skipValue();

    whitespace();
    if (source.charCodeAt(pos) !== 44) break;
    pos++;
    whitespace();
  }

  pos++;
  return channel;
}

function usdCents(amount, rate) {
  if (rate.integer === 0n) return 0;

  let cents = 0;
  let dot = -1;

  for (let i = 0; i < amount.length; i++) {
    const c = amount.charCodeAt(i);
    if (c === 46) dot = i;
    else cents = cents * 10 + c - 48;
  }

  let multiplier = 1;
  if (dot === -1) multiplier = 100;
  else if (amount.length - dot === 2) multiplier = 10;
  cents *= multiplier;

  if (cents === 0) return 0;

  if (rate.safe && Number.isSafeInteger(cents)) {
    const product = cents * rate.numeric;
    if (Number.isSafeInteger(product)) {
      return Math.floor(product / 1000000);
    }
  }

  const digits = dot === -1
    ? amount
    : amount.slice(0, dot) + amount.slice(dot + 1);

  const exactCents = BigInt(digits) * BigInt(multiplier);
  const product = exactCents * rate.integer;
  let converted = product / 1000000n;

  if (product < 0n && product % 1000000n !== 0n) converted--;

  return Number(converted);
}

function addExact(total, value) {
  if (typeof total === 'number') {
    const sum = total + value;
    if (Number.isSafeInteger(sum)) return sum;
    return BigInt(total) + BigInt(value);
  }
  return total + BigInt(value);
}

const channels = new Map();
const accounts = new Map();
let counted = 0;
let net = 0;

function parseTransaction(line) {
  source = line;
  pos = 0;
  whitespace();
  pos++;
  whitespace();

  let account;
  let type;
  let amount;
  let currency;
  let channel;
  let test = false;

  while (source.charCodeAt(pos) !== 125) {
    const key = readString();
    whitespace();
    pos++;
    whitespace();

    switch (key) {
      case 'account':
        account = readString();
        break;
      case 'type':
        type = readString();
        break;
      case 'amount':
        amount = readString();
        break;
      case 'currency':
        currency = readString();
        break;
      case 'tags':
        test = readTags();
        break;
      case 'meta':
        channel = readChannel();
        break;
      default:
        skipValue();
    }

    whitespace();
    if (source.charCodeAt(pos) !== 44) break;
    pos++;
    whitespace();
  }

  if (type === 'void' || test) return;

  let value = usdCents(amount, rates.get(currency));
  if (type === 'debit') value = -value;

  counted++;
  net = addExact(net, value);

  const channelData = channels.get(channel);
  if (channelData === undefined) {
    channels.set(channel, { count: 1, net: value });
  } else {
    channelData.count++;
    channelData.net = addExact(channelData.net, value);
  }

  const accountNet = accounts.get(account);
  accounts.set(
    account,
    accountNet === undefined ? value : addExact(accountNet, value)
  );
}

const fd = fs.openSync(process.argv[2], 'r');
const buffer = Buffer.allocUnsafe(8 * 1024 * 1024);
let fragments = [];
let fragmentBytes = 0;
let header = true;

function consume(line) {
  if (header) {
    parseHeader(line);
    header = false;
  } else {
    parseTransaction(line);
  }
}

for (;;) {
  const length = fs.readSync(fd, buffer, 0, buffer.length, null);
  if (length === 0) break;

  const block = buffer.subarray(0, length);
  let start = 0;

  for (;;) {
    const end = block.indexOf(10, start);
    if (end === -1) break;

    if (fragmentBytes === 0) {
      consume(block.toString('utf8', start, end));
    } else {
      fragments.push(block.subarray(start, end));
      const complete = Buffer.concat(
        fragments,
        fragmentBytes + end - start
      );
      fragments = [];
      fragmentBytes = 0;
      consume(complete.toString('utf8'));
    }

    start = end + 1;
  }

  if (start < length) {
    const fragment = Buffer.from(block.subarray(start));
    fragments.push(fragment);
    fragmentBytes += fragment.length;
  }
}

fs.closeSync(fd);
source = '';

function better(a, b) {
  if (a[1] > b[1]) return true;
  if (a[1] < b[1]) return false;
  return a[0] < b[0];
}

const best = [];

for (const entry of accounts) {
  if (best.length === 10 && !better(entry, best[9])) continue;

  let i;
  if (best.length < 10) {
    i = best.length;
    best.push(entry);
  } else {
    i = 9;
  }

  while (i > 0 && better(entry, best[i - 1])) {
    best[i] = best[i - 1];
    i--;
  }
  best[i] = entry;
}

let output = '';

function flush() {
  if (output.length === 0) return;
  const data = Buffer.from(output, 'utf8');
  let offset = 0;
  while (offset < data.length) {
    offset += fs.writeSync(1, data, offset, data.length - offset);
  }
  output = '';
}

function emit(line) {
  output += line + '\n';
  if (output.length >= 65536) flush();
}

emit('counted ' + counted);
emit('net ' + net);

const channelNames = Array.from(channels.keys()).sort();
for (const name of channelNames) {
  const data = channels.get(name);
  emit('channel ' + name + ' ' + data.count + ' ' + data.net);
}

for (const entry of best) {
  emit('account ' + entry[0] + ' ' + entry[1]);
}

flush();
