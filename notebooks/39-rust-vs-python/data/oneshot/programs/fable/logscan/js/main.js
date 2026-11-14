'use strict';
const fs = require('fs');

function keyBefore(tCount, keys, tOff, tLen, a, b) {
  const ca = tCount[a], cb = tCount[b];
  if (ca !== cb) return ca > cb;
  const oa = tOff[a], ob = tOff[b], la = tLen[a], lb = tLen[b];
  const m = la < lb ? la : lb;
  for (let j = 0; j < m; j++) {
    const x = keys[oa + j], y = keys[ob + j];
    if (x !== y) return x < y;
  }
  return la < lb;
}

function fmt(v) {
  const r = v % 10;
  return ((v - r) / 10) + '.' + r;
}

// Exact (BigInt) fallback, used only if a latency does not fit in a double exactly.
function slowPath(inputPath) {
  const re = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) (\/[A-Za-z0-9_\/-]*)(?:\?[^ ]*)? (\d)\d{2} \d+B (\d+)\.(\d)ms "[^"]*"$/;
  const digitsOnly = /^\d+$/;
  const fd = fs.openSync(inputPath, 'r');
  const chunk = Buffer.allocUnsafe(1 << 22);
  let rest = '';
  let lines = 0, malformed = 0;
  const status = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  const map = new Map();
  for (;;) {
    const n = fs.readSync(fd, chunk, 0, chunk.length, null);
    if (n <= 0) break;
    const str = rest + chunk.toString('latin1', 0, n);
    let start = 0;
    for (;;) {
      const nl = str.indexOf('\n', start);
      if (nl < 0) break;
      const line = str.substring(start, nl);
      start = nl + 1;
      lines++;
      const m = re.exec(line);
      if (m === null) { malformed++; continue; }
      status[+m[2]]++;
      const segs = m[1].split('/');
      for (let j = 0; j < segs.length; j++) {
        if (digitsOnly.test(segs[j])) segs[j] = '{id}';
      }
      const tpl = segs.join('/');
      let arr = map.get(tpl);
      if (arr === undefined) { arr = []; map.set(tpl, arr); }
      arr.push(BigInt(m[3] + m[4]));
    }
    rest = str.substring(start);
  }
  fs.closeSync(fd);
  let out = 'lines ' + lines + '\nmalformed ' + malformed + '\n';
  for (let d = 0; d < 10; d++) {
    if (status[d] > 0) out += 'status ' + d + 'xx ' + status[d] + '\n';
  }
  const entries = Array.from(map.entries());
  entries.sort((a, b) => (b[1].length - a[1].length) || (a[0] < b[0] ? -1 : (a[0] > b[0] ? 1 : 0)));
  const lim = entries.length < 10 ? entries.length : 10;
  const f = (v) => (v / 10n).toString() + '.' + (v % 10n).toString();
  for (let r = 0; r < lim; r++) {
    const arr = entries[r][1];
    arr.sort((a, b) => (a < b ? -1 : (a > b ? 1 : 0)));
    const n = arr.length;
    const k50 = Math.floor((50 * n + 99) / 100), k95 = Math.floor((95 * n + 99) / 100);
    out += 'path ' + entries[r][0] + ' ' + n + ' ' + f(arr[k50 - 1]) + ' ' + f(arr[k95 - 1]) + ' ' + f(arr[n - 1]) + '\n';
  }
  process.stdout.write(out);
}

