using System;
using System.IO;
using System.Globalization;
class Program {
    static void Main(string[] args) {
        string data=File.ReadAllText(args[0]); int pos=0;
        double Next(){while(pos<data.Length && char.IsWhiteSpace(data[pos]))pos++; int start=pos;while(pos<data.Length && !char.IsWhiteSpace(data[pos]))pos++;return double.Parse(data.AsSpan(start,pos-start),CultureInfo.InvariantCulture);}
        int n=(int)Next(), steps=(int)Next(); double dt=Next(), P=Next();
        double[] x=new double[n],v=new double[n],m=new double[n],k=new double[n],r=new double[n],c=new double[n],f=new double[n];
        for(int i=0;i<n;i++){x[i]=Next();v[i]=Next();m[i]=Next();k[i]=Next();r[i]=Next();c[i]=Next();}
        for(int t=0;t<steps;t++){
            for(int i=0;i<n-1;i++)f[i]=k[i]*((x[i+1]-x[i])-r[i]);
            f[n-1]=k[n-1]*(((x[0]+P)-x[n-1])-r[n-1]);
            double prev=f[n-1];
            for(int i=0;i<n;i++){double force=(f[i]-prev)-(c[i]*v[i]);prev=f[i];v[i]=v[i]+dt*(force/m[i]);x[i]=x[i]+dt*v[i];}
        }
        double K=0,U=0,X=0,best=-1;int j=0;
        for(int i=0;i<n;i++){K+=((0.5*m[i])*v[i])*v[i];X+=x[i];double a=Math.Abs(v[i]);if(a>best){best=a;j=i;}double s=(i==n-1?((x[0]+P)-x[i]):(x[i+1]-x[i]))-r[i];U+=((0.5*k[i])*s)*s;}
        Console.WriteLine(FormattableString.Invariant($"kinetic {K:G17}\npotential {U:G17}\nposition {X:G17}\nfastest {j}"));
    }
}
