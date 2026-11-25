"use strict";
const fs = require("fs");
const readline = require("readline");
const re = /^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z [a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) (\/[A-Za-z0-9_\/-]*)(?:\?[^ ]*)? ([0-9])[0-9]{2} [0-9]+B ([0-9]+)\.([0-9])ms "[^"]*"$/;
const paths = new Map(), statuses = Array(10).fill(0); let lines=0, malformed=0;
function numberCompare(a,b) { return a.length-b.length || (a<b?-1:a>b?1:0); }
function format(s) { return s.length===1 ? '0.'+s : s.slice(0,-1)+'.'+s.slice(-1); }
(async () => {
 for await (const line of readline.createInterface({input:fs.createReadStream(process.argv[2]), crlfDelay:Infinity})) {
  lines++; const m=re.exec(line); if(!m){malformed++;continue;}
  const path=m[1].replace(/(^|\/)\d+(?=\/|$)/g,'$1{id}');
  let v=paths.get(path); if(!v){v=[]; paths.set(path,v);} v.push((m[3]+m[4]).replace(/^0+(?=.)/,'')); statuses[+m[2]]++;
 }
 let out=`lines ${lines}\nmalformed ${malformed}\n`;
 for(let i=0;i<10;i++) if(statuses[i]) out+=`status ${i}xx ${statuses[i]}\n`;
 const top=[...paths.entries()].sort((a,b)=>b[1].length-a[1].length||(a[0]<b[0]?-1:a[0]>b[0]?1:0)).slice(0,10);
 for(const [p,v] of top){v.sort(numberCompare);let n=v.length;out+=`path ${p} ${n} ${format(v[Math.floor((n-1)/2)])} ${format(v[n-Math.floor(n/20)-1])} ${format(v[n-1])}\n`;}
 process.stdout.write(out);
})();
