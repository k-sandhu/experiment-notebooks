'use strict';

const fs = require('fs');

const pattern = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) (\/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? ([0-9])[0-9]{2} \d+B (\d+)\.(\d)ms "[^"\n]*"\n/y;
const numericSegment = /\/[0-9]+(?=\/|$)/g;

const statuses = new Float64Array(10);
const paths = new Map();

let lines = 0;
let malformed = 0;

function scan(text, end) {
    let position = 0;

    while (position < end) {
        ++lines;
        pattern.lastIndex = position;
        const match = pattern.exec(text);

        if (match === null) {
            ++malformed;
            position = text.indexOf('\n', position) + 1;
            continue;
        }

        position = pattern.lastIndex;
        ++statuses[match[2].charCodeAt(0) - 48];

        let template = match[1].replace(numericSegment, '/{id}');
        let entry = paths.get(template);

        if (entry === undefined) {
            // Copy new keys so they do not retain entire input chunks.
            template = Buffer.from(template, 'latin1').toString('latin1');
            entry = { template, values: [], big: false };
            paths.set(template, entry);
        }

        const fraction = match[4].charCodeAt(0) - 48;
        let latency = Number(match[3]) * 10 + fraction;

        if (!Number.isSafeInteger(latency)) {
            latency = BigInt(match[3]) * 10n + BigInt(fraction);
            entry.big = true;
        }

        entry.values.push(latency);
    }
}

const fd = fs.openSync(process.argv[2], 'r');
const buffer = Buffer.allocUnsafe(8 * 1024 * 1024);
let fragments = [];

for (;;) {
    const bytes = fs.readSync(fd, buffer, 0, buffer.length, null);
    if (bytes === 0) break;

    let text = buffer.toString('latin1', 0, bytes);
    const lastNewline = text.lastIndexOf('\n');

    if (lastNewline === -1) {
        fragments.push(text);
        continue;
    }

    if (fragments.length !== 0) {
        fragments.push(text.slice(0, lastNewline + 1));
        const complete = fragments.join('');
        scan(complete, complete.length);
        fragments = [];
    } else {
        scan(text, lastNewline + 1);
    }

    if (lastNewline + 1 < text.length) {
        fragments.push(text.slice(lastNewline + 1));
    }
}

fs.closeSync(fd);

function compareEntries(a, b) {
    const difference = b.values.length - a.values.length;
    if (difference !== 0) return difference;
    return a.template < b.template ? -1 : a.template > b.template ? 1 : 0;
}

const top = [];

for (const entry of paths.values()) {
    if (top.length === 10 && compareEntries(entry, top[9]) >= 0) {
        continue;
    }

    let index = top.length;
    while (index > 0 && compareEntries(entry, top[index - 1]) < 0) {
        --index;
    }

    top.splice(index, 0, entry);
    if (top.length > 10) top.pop();
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

for (let digit = 0; digit < 10; ++digit) {
    if (statuses[digit] !== 0) {
        output.push('status ' + digit + 'xx ' + statuses[digit]);
    }
}

for (const entry of top) {
    let sorted;

    if (entry.big) {
        sorted = entry.values;
        sorted.sort((a, b) => a < b ? -1 : a > b ? 1 : 0);
    } else {
        sorted = Float64Array.from(entry.values);
        sorted.sort();
    }

    const count = sorted.length;
    const p50 = sorted[Math.floor((count - 1) / 2)];
    const p95 = sorted[Math.floor((95 * count + 99) / 100) - 1];
    const maximum = sorted[count - 1];

    output.push(
        'path ' + entry.template + ' ' + count + ' ' +
        formatLatency(p50) + ' ' +
        formatLatency(p95) + ' ' +
        formatLatency(maximum)
    );
}

process.stdout.write(output.join('\n') + '\n');
