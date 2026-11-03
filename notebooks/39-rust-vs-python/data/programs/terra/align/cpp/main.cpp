#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
int main(int argc, char** argv) {
 std::ifstream f(argv[1],std::ios::binary); std::string in((std::istreambuf_iterator<char>(f)),{}); size_t p=0;
 auto tok=[&](){while(p<in.size()&&in[p]<=' ')++p; size_t s=p; while(p<in.size()&&in[p]>' ')++p; return std::pair<size_t,size_t>{s,p-s};};
 auto num=[&](){auto [s,n]=tok(); int x=0; for(size_t i=s;i<s+n;++i)x=x*10+in[i]-'0'; return x;};
 auto [a,A]=tok(); int ins[128]={},del[128]={},sub[128][128]={};
 for(size_t i=0;i<A;++i)ins[(unsigned char)in[a+i]]=num();
 for(size_t i=0;i<A;++i)del[(unsigned char)in[a+i]]=num();
 for(size_t i=0;i<A;++i)for(size_t j=0;j<A;++j)sub[(unsigned char)in[a+i]][(unsigned char)in[a+j]]=num();
 int P=num(); int64_t total=0; std::string out; std::vector<int64_t> dp;
 for(int k=0;k<P;++k){auto [s,n]=tok(); auto [t,m]=tok(); dp.resize(m+1); dp[0]=0;
  for(size_t j=1;j<=m;++j)dp[j]=dp[j-1]+ins[(unsigned char)in[t+j-1]];
  for(size_t i=0;i<n;++i){unsigned char c=in[s+i]; int dc=del[c]; int64_t diag=dp[0]; dp[0]+=dc; int64_t left=dp[0]; const int* row=sub[c];
   for(size_t j=1;j<=m;++j){unsigned char d=in[t+j-1]; int64_t up=dp[j]; left=std::min({up+dc,left+ins[d],diag+row[d]}); dp[j]=left; diag=up;}}
  total+=dp[m]; out+=std::to_string(dp[m]); out+='\n';}
 out+="total "+std::to_string(total)+'\n'; std::fwrite(out.data(),1,out.size(),stdout);
}
