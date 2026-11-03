import java.nio.file.*;
public class Main {
    static class Result { long spread, bumps, returns, id, distance=-1; }
    public static void main(String[] args) throws Exception {
        String[] f=Files.readString(Path.of(args[0])).trim().split("\\s+");
        long n=Long.parseLong(f[0]), steps=Long.parseLong(f[1]), b=Long.parseLong(f[2]), seed=Long.parseUnsignedLong(f[3]);
        int workers=Integer.parseInt(args[1]); Result[] r=new Result[workers]; Thread[] ts=new Thread[workers];
        for(int k=0;k<workers;k++) { final int i=k; r[k]=new Result(); ts[k]=new Thread(() -> {
            Result a=r[i]; long start=(n/workers)*i+Math.min((long)i,n%workers), end=(n/workers)*(i+1)+Math.min((long)i+1,n%workers);
            for(long j=start;j<end;j++) { long state=seed+j,x=0,y=0;
                for(long s=0;s<steps;s++) { long z=(state+=0x9E3779B97F4A7C15L); z=(z^(z>>>30))*0xBF58476D1CE4E5B9L; z=(z^(z>>>27))*0x94D049BB133111EBL;
                    switch((int)(z>>>62)) {
                        case 0: if(x<b) x++; else {a.bumps++; continue;} break;
                        case 1: if(x>-b) x--; else {a.bumps++; continue;} break;
                        case 2: if(y<b) y++; else {a.bumps++; continue;} break;
                        default: if(y>-b) y--; else {a.bumps++; continue;}
                    }
                    if(x==0 && y==0) a.returns++;
                }
                a.spread+=x*x+y*y; long d=Math.abs(x)+Math.abs(y); if(d>a.distance) {a.distance=d;a.id=j;}
            }
        }); ts[k].start(); }
        Result a=new Result(); for(int k=0;k<workers;k++) { ts[k].join(); Result v=r[k]; a.spread+=v.spread;a.bumps+=v.bumps;a.returns+=v.returns; if(v.distance>a.distance || (v.distance==a.distance && v.id<a.id)) {a.distance=v.distance;a.id=v.id;} }
        System.out.print("spread "+a.spread+"\nbumps "+a.bumps+"\nreturns "+a.returns+"\nfarthest "+a.id+" "+a.distance+"\n");
    }
}
