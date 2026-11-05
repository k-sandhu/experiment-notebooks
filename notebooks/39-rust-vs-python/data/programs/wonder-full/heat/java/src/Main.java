import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;

public class Main {
    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        int pos = 0;
        int[] hdr = new int[3];
        for (int k = 0; k < 3; k++) {
            while (pos < data.length && (data[pos] < '0' || data[pos] > '9')) pos++;
            int v = 0;
            while (pos < data.length && data[pos] >= '0' && data[pos] <= '9') v = v * 10 + (data[pos++] - '0');
            hdr[k] = v;
        }
        int H = hdr[0], W = hdr[1], S = hdr[2];
        while (pos < data.length && data[pos] != '\n') pos++;
        if (pos < data.length) pos++;
        int N = H * W;
        byte[] grid = new byte[N];
        int gi = 0;
        for (int q = pos; q < data.length && gi < N; q++) {
            byte c = data[q];
            if (c == '.' || c == '#' || (c >= '1' && c <= '9')) grid[gi++] = c;
        }

        int[] cur = new int[N];
        int[] nxt = new int[N];
        for (int i = 0; i < N; i++) {
            byte c = grid[i];
            if (c >= '1' && c <= '9') { int v = 1000 * (c - '0'); cur[i] = v; nxt[i] = v; }
        }

        ArrayList<Integer> runsL = new ArrayList<>();
        ArrayList<Integer> specL = new ArrayList<>();
        ArrayList<Integer> openL = new ArrayList<>();
        for (int r = 0; r < H; r++) {
            int runStart = -1;
            for (int c = 0; c < W; c++) {
                int i = r * W + c;
                if (grid[i] != '.') {
                    if (runStart >= 0) { runsL.add(runStart); runsL.add(i - runStart); runStart = -1; }
                    continue;
                }
                openL.add(i);
                boolean interior = r > 0 && r < H - 1 && c > 0 && c < W - 1
                        && grid[i - W] != '#' && grid[i + W] != '#' && grid[i - 1] != '#' && grid[i + 1] != '#';
                if (interior) {
                    if (runStart < 0) runStart = i;
                } else {
                    if (runStart >= 0) { runsL.add(runStart); runsL.add(i - runStart); runStart = -1; }
                    int up = (r > 0     && grid[i - W] != '#') ? i - W : i;
                    int dn = (r < H - 1 && grid[i + W] != '#') ? i + W : i;
                    int lf = (c > 0     && grid[i - 1] != '#') ? i - 1 : i;
                    int rt = (c < W - 1 && grid[i + 1] != '#') ? i + 1 : i;
                    specL.add(i); specL.add(up); specL.add(dn); specL.add(lf); specL.add(rt);
                }
            }
            if (runStart >= 0) { runsL.add(runStart); runsL.add(r * W + W - runStart); }
        }
        int[] runs = toArray(runsL), spec = toArray(specL), openIdx = toArray(openL);

        cur = simulate(cur, nxt, runs, spec, W, S);

        long sum = 0, checksum = 0;
        int best = -1, bestIdx = openIdx.length > 0 ? openIdx[0] : 0;
        for (int i : openIdx) {
            int v = cur[i];
            sum += v;
            checksum += (long) v * (i + 1L);
            if (v > best) { best = v; bestIdx = i; }
        }
        if (best < 0) best = 0;
        int br = W > 0 ? bestIdx / W : 0, bc = W > 0 ? bestIdx % W : 0;
        System.out.print("sum " + sum + "\nmax " + best + " " + br + " " + bc + "\nchecksum " + checksum + "\n");
    }

    static int[] simulate(int[] cur, int[] nxt, int[] runs, int[] spec, int W, int S) {
        for (int step = 0; step < S; step++) {
            int[] cp = cur, np = nxt;
            for (int ri = 0; ri < runs.length; ri += 2) {
                int start = runs[ri], len = runs[ri + 1];
                int up = start - W, dn = start + W;
                for (int k = 0; k < len; k++) {
                    int i = start + k;
                    np[i] = (4 * cp[i] + cp[up + k] + cp[dn + k] + cp[i - 1] + cp[i + 1]) >> 3;
                }
            }
            for (int si = 0; si < spec.length; si += 5) {
                int i = spec[si];
                np[i] = (4 * cp[i] + cp[spec[si + 1]] + cp[spec[si + 2]] + cp[spec[si + 3]] + cp[spec[si + 4]]) >> 3;
            }
            int[] t = cur; cur = nxt; nxt = t;
        }
        return cur;
    }

    static int[] toArray(ArrayList<Integer> l) {
        int[] a = new int[l.size()];
        for (int i = 0; i < a.length; i++) a[i] = l.get(i);
        return a;
    }
}
