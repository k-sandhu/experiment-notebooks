import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {

    // SplitMix64 constants as signed long bit patterns (arithmetic wraps mod 2^64).
    private static final long C = -0x61C8864680B583EBL;
    private static final long M1 = -0x40A7B892E31B1A47L;
    private static final long M2 = -0x6B2FB644ECCEEE15L;

    private static final class Result {
        long spread;
        long bumps;
        long returns;
        long farDist;
        long farIdx;
    }

    // Simulate walkers [start, end) and return partial results.
    private static Result runChunk(long start, long end, long L, long B, long seed) {
        long spread = 0, bumps = 0, returns = 0;
        long farDist = 0, farIdx = start;
        for (long j = start; j < end; ++j) {
            long state = seed + j;  // (SEED + j) mod 2^64
            long x = 0, y = 0;
            long b2 = 0, r2 = 0;
            for (long s = L; s != 0; --s) {
                state += C;
                long z = state;
                z ^= z >>> 30;
                z *= M1;
                z ^= z >>> 27;
                z *= M2;
                long r = z ^ (z >>> 31);
                int d = (int)(r >>> 62);
                boolean bumped;
                if (d == 0) {
                    if (x < B) { ++x; bumped = false; } else bumped = true;
                } else if (d == 1) {
                    if (x > -B) { --x; bumped = false; } else bumped = true;
                } else if (d == 2) {
                    if (y < B) { ++y; bumped = false; } else bumped = true;
                } else {
                    if (y > -B) { --y; bumped = false; } else bumped = true;
                }
                if (bumped) {
                    ++b2;
                } else if (x == 0 && y == 0) {
                    ++r2;
                }
            }
            spread += x * x + y * y;
            bumps += b2;
            returns += r2;
            long dist = (x < 0 ? -x : x) + (y < 0 ? -y : y);
            // Strictly greater keeps the smallest walker index on ties.
            if (dist > farDist) {
                farDist = dist;
                farIdx = j;
            }
        }
        Result res = new Result();
        res.spread = spread;
        res.bumps = bumps;
        res.returns = returns;
        res.farDist = farDist;
        res.farIdx = farIdx;
        return res;
    }

    public static void main(String[] args) throws Exception {
        String[] parts = new String(Files.readAllBytes(Paths.get(args[0])), java.nio.charset.StandardCharsets.UTF_8).trim().split("\\s+");
        long J = Long.parseLong(parts[0]);
        long L = Long.parseLong(parts[1]);
        long B = Long.parseLong(parts[2]);
        long seed = Long.parseUnsignedLong(parts[3]);

        int workers = Integer.parseInt(args[1]);
        if (workers < 1) workers = 1;
        int nThreads = J == 0 ? 0 : (int)Math.min(workers, J);

        Result[] results = new Result[nThreads];
        if (nThreads > 0) {
            long chunk = (J + nThreads - 1) / nThreads;
            Thread[] threads = new Thread[nThreads];
            for (int i = 0; i < nThreads; ++i) {
                final int idx = i;
                final long start = (long)i * chunk;
                final long end = Math.min(start + chunk, J);
                threads[i] = new Thread(() -> results[idx] = runChunk(start, end, L, B, seed));
                threads[i].start();
            }
            for (Thread t : threads) t.join();
        }

        long spread = 0, bumps = 0, returns = 0;
        long farDist = 0, farIdx = 0;
        for (int i = 0; i < nThreads; ++i) {
            Result r = results[i];
            spread += r.spread;
            bumps += r.bumps;
            returns += r.returns;
            if (r.farDist > farDist || (r.farDist == farDist && r.farIdx < farIdx)) {
                farDist = r.farDist;
                farIdx = r.farIdx;
            }
        }

        System.out.println("spread " + spread);
        System.out.println("bumps " + bumps);
        System.out.println("returns " + returns);
        System.out.println("farthest " + farIdx + " " + farDist);
    }
}
