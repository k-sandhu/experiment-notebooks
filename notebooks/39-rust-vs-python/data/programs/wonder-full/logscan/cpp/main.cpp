#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <string>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

static bool isDigit(unsigned char c){ return c>='0' && c<='9'; }
static unsigned char pathCharTab[256];

struct Parser{
    const unsigned char* d;
    size_t n;
    size_t i=0;
    size_t pathS=0,pathE=0;
    int statusDigit=0;
    int latency=0;
};

static bool parseLine(Parser &p){
    const unsigned char* d=p.d; size_t n=p.n; size_t i=p.i;
    auto fail=[&]()->bool{ p.i=i; return false; };
    if(i+25>n) return fail();
    // timestamp fixed layout
    if(!(isDigit(d[i])&&isDigit(d[i+1])&&isDigit(d[i+2])&&isDigit(d[i+3])&&d[i+4]=='-'&&
         isDigit(d[i+5])&&isDigit(d[i+6])&&d[i+7]=='-'&&isDigit(d[i+8])&&isDigit(d[i+9])&&
         d[i+10]=='T'&&isDigit(d[i+11])&&isDigit(d[i+12])&&d[i+13]==':'&&isDigit(d[i+14])&&
         isDigit(d[i+15])&&d[i+16]==':'&&isDigit(d[i+17])&&isDigit(d[i+18])&&d[i+19]=='.'&&
         isDigit(d[i+20])&&isDigit(d[i+21])&&isDigit(d[i+22])&&d[i+23]=='Z'&&d[i+24]==' '))
        return fail();
    i+=25;
    // host [a-z]+-\d+
    { size_t s=i; while(i<n && d[i]>='a'&&d[i]<='z') i++; if(i==s) return fail(); }
    if(i>=n||d[i]!='-') return fail(); i++;
    { size_t s=i; while(i<n && isDigit(d[i])) i++; if(i==s) return fail(); }
    if(i>=n||d[i]!=' ') return fail(); i++;
    // method
    if(i>=n) return fail();
    switch(d[i]){
        case 'G':
            if(i+4<=n&&d[i+1]=='E'&&d[i+2]=='T'&&d[i+3]==' ') i+=4; else return fail(); break;
        case 'D':
            if(i+7<=n&&std::memcmp(d+i,"DELETE ",7)==0) i+=7; else return fail(); break;
        case 'P':
            if(i+1>=n) return fail();
            if(d[i+1]=='O'){ if(i+5<=n&&d[i+2]=='S'&&d[i+3]=='T'&&d[i+4]==' ') i+=5; else return fail(); }
            else if(d[i+1]=='U'){ if(i+4<=n&&d[i+2]=='T'&&d[i+3]==' ') i+=4; else return fail(); }
            else if(d[i+1]=='A'){ if(i+6<=n&&std::memcmp(d+i,"PATCH ",6)==0) i+=6; else return fail(); }
            else return fail();
            break;
        default: return fail();
    }
    // path
    if(i>=n||d[i]!='/') return fail();
    p.pathS=i; i++;
    while(i<n && pathCharTab[d[i]]) i++;
    p.pathE=i;
    // query
    if(i<n && d[i]=='?'){ i++; while(i<n && d[i]!=' ' && d[i]!='\n') i++; }
    if(i>=n||d[i]!=' ') return fail(); i++;
    // status \d{3}
    if(i+3>n||!isDigit(d[i])||!isDigit(d[i+1])||!isDigit(d[i+2])) return fail();
    p.statusDigit=d[i]-'0'; i+=3;
    if(i>=n||d[i]!=' ') return fail(); i++;
    // bytes \d+B
    { size_t s=i; while(i<n && isDigit(d[i])) i++; if(i==s) return fail(); }
    if(i>=n||d[i]!='B') return fail(); i++;
    if(i>=n||d[i]!=' ') return fail(); i++;
    // latency \d+\.\dms
    { size_t s=i; unsigned long long v=0; while(i<n && isDigit(d[i])){ v=v*10+(unsigned)(d[i]-'0'); i++; } if(i==s) return fail();
      if(i>=n||d[i]!='.') return fail(); i++;
      if(i>=n||!isDigit(d[i])) return fail(); v=v*10+(unsigned)(d[i]-'0'); i++;
      p.latency=(int)(uint32_t)v; }
    if(i+2>n||d[i]!='m'||d[i+1]!='s') return fail(); i+=2;
    if(i>=n||d[i]!=' ') return fail(); i++;
    // quoted UA
    if(i>=n||d[i]!='"') return fail(); i++;
    while(i<n && d[i]!='"' && d[i]!='\n') i++;
    if(i>=n||d[i]!='"') return fail(); i++;
    if(i<n && d[i]!='\n') return fail();
    p.i=i; return true;
}

