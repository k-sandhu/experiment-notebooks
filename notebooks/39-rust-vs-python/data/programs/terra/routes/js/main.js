"use strict";
const fs=require("fs");
const data=fs.readFileSync(process.argv[2]);let cursor=0;
function readInt(){while(cursor<data.length&&data[cursor]<=32)cursor++;let n=0;while(cursor<data.length&&data[cursor]>32)n=n*10+data[cursor++]-48;return n;}
const n=readInt(),m=readInt(),q=readInt();const head=new Int32Array(n);head.fill(-1);const to=new Int32Array(2*m),next=new Int32Array(2*m),weight=new Int32Array(2*m);
for(let i=0;i<m;i++){const u=readInt(),v=readInt(),w=readInt(),e=2*i;to[e]=v;weight[e]=w;next[e]=head[u];head[u]=e;to[e+1]=u;weight[e+1]=w;next[e+1]=head[v];head[v]=e+1;}
const sources=new Int32Array(q);for(let i=0;i<q;i++)sources[i]=readInt();const dist=new Float64Array(n),pos=new Int32Array(n),heap=new Int32Array(n);let output="";
for(const s of sources){dist.fill(Infinity);pos.fill(-1);let size=1;heap[0]=s;pos[s]=0;dist[s]=0;let total=0n,partial=0,chunk=0,far=0,count=0,node=s;
 while(size){const u=heap[0],last=heap[--size];pos[u]=-2;if(size){let i=0;while(true){let c=i*2+1;if(c>=size)break;if(c+1<size&&dist[heap[c+1]]<dist[heap[c]])c++;if(dist[last]<=dist[heap[c]])break;heap[i]=heap[c];pos[heap[i]]=i;i=c;}heap[i]=last;pos[last]=i;}
  const du=dist[u];partial+=du;if(++chunk===1024){total+=BigInt(partial);partial=0;chunk=0;}count++;if(du>far||(du===far&&u<node)){far=du;node=u;}
  for(let e=head[u];e!==-1;e=next[e]){const v=to[e],nd=du+weight[e];if(nd<dist[v]){dist[v]=nd;let i=pos[v];if(i<0)i=size++;while(i>0){const p=(i-1)>>1;if(dist[heap[p]]<=nd)break;heap[i]=heap[p];pos[heap[i]]=i;i=p;}heap[i]=v;pos[v]=i;}}
 }total+=BigInt(partial);output+=`${s} ${count} ${total} ${far} ${node}\n`;
}
process.stdout.write(output);
