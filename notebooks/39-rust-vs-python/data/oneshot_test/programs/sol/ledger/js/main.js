'use strict';

const fs = require('fs');

const MAX_SAFE = Number.MAX_SAFE_INTEGER;
const MILLION = 1000000n;

let buffer = Buffer.allocUnsafe(4 * 1024 * 1024);
let p = 0;
let stringStart = 0;
let stringEnd = 0;
let stringEscaped = false;

const rates = new Map();
const accounts = new Map();
const channels = new Map();

let counted = 0;
let net = 0;

function whitespace() {
  while (buffer[p] <= 32) ++p;
}

function scanString() {
  let i = p + 1;
  stringStart = i;
  let escaped = false;

  for (;;) {
    const c = buffer[i];
    if (c === 34) break;
    if (c === 92) {
      escaped = true;
      i += 2;
    } else {
      ++i;
    }
  }

  stringEnd = i;
  stringEscaped = escaped;
  p = i + 1;
}

function decodedString() {
  return stringEscaped
    ? JSON.parse(buffer.toString('utf8', stringStart - 1, p))
    : buffer.toString('utf8', stringStart, stringEnd);
}

function readString() {
  scanString();
  return decodedString();
}

function keyCode(s) {
  switch (s) {
    case 'account': return 1;
    case 'type': return 2;
    case 'amount': return 3;
    case 'currency': return 4;
    case 'tags': return 5;
    case 'meta': return 6;
    case 'channel': return 7;
    case 'rates': return 8;
    default: return 0;
  }
}

function readKey() {
  scanString();

  if (stringEscaped) return keyCode(decodedString());

  const s = stringStart;
  const n = stringEnd - s;
  const b = buffer;

  switch (n) {
    case 4:
      if (b[s] === 116) {
        if (b[s + 1] === 121 && b[s + 2] === 112 &&
            b[s + 3] === 101) return 2;
        if (b[s + 1] === 97 && b[s + 2] === 103 &&
            b[s + 3] === 115) return 5;
      } else if (b[s] === 109 && b[s + 1] === 101 &&
                 b[s + 2] === 116 && b[s + 3] === 97) {
        return 6;
      }
      break;

    case 5:
      if (b[s] === 114 && b[s + 1] === 97 && b[s + 2] === 116 &&
          b[s + 3] === 101 && b[s + 4] === 115) return 8;
      break;

    case 6:
      if (b[s] === 97 && b[s + 1] === 109 && b[s + 2] === 111 &&
          b[s + 3] === 117 && b[s + 4] === 110 &&
          b[s + 5] === 116) return 3;
      break;

    case 7:
      if (b[s] === 97 && b[s + 1] === 99 && b[s + 2] === 99 &&
          b[s + 3] === 111 && b[s + 4] === 117 &&
          b[s + 5] === 110 && b[s + 6] === 116) return 1;

      if (b[s] === 99 && b[s + 1] === 104 && b[s + 2] === 97 &&
          b[s + 3] === 110 && b[s + 4] === 110 &&
          b[s + 5] === 101 && b[s + 6] === 108) return 7;
      break;

    case 8:
      if (b[s] === 99 && b[s + 1] === 117 && b[s + 2] === 114 &&
          b[s + 3] === 114 && b[s + 4] === 101 &&
          b[s + 5] === 110 && b[s + 6] === 99 &&
          b[s + 7] === 121) return 4;
      break;
  }

  return 0;
}

function skipValue() {
  let i = p;
  let c = buffer[i];

  if (c === 34) {
    ++i;
    while (buffer[i] !== 34) {
      i += buffer[i] === 92 ? 2 : 1;
    }
    p = i + 1;
    return;
  }

  if (c === 123 || c === 91) {
    let depth = 1;
    ++i;

    while (depth !== 0) {
      c = buffer[i++];

      if (c === 34) {
        while (buffer[i] !== 34) {
          i += buffer[i] === 92 ? 2 : 1;
        }
        ++i;
      } else if (c === 123 || c === 91) {
        ++depth;
      } else if (c === 125 || c === 93) {
        --depth;
      }
    }

    p = i;
    return;
  }

  while ((c = buffer[i]) > 32 && c !== 44 && c !== 125 && c !== 93) {
    ++i;
  }
  p = i;
}

