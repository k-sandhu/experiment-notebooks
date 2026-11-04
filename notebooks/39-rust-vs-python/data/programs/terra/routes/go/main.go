package main
import (
 "bufio"
 "fmt"
 "os"
 "strconv"
)
type Input struct { f *os.File; b []byte; p,n int }
func (in *Input) next() int { c:=byte(0); for { if in.p==in.n {in.n,_=in.f.Read(in.b);in.p=0}; c=in.b[in.p];in.p++;if c>32 {break} };x:=0;for { x=x*10+int(c-'0');if in.p==in.n {in.n,_=in.f.Read(in.b);in.p=0;if in.n==0 {break}};c=in.b[in.p];in.p++;if c<=32 {break} };return x }
func main(){ f,_:=os.Open(os.Args[1]);in:=Input{f:f,b:make([]byte,1<<16)};n,m,q:=in.next(),in.next(),in.next();head:=make([]int32,n);for i:=range head {head[i]=-1};to:=make([]int32,2*m);next:=make([]int32,2*m);weight:=make([]int32,2*m)
 for i:=0;i<m;i++ {u,v,w:=in.next(),in.next(),int32(in.next());e:=2*i;to[e]=int32(v);weight[e]=w;next[e]=head[u];head[u]=int32(e);to[e+1]=int32(u);weight[e+1]=w;next[e+1]=head[v];head[v]=int32(e+1)}
 sources:=make([]int,q);for i:=range sources {sources[i]=in.next()};dist:=make([]int64,n);pos:=make([]int32,n);heap:=make([]int32,n);out:=bufio.NewWriter(os.Stdout);defer out.Flush()
 for _,s:=range sources {for i:=range dist {dist[i]=int64(^uint64(0)>>1);pos[i]=-1};size:=1;heap[0]=int32(s);pos[s]=0;dist[s]=0;var total,far int64;count,node:=0,s
  for size>0 {u:=heap[0];size--;last:=heap[size];pos[u]=-2;if size>0 {i:=0;for {c:=i*2+1;if c>=size {break};if c+1<size&&dist[heap[c+1]]<dist[heap[c]] {c++};if dist[last]<=dist[heap[c]] {break};heap[i]=heap[c];pos[heap[i]]=int32(i);i=c};heap[i]=last;pos[last]=int32(i)}
   du:=dist[u];total+=du;count++;if du>far||(du==far&&int(u)<node) {far=du;node=int(u)}
   for e:=head[u];e!=-1;e=next[e] {v:=to[e];nd:=du+int64(weight[e]);if nd<dist[v] {dist[v]=nd;i:=int(pos[v]);if i<0 {i=size;size++};for i>0 {p:=(i-1)/2;if dist[heap[p]]<=nd {break};heap[i]=heap[p];pos[heap[i]]=int32(i);i=p};heap[i]=v;pos[v]=int32(i)}}
  };b:=make([]byte,0,100);b=strconv.AppendInt(b,int64(s),10);b=append(b,' ');b=strconv.AppendInt(b,int64(count),10);b=append(b,' ');b=strconv.AppendInt(b,total,10);b=append(b,' ');b=strconv.AppendInt(b,far,10);b=append(b,' ');b=strconv.AppendInt(b,int64(node),10);b=append(b,'\n');fmt.Fprint(out,string(b))
 }
}
