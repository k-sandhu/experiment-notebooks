"use strict";
const data=require('fs').readFileSync(process.argv[2]); let pos=0,start=0,len=0;
function token(){while(pos<data.length&&data[pos]<=32)pos++; start=pos; while(pos<data.length&&data[pos]>32)pos++; len=pos-start;}
function number(){token(); let x=0; for(let i=start;i<start+len;i++)x=x*10+data[i]-48; return x;}
token(); const a=start,A=len,ins=new Int32Array(128),del=new Int32Array(128),sub=new Int32Array(128*128);
for(let i=0;i<A;i++)ins[data[a+i]]=number(); for(let i=0;i<A;i++)del[data[a+i]]=number();
for(let i=0;i<A;i++)for(let j=0;j<A;j++)sub[data[a+i]*128+data[a+j]]=number();
const P=number(); let total=0n,dp=new Float64Array(1),out=[];
for(let k=0;k<P;k++){token(); const s=start,n=len; token(); const t=start,m=len; if(dp.length<=m)dp=new Float64Array(m+1); dp[0]=0;
 for(let j=1;j<=m;j++)dp[j]=dp[j-1]+ins[data[t+j-1]];
 for(let i=0;i<n;i++){const c=data[s+i],dc=del[c],row=c*128; let diag=dp[0]; dp[0]+=dc; let left=dp[0];
  for(let j=1;j<=m;j++){const d=data[t+j-1],up=dp[j],v=up+dc,h=left+ins[d],z=diag+sub[row+d]; left=Math.min(v,h,z); dp[j]=left; diag=up;}}
 total+=BigInt(dp[m]); out.push(String(dp[m]));}
out.push('total '+total); process.stdout.write(out.join('\n')+'\n');