function integerLiteral(s) {
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
  if (value === 0n) return value;

  if (exponent > 0) {
    value *= 10n ** BigInt(exponent);
  } else if (exponent < 0) {
    value /= 10n ** BigInt(-exponent);
  }

  return value;
}

function readRates() {
  ++p;
  whitespace();

  while (buffer[p] !== 125) {
    const currency = readString();
    whitespace();
    ++p;
    whitespace();

    const start = p;
    let c;
    while ((c = buffer[p]) > 32 && c !== 44 && c !== 125) ++p;

    const big = integerLiteral(buffer.toString('ascii', start, p));
    const number = Number(big);

    rates.set(currency, {
      big,
      number: Number.isSafeInteger(number) ? number : null
    });

    whitespace();
    if (buffer[p] !== 44) break;
    ++p;
    whitespace();
  }

  ++p;
}

function readHeader(start) {
  p = start;
  whitespace();
  ++p;
  whitespace();

  while (buffer[p] !== 125) {
    const key = readKey();
    whitespace();
    ++p;
    whitespace();

    if (key === 8) readRates();
    else skipValue();

    whitespace();
    if (buffer[p] !== 44) break;
    ++p;
    whitespace();
  }
}

function bigAmount(s) {
  const dot = s.indexOf('.');
  if (dot === -1) return BigInt(s) * 100n;

  const digits = s.slice(0, dot) + s.slice(dot + 1);
  return BigInt(digits) * (s.length - dot === 2 ? 10n : 1n);
}

function textAmount(s) {
  let value = 0;
  let decimals = -1;

  for (let i = 0; i < s.length; ++i) {
    const c = s.charCodeAt(i);
    if (c === 46) {
      decimals = 0;
    } else {
      value = value * 10 + c - 48;
      if (decimals >= 0) ++decimals;
    }
  }

  if (decimals === -1) value *= 100;
  else if (decimals === 1) value *= 10;

  return Number.isSafeInteger(value) ? value : bigAmount(s);
}

function readAmount() {
  scanString();

  if (stringEscaped) return textAmount(decodedString());

  let value = 0;
  let decimals = -1;

  for (let i = stringStart; i < stringEnd; ++i) {
    const c = buffer[i];
    if (c === 46) {
      decimals = 0;
    } else {
      value = value * 10 + c - 48;
      if (decimals >= 0) ++decimals;
    }
  }

  if (decimals === -1) value *= 100;
  else if (decimals === 1) value *= 10;

  if (Number.isSafeInteger(value)) return value;
  return bigAmount(buffer.toString('ascii', stringStart, stringEnd));
}

function readType() {
  scanString();

  if (stringEscaped) {
    const type = decodedString();
    return type === 'debit' ? 1 : type === 'void' ? 2 : 0;
  }

  const first = buffer[stringStart];
  return first === 100 ? 1 : first === 118 ? 2 : 0;
}

function readTags() {
  let test = false;
  ++p;
  whitespace();

  while (buffer[p] !== 93) {
    scanString();

    if (stringEscaped) {
      if (decodedString() === 'test') test = true;
    } else if (
      stringEnd - stringStart === 4 &&
      buffer[stringStart] === 116 &&
      buffer[stringStart + 1] === 101 &&
      buffer[stringStart + 2] === 115 &&
      buffer[stringStart + 3] === 116
    ) {
      test = true;
    }

    whitespace();
    if (buffer[p] !== 44) break;
    ++p;
    whitespace();
  }

  ++p;
  return test;
}

