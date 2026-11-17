#include <cstdint>
#include <fstream>
#include <iostream>
#include <thread>
#include <vector>
#include <cstdlib>
using namespace std;
struct Result { int64_t spread=0, bumps=0, returns=0, id=0, distance=-1; };
int main(int argc, char** argv) {
    ifstream in(argv[1]); int64_t n, steps, b; uint64_t seed; in >> n >> steps >> b >> seed;
    int workers=atoi(argv[2]); vector<Result> results(workers); vector<thread> threads;
    for(int k=0;k<workers;k++) threads.emplace_back([&,k] {
        auto &a=results[k]; int64_t start=(n/workers)*k+min<int64_t>(k,n%workers), end=(n/workers)*(k+1)+min<int64_t>(k+1,n%workers);
        for(int64_t j=start;j<end;j++) {
            uint64_t state=seed+uint64_t(j); int64_t x=0,y=0;
            for(int64_t s=0;s<steps;s++) {
                uint64_t z=(state+=UINT64_C(0x9E3779B97F4A7C15));
                z=(z^(z>>30))*UINT64_C(0xBF58476D1CE4E5B9); z=(z^(z>>27))*UINT64_C(0x94D049BB133111EB);
                switch(z>>62) {
                  case 0: if(x<b) ++x; else {++a.bumps; continue;} break;
                  case 1: if(x>-b) --x; else {++a.bumps; continue;} break;
                  case 2: if(y<b) ++y; else {++a.bumps; continue;} break;
                  default: if(y>-b) --y; else {++a.bumps; continue;}
                }
                a.returns += (x==0 && y==0);
            }
            a.spread+=x*x+y*y; int64_t d=abs(x)+abs(y); if(d>a.distance) {a.distance=d; a.id=j;}
        }
    });
    for(auto &t:threads) t.join(); Result all;
    for(auto &a:results) {all.spread+=a.spread; all.bumps+=a.bumps; all.returns+=a.returns; if(a.distance>all.distance || (a.distance==all.distance && a.id<all.id)) {all.distance=a.distance; all.id=a.id;}}
    cout<<"spread "<<all.spread<<"\nbumps "<<all.bumps<<"\nreturns "<<all.returns<<"\nfarthest "<<all.id<<' '<<all.distance<<'\n';
}
