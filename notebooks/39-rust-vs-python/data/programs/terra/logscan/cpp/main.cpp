#include <algorithm>
#include <fcntl.h>
#include <io.h>
#include <array>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;
static bool digit(char c){ return c >= '0' && c <= '9'; }
static bool letter(char c){return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');}
static bool parse(const string& s, string& path, string& latency, int& status) {
 size_t n=s.size(), i=0;
 auto digits=[&](int k){for(int j=0;j<k;j++) if(i>=n || !digit(s[i++])) return false; return true;};
 auto ch=[&](char c){return i<n && s[i++]==c;};
 if(!digits(4)||!ch('-')||!digits(2)||!ch('-')||!digits(2)||!ch('T')||!digits(2)||!ch(':')||!digits(2)||!ch(':')||!digits(2)||!ch('.')||!digits(3)||!ch('Z')||!ch(' ')) return false;
 size_t start=i; while(i<n && s[i]>='a' && s[i]<='z') i++; if(i==start||!ch('-')) return false;
 start=i; while(i<n && digit(s[i])) i++; if(i==start||!ch(' ')) return false;
 start=i; while(i<n && s[i]!=' ') i++; string_view m(s.data()+start,i-start);
 if(m!="GET"&&m!="POST"&&m!="PUT"&&m!="DELETE"&&m!="PATCH") return false;
 if(!ch(' ')||i>=n||s[i]!='/') return false;
 path.clear();
 while(i<n && s[i]=='/') {path.push_back('/'); i++; start=i; bool numeric=true;
  while(i<n && (letter(s[i])||digit(s[i])||s[i]=='_')) {if(!digit(s[i])) numeric=false; i++;}
  if(i>start && numeric) path += "{id}"; else path.append(s,start,i-start);
 }
 if(i<n && s[i]=='?'){i++; while(i<n && s[i]!=' ') i++;}
 if(!ch(' ')||i>=n||!digit(s[i])) return false; status=s[i]-'0';
 if(!digits(3)||!ch(' ')) return false;
 start=i; while(i<n && digit(s[i])) i++; if(i==start||!ch('B')||!ch(' ')) return false;
 start=i; while(i<n && digit(s[i])) i++; if(i==start) return false; size_t end=i;
 if(!ch('.')||i>=n||!digit(s[i])) return false; char fraction=s[i++];
 if(!ch('m')||!ch('s')||!ch(' ')||!ch('"')) return false;
 while(i<n && s[i]!='"') i++; if(!ch('"')||i!=n) return false;
 while(start<end && s[start]=='0') start++;
 latency.assign(s,start,end-start); latency.push_back(fraction);
 size_t nonzero=latency.find_first_not_of('0'); if(nonzero==string::npos) latency="0"; else if(nonzero) latency.erase(0,nonzero);
 return true;
}
static bool lessnum(const string&a,const string&b){return a.size()!=b.size()?a.size()<b.size():a<b;}
static string fmt(const string& s){return s.size()==1 ? "0."+s : s.substr(0,s.size()-1)+"."+s.back();}
int main(int argc,char**argv){_setmode(_fileno(stdout), _O_BINARY); ifstream in(argv[1],ios::binary); string line,path,lat; unordered_map<string,vector<string>> paths; array<size_t,10> statuses{}; size_t lines=0,bad=0; int status;
 while(getline(in,line)){lines++; if(!parse(line,path,lat,status)){bad++;continue;} statuses[status]++; paths[path].push_back(move(lat));}
 cout<<"lines "<<lines<<"\nmalformed "<<bad<<'\n'; for(int i=0;i<10;i++) if(statuses[i]) cout<<"status "<<i<<"xx "<<statuses[i]<<'\n';
 vector<decltype(paths)::value_type*> top; for(auto& p:paths) top.push_back(&p); sort(top.begin(),top.end(),[](auto a,auto b){return a->second.size()!=b->second.size()?a->second.size()>b->second.size():a->first<b->first;});
 for(size_t i=0;i<min<size_t>(10,top.size());i++){auto& v=top[i]->second; sort(v.begin(),v.end(),lessnum); size_t n=v.size(); cout<<"path "<<top[i]->first<<' '<<n<<' '<<fmt(v[(n-1)/2])<<' '<<fmt(v[n-n/20-1])<<' '<<fmt(v.back())<<'\n';}
}
