'use strict';
const data=require('fs').readFileSync(process.argv[2]); let at=0;
function number() { while(data[at]<=32) at++; let n=0; while(at<data.length && data[at]>32) n=n*10+data[at++]-48; return n; }
const h=number(),w=number(),steps=number(),stride=w+2,size=(h+2)*stride;
let a=new Int32Array(size),b=new Int32Array(size);
const coeff=new Int32Array(size),cells=new Int32Array(h*w); let count=0;
for(let r=0;r<h;r++) {
    while(data[at]<=32) at++;
    for(let c=0;c<w;c++) {
        const ch=data[at++],p=(r+1)*stride+c+1;
        if(ch===46) { cells[count++]=p; coeff[p]=4; }
        else if(ch!==35) a[p]=b[p]=(ch-48)*1000;
        if(ch!==35) coeff[p] |= 16;
    }
}
for(let i=0;i<count;i++) { const p=cells[i]; coeff[p]=8-((coeff[p-stride]!==0)+(coeff[p+stride]!==0)+(coeff[p-1]!==0)+(coeff[p+1]!==0)); }
for(let s=0;s<steps;s++) {
    for(let i=0;i<count;i++) { const p=cells[i]; b[p]=(coeff[p]*a[p]+a[p-stride]+a[p+stride]+a[p-1]+a[p+1])>>3; }
    [a,b]=[b,a];
}
let sum=0n,checksum=0n,best=-1,pos=0;
for(let i=0;i<count;i++) { const p=cells[i],v=a[p],r=Math.floor(p/stride)-1,c=p%stride-1; sum+=BigInt(v); checksum+=BigInt(v)*(BigInt(r)*BigInt(w)+BigInt(c)+1n); if(v>best) { best=v; pos=p; } }
console.log(`sum ${sum}\nmax ${best} ${Math.floor(pos/stride)-1} ${pos%stride-1}\nchecksum ${checksum}`);
