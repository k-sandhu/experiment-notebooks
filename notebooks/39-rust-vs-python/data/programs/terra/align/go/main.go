package main
import ("os"; "bufio"; "strconv")
func main(){
 data,_:=os.ReadFile(os.Args[1]); pos,start,length:=0,0,0
 token:=func(){for pos<len(data)&&data[pos]<=32{pos++}; start=pos; for pos<len(data)&&data[pos]>32{pos++}; length=pos-start}
 number:=func()int{token(); x:=0; for i:=start;i<start+length;i++{x=x*10+int(data[i]-'0')}; return x}
 token(); a,A:=start,length; var ins,del [128]int64; var sub [128][128]int64
 for i:=0;i<A;i++{ins[data[a+i]]=int64(number())}; for i:=0;i<A;i++{del[data[a+i]]=int64(number())}
 for i:=0;i<A;i++{for j:=0;j<A;j++{sub[data[a+i]][data[a+j]]=int64(number())}}
 P:=number(); var total int64; dp:=make([]int64,1); out:=bufio.NewWriter(os.Stdout)
 for k:=0;k<P;k++{token(); s,n:=start,length; token(); t,m:=start,length; if len(dp)<=m{dp=make([]int64,m+1)}; dp[0]=0
  for j:=1;j<=m;j++{dp[j]=dp[j-1]+ins[data[t+j-1]]}
  for i:=0;i<n;i++{c:=data[s+i]; dc:=del[c]; row:=&sub[c]; diag:=dp[0]; dp[0]+=dc; left:=dp[0]
   for j:=1;j<=m;j++{d:=data[t+j-1]; up:=dp[j]; v,h,z:=up+dc,left+ins[d],diag+row[d]; if h<v{v=h}; if z<v{v=z}; left=v; dp[j]=v; diag=up}}
  total+=dp[m]; out.WriteString(strconv.FormatInt(dp[m],10)); out.WriteByte('\n')}
 out.WriteString("total "); out.WriteString(strconv.FormatInt(total,10)); out.WriteByte('\n'); out.Flush()
}
