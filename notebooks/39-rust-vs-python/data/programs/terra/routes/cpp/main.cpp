#include <cstdio>
#include <vector>
#include <cstdint>
#include <limits>
#include <algorithm>
using namespace std;
struct Input { FILE* f; char b[1<<16]; size_t p=0,n=0; Input(const char* path){f=fopen(path,"rb");} int next(){int c; do {if(p==n){n=fread(b,1,sizeof b,f);p=0;} c=b[p++];} while(c<=32); int x=0; do {x=x*10+c-'0'; if(p==n){n=fread(b,1,sizeof b,f);p=0;if(!n)break;} c=b[p++];} while(c>32); return x;} };
int main(int argc,char** argv){
 Input in(argv[1]); int n=in.next(),m=in.next(),q=in.next();
 vector<int> head(n,-1),to(2LL*m),next(2LL*m),weight(2LL*m);
 for(int i=0;i<m;i++){int u=in.next(),v=in.next(),w=in.next(),e=2*i;to[e]=v;weight[e]=w;next[e]=head[u];head[u]=e;to[e+1]=u;weight[e+1]=w;next[e+1]=head[v];head[v]=e+1;}
 vector<int> sources(q);for(int &s:sources)s=in.next();
 vector<long long> dist(n);vector<int> pos(n),heap(n);
 for(int s:sources){fill(dist.begin(),dist.end(),numeric_limits<long long>::max());fill(pos.begin(),pos.end(),-1);int size=1;heap[0]=s;pos[s]=0;dist[s]=0;long long total=0,far=0;int count=0,node=s;
 while(size){int u=heap[0],last=heap[--size];pos[u]=-2;if(size){int i=0;while(true){int c=i*2+1;if(c>=size)break;if(c+1<size&&dist[heap[c+1]]<dist[heap[c]])c++;if(dist[last]<=dist[heap[c]])break;heap[i]=heap[c];pos[heap[i]]=i;i=c;}heap[i]=last;pos[last]=i;}
 long long du=dist[u];total+=du;count++;if(du>far||(du==far&&u<node)){far=du;node=u;}
 for(int e=head[u];e!=-1;e=next[e]){int v=to[e];long long nd=du+weight[e];if(nd<dist[v]){dist[v]=nd;int i=pos[v];if(i<0){i=size++;}while(i>0){int p=(i-1)/2;if(dist[heap[p]]<=nd)break;heap[i]=heap[p];pos[heap[i]]=i;i=p;}heap[i]=v;pos[v]=i;}}
 }
 printf("%d %d %lld %lld %d\n",s,count,total,far,node);
 }
}
