import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static long J, L;
    static int B;
    static long SEED;

    static class Partial {
        long spread, bumps, returns;
        long bestD = -1, bestJ;
    }

    static void runChunk(long start, long end, Partial out) {
        final int bnd = B;
        final long steps = L;
        long spread = 0, bumps = 0, returns = 0;
        long bestD = -1, bestJ = start;
        for (long j = start; j < end; j++) {
            long state = SEED + j;
            int x = 0, y = 0;
            long b = 0, r = 0;
            for (long i = 0; i < steps; i++) {
                state += 0x9E3779B97F4A7C15L;
                long z = state;
                z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
                z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
                long rr = z ^ (z >>> 31);
                int d = (int)(rr >>> 62);
                int sign = 1 - ((d & 1) << 1);
                int axis = d >> 1; // 0 -> x, 1 -> y
                int nx = x + sign * (1 - axis);
                int ny = y + sign * axis;
                boolean outb = (nx > bnd) | (nx < -bnd) | (ny > bnd) | (ny < -bnd);
                if (outb) b++; else { x = nx; y = ny; if (x == 0 && y == 0) r++; }
            }
            bumps += b; returns += r;
            spread += (long)x * x + (long)y * y;
            long dist = Math.abs((long)x) + Math.abs((long)y);
            if (dist > bestD) { bestD = dist; bestJ = j; }
        }
        out.spread = spread; out.bumps = bumps; out.returns = returns;
        out.bestD = bestD; out.bestJ = bestJ;
    }

    public static void main(String[] args) throws Exception {
        int workers = 1;
        if (args.length >= 2) workers = Integer.parseInt(args[1].trim());
        if (workers < 1) workers = 1;
        if (workers > 32) workers = 32;
        byte[] data = Files.readAllBytes(Paths.get(args[0]));
        // parse 4 tokens
        long[] vals = new long[4];
        int idx = 0, i = 0;
        while (idx < 4 && i < data.length) {
            while (i < data.length && (data[i]==' '||data[i]=='\n'||data[i]=='\r'||data[i]=='\t')) i++;
            if (i >= data.length) break;
            boolean neg = false;
            if (data[i]=='-') { neg=true; i++; }
            long v = 0;
            while (i < data.length && data[i]>='0' && data[i]<='9') { v = v*10 + (data[i]-'0'); i++; }
            vals[idx++] = neg ? -v : v;
        }
        J = vals[0]; L = vals[1]; B = (int)vals[2]; SEED = vals[3]; // long bits = unsigned seed (wrap ok for idx<3? seed parsed as signed wrap via overflow of *10 in long: same bits)
        // Note: parsing seed as long with overflow gives correct unsigned bits because arithmetic is mod 2^64.

        if (J <= 0) {
            System.out.print("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
            return;
        }
        if (workers > J) workers = (int)J;
        // Warm up the JIT on the main thread with walker 0 (real work, kept as
        // its own partial) so worker threads run already-compiled code instead
        // of contending on on-stack-replacement compilation.
        Partial warm = null;
        long restStart = 0;
        if (workers > 1 && J > 1 && L >= 10000) {
            warm = new Partial();
            runChunk(0, 1, warm);
            restStart = 1;
        }
        long rest = J - restStart;
        if (workers > rest && rest > 0) workers = (int)rest;
        final Partial[] parts = new Partial[workers];
        for (int w=0;w<workers;w++) parts[w]=new Partial();
        if (workers == 1) {
            runChunk(restStart, J, parts[0]);
        } else {
            Thread[] th = new Thread[workers-1];
            long base = rest / workers, rem = rest % workers;
            long s = restStart;
            for (int w=0;w<workers;w++) {
                long cnt = base + (w < rem ? 1 : 0);
                final long st = s, en = s+cnt; s=en;
                final int wi = w;
                if (w == workers-1) {
                    runChunk(st,en,parts[wi]);
                } else {
                    th[w] = new Thread(() -> runChunk(st,en,parts[wi]));
                    th[w].start();
                }
            }
            for (Thread t: th) if (t!=null) t.join();
        }
        long spread=0, bumps=0, returns=0, bestD=-1, bestJ=0;
        if (warm != null) {
            spread+=warm.spread; bumps+=warm.bumps; returns+=warm.returns;
            if (warm.bestD > bestD) { bestD=warm.bestD; bestJ=warm.bestJ; }
        }
        for (Partial p: parts) {
            spread+=p.spread; bumps+=p.bumps; returns+=p.returns;
            if (p.bestD > bestD) { bestD=p.bestD; bestJ=p.bestJ; }
        }
        if (bestD<0) bestD=0;
        StringBuilder sb = new StringBuilder(64);
        sb.append("spread ").append(spread).append('\n');
        sb.append("bumps ").append(bumps).append('\n');
        sb.append("returns ").append(returns).append('\n');
        sb.append("farthest ").append(bestJ).append(' ').append(bestD).append('\n');
        System.out.print(sb.toString());
    }
}
