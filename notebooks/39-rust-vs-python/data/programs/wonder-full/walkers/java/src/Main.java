import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    static final long GOLD = 0x9E3779B97F4A7C15L;
    static final long C1 = 0xBF58476D1CE4E5B9L;
    static final long C2 = 0x94D049BB133111EBL;
    static final int[] DX = {1, -1, 0, 0};
    static final int[] DY = {0, 0, 1, -1};

    static final class Partial {
        long spread, bumps, returns, farIdx, farDist = -1;
    }

    static void runRange(long begin, long end, long L, int B, long seed, Partial out) {
        long spread = 0, bumps = 0, returns = 0;
        long farIdx = begin, farDist = -1;
        // Coordinates offset by +B into unsigned [0, 2B] (int bit patterns);
        // one unsigned compare per axis detects a bump.
        final int UB = 2 * B;
        // Sign-flipped bound: (v ^ MIN) > UBf in signed order == unsigned v > UB.
        // Plain bytecode ops, cheap before the JIT kicks in (no method call).
        final int UBf = UB ^ Integer.MIN_VALUE;
        final int ORG = B;
        long L4 = L & ~3L;
        for (long j = begin; j < end; j++) {
            long state = seed + j;
            int ux = ORG, uy = ORG;
            long b = 0, r = 0;
            long i = 0;
            for (; i < L4; i += 4) {
                long s0 = state + GOLD;
                long s1 = s0 + GOLD;
                long s2 = s1 + GOLD;
                long s3 = s2 + GOLD;
                state = s3;
                int d0 = dir(s0), d1 = dir(s1), d2 = dir(s2), d3 = dir(s3);
                {
                    int nx = ux + DX[d0], ny = uy + DY[d0];
                    if ((nx ^ Integer.MIN_VALUE) > UBf | (ny ^ Integer.MIN_VALUE) > UBf) b++;
                    else { ux = nx; uy = ny; if (ux == ORG & uy == ORG) r++; }
                }
                {
                    int nx = ux + DX[d1], ny = uy + DY[d1];
                    if ((nx ^ Integer.MIN_VALUE) > UBf | (ny ^ Integer.MIN_VALUE) > UBf) b++;
                    else { ux = nx; uy = ny; if (ux == ORG & uy == ORG) r++; }
                }
                {
                    int nx = ux + DX[d2], ny = uy + DY[d2];
                    if ((nx ^ Integer.MIN_VALUE) > UBf | (ny ^ Integer.MIN_VALUE) > UBf) b++;
                    else { ux = nx; uy = ny; if (ux == ORG & uy == ORG) r++; }
                }
                {
                    int nx = ux + DX[d3], ny = uy + DY[d3];
                    if ((nx ^ Integer.MIN_VALUE) > UBf | (ny ^ Integer.MIN_VALUE) > UBf) b++;
                    else { ux = nx; uy = ny; if (ux == ORG & uy == ORG) r++; }
                }
            }
            for (; i < L; i++) {
                state += GOLD;
                int d = dir(state);
                int nx = ux + DX[d], ny = uy + DY[d];
                if ((nx ^ Integer.MIN_VALUE) > UBf | (ny ^ Integer.MIN_VALUE) > UBf) b++;
                else { ux = nx; uy = ny; if (ux == ORG & uy == ORG) r++; }
            }
            bumps += b; returns += r;
            long x = (ux & 0xFFFFFFFFL) - B, y = (uy & 0xFFFFFFFFL) - B;
            spread += x * x + y * y;
            long dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
            if (dist > farDist) { farDist = dist; farIdx = j; }
        }
        out.spread = spread; out.bumps = bumps; out.returns = returns;
        out.farIdx = farIdx; out.farDist = farDist;
    }

    static int dir(long state) {
        long z = state;
        z = (z ^ (z >>> 30)) * C1;
        z = (z ^ (z >>> 27)) * C2;
        return (int) (z >>> 62);
    }

    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        // Manual parse of 4 unsigned decimals (seed wraps into long bits).
        long[] vals = new long[4];
        int idx = 0, p = 0;
        while (idx < 4 && p < data.length) {
            while (p < data.length && (data[p] < '0' || data[p] > '9')) p++;
            if (p >= data.length) break;
            long v = 0;
            while (p < data.length && data[p] >= '0' && data[p] <= '9') {
                v = v * 10 + (data[p] - '0'); // unsigned wrap is fine: values < 2^64
                p++;
            }
            vals[idx++] = v;
        }
        long J = vals[0], L = vals[1];
        long Bv = vals[2];
        int B = Bv > Integer.MAX_VALUE ? Integer.MAX_VALUE : (int) Bv;
        long seed = vals[3];

        int workers = args.length >= 2 ? Integer.parseInt(args[1].trim())
                : Runtime.getRuntime().availableProcessors();
        if (workers < 1) workers = 1;
        if (workers > 32) workers = 32;
        if (J > 0 && workers > J) workers = (int) J;
        if (workers < 1) workers = 1;

        if (J <= 0) {
            System.out.print("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n");
            return;
        }
        Partial[] parts = new Partial[workers];
        for (int w = 0; w < workers; w++) parts[w] = new Partial();
        long[][] ranges = new long[workers][2];
        long base = J / workers, rem = J % workers, start = 0;
        for (int w = 0; w < workers; w++) {
            long cnt = base + (w < rem ? 1 : 0);
            ranges[w][0] = start; ranges[w][1] = start + cnt; start += cnt;
        }
        if (workers == 1) {
            runRange(ranges[0][0], ranges[0][1], L, B, seed, parts[0]);
        } else {
            Thread[] th = new Thread[workers - 1];
            for (int w = 1; w < workers; w++) {
                final int ww = w;
                th[w - 1] = new Thread(() -> runRange(ranges[ww][0], ranges[ww][1], L, B, seed, parts[ww]));
                th[w - 1].start();
            }
            runRange(ranges[0][0], ranges[0][1], L, B, seed, parts[0]);
            for (Thread t : th) t.join();
        }
        long spread = 0, bumps = 0, returns = 0, farIdx = 0, farDist = -1;
        for (Partial pt : parts) {
            spread += pt.spread; bumps += pt.bumps; returns += pt.returns;
            if (pt.farDist > farDist) { farDist = pt.farDist; farIdx = pt.farIdx; }
        }
        if (farDist < 0) farDist = 0;
        System.out.print("spread " + spread + "\nbumps " + bumps + "\nreturns " + returns
                + "\nfarthest " + farIdx + " " + farDist + "\n");
    }
}
