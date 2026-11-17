'use strict';

const fs = require('fs');
const data = fs.readFileSync(process.argv[2]);
const length = data.length;
let pos = 0;

function whitespace() {
  while (pos < length && data[pos] <= 32) pos++;
}

function readString() {
  const quote = pos++;
  const start = pos;
  let escaped = false;

  while (data[pos] !== 34) {
    if (data[pos] === 92) {
      escaped = true;
      pos += 2;
    } else {
      pos++;
    }
  }

  const end = pos++;
  return escaped
    ? JSON.parse(data.toString('utf8', quote, pos))
    : data.toString('utf8', start, end);
}

function decodedKeyCode(key) {
  switch (key) {
    case 'type': return 1;
    case 'amount': return 2;
    case 'currency': return 3;
    case 'account': return 4;
    case 'tags': return 5;
    case 'meta': return 6;
    case 'channel': return 7;
    case 'rates': return 8;
    default: return 0;
  }
}

function readKey() {
  const quote = pos++;
  const start = pos;

  while (data[pos] !== 34) {
    if (data[pos] === 92) {
      pos = quote;
      return decodedKeyCode(readString());
    }
    pos++;
  }

  const end = pos++;
  switch (end - start) {
    case 4:
      if (data[start] === 116) {
        if (data[start + 1] === 121 &&
            data[start + 2] === 112 &&
            data[start + 3] === 101) return 1;
        if (data[start + 1] === 97 &&
            data[start + 2] === 103 &&
            data[start + 3] === 115) return 5;
      } else if (data[start] === 109 &&
                 data[start + 1] === 101 &&
                 data[start + 2] === 116 &&
                 data[start + 3] === 97) {
        return 6;
      }
      break;

    case 5:
      if (data[start] === 114 &&
          data[start + 1] === 97 &&
          data[start + 2] === 116 &&
          data[start + 3] === 101 &&
          data[start + 4] === 115) return 8;
      break;

    case 6:
      if (data[start] === 97 &&
          data[start + 1] === 109 &&
          data[start + 2] === 111 &&
          data[start + 3] === 117 &&
          data[start + 4] === 110 &&
          data[start + 5] === 116) return 2;
      break;

    case 7:
      if (data[start] === 97 &&
          data[start + 1] === 99 &&
          data[start + 2] === 99 &&
          data[start + 3] === 111 &&
          data[start + 4] === 117 &&
          data[start + 5] === 110 &&
          data[start + 6] === 116) return 4;
      if (data[start] === 99 &&
          data[start + 1] === 104 &&
          data[start + 2] === 97 &&
          data[start + 3] === 110 &&
          data[start + 4] === 110 &&
          data[start + 5] === 101 &&
          data[start + 6] === 108) return 7;
      break;

    case 8:
      if (data[start] === 99 &&
          data[start + 1] === 117 &&
          data[start + 2] === 114 &&
          data[start + 3] === 114 &&
          data[start + 4] === 101 &&
          data[start + 5] === 110 &&
          data[start + 6] === 99 &&
          data[start + 7] === 121) return 3;
      break;
  }
  return 0;
}

function skipString() {
  pos++;
  for (;;) {
    const c = data[pos++];
    if (c === 34) return;
    if (c === 92) pos++;
  }
}

function skipValue() {
  const first = data[pos];

  if (first === 34) {
    skipString();
    return;
  }

  if (first === 123 || first === 91) {
    pos++;
    let depth = 1;

    while (depth !== 0) {
      const c = data[pos++];
      if (c === 34) {
        for (;;) {
          const s = data[pos++];
          if (s === 34) break;
          if (s === 92) pos++;
        }
      } else if (c === 123 || c === 91) {
        depth++;
      } else if (c === 125 || c === 93) {
        depth--;
      }
    }
    return;
  }

  while (pos < length) {
    const c = data[pos];
    if (c <= 32 || c === 44 || c === 125 || c === 93) return;
    pos++;
  }
}

function integerFromJSON(token) {
  if (!token.includes('.') && !token.includes('e') && !token.includes('E')) {
    return BigInt(token);
  }

  const match = /^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(token);
  const fraction = match[3] || '';
  let value = BigInt(match[1] + match[2] + fraction);

  if (value === 0n) return value;

  const shift = Number(match[4] || 0) - fraction.length;
  if (shift > 0) value *= 10n ** BigInt(shift);
  else if (shift < 0) value /= 10n ** BigInt(-shift);
  return value;
}

function readRates() {
  const result = new Map();
  pos++;
  whitespace();

  while (data[pos] !== 125) {
    const currency = readString();
    whitespace();
    pos++;
    whitespace();

    const start = pos;
    while (data[pos] > 32 && data[pos] !== 44 && data[pos] !== 125) pos++;

    const exact = integerFromJSON(data.toString('ascii', start, pos));
    const numeric = Number(exact);
    result.set(currency, {
      exact,
      fast: Number.isSafeInteger(numeric) ? numeric : null
    });

    whitespace();
    if (data[pos] !== 44) break;
    pos++;
    whitespace();
  }

  pos++;
  return result;
}

