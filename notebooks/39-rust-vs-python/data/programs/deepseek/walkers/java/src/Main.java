import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class Main {

    static final long GAMMA = 0x9E3779B97F4A7C15L;
    static final long C1    = 0xBF58476D1CE4E5B9L;
    static final long C2    = 0x94D049BB133111EBL;

    static long[] spread;
    static long[] bumps;
    static long[] returns;
    static long[] fx;
    static long[] fy;

    static void runWalker(long state, long steps, long B, int j) {
        long x = 0, y = 0;
        long np = 0, nr = 0;
        final long nb = -B;

        for (long k = 0; k < steps; ++k) {
            state += GAMMA;
            long z = state;
            z = (z ^ (z >>> 30)) * C1;
            z = (z ^ (z >>> 27)) * C2;
            z ^= z >>> 31;

            long d = z >>> 62;
            long dir = 1 - 2 * (d & 1);
            long mx = (d < 2) ? -1L : 0L;
            long dx = dir & mx;
            long dy = dir & ~mx;
            long nx = x + dx, ny = y + dy;
            long ox = (nx > B ? 1L : 0L) - (nx < nb ? 1L : 0L);
            long oy = (ny > B ? 1L : 0L) - (ny < nb ? 1L : 0L);
            nx -= ox;
            ny -= oy;
            np += ((ox | oy) != 0) ? 1 : 0;
            nr += ((nx | ny) == 0) ? 1 : 0;
            x = nx;
            y = ny;
        }

        spread[j]  = x * x + y * y;
        bumps[j]   = np;
        returns[j] = nr;
        fx[j] = x;
        fy[j] = y;
    }

    static void runWalker2(long s0, long s1, long steps, long B, int j0, int j1) {
        long x0 = 0, y0 = 0, x1 = 0, y1 = 0;
        long b0 = 0, r0 = 0, b1 = 0, r1 = 0;
        final long nb = -B;

        for (long k = 0; k < steps; ++k) {
            s0 += GAMMA;
            long z0 = s0;
            z0 = (z0 ^ (z0 >>> 30)) * C1;
            z0 = (z0 ^ (z0 >>> 27)) * C2;
            z0 ^= z0 >>> 31;

            s1 += GAMMA;
            long z1 = s1;
            z1 = (z1 ^ (z1 >>> 30)) * C1;
            z1 = (z1 ^ (z1 >>> 27)) * C2;
            z1 ^= z1 >>> 31;

            long d0 = z0 >>> 62;
            long dir0 = 1 - 2 * (d0 & 1);
            long mx0 = (d0 < 2) ? -1L : 0L;
            long nx0 = x0 + (dir0 & mx0);
            long ny0 = y0 + (dir0 & ~mx0);
            long ox0 = (nx0 > B ? 1L : 0L) - (nx0 < nb ? 1L : 0L);
            long oy0 = (ny0 > B ? 1L : 0L) - (ny0 < nb ? 1L : 0L);
            nx0 -= ox0;
            ny0 -= oy0;
            b0 += ((ox0 | oy0) != 0) ? 1 : 0;
            r0 += ((nx0 | ny0) == 0) ? 1 : 0;
            x0 = nx0;
            y0 = ny0;

            long d1 = z1 >>> 62;
            long dir1 = 1 - 2 * (d1 & 1);
            long mx1 = (d1 < 2) ? -1L : 0L;
            long nx1 = x1 + (dir1 & mx1);
            long ny1 = y1 + (dir1 & ~mx1);
            long ox1 = (nx1 > B ? 1L : 0L) - (nx1 < nb ? 1L : 0L);
            long oy1 = (ny1 > B ? 1L : 0L) - (ny1 < nb ? 1L : 0L);
            nx1 -= ox1;
            ny1 -= oy1;
            b1 += ((ox1 | oy1) != 0) ? 1 : 0;
            r1 += ((nx1 | ny1) == 0) ? 1 : 0;
            x1 = nx1;
            y1 = ny1;
        }

        spread[j0] = x0 * x0 + y0 * y0;
        bumps[j0] = b0;
        returns[j0] = r0;
        fx[j0] = x0;
        fy[j0] = y0;
        spread[j1] = x1 * x1 + y1 * y1;
        bumps[j1] = b1;
        returns[j1] = r1;
        fx[j1] = x1;
        fy[j1] = y1;
    }

    static void runRange(long seed, long steps, long B, int start, int end) {
        int j = start;
        for (; j + 1 < end; j += 2)
            runWalker2(seed + j, seed + j + 1, steps, B, j, j + 1);
        if (j < end)
            runWalker(seed + j, steps, B, j);
    }

    public static void main(String[] args) throws IOException {
        String text = new String(Files.readAllBytes(Path.of(args[0])), StandardCharsets.US_ASCII);
        String[] tok = text.trim().split("\\s+");
        int J = Integer.parseInt(tok[0]);
        long L = Long.parseLong(tok[1]);
        long B = Long.parseLong(tok[2]);
        long seed = Long.parseUnsignedLong(tok[3]);

        int workers = Integer.parseInt(args[1].trim());
        if (workers < 1) workers = 1;
        if (workers > J) workers = J;
        if (workers < 1) workers = 1;

        spread  = new long[J];
        bumps   = new long[J];
        returns = new long[J];
        fx      = new long[J];
        fy      = new long[J];

        if (J > 0) {
            if (workers == 1) {
                runRange(seed, L, B, 0, J);
            } else {
                Thread[] threads = new Thread[workers];
                int base = J / workers;
                int rem = J % workers;
                int start = 0;
                for (int t = 0; t < workers; ++t) {
                    int cnt = base + (t < rem ? 1 : 0);
                    int s = start;
                    int e = start + cnt;
                    start = e;
                    final int ss = s, ee = e;
                    threads[t] = new Thread(() -> runRange(seed, L, B, ss, ee));
                    threads[t].start();
                }
                for (Thread th : threads) {
                    try {
                        th.join();
                    } catch (InterruptedException ex) {
                        Thread.currentThread().interrupt();
                    }
                }
            }
        }

        long totalSpread = 0, totalBumps = 0, totalReturns = 0;
        long bestDist = 0;
        int bestJ = 0;
        for (int j = 0; j < J; ++j) {
            totalSpread  += spread[j];
            totalBumps   += bumps[j];
            totalReturns += returns[j];
            long ax = fx[j] < 0 ? -fx[j] : fx[j];
            long ay = fy[j] < 0 ? -fy[j] : fy[j];
            long d = ax + ay;
            if (d > bestDist) {
                bestDist = d;
                bestJ = j;
            }
        }

        StringBuilder sb = new StringBuilder(96);
        sb.append("spread ").append(totalSpread).append('\n');
        sb.append("bumps ").append(totalBumps).append('\n');
        sb.append("returns ").append(totalReturns).append('\n');
        sb.append("farthest ").append(bestJ).append(' ').append(bestDist).append('\n');
        System.out.print(sb);
    }
}