function main() {
  const inputPath = process.argv[2];
  const fd = fs.openSync(inputPath, 'r');

  // 1 = digit, 2 = other path segment char, 0 = everything else (including '/')
  const CLS = new Uint8Array(256);
  for (let c = 48; c <= 57; c++) CLS[c] = 1;
  for (let c = 65; c <= 90; c++) CLS[c] = 2;
  for (let c = 97; c <= 122; c++) CLS[c] = 2;
  CLS[95] = 2;
  CLS[45] = 2;

  let buf = Buffer.allocUnsafe(1 << 20);
  let tmp = new Uint8Array(buf.length * 3 + 16);

  let lines = 0, malformed = 0;
  const statusCount = new Float64Array(10);

  // template hash table
  let tCap = 1024, tMask = tCap - 1;
  let slots = new Int32Array(tCap);
  let nT = 0, idCap = 256;
  let tHash = new Int32Array(idCap);
  let tLen = new Int32Array(idCap);
  let tOff = new Int32Array(idCap);
  let tCount = new Float64Array(idCap);
  let keys = new Uint8Array(1 << 16);
  let keysLen = 0;

  // records
  let recCap = 1 << 21;
  let recId = new Int32Array(recCap);
  let recLat = new Float64Array(recCap);
  let nrec = 0;

  let big = false;
  let carry = 0;

  reading:
  for (;;) {
    if (buf.length - carry < 65536) {
      const nb = Buffer.allocUnsafe(buf.length * 2);
      buf.copy(nb, 0, 0, carry);
      buf = nb;
      tmp = new Uint8Array(buf.length * 3 + 16);
    }
    const n = fs.readSync(fd, buf, carry, buf.length - carry, null);
    if (n <= 0) break;
    const end = carry + n;
    const stop = buf.lastIndexOf(10, end - 1) + 1;
    if (stop === 0) { carry = end; continue; }

    let s = 0;
    while (s < stop) {
      lines++;
      let i = s;
      let c = 0;
      ok: {
        if (((buf[s] - 48) >>> 0) > 9 || ((buf[s + 1] - 48) >>> 0) > 9 ||
            ((buf[s + 2] - 48) >>> 0) > 9 || ((buf[s + 3] - 48) >>> 0) > 9 ||
            buf[s + 4] !== 45 ||
            ((buf[s + 5] - 48) >>> 0) > 9 || ((buf[s + 6] - 48) >>> 0) > 9 ||
            buf[s + 7] !== 45 ||
            ((buf[s + 8] - 48) >>> 0) > 9 || ((buf[s + 9] - 48) >>> 0) > 9 ||
            buf[s + 10] !== 84 ||
            ((buf[s + 11] - 48) >>> 0) > 9 || ((buf[s + 12] - 48) >>> 0) > 9 ||
            buf[s + 13] !== 58 ||
            ((buf[s + 14] - 48) >>> 0) > 9 || ((buf[s + 15] - 48) >>> 0) > 9 ||
            buf[s + 16] !== 58 ||
            ((buf[s + 17] - 48) >>> 0) > 9 || ((buf[s + 18] - 48) >>> 0) > 9 ||
            buf[s + 19] !== 46 ||
            ((buf[s + 20] - 48) >>> 0) > 9 || ((buf[s + 21] - 48) >>> 0) > 9 ||
            ((buf[s + 22] - 48) >>> 0) > 9 ||
            buf[s + 23] !== 90 || buf[s + 24] !== 32) break ok;

        i = s + 25;
        // host: [a-z]+-\d+
        c = buf[i];
        if (((c - 97) >>> 0) > 25) break ok;
        do { c = buf[++i]; } while (((c - 97) >>> 0) <= 25);
        if (c !== 45) break ok;
        c = buf[++i];
        if (((c - 48) >>> 0) > 9) break ok;
        do { c = buf[++i]; } while (((c - 48) >>> 0) <= 9);
        if (c !== 32) break ok;
        c = buf[++i];

        // method
        if (c === 71) { // GET
          if (buf[i + 1] !== 69 || buf[i + 2] !== 84) break ok;
          i += 3;
        } else if (c === 80) {
          c = buf[i + 1];
          if (c === 79) { // POST
            if (buf[i + 2] !== 83 || buf[i + 3] !== 84) break ok;
            i += 4;
          } else if (c === 85) { // PUT
            if (buf[i + 2] !== 84) break ok;
            i += 3;
          } else if (c === 65) { // PATCH
            if (buf[i + 2] !== 84 || buf[i + 3] !== 67 || buf[i + 4] !== 72) break ok;
            i += 5;
          } else break ok;
        } else if (c === 68) { // DELETE
          if (buf[i + 1] !== 69 || buf[i + 2] !== 76 || buf[i + 3] !== 69 ||
              buf[i + 4] !== 84 || buf[i + 5] !== 69) break ok;
          i += 6;
        } else break ok;
        if (buf[i] !== 32 || buf[i + 1] !== 47) break ok;
        i++;

        // path -> template in tmp[0..p), hash h
        let h = 0, p = 0;
        for (;;) {
          tmp[p++] = 47;
          h = (Math.imul(h, 31) + 47) | 0;
          const p0 = p, h0 = h;
          let nd = 0;
          c = buf[++i];
          let k = CLS[c];
          while (k !== 0) {
            nd |= k;
            tmp[p++] = c;
            h = (Math.imul(h, 31) + c) | 0;
            c = buf[++i];
            k = CLS[c];
          }
          if (nd === 1) {
            tmp[p0] = 123; tmp[p0 + 1] = 105; tmp[p0 + 2] = 100; tmp[p0 + 3] = 125;
            p = p0 + 4;
            h = (Math.imul(h0, 31) + 123) | 0;
          }
          if (c !== 47) break;
        }

        // optional query
        if (c === 63) {
          do { c = buf[++i]; } while (c !== 32 && c !== 10);
        }
        if (c !== 32) break ok;

        // status
        const sc = buf[i + 1] - 48;
        if ((sc >>> 0) > 9 || ((buf[i + 2] - 48) >>> 0) > 9 ||
            ((buf[i + 3] - 48) >>> 0) > 9 || buf[i + 4] !== 32) break ok;
        i += 5;

        // size
        c = buf[i];
        if (((c - 48) >>> 0) > 9) break ok;
        do { c = buf[++i]; } while (((c - 48) >>> 0) <= 9);
        if (c !== 66 || buf[i + 1] !== 32) break ok;
        i += 2;

        // latency
        c = buf[i];
        if (((c - 48) >>> 0) > 9) break ok;
        let lat = 0;
        do {
          lat = lat * 10 + (c - 48);
          c = buf[++i];
        } while (((c - 48) >>> 0) <= 9);
        if (c !== 46) break ok;
        c = buf[i + 1];
        if (((c - 48) >>> 0) > 9 || buf[i + 2] !== 109 || buf[i + 3] !== 115 ||
            buf[i + 4] !== 32 || buf[i + 5] !== 34) break ok;
        lat = lat * 10 + (c - 48);
        i += 5;

        // user agent
        do { c = buf[++i]; } while (c !== 34 && c !== 10);
        if (c !== 34 || buf[i + 1] !== 10) break ok;
        i++;

        if (lat >= 9007199254740992) { big = true; break reading; }

        // template lookup
        let slot = (h ^ (h >>> 15)) & tMask;
        let id = slots[slot] - 1;
        while (id >= 0) {
          if (tHash[id] === h && tLen[id] === p) {
            const o = tOff[id];
            let j = 0;
            while (j < p && keys[o + j] === tmp[j]) j++;
            if (j === p) break;
          }
          slot = (slot + 1) & tMask;
          id = slots[slot] - 1;
        }
        if (id < 0) {
          if (nT === idCap) {
            idCap *= 2;
            let a = new Int32Array(idCap); a.set(tHash); tHash = a;
            a = new Int32Array(idCap); a.set(tLen); tLen = a;
            a = new Int32Array(idCap); a.set(tOff); tOff = a;
            const f = new Float64Array(idCap); f.set(tCount); tCount = f;
          }
          if (keysLen + p > keys.length) {
            let nl = keys.length * 2;
            while (nl < keysLen + p) nl *= 2;
            const nk = new Uint8Array(nl);
            nk.set(keys.subarray(0, keysLen));
            keys = nk;
          }
          id = nT++;
          tHash[id] = h;
          tLen[id] = p;
          tOff[id] = keysLen;
          tCount[id] = 0;
          for (let j = 0; j < p; j++) keys[keysLen + j] = tmp[j];
          keysLen += p;
          slots[slot] = id + 1;
          if (nT * 2 > tCap) {
            tCap *= 2;
            tMask = tCap - 1;
            slots = new Int32Array(tCap);
            for (let t = 0; t < nT; t++) {
              const th = tHash[t];
              let q = (th ^ (th >>> 15)) & tMask;
              while (slots[q] !== 0) q = (q + 1) & tMask;
              slots[q] = t + 1;
            }
          }
        }
        tCount[id]++;
        statusCount[sc]++;
        if (nrec === recCap) {
          recCap *= 2;
          const a = new Int32Array(recCap); a.set(recId); recId = a;
          const f = new Float64Array(recCap); f.set(recLat); recLat = f;
        }
        recId[nrec] = id;
        recLat[nrec] = lat;
        nrec++;
        s = i + 1;
        continue;
      }
      malformed++;
      while (buf[i] !== 10) i++;
      s = i + 1;
    }

    carry = end - stop;
    if (carry > 0) buf.copyWithin(0, stop, end);
  }
  fs.closeSync(fd);

  if (big) {
    slowPath(inputPath);
    return;
  }

  // top 10 templates
  const top = new Int32Array(10);
  let nTop = 0;
  for (let t = 0; t < nT; t++) {
    let pos = nTop;
    while (pos > 0 && keyBefore(tCount, keys, tOff, tLen, t, top[pos - 1])) pos--;
    if (pos >= 10) continue;
    const lim = nTop < 10 ? nTop : 9;
    for (let j = lim; j > pos; j--) top[j] = top[j - 1];
    top[pos] = t;
    if (nTop < 10) nTop++;
  }

  const rank = new Int32Array(nT).fill(-1);
  const lists = [];
  const fillPos = new Int32Array(10);
  const maxs = new Float64Array(10);
  for (let r = 0; r < nTop; r++) {
    rank[top[r]] = r;
    lists.push(new Float64Array(tCount[top[r]]));
  }
  for (let j = 0; j < nrec; j++) {
    const r = rank[recId[j]];
    if (r >= 0) {
      const v = recLat[j];
      lists[r][fillPos[r]++] = v;
      if (v > maxs[r]) maxs[r] = v;
    }
  }

  let out = 'lines ' + lines + '\nmalformed ' + malformed + '\n';
  for (let d = 0; d < 10; d++) {
    if (statusCount[d] > 0) out += 'status ' + d + 'xx ' + statusCount[d] + '\n';
  }

  let hist = null;
  for (let r = 0; r < nTop; r++) {
    const id = top[r];
    const arr = lists[r];
    const n = arr.length;
    const k50 = Math.floor((50 * n + 99) / 100);
    const k95 = Math.floor((95 * n + 99) / 100);
    const mx = maxs[r];
    let p50 = 0, p95 = 0;
    if (mx < 67108864 && (mx < 65536 || mx < 16 * n)) {
      if (hist === null || hist.length < mx + 1) hist = new Uint32Array(mx + 1);
      else hist.fill(0, 0, mx + 1);
      for (let j = 0; j < n; j++) hist[arr[j] | 0]++;
      let cum = 0, v = 0;
      for (;; v++) {
        cum += hist[v];
        if (cum >= k50) break;
      }
      p50 = v;
      while (cum < k95) {
        v++;
        cum += hist[v];
      }
      p95 = v;
    } else {
      arr.sort();
      p50 = arr[k50 - 1];
      p95 = arr[k95 - 1];
    }
    const o = tOff[id];
    const name = Buffer.from(keys.subarray(o, o + tLen[id])).toString('latin1');
    out += 'path ' + name + ' ' + n + ' ' + fmt(p50) + ' ' + fmt(p95) + ' ' + fmt(mx) + '\n';
  }

  process.stdout.write(out);
}

main();
