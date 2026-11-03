import java.io.*;
import java.util.Arrays;
public class Main {
 static class Input { final InputStream in; final byte[] buf=new byte[1<<16]; int p,n; Input(String path)throws Exception{in=new FileInputStream(path);} int read()throws Exception{if(p==n){n=in.read(buf);p=0;if(n<0)return -1;}return buf[p++]&255;} int next()throws Exception{int c;do{c=read();}while(c<=32&&c>=0);int x=0;while(c>32){x=x*10+c-48;c=read();}return x;} }
 public static void main(String[] args)throws Exception {
  Input in=new Input(args[0]);int n=in.next(),m=in.next(),q=in.next();int[] head=new int[n],to=new int[2*m],next=new int[2*m],weight=new int[2*m];Arrays.fill(head,-1);
  for(int i=0;i<m;i++){int u=in.next(),v=in.next(),w=in.next(),e=2*i;to[e]=v;weight[e]=w;next[e]=head[u];head[u]=e;to[e+1]=u;weight[e+1]=w;next[e+1]=head[v];head[v]=e+1;}
  int[] sources=new int[q];for(int i=0;i<q;i++)sources[i]=in.next();long[] dist=new long[n];int[] pos=new int[n],heap=new int[n];StringBuilder out=new StringBuilder();
  for(int s:sources){Arrays.fill(dist,Long.MAX_VALUE);Arrays.fill(pos,-1);int size=1;heap[0]=s;pos[s]=0;dist[s]=0;long total=0,far=0;int count=0,node=s;
   while(size>0){int u=heap[0],last=heap[--size];pos[u]=-2;if(size>0){int i=0;while(true){int c=i*2+1;if(c>=size)break;if(c+1<size&&dist[heap[c+1]]<dist[heap[c]])c++;if(dist[last]<=dist[heap[c]])break;heap[i]=heap[c];pos[heap[i]]=i;i=c;}heap[i]=last;pos[last]=i;}
    long du=dist[u];total+=du;count++;if(du>far||(du==far&&u<node)){far=du;node=u;}
    for(int e=head[u];e!=-1;e=next[e]){int v=to[e];long nd=du+weight[e];if(nd<dist[v]){dist[v]=nd;int i=pos[v];if(i<0)i=size++;while(i>0){int p=(i-1)/2;if(dist[heap[p]]<=nd)break;heap[i]=heap[p];pos[heap[i]]=i;i=p;}heap[i]=v;pos[v]=i;}}
   }out.append(s).append(' ').append(count).append(' ').append(total).append(' ').append(far).append(' ').append(node).append('\n');
  }System.out.print(out);
 }
}
