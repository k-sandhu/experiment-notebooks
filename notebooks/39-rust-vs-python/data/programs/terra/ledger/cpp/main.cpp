#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <nlohmann/json.hpp>
using namespace std;
using json = nlohmann::json;
struct Stat { int64_t count = 0, net = 0; };
int main(int argc, char** argv) {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    ifstream f(argv[1], ios::binary); string line;
    getline(f, line); auto first = json::parse(line);
    unordered_map<string,int64_t> rates;
    for (auto it=first["rates"].begin(); it!=first["rates"].end(); ++it) rates.emplace(it.key(), it.value().get<int64_t>());
    unordered_map<string,int64_t> accounts; unordered_map<string,Stat> channels;
    int64_t count=0, net=0;
    while (getline(f,line)) {
        auto j=json::parse(line);
        auto &type=j["type"].get_ref<const string&>();
        if(type=="void") continue;
        bool skip=false; for(auto &tag:j["tags"]) if(tag=="test") {skip=true; break;}
        if(skip) continue;
        auto rate=rates.at(j["currency"].get_ref<const string&>());
        auto &a=j["amount"].get_ref<const string&>(); uint64_t amount=0; size_t i=0;
        while(rate!=0 && i<a.size() && a[i]!='.') amount=amount*10+(a[i++]-'0');
        amount*=100; if(rate!=0 && i<a.size()) { ++i; amount+=(a[i++]-'0')*10; if(i<a.size()) amount+=a[i]-'0'; }
        int64_t product=static_cast<int64_t>(amount*static_cast<uint64_t>(rate));
        int64_t value=product/1000000; if(product<0 && product%1000000) --value;
        if(type=="debit") value=-value;
        ++count; net+=value; accounts[j["account"].get_ref<const string&>()]+=value;
        auto &s=channels[j["meta"]["channel"].get_ref<const string&>()]; ++s.count; s.net+=value;
    }
    cout<<"counted "<<count<<"\nnet "<<net<<'\n';
    vector<pair<string,Stat>> cs(channels.begin(),channels.end());
    sort(cs.begin(),cs.end(),[](auto &a,auto &b){return a.first<b.first;});
    for(auto &p:cs) cout<<"channel "<<p.first<<' '<<p.second.count<<' '<<p.second.net<<'\n';
    vector<pair<string,int64_t>> as(accounts.begin(),accounts.end());
    auto cmp=[](auto &a,auto &b){return a.second!=b.second?a.second>b.second:a.first<b.first;};
    auto n=min<size_t>(10,as.size()); partial_sort(as.begin(),as.begin()+n,as.end(),cmp);
    for(size_t i=0;i<n;++i) cout<<"account "<<as[i].first<<' '<<as[i].second<<'\n';
}