let rates = new Map();

whitespace();
pos++;
whitespace();

while (data[pos] !== 125) {
  const key = readKey();
  whitespace();
  pos++;
  whitespace();

  if (key === 8) rates = readRates();
  else skipValue();

  whitespace();
  if (data[pos] !== 44) break;
  pos++;
  whitespace();
}
pos++;

function readTags() {
  let hasTest = false;
  pos++;
  whitespace();

  while (data[pos] !== 93) {
    if (hasTest) skipString();
    else if (readString() === 'test') hasTest = true;

    whitespace();
    if (data[pos] !== 44) break;
    pos++;
    whitespace();
  }

  pos++;
  return hasTest;
}

function readMeta() {
  let channel;
  pos++;
  whitespace();

  while (data[pos] !== 125) {
    const key = readKey();
    whitespace();
    pos++;
    whitespace();

    if (key === 7) channel = readString();
    else skipValue();

    whitespace();
    if (data[pos] !== 44) break;
    pos++;
    whitespace();
  }

  pos++;
  return channel;
}

function hundredths(amount) {
  let value = 0;
  let dot = -1;

  for (let i = 0; i < amount.length; i++) {
    const c = amount.charCodeAt(i);
    if (c === 46) dot = i;
    else value = value * 10 + c - 48;
  }

  if (dot === -1) value *= 100;
  else if (amount.length - dot === 2) value *= 10;

  if (Number.isSafeInteger(value)) return value;

  if (dot === -1) return BigInt(amount) * 100n;

  const fraction = amount.slice(dot + 1);
  return BigInt(amount.slice(0, dot)) * 100n +
    BigInt(fraction) * (fraction.length === 1 ? 10n : 1n);
}

function convert(amount, rate) {
  const cents = hundredths(amount);

  if (typeof cents === 'number' && rate.fast !== null) {
    const product = cents * rate.fast;
    if (Number.isSafeInteger(product)) {
      return Math.floor(product / 1000000);
    }
  }

  const product = BigInt(cents) * rate.exact;
  let value = product / 1000000n;
  if (product < 0n && product % 1000000n !== 0n) value--;
  return Number(value);
}

function add(sum, value) {
  if (typeof sum === 'number') {
    const result = sum + value;
    if (Number.isSafeInteger(result)) return result;
    return BigInt(sum) + BigInt(value);
  }
  return sum + BigInt(value);
}

const channels = new Map();
const accounts = new Map();
let counted = 0;
let net = 0;

function transaction() {
  let type;
  let amount;
  let currency;
  let account;
  let channel;
  let hasTest = false;

  pos++;
  whitespace();

  while (data[pos] !== 125) {
    const key = readKey();
    whitespace();
    pos++;
    whitespace();

    switch (key) {
      case 1: type = readString(); break;
      case 2: amount = readString(); break;
      case 3: currency = readString(); break;
      case 4: account = readString(); break;
      case 5: hasTest = readTags(); break;
      case 6: channel = readMeta(); break;
      default: skipValue(); break;
    }

    whitespace();
    if (data[pos] !== 44) break;
    pos++;
    whitespace();
  }

  pos++;

  if (type === 'void' || hasTest) return;

  let value = convert(amount, rates.get(currency));
  if (type === 'debit') value = -value;

  counted++;
  net = add(net, value);

  const channelTotal = channels.get(channel);
  if (channelTotal === undefined) {
    channels.set(channel, { count: 1, net: value });
  } else {
    channelTotal.count++;
    channelTotal.net = add(channelTotal.net, value);
  }

  const accountTotal = accounts.get(account);
  accounts.set(account,
    accountTotal === undefined ? value : add(accountTotal, value));
}

whitespace();
while (pos < length) {
  transaction();
  whitespace();
}

const output = [`counted ${counted}`, `net ${net}`];

const channelNames = Array.from(channels.keys()).sort();
for (const name of channelNames) {
  const total = channels.get(name);
  output.push(`channel ${name} ${total.count} ${total.net}`);
}

function better(id, value, other) {
  return value > other.value || (value == other.value && id < other.id);
}

const top = [];

for (const [id, value] of accounts) {
  if (top.length === 10 && !better(id, value, top[9])) continue;

  let index = top.length;
  if (index < 10) top.push(null);
  else index = 9;

  while (index > 0 && better(id, value, top[index - 1])) {
    top[index] = top[index - 1];
    index--;
  }

  top[index] = { id, value };
}

for (const entry of top) {
  output.push(`account ${entry.id} ${entry.value}`);
}

process.stdout.write(output.join('\n') + '\n');
