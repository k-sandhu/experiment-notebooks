"use strict";

const fs = require("fs");

function isDig(c) {
    return c >= 48 && c <= 57;
}

function isPathCh(c) {
    return (c >= 65 && c <= 90) || (c >= 97 && c <= 122) ||
        (c >= 48 && c <= 57) || c === 95 || c === 45 || c === 47;
}

function tsOk(b, p) {
    return isDig(b[p]) && isDig(b[p + 1]) && isDig(b[p + 2]) && isDig(b[p + 3]) && b[p + 4] === 45 &&
        isDig(b[p + 5]) && isDig(b[p + 6]) && b[p + 7] === 45 &&
        isDig(b[p + 8]) && isDig(b[p + 9]) && b[p + 10] === 84 &&
        isDig(b[p + 11]) && isDig(b[p + 12]) && b[p + 13] === 58 &&
        isDig(b[p + 14]) && isDig(b[p + 15]) && b[p + 16] === 58 &&
        isDig(b[p + 17]) && isDig(b[p + 18]) && b[p + 19] === 46 &&
        isDig(b[p + 20]) && isDig(b[p + 21]) && isDig(b[p + 22]) && b[p + 23] === 90;
}

function main() {
    const fd = fs.openSync(process.argv[2], "r");
    let buf = Buffer.allocUnsafe(1 << 22);
    let used = 0;
    let eof = false;

    const map = new Map();
    const names = [];
    const latArr = [];
    const lens = [];
    const maxes = [];
    let scratch = Buffer.allocUnsafe(2048);

    let lines = 0, malformed = 0;
    const statusCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

    while (!eof) {
        if (used === buf.length) {
            const nb = Buffer.allocUnsafe(used << 1);
            buf.copy(nb, 0, 0, used);
            buf = nb;
        }
        const nread = fs.readSync(fd, buf, used, buf.length - used, null);
        if (nread > 0) {
            used += nread;
        }
        if (nread === 0) {
            if (used > 0 && buf[used - 1] !== 10) {
                if (used === buf.length) {
                    const nb = Buffer.allocUnsafe(used << 1);
                    buf.copy(nb, 0, 0, used);
                    buf = nb;
                }
                buf[used++] = 10;
            }
            eof = true;
        }

        let start = 0;
        while (start < used) {
            const nl = buf.indexOf(10, start);
            if (nl < 0 || nl >= used) break;
            const e = nl;
            lines++;

            let ok = true;
            let statusClass = 0;
            let lat = 0;
            let pathStart = 0, pathEnd = 0;

            {
                let q = start;
                const end = e;

                for (; ;) {
                    if (end - q < 25 || !tsOk(buf, q)) { ok = false; break; }
                    q += 24;
                    if (buf[q] !== 32) { ok = false; break; }
                    q++;
                    if (q >= end || buf[q] < 97 || buf[q] > 122) { ok = false; break; }
                    q++;
                    while (q < end && buf[q] >= 97 && buf[q] <= 122) q++;
                    if (q >= end || buf[q] !== 45) { ok = false; break; }
                    q++;
                    if (q >= end || !isDig(buf[q])) { ok = false; break; }
                    while (q < end && isDig(buf[q])) q++;
                    if (q >= end || buf[q] !== 32) { ok = false; break; }
                    q++;

                    const rem = end - q;
                    if (rem >= 4 && buf[q] === 71 && buf[q + 1] === 69 && buf[q + 2] === 84 && buf[q + 3] === 32) {
                        q += 4;
                    } else if (rem >= 5 && buf[q] === 80 && buf[q + 1] === 79 && buf[q + 2] === 83 && buf[q + 3] === 84 && buf[q + 4] === 32) {
                        q += 5;
                    } else if (rem >= 4 && buf[q] === 80 && buf[q + 1] === 85 && buf[q + 2] === 84 && buf[q + 3] === 32) {
                        q += 4;
                    } else if (rem >= 7 && buf[q] === 68 && buf[q + 1] === 69 && buf[q + 2] === 76 && buf[q + 3] === 69 && buf[q + 4] === 84 && buf[q + 5] === 69 && buf[q + 6] === 32) {
                        q += 7;
                    } else if (rem >= 6 && buf[q] === 80 && buf[q + 1] === 65 && buf[q + 2] === 84 && buf[q + 3] === 67 && buf[q + 4] === 72 && buf[q + 5] === 32) {
                        q += 6;
                    } else {
                        ok = false;
                        break;
                    }

                    if (q >= end || buf[q] !== 47) { ok = false; break; }
                    pathStart = q;
                    while (q < end && isPathCh(buf[q])) q++;
                    pathEnd = q;
                    if (q < end && buf[q] === 63) {
                        q++;
                        while (q < end && buf[q] !== 32) q++;
                    }
                    if (q >= end || buf[q] !== 32) { ok = false; break; }
                    q++;
                    if (end - q < 4 || !isDig(buf[q]) || !isDig(buf[q + 1]) || !isDig(buf[q + 2]) || buf[q + 3] !== 32) {
                        ok = false;
                        break;
                    }
                    statusClass = buf[q] - 48;
                    q += 4;
                    if (q >= end || !isDig(buf[q])) { ok = false; break; }
                    while (q < end && isDig(buf[q])) q++;
                    if (q >= end || buf[q] !== 66) { ok = false; break; }
                    q++;
                    if (q >= end || buf[q] !== 32) { ok = false; break; }
                    q++;
                    if (q >= end || !isDig(buf[q])) { ok = false; break; }
                    let v = 0;
                    while (q < end && isDig(buf[q])) { v = v * 10 + (buf[q] - 48); q++; }
                    if (q >= end || buf[q] !== 46) { ok = false; break; }
                    q++;
                    if (q >= end || !isDig(buf[q])) { ok = false; break; }
                    v = v * 10 + (buf[q] - 48);
                    q++;
                    if (end - q < 3 || buf[q] !== 109 || buf[q + 1] !== 115 || buf[q + 2] !== 32) {
                        ok = false;
                        break;
                    }
                    q += 3;
                    if (q >= end || buf[q] !== 34) { ok = false; break; }
                    q++;
                    while (q < end && buf[q] !== 34) q++;
                    if (q >= end) { ok = false; break; }
                    q++;
                    if (q !== end) { ok = false; break; }
                    lat = v;
                    break;
                }
            }

            if (!ok) {
                malformed++;
            } else {
                statusCount[statusClass]++;
                const need = (pathEnd - pathStart) * 4 + 4;
                if (need > scratch.length) scratch = Buffer.allocUnsafe(need);
                let tlen = 0;
                let t = pathStart;
                while (t < pathEnd) {
                    scratch[tlen++] = 47;
                    t++;
                    const s = t;
                    let digits = true, nonempty = false;
                    while (t < pathEnd && buf[t] !== 47) {
                        const c = buf[t];
                        if (c < 48 || c > 57) digits = false;
                        nonempty = true;
                        t++;
                    }
                    if (nonempty && digits) {
                        scratch[tlen++] = 123;
                        scratch[tlen++] = 105;
                        scratch[tlen++] = 100;
                        scratch[tlen++] = 125;
                    } else {
                        for (let k = s; k < t; k++) scratch[tlen++] = buf[k];
                    }
                }
                const tpl = scratch.toString("latin1", 0, tlen);
                let id = map.get(tpl);
                if (id === undefined) {
                    id = names.length;
                    map.set(tpl, id);
                    names.push(tpl);
                    latArr.push(new Int32Array(64));
                    lens.push(0);
                    maxes.push(0);
                }
                let arr = latArr[id];
                const len = lens[id];
                if (len === arr.length) {
                    const na = new Int32Array(len << 1);
                    na.set(arr);
                    arr = na;
                    latArr[id] = na;
                }
                arr[len] = lat;
                lens[id] = len + 1;
                if (lat > maxes[id]) maxes[id] = lat;
            }

            start = e + 1;
        }
        if (start > 0) {
            buf.copy(buf, 0, start, used);
            used -= start;
        }
    }
    fs.closeSync(fd);

    const out = [];
    out.push("lines " + lines);
    out.push("malformed " + malformed);
    for (let d = 0; d < 10; d++) {
        if (statusCount[d] !== 0) out.push("status " + d + "xx " + statusCount[d]);
    }

    const order = new Array(names.length);
    for (let i = 0; i < order.length; i++) order[i] = i;
    order.sort((a, c) => {
        const ca = lens[a], cc = lens[c];
        if (ca !== cc) return cc - ca;
        return names[a] < names[c] ? -1 : (names[a] > names[c] ? 1 : 0);
    });

    const top = Math.min(10, order.length);
    for (let k = 0; k < top; k++) {
        const idx = order[k];
        const cnt = lens[idx];
        const v = latArr[idx].subarray(0, cnt);
        v.sort();
        const i50 = Math.floor((50 * cnt + 99) / 100) - 1;
        const i95 = Math.floor((95 * cnt + 99) / 100) - 1;
        const p50 = v[i50], p95 = v[i95], mx = v[cnt - 1];
        out.push("path " + names[idx] + " " + cnt + " " +
            Math.floor(p50 / 10) + "." + (p50 % 10) + " " +
            Math.floor(p95 / 10) + "." + (p95 % 10) + " " +
            Math.floor(mx / 10) + "." + (mx % 10));
    }
    process.stdout.write(out.join("\n") + "\n");
}

main();
