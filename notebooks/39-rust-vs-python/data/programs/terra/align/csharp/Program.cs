using System.Text;
byte[] data=File.ReadAllBytes(args[0]); int pos=0,start=0,len=0;
void Token(){while(pos<data.Length&&data[pos]<=32)pos++; start=pos; while(pos<data.Length&&data[pos]>32)pos++; len=pos-start;}
int Number(){Token(); int x=0; for(int i=start;i<start+len;i++)x=x*10+data[i]-'0'; return x;}
Token(); int a=start,A=len; int[] ins=new int[128],del=new int[128],sub=new int[128*128];
for(int i=0;i<A;i++)ins[data[a+i]]=Number(); for(int i=0;i<A;i++)del[data[a+i]]=Number();
for(int i=0;i<A;i++)for(int j=0;j<A;j++)sub[data[a+i]*128+data[a+j]]=Number();
int P=Number(); long total=0; var output=new StringBuilder(); long[] dp=new long[1];
for(int k=0;k<P;k++){Token(); int s=start,n=len; Token(); int t=start,m=len; if(dp.Length<=m)dp=new long[m+1]; dp[0]=0;
 for(int j=1;j<=m;j++)dp[j]=dp[j-1]+ins[data[t+j-1]];
 for(int i=0;i<n;i++){int c=data[s+i],dc=del[c],row=c*128; long diag=dp[0]; dp[0]+=dc; long left=dp[0];
  for(int j=1;j<=m;j++){int d=data[t+j-1]; long up=dp[j],v=up+dc,h=left+ins[d],z=diag+sub[row+d]; left=Math.Min(Math.Min(v,h),z); dp[j]=left; diag=up;}}
 total+=dp[m]; output.Append(dp[m]).Append('\n');}
output.Append("total ").Append(total).Append('\n'); Console.Write(output.ToString());
