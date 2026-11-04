#include <cstdio>
#include <cstdlib>
#include <vector>
#include <fstream>
#include <iterator>
#include <cmath>
using namespace std;
int main(int argc, char** argv) {
    ifstream in(argv[1], ios::binary);
    string data((istreambuf_iterator<char>(in)), {}); const char* p=data.c_str(); char* e;
    auto num=[&](){ double a=strtod(p,&e); p=e; return a; };
    int n=(int)num(), steps=(int)num(); double dt=num(), P=num();
    vector<double> x(n),v(n),m(n),k(n),r(n),c(n),f(n);
    for(int i=0;i<n;i++){x[i]=num();v[i]=num();m[i]=num();k[i]=num();r[i]=num();c[i]=num();}
    for(int t=0;t<steps;t++){
        for(int i=0;i<n-1;i++) f[i]=k[i]*((x[i+1]-x[i])-r[i]);
        f[n-1]=k[n-1]*(((x[0]+P)-x[n-1])-r[n-1]);
        double prev=f[n-1];
        for(int i=0;i<n;i++){double force=(f[i]-prev)-(c[i]*v[i]); prev=f[i]; v[i]=v[i]+dt*(force/m[i]); x[i]=x[i]+dt*v[i];}
    }
    double K=0,U=0,X=0,best=-1; int j=0;
    for(int i=0;i<n;i++){K+=((0.5*m[i])*v[i])*v[i]; X+=x[i]; double a=fabs(v[i]); if(a>best){best=a;j=i;} double s=(i==n-1?((x[0]+P)-x[i]):(x[i+1]-x[i]))-r[i]; U+=((0.5*k[i])*s)*s;}
    printf("kinetic %.17g\npotential %.17g\nposition %.17g\nfastest %d\n",K,U,X,j);
}
