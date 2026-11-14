import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.concurrent.atomic.AtomicLong;

public class Main {
    static final long GAMMA = 0x9E3779B97F4A7C15L;
    static final long M1 = 0xBF58476D1CE4E5B9L;
    static final long M2 = 0x94D049BB133111EBL;
    static final int CHUNK = 8192;

    static final class Task implements Runnable {
        final AtomicLong next;
        final long walkers, steps, box, seed;

        // per-walk state
        long s, x, y;
        // aggregates
        long spread, bumps, returns;
        long bestD = -1, bestJ = Long.MAX_VALUE;

        Task(AtomicLong next, long walkers, long steps, long box, long seed) {
            this.next = next;
            this.walkers = walkers;
            this.steps = steps;
            this.box = box;
            this.seed = seed;
        }

        @Override
        public void run() {
            final long J = walkers, L = steps, B = box;
            while (true) {
                long j = next.getAndIncrement();
                if (j >= J) break;
                s = seed + j;
                x = 0;
                y = 0;
                long rem = L;
                while (rem > 0) {
                    int n = rem > CHUNK ? CHUNK : (int) rem;
                    step(n, B);
                    rem -= n;
                }
                long fx = x, fy = y;
                spread += fx * fx + fy * fy;
                long d = (fx < 0 ? -fx : fx) + (fy < 0 ? -fy : fy);
                if (d > bestD || (d == bestD && j < bestJ)) {
                    bestD = d;
                    bestJ = j;
                }
            }
        }

        private void step(int n, long B) {
            long s = this.s, x = this.x, y = this.y;
            long bm = 0, rt = 0;
            for (int i = 0; i < n; i++) {
                s += GAMMA;
                long z = (s ^ (s >>> 30)) * M1;
                z = (z ^ (z >>> 27)) * M2;
                // top two bits of the output equal top two bits of z
                long ax = z >> 63;                 // 0 -> x axis, -1 -> y axis
                long sg = 1 - ((z >>> 61) & 2);    // +1 or -1
                long nx = x + (sg & ~ax);
                long ny = y + (sg & ax);
                if (((B - nx) | (B + nx) | (B - ny) | (B + ny)) < 0) {
                    bm++;
                } else {
                    x = nx;
                    y = ny;
                    if ((nx | ny) == 0) rt++;
                }
            }
            this.s = s;
            this.x = x;
            this.y = y;
            this.bumps += bm;
            this.returns += rt;
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        byte[] data = Files.readAllBytes(Paths.get(args[0]));
        long[] v = new long[4];
        int p = 0;
        final int len = data.length;
        for (int k = 0; k < 4; k++) {
            while (p < len && (data[p] < '0' || data[p] > '9')) p++;
            long val = 0;
            boolean sat = false;
            while (p < len && data[p] >= '0' && data[p] <= '9') {
                int d = data[p] - '0';
                if (k < 3) {
                    if (sat || val > (Long.MAX_VALUE - d) / 10) {
                        sat = true;
                    } else {
                        val = val * 10 + d;
                    }
                } else {
                    val = val * 10 + d; // wraps mod 2^64
                }
                p++;
            }
            v[k] = sat ? Long.MAX_VALUE : val;
        }
        final long J = v[0];
        final long L = v[1];
        long B = v[2];
        final long seed = v[3];
        if (B > L) B = L; // a walker can never be farther than L from the origin
        if (B < 1) B = 1;

        int workers = 1;
        if (args.length > 1) {
            try {
                workers = Integer.parseInt(args[1].trim());
            } catch (NumberFormatException e) {
                workers = 1;
            }
        }
        if (workers < 1) workers = 1;
        if (workers > J) workers = (int) Math.max(1L, J);

        AtomicLong next = new AtomicLong(0);
        Task[] tasks = new Task[workers];
        Thread[] threads = new Thread[workers];
        for (int i = 0; i < workers; i++) {
            tasks[i] = new Task(next, J, L, B, seed);
        }
        for (int i = 1; i < workers; i++) {
            threads[i] = new Thread(tasks[i]);
            threads[i].start();
        }
        tasks[0].run();
        for (int i = 1; i < workers; i++) {
            threads[i].join();
        }

        long spread = 0, bumps = 0, returns = 0;
        long bestD = -1, bestJ = Long.MAX_VALUE;
        for (int i = 0; i < workers; i++) {
            Task t = tasks[i];
            spread += t.spread;
            bumps += t.bumps;
            returns += t.returns;
            if (t.bestD > bestD || (t.bestD == bestD && t.bestJ < bestJ)) {
                bestD = t.bestD;
                bestJ = t.bestJ;
            }
        }
        if (bestD < 0) {
            bestD = 0;
            bestJ = 0;
        }

        StringBuilder sb = new StringBuilder(128);
        sb.append("spread ").append(spread).append('\n');
        sb.append("bumps ").append(bumps).append('\n');
        sb.append("returns ").append(returns).append('\n');
        sb.append("farthest ").append(bestJ).append(' ').append(bestD).append('\n');
        PrintStream out = System.out;
        byte[] ob = sb.toString().getBytes(StandardCharsets.US_ASCII);
        out.write(ob, 0, ob.length);
        out.flush();
    }
}
