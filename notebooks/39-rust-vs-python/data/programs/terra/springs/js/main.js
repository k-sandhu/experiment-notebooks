"use strict";
const fields=require('fs').readFileSync(process.argv[2],'utf8').trim().split(/\s+/); let p=0;
const next=()=>Number(fields[p++]);
const n=next(), steps=next(), dt=next(), P=next();
const x=new Float64Array(n),v=new Float64Array(n),m=new Float64Array(n),k=new Float64Array(n),r=new Float64Array(n),c=new Float64Array(n),f=new Float64Array(n);
for(let i=0;i<n;i++){x[i]=next();v[i]=next();m[i]=next();k[i]=next();r[i]=next();c[i]=next();}
for(let t=0;t<steps;t++){
 for(let i=0;i<n-1;i++)f[i]=k[i]*((x[i+1]-x[i])-r[i]);
 f[n-1]=k[n-1]*(((x[0]+P)-x[n-1])-r[n-1]);let prev=f[n-1];
 for(let i=0;i<n;i++){const force=(f[i]-prev)-(c[i]*v[i]);prev=f[i];v[i]=v[i]+dt*(force/m[i]);x[i]=x[i]+dt*v[i];}
}
let K=0,U=0,X=0,best=-1,j=0;
for(let i=0;i<n;i++){K+=((0.5*m[i])*v[i])*v[i];X+=x[i];const a=Math.abs(v[i]);if(a>best){best=a;j=i;}const s=(i===n-1?((x[0]+P)-x[i]):(x[i+1]-x[i]))-r[i];U+=((0.5*k[i])*s)*s;}
console.log(`kinetic ${K.toPrecision(17)}\npotential ${U.toPrecision(17)}\nposition ${X.toPrecision(17)}\nfastest ${j}`);
