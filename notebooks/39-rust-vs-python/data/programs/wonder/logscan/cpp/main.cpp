#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>
#include <io.h>
#include <fcntl.h>

struct Entry {
    std::string key;
    std::vector<int> lats;
    int mx = 0;
};

static inline bool isDig(unsigned char c){ return (unsigned)(c-'0')<=9u; }
static inline bool isLow(unsigned char c){ return (unsigned)(c-'a')<=25u; }
static inline bool isPathCh(unsigned char c){
    return (unsigned)(c-'a')<=25u || (unsigned)(c-'A')<=25u || (unsigned)(c-'0')<=9u || c=='_' || c=='/' || c=='-';
}

int main(int argc, char** argv){
    _setmode(_fileno(stdout), _O_BINARY);
    if(argc<2) return 1;
    FILE* f = fopen(argv[1],"rb");
    if(!f) return 1;
    // read all
    size_t cap = 1<<20, len=0;
    char* buf = (char*)malloc(cap);
    if(!buf) return 1;
    for(;;){
        if(len==cap){ cap*=2; buf=(char*)realloc(buf,cap); if(!buf) return 1; }
        size_t r = fread(buf+len,1,cap-len,f);
        if(r==0) break;
        len+=r;
    }
    fclose(f);

    long long totalLines=0, malformed=0;
    long long statusCnt[10]={0};

    // custom open addressing hash table: slots store entry index+1
    size_t tcap = 1024;
    // grow threshold handled dynamically
    std::vector<int> slots(tcap,0);
    std::vector<Entry> entries;
    entries.reserve(1024);
    size_t usedSlots=0;

    // template scratch
    std::vector<char> tmp;
    tmp.resize(256);

    size_t pos=0;
    const unsigned char* data=(const unsigned char*)buf;
    while(pos<len){
        size_t lineStart=pos;
        const void* nl = memchr(buf+pos,'\n',len-pos);
        size_t lineEnd;
        if(nl){ lineEnd=(size_t)((const char*)nl-buf); pos=lineEnd+1; }
        else { lineEnd=len; pos=len; }
        totalLines++;
        const unsigned char* s=data+lineStart;
        const unsigned char* e=data+lineEnd;
        size_t n=(size_t)(e-s);

        bool ok=true;
        int statusClass=0;
        int latency=0;
        size_t pathStart=0, pathEnd=0;

        // parse
        if(n<25) ok=false;
        else {
            // timestamp fixed
            if(!(isDig(s[0])&&isDig(s[1])&&isDig(s[2])&&isDig(s[3])&&s[4]=='-'&&isDig(s[5])&&isDig(s[6])&&s[7]=='-'&&isDig(s[8])&&isDig(s[9])&&s[10]=='T'&&isDig(s[11])&&isDig(s[12])&&s[13]==':'&&isDig(s[14])&&isDig(s[15])&&s[16]==':'&&isDig(s[17])&&isDig(s[18])&&s[19]=='.'&&isDig(s[20])&&isDig(s[21])&&isDig(s[22])&&s[23]=='Z'&&s[24]==' ')) ok=false;
            else {
                size_t i=25;
                // server [a-z]+ - \d+ space
                size_t st=i;
                while(i<n && isLow(s[i])) i++;
                if(i==st) ok=false;
                else {
                    if(i>=n || s[i]!='-') ok=false;
                    else {
                        i++; st=i;
                        while(i<n && isDig(s[i])) i++;
                        if(i==st) ok=false;
                        else if(i>=n || s[i]!=' ') ok=false;
                        else {
                            i++;
                            // method
                            size_t rem=n-i;
                            if(rem>=4 && memcmp(s+i,"GET ",4)==0) i+=4;
                            else if(rem>=4 && memcmp(s+i,"PUT ",4)==0) i+=4;
                            else if(rem>=5 && memcmp(s+i,"POST ",5)==0) i+=5;
                            else if(rem>=6 && memcmp(s+i,"PATCH ",6)==0) i+=6;
                            else if(rem>=7 && memcmp(s+i,"DELETE ",7)==0) i+=7;
                            else ok=false;
                            if(ok){
                                // path
                                if(i>=n || s[i]!='/') ok=false;
                                else {
                                    pathStart=i;
                                    while(i<n && s[i]!=' ' && s[i]!='?'){
                                        if(!isPathCh(s[i])){ ok=false; break; }
                                        i++;
                                    }
                                    if(ok){
                                        pathEnd=i;
                                        if(i<n && s[i]=='?'){
                                            i++;
                                            while(i<n && s[i]!=' ') i++;
                                        }
                                        if(i>=n || s[i]!=' ') ok=false;
                                        else {
                                            i++;
                                            // status 3 digits space
                                            if(i+4>n || !isDig(s[i]) || !isDig(s[i+1]) || !isDig(s[i+2]) || s[i+3]!=' ') ok=false;
                                            else {
                                                statusClass=s[i]-'0';
                                                i+=4;
                                                // bytes \d+ B space
                                                st=i;
                                                while(i<n && isDig(s[i])) i++;
                                                if(i==st || i>=n || s[i]!='B') ok=false;
                                                else {
                                                    i++;
                                                    if(i>=n || s[i]!=' ') ok=false;
                                                    else {
                                                        i++;
                                                        // latency \d+ . \d ms space " ... "
                                                        st=i;
                                                        long long v=0;
                                                        while(i<n && isDig(s[i])){ v=v*10+(s[i]-'0'); i++; }
                                                        if(i==st || i>=n || s[i]!='.') ok=false;
                                                        else {
                                                            i++;
                                                            if(i>=n || !isDig(s[i])) ok=false;
                                                            else {
                                                                v=v*10+(s[i]-'0'); i++;
                                                                latency=(int)v;
                                                                if(i+2>n || s[i]!='m' || s[i+1]!='s') ok=false;
                                                                else {
                                                                    i+=2;
                                                                    if(i>=n || s[i]!=' ') ok=false;
                                                                    else {
                                                                        i++;
                                                                        if(i>=n || s[i]!='"') ok=false;
                                                                        else {
                                                                            // last char must be " and no " inside
                                                                            if(n<1 || s[n-1]!='"' || i+1>=n) ok=false;
                                                                            else {
                                                                                // search quote in (i+1 .. n-2)
                                                                                if(n-1 > i+1){
                                                                                    const void* q = memchr(s+i+1,'"', (n-1)-(i+1));
                                                                                    if(q) ok=false;
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        if(!ok){ malformed++; continue; }
        statusCnt[statusClass]++;

        // build template into tmp
        size_t plen=pathEnd-pathStart;
        if(tmp.size()<plen+16) tmp.resize(plen+64);
        size_t tlen=0;
        size_t p=pathStart;
        // segments
        while(true){
            size_t segStart=p;
            while(p<pathEnd && s[p]!='/') p++;
            size_t segLen=p-segStart;
            bool allDig = segLen>0;
            for(size_t k=segStart;k<p;k++) if(!isDig(s[k])){ allDig=false; break; }
            if(tlen + (allDig?4:segLen) + 1 > tmp.size()) tmp.resize((tlen+(allDig?4:segLen)+1)*2+32);
            if(allDig){ memcpy(tmp.data()+tlen,"{id}",4); tlen+=4; }
            else if(segLen){ memcpy(tmp.data()+tlen, s+segStart, segLen); tlen+=segLen; }
            if(p>=pathEnd) break;
            tmp[tlen++]='/';
            p++; // skip '/'
        }

        // hash FNV-1a 64
        uint64_t h=1469598103934665603ULL;
        for(size_t k=0;k<tlen;k++){ h ^= (unsigned char)tmp[k]; h *= 1099511628211ULL; }
        // lookup / insert
        if((usedSlots+1)*10 > tcap*7){
            // grow
            size_t ncap=tcap*2;
            std::vector<int> nslots(ncap,0);
            for(size_t ei=0; ei<entries.size(); ei++){
                uint64_t hh=1469598103934665603ULL;
                for(char ch: entries[ei].key){ hh ^= (unsigned char)ch; hh *= 1099511628211ULL; }
                size_t mask=ncap-1;
                size_t idx=(size_t)(hh & mask);
                while(nslots[idx]!=0) idx=(idx+1)&mask;
                nslots[idx]=(int)(ei+1);
            }
            slots.swap(nslots); tcap=ncap;
        }
        {
            size_t mask=tcap-1;
            size_t idx=(size_t)(h & mask);
            int found=-1;
            while(true){
                int v=slots[idx];
                if(v==0) break;
                Entry& en=entries[v-1];
                if(en.key.size()==tlen && memcmp(en.key.data(), tmp.data(), tlen)==0){ found=v-1; break; }
                idx=(idx+1)&mask;
            }
            if(found>=0){
                Entry& en=entries[found];
                en.lats.push_back(latency);
                if(latency>en.mx) en.mx=latency;
            } else {
                Entry en;
                en.key.assign(tmp.data(), tlen);
                en.lats.push_back(latency);
                en.mx=latency;
                entries.push_back(std::move(en));
                slots[idx]=(int)entries.size(); // index+1
                usedSlots++;
            }
        }
    }

    // sort entries indices
    std::vector<int> order(entries.size());
    for(size_t i=0;i<order.size();i++) order[i]=(int)i;
    std::sort(order.begin(), order.end(), [&](int a, int b){
        size_t ca=entries[a].lats.size(), cb=entries[b].lats.size();
        if(ca!=cb) return ca>cb;
        return entries[a].key < entries[b].key;
    });
    size_t top = order.size()<10?order.size():10;

    std::string out;
    out.reserve(4096);
    char numbuf[64];
    auto appendLL=[&](long long v){ int l=snprintf(numbuf,sizeof(numbuf),"%lld",v); out.append(numbuf,l); };
    auto appendLat=[&](int v){ int l=snprintf(numbuf,sizeof(numbuf),"%d.%d", v/10, v%10); out.append(numbuf,l); };
    out += "lines "; appendLL(totalLines); out+='\n';
    out += "malformed "; appendLL(malformed); out+='\n';
    for(int c=0;c<10;c++) if(statusCnt[c]>0){
        out += "status "; out += (char)('0'+c); out += "xx "; appendLL(statusCnt[c]); out+='\n';
    }
    for(size_t ti=0; ti<top; ti++){
        Entry& en=entries[order[ti]];
        auto& vec=en.lats;
        std::sort(vec.begin(), vec.end());
        long long nn=(long long)vec.size();
        long long r50=(50*nn+99)/100;
        long long r95=(95*nn+99)/100;
        int p50=vec[(size_t)(r50-1)];
        int p95=vec[(size_t)(r95-1)];
        out += "path "; out += en.key; out+=' '; appendLL(nn); out+=' ';
        appendLat(p50); out+=' '; appendLat(p95); out+=' '; appendLat(en.mx); out+='\n';
    }
    fwrite(out.data(),1,out.size(),stdout);
    free(buf);
    return 0;
}
