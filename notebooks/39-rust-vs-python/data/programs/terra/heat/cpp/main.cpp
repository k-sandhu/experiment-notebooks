#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int main(int argc, char** argv) {
    if (argc < 2) return 1;
    ifstream in(argv[1]);
    int h,w,steps; in >> h >> w >> steps;
    int stride=w+2, size=(h+2)*stride;
    vector<int> a(size),b(size),coeff(size),cells;
    string row;
    for(int r=0;r<h;r++) {
        in >> row;
        for(int c=0;c<w;c++) {
            int p=(r+1)*stride+c+1; char ch=row[c];
            if(ch=='.') { cells.push_back(p); coeff[p]=4; }
            else if(ch!='#') a[p]=b[p]=(ch-'0')*1000;
            if(ch!='#') coeff[p] |= 16;
        }
    }
    for(int p:cells) coeff[p]=8-((coeff[p-stride]!=0)+(coeff[p+stride]!=0)+(coeff[p-1]!=0)+(coeff[p+1]!=0));
    for(int s=0;s<steps;s++) {
        for(int p:cells) b[p]=(coeff[p]*a[p]+a[p-stride]+a[p+stride]+a[p-1]+a[p+1])>>3;
        a.swap(b);
    }
    int best=-1,pos=0; int64_t sum=0,checksum=0;
    for(int p:cells) {
        int v=a[p],r=p/stride-1,c=p%stride-1;
        sum+=v; checksum+=int64_t(v)*(int64_t(r)*w+c+1);
        if(v>best) { best=v; pos=p; }
    }
    cout<<"sum "<<sum<<"\nmax "<<best<<' '<<pos/stride-1<<' '<<pos%stride-1<<"\nchecksum "<<checksum<<'\n';
}