static inline uint64_t hashBytes(const unsigned char* s,size_t len){
    uint64_t h=(uint64_t)len*0x9E3779B97F4A7C15ULL;
    size_t k=0;
    while(k+8<=len){
        uint64_t chunk; std::memcpy(&chunk,s+k,8); k+=8;
        h^=chunk; h*=0xBF58476D1CE4E5B9ULL; h^=h>>27;
    }
    if(k<len){
        uint64_t chunk=0;
        for(size_t t=0;k<len;k++,t+=8) chunk |= (uint64_t)s[k]<<t;
        h^=chunk; h*=0xBF58476D1CE4E5B9ULL; h^=h>>27;
    }
    h^=h>>33; h*=0xff51afd7ed558ccdULL; h^=h>>33;
    return h;
}

int main(int argc,char** argv){
    _setmode(_fileno(stdout), _O_BINARY);
    for(int c=0;c<256;c++) pathCharTab[c]= ( (c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='/'||c=='-' );
    if(argc<2) return 1;
    FILE* f=std::fopen(argv[1],"rb");
    if(!f) return 1;
    std::fseek(f,0,SEEK_END);
    long long szll=_ftelli64(f);
    std::fseek(f,0,SEEK_SET);
    size_t sz = szll>0 ? (size_t)szll : 0;
    std::vector<unsigned char> data(sz);
    if(sz){ size_t rd=std::fread(data.data(),1,sz,f); data.resize(rd); sz=rd; }
    std::fclose(f);

    Parser p; p.d=data.data(); p.n=sz;

    long long lines=0, malformed=0;
    long long statusCnt[10]={0};

    // template store
    std::vector<char> arena; arena.reserve(1<<16);
    std::vector<uint32_t> offs; std::vector<uint32_t> lens; std::vector<int> counts; std::vector<uint64_t> hashes;
    size_t tableSize=1024; std::vector<int> table(tableSize,-1); size_t mask=tableSize-1;

    std::vector<int> lats; std::vector<int> ids;
    size_t est = sz/100+16; lats.reserve(est); ids.reserve(est);

    std::vector<unsigned char> scratch; scratch.resize(256);

    auto rehash=[&](size_t newSize){
        std::vector<int> nt(newSize,-1); size_t nm=newSize-1;
        for(size_t id=0;id<hashes.size();id++){ size_t h=(size_t)hashes[id]&nm; while(nt[h]!=-1) h=(h+1)&nm; nt[h]=(int)id; }
        table=std::move(nt); tableSize=newSize; mask=nm;
    };

    const unsigned char* d=data.data();
    while(p.i<p.n){
        lines++;
        if(parseLine(p)){
            statusCnt[p.statusDigit]++;
            // build template in scratch
            size_t pathLen=p.pathE-p.pathS;
            size_t need=pathLen*3+8;
            if(scratch.size()<need) scratch.resize(need);
            size_t sl=0; size_t j=p.pathS;
            while(true){
                size_t segS=j; bool allDig=true;
                while(j<p.pathE && d[j]!='/'){ if(!isDigit(d[j])) allDig=false; j++; }
                if(j>segS && allDig){ std::memcpy(scratch.data()+sl,"{id}",4); sl+=4; }
                else if(j>segS){ std::memcpy(scratch.data()+sl,d+segS,j-segS); sl+=j-segS; }
                if(j>=p.pathE) break;
                scratch[sl++]='/'; j++;
            }
            uint64_t h=hashBytes(scratch.data(),sl);
            size_t hidx=(size_t)h & mask; int id=-1;
            while(true){
                int t=table[hidx];
                if(t==-1) break;
                if(hashes[(size_t)t]==h && lens[(size_t)t]==sl && std::memcmp(arena.data()+offs[(size_t)t],scratch.data(),sl)==0){ id=t; break; }
                hidx=(hidx+1)&mask;
            }
            if(id==-1){
                if((counts.size()+1)*10 > tableSize*7){
                    rehash(tableSize*2);
                    hidx=(size_t)h & mask; while(table[hidx]!=-1) hidx=(hidx+1)&mask;
                }
                id=(int)counts.size();
                table[hidx]=id;
                offs.push_back((uint32_t)arena.size());
                arena.insert(arena.end(),(char*)scratch.data(),(char*)scratch.data()+sl);
                lens.push_back((uint32_t)sl); counts.push_back(0); hashes.push_back(h);
            }
            counts[(size_t)id]++;
            lats.push_back(p.latency); ids.push_back(id);
            if(p.i<p.n) p.i++; // skip '\n'
        }else{
            malformed++;
            const void* nl=std::memchr(d+p.i,'\n',p.n-p.i);
            p.i = nl ? (size_t)((const unsigned char*)nl-d)+1 : p.n;
        }
    }
    data.clear(); data.shrink_to_fit();

    int T=(int)counts.size();
    std::vector<int> order((size_t)T);
    for(int k=0;k<T;k++) order[(size_t)k]=k;
    std::sort(order.begin(),order.end(),[&](int a,int b){
        if(counts[(size_t)a]!=counts[(size_t)b]) return counts[(size_t)a]>counts[(size_t)b];
        uint32_t la=lens[(size_t)a],lb=lens[(size_t)b]; uint32_t m=la<lb?la:lb;
        int c=m?std::memcmp(arena.data()+offs[(size_t)a],arena.data()+offs[(size_t)b],m):0;
        if(c!=0) return c<0;
        return la<lb;
    });
    int K=T<10?T:10;
    std::vector<std::vector<int>> tops((size_t)K);
    std::vector<int> slot((size_t)T,-1);
    for(int k=0;k<K;k++){ slot[(size_t)order[(size_t)k]]=k; tops[(size_t)k].resize((size_t)counts[(size_t)order[(size_t)k]]); }
    std::vector<int> fill((size_t)K,0);
    for(size_t q=0;q<ids.size();q++){ int s=slot[(size_t)ids[q]]; if(s>=0) tops[(size_t)s][(size_t)fill[(size_t)s]++]=lats[q]; }
    for(int k=0;k<K;k++) std::sort(tops[(size_t)k].begin(),tops[(size_t)k].end());

    std::string out; out.reserve(1024);
    out+="lines "; out+=std::to_string(lines); out+='\n';
    out+="malformed "; out+=std::to_string(malformed); out+='\n';
    for(int dig=0;dig<10;dig++) if(statusCnt[dig]>0){
        out+="status "; out+=(char)('0'+dig); out+="xx "; out+=std::to_string(statusCnt[dig]); out+='\n';
    }
    auto fmtLat=[&](int v){ out+=std::to_string(v/10); out+='.'; out+=(char)('0'+(v%10)); };
    for(int k=0;k<K;k++){
        int id=order[(size_t)k]; auto &vec=tops[(size_t)k]; long long nn=(long long)vec.size();
        int p50=vec[(size_t)((50*nn+99)/100-1)];
        int p95=vec[(size_t)((95*nn+99)/100-1)];
        int mx=vec[(size_t)(nn-1)];
        out+="path "; out.append(arena.data()+offs[(size_t)id],lens[(size_t)id]);
        out+=' '; out+=std::to_string(counts[(size_t)id]); out+=' ';
        fmtLat(p50); out+=' '; fmtLat(p95); out+=' '; fmtLat(mx); out+='\n';
    }
    std::fwrite(out.data(),1,out.size(),stdout);
    return 0;
}
