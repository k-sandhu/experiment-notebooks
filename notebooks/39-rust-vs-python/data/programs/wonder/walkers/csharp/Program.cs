using System;
using System.IO;
using System.Threading;

class Program
{
    static long Jg, Lg;
    static int Bg;
    static ulong SEEDg;

    class Partial { public long spread, bumps, returns; public long bestD = -1, bestJ; }

    static void RunChunk(long start, long end, Partial output)
    {
        int B = Bg; long L = Lg;
        long spread=0, bumps=0, returns=0;
        long bestD=-1, bestJ=start;
        for (long j=start;j<end;j++)
        {
            ulong state = SEEDg + (ulong)j;
            int x=0,y=0;
            long b=0,r=0;
            for (long i=0;i<L;i++)
            {
                state += 0x9E3779B97F4A7C15UL;
                ulong z = state;
                z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
                z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
                ulong rr = z ^ (z >> 31);
                int d = (int)(rr >> 62);
                int sign = 1 - ((d & 1) << 1);
                int axis = d >> 1;
                int nx = x + sign * (1 - axis);
                int ny = y + sign * axis;
                bool outb = (nx > B) | (nx < -B) | (ny > B) | (ny < -B);
                if (outb) b++; else { x=nx; y=ny; if (x==0 && y==0) r++; }
            }
            bumps+=b; returns+=r;
            spread += (long)x*x + (long)y*y;
            long dist = Math.Abs((long)x)+Math.Abs((long)y);
            if (dist>bestD){bestD=dist;bestJ=j;}
        }
        output.spread=spread; output.bumps=bumps; output.returns=returns; output.bestD=bestD; output.bestJ=bestJ;
    }

    static void Main(string[] args)
    {
        int workers = 1;
        if (args.Length>=2) int.TryParse(args[1], out workers);
        if (workers<1) workers=1;
        if (workers>32) workers=32;
        byte[] data = File.ReadAllBytes(args[0]);
        long[] vals = new long[4];
        int idx=0,i=0;
        while(idx<4 && i<data.Length)
        {
            while(i<data.Length && (data[i]==32||data[i]==10||data[i]==13||data[i]==9)) i++;
            if(i>=data.Length) break;
            bool neg=false; if(data[i]==45){neg=true;i++;}
            // parse unsigned for seed (idx==3) using ulong wrap, else long
            if(idx==3)
            {
                ulong v=0; while(i<data.Length && data[i]>=48 && data[i]<=57){v=v*10+(ulong)(data[i]-48); i++;}
                SEEDg=v; idx++; break;
            } else {
                long v=0; while(i<data.Length && data[i]>=48 && data[i]<=57){v=v*10+(data[i]-48); i++;}
                vals[idx++]= neg?-v:v;
            }
        }
        Jg=vals[0]; Lg=vals[1]; Bg=(int)vals[2];
        if (Jg<=0){ Console.Write("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n"); return; }
        if (workers>Jg) workers=(int)Jg;
        Partial[] parts=new Partial[workers];
        for(int w=0;w<workers;w++) parts[w]=new Partial();
        if(workers==1){ RunChunk(0,Jg,parts[0]); }
        else {
            Thread[] th=new Thread[workers-1];
            long bse=Jg/workers, rem=Jg%workers;
            long s=0; int ti=0;
            for(int w=0;w<workers;w++){
                long cnt=bse+(w<rem?1:0); long st=s, en=s+cnt; s=en; int wi=w;
                if(w==workers-1){ RunChunk(st,en,parts[wi]); }
                else { var t=new Thread(()=>RunChunk(st,en,parts[wi])); th[ti++]=t; t.Start(); }
            }
            foreach(var t in th) if(t!=null) t.Join();
        }
        long spread=0,bumps=0,returns=0,bestD=-1,bestJ=0;
        foreach(var p in parts){ spread+=p.spread; bumps+=p.bumps; returns+=p.returns; if(p.bestD>bestD){bestD=p.bestD;bestJ=p.bestJ;} }
        if(bestD<0) bestD=0;
        Console.Write($"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {bestJ} {bestD}\n");
    }
}
