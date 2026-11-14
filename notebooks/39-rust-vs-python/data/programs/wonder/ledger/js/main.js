"use strict";
const fs = require("fs");
const b = fs.readFileSync(process.argv[2]);
const n = b.length;
let p = 0;

// string span state
let sStart = 0, sEnd = 0, sEscaped = null; // if sEscaped !== null, decoded string

function skipWs() {
  while (p < n) { const c = b[p]; if (c===32||c===9||c===13||c===10) p++; else break; }
}
function decodeSpan(s, e) {
  let out = "";
  let i = s;
  // Build via array of chunks for speed on rare path
  let parts = [];
  let chunkStart = i;
  while (i < e) {
    const c = b[i];
    if (c !== 92) { i++; continue; }
    if (i > chunkStart) parts.push(b.toString("utf8", chunkStart, i));
    i++;
    if (i >= e) break;
    const esc = b[i++];
    if (esc === 34) parts.push('"');
    else if (esc === 92) parts.push('\\');
    else if (esc === 47) parts.push('/');
    else if (esc === 98) parts.push('\b');
    else if (esc === 102) parts.push('\f');
    else if (esc === 110) parts.push('\n');
    else if (esc === 114) parts.push('\r');
    else if (esc === 116) parts.push('\t');
    else if (esc === 117) {
      const cp = parseInt(b.toString("ascii", i, i+4), 16); i += 4;
      // surrogate pairs naturally form if we push code units; but combined handling:
      if (cp >= 0xD800 && cp <= 0xDBFF && i+1 < e && b[i]===92 && b[i+1]===117) {
        const lo = parseInt(b.toString("ascii", i+2, i+6), 16);
        if (lo >= 0xDC00 && lo <= 0xDFFF) { i += 6; parts.push(String.fromCodePoint(0x10000 + ((cp-0xD800)<<10) + (lo-0xDC00))); chunkStart = i; continue; }
      }
      parts.push(String.fromCharCode(cp));
    } else parts.push(String.fromCharCode(esc));
    chunkStart = i;
  }
  if (e > chunkStart) parts.push(b.toString("utf8", chunkStart, e));
  return parts.join("");
}
function parseString() {
  p++;
  const start = p;
  let i = p;
  let esc = false;
  while (i < n) {
    const c = b[i];
    if (c === 34) break;
    if (c === 92) { esc = true; i += 2; continue; }
    i++;
  }
  const end = i;
  p = i < n ? i + 1 : i;
  sStart = start; sEnd = end;
  sEscaped = esc ? decodeSpan(start, end) : null;
}
// compare current span to ascii literal (string)
function spanEqStr(lit) {
  if (sEscaped !== null) return sEscaped === lit;
  const len = sEnd - sStart;
  if (len !== lit.length) return false;
  for (let i = 0; i < len; i++) if (b[sStart + i] !== lit.charCodeAt(i)) return false;
  return true;
}
function spanToString() {
  if (sEscaped !== null) return sEscaped;
  return b.toString("utf8", sStart, sEnd);
}
function skipString() {
  p++;
  while (p < n) { const c = b[p]; if (c===34){p++;return;} if (c===92){p+=2;continue;} p++; }
}
function skipValue() {
  skipWs();
  if (p >= n) return;
  const c = b[p];
  if (c === 34) { skipString(); return; }
  if (c === 123 || c === 91) {
    let depth = 0;
    while (p < n) {
      const ch = b[p];
      if (ch === 34) { skipString(); continue; }
      if (ch === 123 || ch === 91) { depth++; p++; continue; }
      if (ch === 125 || ch === 93) { p++; if (--depth===0) return; continue; }
      p++;
    }
    return;
  }
  while (p < n) { const ch=b[p]; if (ch===44||ch===125||ch===93||ch===32||ch===9||ch===13||ch===10) break; p++; }
}
function parseIntValue() {
  skipWs(); let neg=false;
  if (p<n && b[p]===45){neg=true;p++;}
  let v=0;
  while (p<n && b[p]>=48 && b[p]<=57){ v=v*10+(b[p]-48); p++; }
  while (p<n){ const c=b[p]; if ((c>=48&&c<=57)||c===46||c===101||c===69||c===43||c===45) p++; else break; }
  return neg?-v:v;
}
function parseAmountFromSpan() {
  // use sStart/sEnd unless escaped (amount shouldn't be escaped; handle)
  if (sEscaped !== null) {
    const s = sEscaped; let v=0,i=0;
    while(i<s.length && s.charCodeAt(i)>=48 && s.charCodeAt(i)<=57){ v=v*10+(s.charCodeAt(i)-48); i++; }
    v*=100;
    if(i<s.length && s[i]==='.'){ i++; let frac=0,dig=0; while(i<s.length && s.charCodeAt(i)>=48 && s.charCodeAt(i)<=57 && dig<2){ frac=frac*10+(s.charCodeAt(i)-48); i++; dig++; } if(dig===1)frac*=10; v+=frac; }
    return v;
  }
  let v=0; let i=sStart;
  while(i<sEnd && b[i]>=48 && b[i]<=57){ v=v*10+(b[i]-48); i++; }
  v*=100;
  if(i<sEnd && b[i]===46){ i++; let frac=0,dig=0; while(i<sEnd && b[i]>=48 && b[i]<=57 && dig<2){ frac=frac*10+(b[i]-48); i++; dig++; } if(dig===1)frac*=10; v+=frac; }
  return v;
}

if (n === 0) { process.stdout.write("counted 0\nnet 0\n"); process.exit(0); }

