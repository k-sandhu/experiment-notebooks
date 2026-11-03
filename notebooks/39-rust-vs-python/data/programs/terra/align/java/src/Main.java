import java.nio.file.Files;
import java.nio.file.Path;
public class Main {
 static byte[] data; static int pos,start,len;
 static void token(){while(pos<data.length&&data[pos]<=32)pos++; start=pos; while(pos<data.length&&data[pos]>32)pos++; len=pos-start;}
 static int number(){token(); int x=0; for(int i=start;i<start+len;i++)x=x*10+data[i]-'0'; return x;}
 public static void main(String[] args)throws Exception{
  data=Files.readAllBytes(Path.of(args[0])); token(); int a=start,A=len; int[] ins=new int[128],del=new int[128]; int[][] sub=new int[128][128];
  for(int i=0;i<A;i++)ins[data[a+i]]=number(); for(int i=0;i<A;i++)del[data[a+i]]=number();
  for(int i=0;i<A;i++)for(int j=0;j<A;j++)sub[data[a+i]][data[a+j]]=number();
  int P=number(); long total=0; StringBuilder out=new StringBuilder(); long[] dp=new long[1];
  for(int k=0;k<P;k++){token(); int s=start,n=len; token(); int t=start,m=len; if(dp.length<=m)dp=new long[m+1]; dp[0]=0;
   for(int j=1;j<=m;j++)dp[j]=dp[j-1]+ins[data[t+j-1]];
   for(int i=0;i<n;i++){int c=data[s+i],dc=del[c]; int[] row=sub[c]; long diag=dp[0]; dp[0]+=dc; long left=dp[0];
    for(int j=1;j<=m;j++){int d=data[t+j-1]; long up=dp[j],v=up+dc,h=left+ins[d],z=diag+row[d]; left=Math.min(Math.min(v,h),z); dp[j]=left; diag=up;}}
   total+=dp[m]; out.append(dp[m]).append('\n');}
  out.append("total ").append(total).append('\n'); System.out.print(out);
 }
}
