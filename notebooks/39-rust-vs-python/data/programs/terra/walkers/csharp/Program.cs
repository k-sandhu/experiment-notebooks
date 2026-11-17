using System;
using System.IO;
using System.Threading;
class Result { public long Spread, Bumps, Returns, Id, Distance = -1; }
class Program {
 static void Main(string[] args) {
  var f=File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
  long n=long.Parse(f[0]), steps=long.Parse(f[1]), b=long.Parse(f[2]); ulong seed=ulong.Parse(f[3]); int workers=int.Parse(args[1]);
  var results=new Result[workers]; var threads=new Thread[workers];
  for(int k=0;k<workers;k++) { int i=k; results[i]=new Result(); threads[i]=new Thread(() => {
   var a=results[i]; long start=n/workers*i+Math.Min((long)i,n%workers), end=n/workers*(i+1)+Math.Min((long)i+1,n%workers);
   for(long j=start;j<end;j++) { ulong state=unchecked(seed+(ulong)j); long x=0,y=0;
    for(long s=0;s<steps;s++) { ulong z=unchecked(state+=0x9E3779B97F4A7C15UL); z=unchecked((z^(z>>30))*0xBF58476D1CE4E5B9UL); z=unchecked((z^(z>>27))*0x94D049BB133111EBUL);
     switch(z>>62) { case 0: if(x<b) x++; else {a.Bumps++;continue;} break; case 1: if(x>-b) x--; else {a.Bumps++;continue;} break; case 2: if(y<b) y++; else {a.Bumps++;continue;} break; default: if(y>-b) y--; else {a.Bumps++;continue;} break; }
     if(x==0 && y==0) a.Returns++;
    }
    a.Spread+=x*x+y*y; long d=Math.Abs(x)+Math.Abs(y); if(d>a.Distance){a.Distance=d;a.Id=j;}
   }
  }); threads[i].Start(); }
  var all=new Result(); for(int i=0;i<workers;i++){threads[i].Join(); var a=results[i];all.Spread+=a.Spread;all.Bumps+=a.Bumps;all.Returns+=a.Returns; if(a.Distance>all.Distance || (a.Distance==all.Distance && a.Id<all.Id)){all.Distance=a.Distance;all.Id=a.Id;}}
  Console.Write($"spread {all.Spread}\nbumps {all.Bumps}\nreturns {all.Returns}\nfarthest {all.Id} {all.Distance}\n");
 }
}
