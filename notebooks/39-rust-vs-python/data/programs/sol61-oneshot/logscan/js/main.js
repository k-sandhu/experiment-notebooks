'use strict';

const fs = require('fs');

const linePattern = /(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) (\/[A-Za-z0-9_\/-]*)(?:\?[^ \n]*)? (\d)\d{2} \d+B (\d+)\.(\d)ms "[^"\n]*"|[^\n]*)\n/g;
const numericSegment = /\/\d+(?=\/|$)/g;

let lines = 0;
let malformed = 0;
const statuses = new Array(10).fill(0);
const paths = new Map();

function scan(text) {
  linePattern.lastIndex = 0;
  let match;

  while ((match = linePattern.exec(text)) !== null) {
    ++lines;

    if (match[1] === undefined) {
      ++malformed;
      continue;
    }

    ++statuses[match[2].charCodeAt(0) - 48];

    const template = match[1].replace(numericSegment, '/{id}');
    const digit = match[4].charCodeAt(0) - 48;
    let latency = Number(match[3]) * 10 + digit;

    if (!Number.isSafeInteger(latency)) {
      latency = BigInt(match[3]) * 10n + BigInt(digit);
    }

    const entry = paths.get(template);
    if (entry === undefined) {
      paths.set(template, { template, values: [latency] });
    } else {
      entry.values.push(latency);
    }
  }
}

const fd = fs.openSync(process.argv[2], 'r');
const buffer = Buffer.allocUnsafe(4 * 1024 * 1024);
const fragments = [];

for (;;) {
  const size = fs.readSync(fd, buffer, 0, buffer.length, null);
  if (size === 0) break;

  const chunk = buffer.toString('latin1', 0, size);
  let start = 0;

  if (fragments.length !== 0) {
    const firstNewline = chunk.indexOf('\n');

    if (firstNewline === -1) {
      fragments.push(chunk);
      continue;
    }

    fragments.push(chunk.slice(0, firstNewline + 1));
    scan(fragments.join(''));
    fragments.length = 0;
    start = firstNewline + 1;
  }

  const end = chunk.lastIndexOf('\n') + 1;

  if (end > start) {
    scan(start === 0 && end === chunk.length
      ? chunk
      : chunk.slice(start, end));
  }

  if (end < chunk.length) {
    fragments.push(chunk.slice(end));
  }
}

fs.closeSync(fd);

function better(a, b) {
  const ac = a.values.length;
  const bc = b.values.length;
  return ac > bc || (ac === bc && a.template < b.template);
}

const top = [];

for (const entry of paths.values()) {
  let position = top.length;

  if (position === 10) {
    if (!better(entry, top[9])) continue;
    position = 9;
  }

  while (position > 0 && better(entry, top[position - 1])) {
    top[position] = top[position - 1];
    --position;
  }

  top[position] = entry;
}

function compareValues(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

function select(values, rank, left, right) {
  let budget = 2 * (32 - Math.clz32(right - left + 1));

  while (left < right) {
    if (--budget < 0) {
      const sorted = values.slice(left, right + 1);
      sorted.sort(compareValues);

      for (let i = 0; i < sorted.length; ++i) {
        values[left + i] = sorted[i];
      }

      return values[rank];
    }

    const middle = left + ((right - left) >>> 1);
    const a = values[left];
    const b = values[middle];
    const c = values[right];

    let pivot;
    if (a < b) {
      pivot = b < c ? b : a < c ? c : a;
    } else {
      pivot = a < c ? a : b < c ? c : b;
    }

    let i = left;
    let j = right;

    while (i <= j) {
      while (values[i] < pivot) ++i;
      while (values[j] > pivot) --j;

      if (i <= j) {
        const temporary = values[i];
        values[i] = values[j];
        values[j] = temporary;
        ++i;
        --j;
      }
    }

    if (rank <= j) {
      right = j;
    } else if (rank >= i) {
      left = i;
    } else {
      return values[rank];
    }
  }

  return values[rank];
}

function formatLatency(value) {
  if (typeof value === 'bigint') {
    return (value / 10n).toString() + '.' + (value % 10n).toString();
  }

  return Math.floor(value / 10).toString() + '.' + (value % 10).toString();
}

const output = [
  'lines ' + lines,
  'malformed ' + malformed
];

for (let i = 0; i < 10; ++i) {
  if (statuses[i] !== 0) {
    output.push('status ' + i + 'xx ' + statuses[i]);
  }
}

for (const entry of top) {
  const values = entry.values;
  const count = values.length;
  const rank50 = Math.floor((count - 1) / 2);
  const rank95 = Math.floor((95 * count - 1) / 100);

  const p95 = select(values, rank95, 0, count - 1);
  let maximum = p95;

  for (let i = rank95 + 1; i < count; ++i) {
    if (values[i] > maximum) maximum = values[i];
  }

  const p50 = rank50 === rank95
    ? p95
    : select(values, rank50, 0, rank95 - 1);

  output.push(
    'path ' + entry.template + ' ' + count + ' ' +
    formatLatency(p50) + ' ' +
    formatLatency(p95) + ' ' +
    formatLatency(maximum)
  );
}

process.stdout.write(output.join('\n') + '\n');
