"use strict";
const fs = require("fs");

function isDig(c){ return c>=48 && c<=57; }
function isLow(c){ return c>=97 && c<=122; }
function isPathCh(c){
  return (c>=97&&c<=122)||(c>=65&&c<=90)||(c>=48&&c<=57)||c===95||c===47||c===45;
}

function main(){
  const path = process.argv[2];
  if(!path) process.exit(1);
  const data = fs.readFileSync(path);
  const n = data.length;
  let total=0, malformed=0;
  const statusCnt = new Array(10).fill(0);

  let entries = [];
  let tcap=1024;
  let slots=new Int32Array(tcap);
  let usedSlots=0;
  let tmp=new Uint8Array(256);

  let pos=0;
  while(pos<n){
    const lineStart=pos;
    const nl=data.indexOf(10,pos);
    let lineEnd;
    if(nl>=0){ lineEnd=nl; pos=nl+1; } else { lineEnd=n; pos=n; }
    total++;
    const ln=lineEnd-lineStart;
    const b=lineStart;
    let ok=true;
    let statusClass=0;
    let latency=0;
    let pathStart=0, pathEnd=0;

    if(ln<25) ok=false;
    else if(!(isDig(data[b])&&isDig(data[b+1])&&isDig(data[b+2])&&isDig(data[b+3])&&data[b+4]===45&&isDig(data[b+5])&&isDig(data[b+6])&&data[b+7]===45&&isDig(data[b+8])&&isDig(data[b+9])&&data[b+10]===84&&isDig(data[b+11])&&isDig(data[b+12])&&data[b+13]===58&&isDig(data[b+14])&&isDig(data[b+15])&&data[b+16]===58&&isDig(data[b+17])&&isDig(data[b+18])&&data[b+19]===46&&isDig(data[b+20])&&isDig(data[b+21])&&isDig(data[b+22])&&data[b+23]===90&&data[b+24]===32)) ok=false;
    else {
      let i=25;
      let st=i;
      while(i<ln && isLow(data[b+i])) i++;
      if(i===st) ok=false;
      else if(i>=ln || data[b+i]!==45) ok=false;
      else {
        i++; st=i;
        while(i<ln && isDig(data[b+i])) i++;
        if(i===st || i>=ln || data[b+i]!==32) ok=false;
        else {
          i++;
          const rem=ln-i;
          if(rem>=4 && data[b+i]===71&&data[b+i+1]===69&&data[b+i+2]===84&&data[b+i+3]===32) i+=4;
          else if(rem>=4 && data[b+i]===80&&data[b+i+1]===85&&data[b+i+2]===84&&data[b+i+3]===32) i+=4;
          else if(rem>=5 && data[b+i]===80&&data[b+i+1]===79&&data[b+i+2]===83&&data[b+i+3]===84&&data[b+i+4]===32) i+=5;
          else if(rem>=6 && data[b+i]===80&&data[b+i+1]===65&&data[b+i+2]===84&&data[b+i+3]===67&&data[b+i+4]===72&&data[b+i+5]===32) i+=6;
          else if(rem>=7 && data[b+i]===68&&data[b+i+1]===69&&data[b+i+2]===76&&data[b+i+3]===69&&data[b+i+4]===84&&data[b+i+5]===69&&data[b+i+6]===32) i+=7;
          else ok=false;
          if(ok){
            if(i>=ln || data[b+i]!==47) ok=false;
            else {
              pathStart=i;
              while(i<ln && data[b+i]!==32 && data[b+i]!==63){
                if(!isPathCh(data[b+i])){ ok=false; break; }
                i++;
              }
              if(ok){
                pathEnd=i;
                if(i<ln && data[b+i]===63){
                  i++;
                  while(i<ln && data[b+i]!==32) i++;
                }
                if(i>=ln || data[b+i]!==32) ok=false;
                else {
                  i++;
                  if(i+4>ln || !isDig(data[b+i])||!isDig(data[b+i+1])||!isDig(data[b+i+2])||data[b+i+3]!==32) ok=false;
                  else {
                    statusClass=data[b+i]-48;
                    i+=4;
                    st=i;
                    while(i<ln && isDig(data[b+i])) i++;
                    if(i===st || i>=ln || data[b+i]!==66) ok=false;
                    else {
                      i++;
                      if(i>=ln || data[b+i]!==32) ok=false;
                      else {
                        i++;
                        st=i; let v=0;
                        while(i<ln && isDig(data[b+i])){ v=v*10+(data[b+i]-48); i++; }
                        if(i===st || i>=ln || data[b+i]!==46) ok=false;
                        else {
                          i++;
                          if(i>=ln || !isDig(data[b+i])) ok=false;
                          else {
                            v=v*10+(data[b+i]-48); i++; latency=v;
                            if(i+2>ln || data[b+i]!==109 || data[b+i+1]!==115) ok=false;
                            else {
                              i+=2;
                              if(i>=ln || data[b+i]!==32) ok=false;
                              else {
                                i++;
                                if(i>=ln || data[b+i]!==34) ok=false;
                                else if(data[b+ln-1]!==34 || i+1>=ln) ok=false;
                                else {
                                  const q=data.indexOf(34, b+i+1);
                                  if(q>=0 && q < b+ln-1) ok=false;
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    if(!ok){ malformed++; continue; }
    statusCnt[statusClass]++;

    if(tmp.length < (pathEnd-pathStart)+16) tmp=new Uint8Array((pathEnd-pathStart)+64);
    let tlen=0;
    let p=pathStart;
    while(true){
      const segStart=p;
      while(p<pathEnd && data[b+p]!==47) p++;
      const segLen=p-segStart;
      let allDig=segLen>0;
      if(allDig) for(let k=segStart;k<p;k++) if(!isDig(data[b+k])){ allDig=false; break; }
      if(tlen+(allDig?4:segLen)+1>tmp.length){
        const nt=new Uint8Array(tmp.length*2+32); nt.set(tmp); tmp=nt;
      }
      if(allDig){ tmp[tlen++]=123; tmp[tlen++]=105; tmp[tlen++]=100; tmp[tlen++]=125; }
      else if(segLen>0){ tmp.set(data.subarray(b+segStart,b+p), tlen); tlen+=segLen; }
      if(p>=pathEnd) break;
      tmp[tlen++]=47;
      p++;
    }

    let h=2166136261>>>0;
    for(let k=0;k<tlen;k++){ h ^= tmp[k]; h=Math.imul(h,16777619); }
    h>>>=0;

    if((usedSlots+1)*10 > tcap*7){
      const ncap=tcap*2;
      const nslots=new Int32Array(ncap);
      const mask2=ncap-1;
      for(let ei=0; ei<entries.length; ei++){
        const en=entries[ei];
        let hh=2166136261>>>0;
        for(let k=0;k<en.key.length;k++){ hh ^= en.key[k]; hh=Math.imul(hh,16777619); }
        hh>>>=0;
        let idx2=hh & mask2;
        while(nslots[idx2]!==0) idx2=(idx2+1)&mask2;
        nslots[idx2]=ei+1;
      }
      slots=nslots; tcap=ncap;
    }
    const mask=tcap-1;
    let idx=h & mask;
    let found=null;
    while(true){
      const v=slots[idx];
      if(v===0) break;
      const en=entries[v-1];
      if(en.key.length===tlen){
        let eq=true;
        for(let k=0;k<tlen;k++) if(en.key[k]!==tmp[k]){ eq=false; break; }
        if(eq){ found=en; break; }
      }
      idx=(idx+1)&mask;
    }
    if(found){
      found.lats.push(latency);
      if(latency>found.mx) found.mx=latency;
    } else {
      const key=new Uint8Array(tlen);
      key.set(tmp.subarray(0,tlen));
      const en={key, lats:[latency], mx:latency};
      entries.push(en);
      slots[idx]=entries.length;
      usedSlots++;
    }
  }

  entries.sort((x,y)=>{
    if(x.lats.length!==y.lats.length) return y.lats.length-x.lats.length;
    const ml=Math.min(x.key.length,y.key.length);
    for(let k=0;k<ml;k++) if(x.key[k]!==y.key[k]) return x.key[k]-y.key[k];
    return x.key.length-y.key.length;
  });
  const top=Math.min(10, entries.length);
  let out="";
  out += "lines "+total+"\n";
  out += "malformed "+malformed+"\n";
  for(let c=0;c<10;c++) if(statusCnt[c]>0) out += "status "+c+"xx "+statusCnt[c]+"\n";
  const fmt=v=> (v/10|0)+"."+(v%10);
  // Note: v/10|0 works for v < 2^31
  for(let ti=0; ti<top; ti++){
    const en=entries[ti];
    en.lats.sort((a,b)=>a-b);
    const nn=en.lats.length;
    const r50=Math.floor((50*nn+99)/100);
    const r95=Math.floor((95*nn+99)/100);
    const p50=en.lats[r50-1];
    const p95=en.lats[r95-1];
    let keyStr="";
    // decode latin1 in chunks
    keyStr=Buffer.from(en.key).toString("latin1");
    out += "path "+keyStr+" "+nn+" "+fmt(p50)+" "+fmt(p95)+" "+fmt(en.mx)+"\n";
  }
  process.stdout.write(out);
}
main();
