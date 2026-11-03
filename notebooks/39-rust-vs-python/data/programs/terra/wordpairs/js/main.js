'use strict';
const fs = require('fs');
const data = fs.readFileSync(process.argv[2]);
for (let i=0;i<data.length;i++) if(data[i]>=65&&data[i]<=90) data[i]+=32;
let offsets=new Uint32Array(1024), lengths=new Uint32Array(1024), slots=new Uint32Array(2048), wordCount=0;
function wordHash(s,e){let h=0x811c9dc5;for(let i=s;i<e;i++) h=Math.imul(h^data[i],0x01000193);return (h^(h>>>16))>>>0;}
function growWords(){const old=slots;slots=new Uint32Array(old.length*2);for(let i=0;i<old.length;i++){const id=old[i];if(id){let p=wordHash(offsets[id],offsets[id]+lengths[id])&(slots.length-1);while(slots[p])p=(p+1)&(slots.length-1);slots[p]=id;}}}
function intern(s,e){if((wordCount+1)*10>=slots.length*7)growWords();let p=wordHash(s,e)&(slots.length-1);while(slots[p]){const id=slots[p];if(lengths[id]===e-s){let j=0;while(j<e-s&&data[offsets[id]+j]===data[s+j])j++;if(j===e-s)return id;}p=(p+1)&(slots.length-1);}const id=++wordCount;if(id===offsets.length){let a=new Uint32Array(id*2),b=new Uint32Array(id*2);a.set(offsets);b.set(lengths);offsets=a;lengths=b;}offsets[id]=s;lengths[id]=e-s;slots[p]=id;return id;}
let first=new Uint32Array(1024),second=new Uint32Array(1024),counts=new Float64Array(1024),distinct=0;
function pairHash(a,b){let h=(Math.imul(a,0x9e3779b1)^Math.imul(b,0x85ebca6b))|0;h=Math.imul(h^(h>>>16),0x7feb352d);h=Math.imul(h^(h>>>15),0x846ca68b);return (h^(h>>>16))>>>0;}
function growPairs(){const of=first,os=second,oc=counts;first=new Uint32Array(of.length*2);second=new Uint32Array(first.length);counts=new Float64Array(first.length);const mask=first.length-1;for(let i=0;i<of.length;i++)if(of[i]){let p=pairHash(of[i],os[i])&mask;while(first[p])p=(p+1)&mask;first[p]=of[i];second[p]=os[i];counts[p]=oc[i];}}
function add(a,b){if((distinct+1)*10>=first.length*7)growPairs();const mask=first.length-1;let p=pairHash(a,b)&mask;while(first[p]&&(first[p]!==a||second[p]!==b))p=(p+1)&mask;if(!first[p]){first[p]=a;second[p]=b;distinct++;}counts[p]++;}
let total=0,pairs=0,prev=0;for(let i=0;i<data.length;){const c=data[i];if(c>=97&&c<=122){const s=i++;while(i<data.length&&data[i]>=97&&data[i]<=122)i++;const id=intern(s,i);total++;if(prev){add(prev,id);pairs++;}prev=id;}else{if(c===46||c===33||c===63)prev=0;i++;}}
function cmpWord(a,b){const n=Math.min(lengths[a],lengths[b]);for(let i=0;i<n;i++){const d=data[offsets[a]+i]-data[offsets[b]+i];if(d)return d;}return lengths[a]-lengths[b];}
function cmp(a,b){return b.c-a.c||cmpWord(a.a,b.a)||cmpWord(a.b,b.b);}
const top=[];for(let i=0;i<first.length;i++)if(first[i]&&(top.length<20||counts[i]>=top[top.length-1].c)){const r={a:first[i],b:second[i],c:counts[i]};let p=0;while(p<top.length&&cmp(top[p],r)<0)p++;if(p<20){top.splice(p,0,r);if(top.length>20)top.pop();}}
let out=`words ${total}\npairs ${pairs}\ndistinct ${distinct}\n`;for(const r of top)out+=`${r.c} ${data.toString('ascii',offsets[r.a],offsets[r.a]+lengths[r.a])} ${data.toString('ascii',offsets[r.b],offsets[r.b]+lengths[r.b])}\n`;process.stdout.write(out);