const rates = []; // [codeString, rate]
skipWs();
if (p < n && b[p]===123) {
  p++;
  while (p < n) {
    skipWs(); if (p>=n) break;
    if (b[p]===125){p++;break;}
    if (b[p]===44){p++;continue;}
    parseString();
    const isRates = spanEqStr("rates");
    const keyStr = isRates ? null : null;
    skipWs(); if (p<n && b[p]===58) p++;
    if (isRates) {
      skipWs();
      if (p<n && b[p]===123) {
        p++;
        while (p<n) {
          skipWs(); if(p>=n)break;
          if (b[p]===125){p++;break;}
          if (b[p]===44){p++;continue;}
          parseString(); const code = spanToString();
          skipWs(); if(p<n && b[p]===58)p++;
          const rate = parseIntValue();
          rates.push([code, rate]);
        }
      } else skipValue();
    } else skipValue();
  }
}
const rateMap = new Map(rates);
const chanMap = new Map(); // name -> [count, net]
const accounts = new Map();
let counted = 0, totalNet = 0;

while (true) {
  while (p<n && (b[p]===10||b[p]===13||b[p]===32||b[p]===9)) p++;
  if (p>=n) break;
  if (b[p]!==123){ while(p<n && b[p]!==10) p++; continue; }
  p++;
  let account = null, channel = null;
  let hundredths = 0, rate = 1000000, sign = 1, skip = false;
  while (p<n) {
    skipWs(); if(p>=n)break;
    const c=b[p];
    if (c===125){p++;break;}
    if (c===44){p++;continue;}
    parseString();
    // identify key: compare span
    let kid = -1;
    if (sEscaped !== null) {
      if (sEscaped==="account") kid=0; else if (sEscaped==="type") kid=1; else if (sEscaped==="amount") kid=2;
      else if (sEscaped==="currency") kid=3; else if (sEscaped==="tags") kid=4; else if (sEscaped==="meta") kid=5;
    } else {
      const len = sEnd - sStart;
      if (len===7 && spanEqStr("account")) kid=0;
      else if (len===4 && spanEqStr("type")) kid=1;
      else if (len===6 && spanEqStr("amount")) kid=2;
      else if (len===8 && spanEqStr("currency")) kid=3;
      else if (len===4 && spanEqStr("tags")) kid=4;
      else if (len===4 && spanEqStr("meta")) kid=5;
    }
    skipWs(); if(p<n && b[p]===58)p++; skipWs();
    if (kid===0) {
      if (p<n && b[p]===34){ parseString(); account = spanToString(); } else skipValue();
    } else if (kid===1) {
      if (p<n && b[p]===34){ parseString(); if (spanEqStr("void")) skip=true; else if (spanEqStr("debit")) sign=-1; else sign=1; } else skipValue();
    } else if (kid===2) {
      if (p<n && b[p]===34){ parseString(); hundredths = parseAmountFromSpan(); } else skipValue();
    } else if (kid===3) {
      if (p<n && b[p]===34){ parseString(); const cur = spanToString(); rate = rateMap.has(cur) ? rateMap.get(cur) : 0; } else skipValue();
    } else if (kid===4) {
      skipWs();
      if (p<n && b[p]===91) {
        p++;
        while (p<n) {
          skipWs(); if(p>=n)break;
          if (b[p]===93){p++;break;}
          if (b[p]===44){p++;continue;}
          if (b[p]===34){ parseString(); if (spanEqStr("test")) skip=true; } else skipValue();
          if (skip) break;
        }
      } else skipValue();
    } else if (kid===5) {
      skipWs();
      if (p<n && b[p]===123) {
        p++;
        while (p<n) {
          skipWs(); if(p>=n)break;
          if (b[p]===125){p++;break;}
          if (b[p]===44){p++;continue;}
          parseString(); const isCh = spanEqStr("channel");
          skipWs(); if(p<n && b[p]===58)p++; skipWs();
          if (isCh) { if (p<n && b[p]===34){ parseString(); channel = spanToString(); } else skipValue(); }
          else skipValue();
        }
      } else skipValue();
    } else skipValue();
    if (skip) { while(p<n && b[p]!==10) p++; if(p<n)p++; break; }
  }
  if (skip) continue;
  // exact conversion: use BigInt only if product risks >2^53
  let usd;
  if (hundredths <= 4503599627 && rate <= 2000000) {
    // product <= ~9e15 borderline; use decomposition to be safe
    const prod = hundredths * rate;
    usd = Math.floor(prod / 1000000);
    // decomposition correction for large prod: recompute via split if prod > 2^48
    if (prod > 281474976710656) {
      const a = Math.floor(hundredths / 1000000);
      const rem = hundredths - a * 1000000;
      usd = a * rate + Math.floor((rem * rate) / 1000000);
    }
  } else {
    usd = Number((BigInt(hundredths) * BigInt(rate)) / 1000000n);
  }
  const signed = sign * usd;
  counted++; totalNet += signed;
  if (channel !== null) {
    let e = chanMap.get(channel);
    if (e === undefined) { e = [0,0]; chanMap.set(channel, e); }
    e[0]++; e[1] += signed;
  }
  if (account !== null) {
    accounts.set(account, (accounts.get(account) || 0) + signed);
  }
}

const chans = Array.from(chanMap.entries()).sort((a,b)=> a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
const accs = Array.from(accounts.entries()).sort((a,b)=> (b[1]-a[1]) || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
let out = `counted ${counted}\nnet ${totalNet}\n`;
for (const [name, e] of chans) out += `channel ${name} ${e[0]} ${e[1]}\n`;
const top = Math.min(10, accs.length);
for (let i=0;i<top;i++) out += `account ${accs[i][0]} ${accs[i][1]}\n`;
process.stdout.write(out);
