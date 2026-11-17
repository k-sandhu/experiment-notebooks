using System;
using System.IO;
class Program {
    static void Main(string[] args) {
        byte[] data=File.ReadAllBytes(args[0]); int at=0;
        int Number() { while(data[at]<=32) at++; int n=0; while(at<data.Length && data[at]>32) n=n*10+data[at++]-'0'; return n; }
        int h=Number(),w=Number(),steps=Number(),stride=w+2,size=(h+2)*stride;
        int[] a=new int[size],b=new int[size],coeff=new int[size],cells=new int[h*w]; int count=0;
        for(int r=0;r<h;r++) {
            while(data[at]<=32) at++;
            for(int c=0;c<w;c++) {
                int ch=data[at++],p=(r+1)*stride+c+1;
                if(ch=='.') { cells[count++]=p; coeff[p]=4; }
                else if(ch!='#') a[p]=b[p]=(ch-'0')*1000;
                if(ch!='#') coeff[p] |= 16;
            }
        }
        for(int i=0;i<count;i++) { int p=cells[i]; coeff[p]=8-((coeff[p-stride]!=0?1:0)+(coeff[p+stride]!=0?1:0)+(coeff[p-1]!=0?1:0)+(coeff[p+1]!=0?1:0)); }
        for(int s=0;s<steps;s++) {
            for(int i=0;i<count;i++) { int p=cells[i]; b[p]=(coeff[p]*a[p]+a[p-stride]+a[p+stride]+a[p-1]+a[p+1])>>3; }
            (a,b)=(b,a);
        }
        long sum=0,checksum=0; int best=-1,pos=0;
        for(int i=0;i<count;i++) { int p=cells[i],v=a[p],r=p/stride-1,c=p%stride-1; sum+=v; checksum+=(long)v*((long)r*w+c+1); if(v>best) { best=v; pos=p; } }
        Console.Write($"sum {sum}\nmax {best} {pos/stride-1} {pos%stride-1}\nchecksum {checksum}\n");
    }
}
