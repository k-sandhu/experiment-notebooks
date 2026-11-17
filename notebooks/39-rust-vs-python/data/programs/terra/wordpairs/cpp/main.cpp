#include <algorithm>
#include <fcntl.h>
#include <io.h>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>
using namespace std;
struct Table {
 vector<uint64_t> keys, counts; size_t used=0;
 Table():keys(1024),counts(1024){}
 static uint64_t hash(uint64_t x){x^=x>>30; x*=0xbf58476d1ce4e5b9ULL; x^=x>>27; x*=0x94d049bb133111ebULL; return x^(x>>31);}
 void grow(){auto k=move(keys), c=move(counts); keys.assign(k.size()*2,0); counts.assign(keys.size(),0); for(size_t i=0;i<k.size();i++) if(k[i]) {size_t p=hash(k[i])&(keys.size()-1); while(keys[p]) p=(p+1)&(keys.size()-1); keys[p]=k[i]; counts[p]=c[i];}}
 void add(uint64_t k){if((used+1)*10>=keys.size()*7) grow(); size_t p=hash(k)&(keys.size()-1); while(keys[p] && keys[p]!=k) p=(p+1)&(keys.size()-1); if(!keys[p]){keys[p]=k; used++;} counts[p]++;}
};
int main(int argc,char** argv){
 if(argc<2) return 1; _setmode(_fileno(stdout), _O_BINARY); ifstream f(argv[1],ios::binary); if(!f) return 1; string s((istreambuf_iterator<char>(f)),{}); for(char& c:s) if(c>='A'&&c<='Z') c+=32;
 unordered_map<string_view,uint32_t> ids; vector<string_view> words(1); Table table; uint64_t total=0,pairs=0; uint32_t prev=0;
 for(size_t i=0;i<s.size();){unsigned char c=s[i]; if(c>='a'&&c<='z'){size_t start=i++; while(i<s.size() && s[i]>='a'&&s[i]<='z') i++; string_view w(s.data()+start,i-start); auto [it,inserted]=ids.try_emplace(w,(uint32_t)words.size()); if(inserted) words.push_back(w); uint32_t id=it->second; total++; if(prev){table.add((uint64_t(prev)<<32)|id); pairs++;} prev=id;} else {if(c=='.'||c=='!'||c=='?') prev=0; i++;}}
 struct Row{uint64_t key,count;}; vector<Row> top; auto better=[&](const Row&a,const Row&b){if(a.count!=b.count) return a.count>b.count; auto af=words[a.key>>32],bf=words[b.key>>32]; if(af!=bf) return af<bf; return words[(uint32_t)a.key]<words[(uint32_t)b.key];};
 for(size_t i=0;i<table.keys.size();i++) if(table.keys[i] && (top.size()<20 || table.counts[i]>=top.back().count)){Row r{table.keys[i],table.counts[i]}; auto pos=lower_bound(top.begin(),top.end(),r,better); if(pos!=top.end()||top.size()<20){top.insert(pos,r); if(top.size()>20) top.pop_back();}}
 cout<<"words "<<total<<"\npairs "<<pairs<<"\ndistinct "<<table.used<<'\n'; for(auto r:top) cout<<r.count<<' '<<words[r.key>>32]<<' '<<words[(uint32_t)r.key]<<'\n';
}
