import java.io.*;
import java.nio.file.*;

public class Main {
    public static void main(String[] args) throws Exception {
        byte[] buf = Files.readAllBytes(Path.of(args[0]));
        int n = buf.length, p = 0;
        int[] hdr = new int[3];
        for (int k = 0; k < 3; k++) {
            while (p < n && (buf[p] < '0' || buf[p] > '9')) p++;
            int v = 0;
            while (p < n && buf[p] >= '0' && buf[p] <= '9') { v = v * 10 + (buf[p] - '0'); p++; }
            hdr[k] = v;
        }
        int H = hdr[0], W = hdr[1], S = hdr[2];
        while (p < n && buf[p] != '\n') p++;
        if (p < n) p++;
        int N = H * W;
        int[] cur = new int[N], nxt = new int[N];
        byte[] kind = new byte[N];
        for (int r = 0; r < H; r++) {
            while (p < n && (buf[p] == '\r' || buf[p] == '\n')) p++;
            for (int c = 0; c < W; c++) {
                byte ch = p < n ? buf[p++] : (byte) '.';
                int i = r * W + c;
                if (ch == '#') kind[i] = 0;
                else if (ch == '.') kind[i] = 1;
                else { kind[i] = 2; int v = 1000 * (ch - '0'); cur[i] = v; nxt[i] = v; }
            }
        }
        buf = null;
        // counts first pass inline build with growable arrays
        int[] openIdx = new int[N]; int nOpen = 0;
        int[] runStart = new int[N]; int[] runLen = new int[N]; int nRuns = 0;
        int[] eIdx = new int[N]; int[] eU = new int[N]; int[] eD = new int[N]; int[] eL = new int[N]; int[] eR = new int[N]; int nEdge = 0;
        for (int r = 0; r < H; r++) {
            int c = 0;
            while (c < W) {
                int i = r * W + c;
                if (kind[i] != 1) { c++; continue; }
                boolean fast = r > 0 && r + 1 < H && c > 0 && c + 1 < W
                    && kind[i - W] != 0 && kind[i + W] != 0 && kind[i - 1] != 0 && kind[i + 1] != 0;
                if (fast) {
                    int start = i, len = 0;
                    while (c < W) {
                        int j = r * W + c;
                        if (kind[j] != 1) break;
                        if (!(r > 0 && r + 1 < H && c > 0 && c + 1 < W && kind[j - W] != 0 && kind[j + W] != 0 && kind[j - 1] != 0 && kind[j + 1] != 0)) break;
                        openIdx[nOpen++] = j; len++; c++;
                    }
                    runStart[nRuns] = start; runLen[nRuns] = len; nRuns++;
                } else {
                    openIdx[nOpen++] = i;
                    eIdx[nEdge] = i;
                    eU[nEdge] = (r > 0 && kind[i - W] != 0) ? i - W : i;
                    eD[nEdge] = (r + 1 < H && kind[i + W] != 0) ? i + W : i;
                    eL[nEdge] = (c > 0 && kind[i - 1] != 0) ? i - 1 : i;
                    eR[nEdge] = (c + 1 < W && kind[i + 1] != 0) ? i + 1 : i;
                    nEdge++; c++;
                }
            }
        }
        kind = null;
        for (int step = 0; step < S; step++) {
            for (int ri = 0; ri < nRuns; ri++) {
                int start = runStart[ri], len = runLen[ri];
                for (int k = 0; k < len; k++) {
                    int i = start + k;
                    int old = cur[i];
                    nxt[i] = ((old << 2) + cur[i - W] + cur[i + W] + cur[i - 1] + cur[i + 1]) >> 3;
                }
            }
            for (int k = 0; k < nEdge; k++) {
                int i = eIdx[k];
                int old = cur[i];
                nxt[i] = ((old << 2) + cur[eU[k]] + cur[eD[k]] + cur[eL[k]] + cur[eR[k]]) >> 3;
            }
            int[] t = cur; cur = nxt; nxt = t;
        }
        long sum = 0, checksum = 0;
        int best = -1, bestIdx = nOpen > 0 ? openIdx[0] : 0;
        for (int k = 0; k < nOpen; k++) {
            int i = openIdx[k], v = cur[i];
            sum += v; checksum += (long) v * (long) (i + 1);
            if (v > best) { best = v; bestIdx = i; }
        }
        int br = W != 0 ? bestIdx / W : 0, bc = W != 0 ? bestIdx % W : 0;
        System.out.print("sum " + sum + "\nmax " + best + " " + br + " " + bc + "\nchecksum " + checksum + "\n");
    }
}