function readMeta() {
  let channel = '';
  ++p;
  whitespace();

  while (buffer[p] !== 125) {
    const key = readKey();
    whitespace();
    ++p;
    whitespace();

    if (key === 7) channel = readString();
    else skipValue();

    whitespace();
    if (buffer[p] !== 44) break;
    ++p;
    whitespace();
  }

  ++p;
  return channel;
}

function addExact(sum, value) {
  if (typeof sum === 'number') {
    const result = sum + value;
    if (result >= -MAX_SAFE && result <= MAX_SAFE) return result;
    return BigInt(sum) + BigInt(value);
  }
  return sum + BigInt(value);
}

function convert(amount, rate) {
  if (typeof amount === 'number' && rate.number !== null) {
    const product = amount * rate.number;
    if (Number.isSafeInteger(product)) {
      return Math.floor(product / 1000000);
    }
  }

  const product = BigInt(amount) * rate.big;
  let result = product / MILLION;

  if (product < 0n && product % MILLION !== 0n) --result;

  return Number(result);
}

function readTransaction(start) {
  p = start;
  whitespace();
  ++p;
  whitespace();

  let account = '';
  let currency = '';
  let channel = '';
  let amount = 0;
  let type = 0;
  let test = false;

  while (buffer[p] !== 125) {
    const key = readKey();
    whitespace();
    ++p;
    whitespace();

    switch (key) {
      case 1: account = readString(); break;
      case 2: type = readType(); break;
      case 3: amount = readAmount(); break;
      case 4: currency = readString(); break;
      case 5: test = readTags(); break;
      case 6: channel = readMeta(); break;
      default: skipValue(); break;
    }

    whitespace();
    if (buffer[p] !== 44) break;
    ++p;
    whitespace();
  }

  if (type === 2 || test) return;

  let value = convert(amount, rates.get(currency));
  if (type === 1) value = -value;

  ++counted;
  net = addExact(net, value);

  const previous = accounts.get(account);
  accounts.set(
    account,
    previous === undefined ? value : addExact(previous, value)
  );

  const entry = channels.get(channel);
  if (entry === undefined) {
    channels.set(channel, { count: 1, net: value });
  } else {
    ++entry.count;
    entry.net = addExact(entry.net, value);
  }
}

const fd = fs.openSync(process.argv[2], 'r');
let pending = 0;
let header = true;

for (;;) {
  if (pending === buffer.length) {
    const larger = Buffer.allocUnsafe(buffer.length * 2);
    buffer.copy(larger, 0, 0, pending);
    buffer = larger;
  }

  const bytesRead = fs.readSync(
    fd, buffer, pending, buffer.length - pending, null
  );

  if (bytesRead === 0) {
    if (pending !== 0) {
      if (header) readHeader(0);
      else readTransaction(0);
    }
    break;
  }

  const end = pending + bytesRead;
  let start = 0;

  for (;;) {
    const newline = buffer.indexOf(10, start);
    if (newline === -1 || newline >= end) break;

    if (header) {
      readHeader(start);
      header = false;
    } else {
      readTransaction(start);
    }

    start = newline + 1;
    if (start === end) break;
  }

  pending = end - start;
  if (pending !== 0 && start !== 0) {
    buffer.copy(buffer, 0, start, end);
  }
}

fs.closeSync(fd);

function before(entry, other) {
  return entry[1] > other[1] ||
    (entry[1] == other[1] && entry[0] < other[0]);
}

const top = [];

for (const entry of accounts) {
  if (top.length === 10 && !before(entry, top[9])) continue;

  let i = top.length;
  while (i > 0 && before(entry, top[i - 1])) --i;

  top.splice(i, 0, entry);
  if (top.length > 10) top.pop();
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

const channelNames = Array.from(channels.keys());
channelNames.sort();

for (const name of channelNames) {
  const entry = channels.get(name);
  emit('channel ' + name + ' ' + entry.count + ' ' + entry.net);
}

for (const entry of top) {
  emit('account ' + entry[0] + ' ' + entry[1]);
}

flush();
