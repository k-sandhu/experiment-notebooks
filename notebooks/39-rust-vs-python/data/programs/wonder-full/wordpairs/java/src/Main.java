import java.nio.file.*;
import java.util.*;

public class Main {
    static long mix64(long x) {
        x += 0x9e3779b97f4a7c15L;
        x = (x ^ (x >>> 30)) * 0xbf58476d1ce4e5b9L;
        x = (x ^ (x >>> 27)) * 0x94d049bb133111ebL;
        return x ^ (x >>> 31);
    }

    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Path.of(args[0]));
        int n = data.length;

        int wcap = 1024;
        while (wcap < (1 << 17) && (long) wcap * 64 < n) wcap <<= 1;
        int[] wtab = new int[wcap];
        Arrays.fill(wtab, -1);
        int wmask = wcap - 1;

        byte[] arena = new byte[1 << 20];
        int arenaLen = 0;
        int[] woff = new int[65536];
        int[] wlen = new int[65536];
        long[] whash = new long[65536];
        int V = 0;

        int est = n / 6 + 1024;
        if (est > (1 << 24)) est = 1 << 24;
        if (est < 1024) est = 1024;
        long[] pairs = new long[est];
        int pc = 0;

        long W = 0;
        int prev = -1;
        int i = 0;
        while (i < n) {
            int b = data[i] & 0xFF;
            int lo = b | 32;
            if (lo - 97 >= 0 && lo - 97 < 26) {
                int start = i;
                long h = -3750763034362895579L; // FNV offset basis
                for (;;) {
                    h ^= lo;
                    h *= 1099511628211L;
                    i++;
                    if (i >= n) break;
                    b = data[i] & 0xFF;
                    lo = b | 32;
                    if (lo - 97 < 0 || lo - 97 >= 26) break;
                }
                int len = i - start;
                long mh = mix64(h);
                int idx = (int) mh & wmask;
                int id;
                for (;;) {
                    id = wtab[idx];
                    if (id < 0) {
                        id = V++;
                        wtab[idx] = id;
                        if (V >= whash.length) {
                            int nc = whash.length << 1;
                            whash = Arrays.copyOf(whash, nc);
                            woff = Arrays.copyOf(woff, nc);
                            wlen = Arrays.copyOf(wlen, nc);
                        }
                        whash[id] = mh;
                        woff[id] = arenaLen;
                        wlen[id] = len;
                        if (arenaLen + len > arena.length) {
                            int nc = arena.length;
                            while (nc < arenaLen + len) nc <<= 1;
                            arena = Arrays.copyOf(arena, nc);
                        }
                        for (int k = 0; k < len; k++) arena[arenaLen++] = (byte) (data[start + k] | 32);
                        if (V * 4 > wcap * 3) {
                            int ncap = wcap << 1;
                            int[] nt = new int[ncap];
                            Arrays.fill(nt, -1);
                            int nmask = ncap - 1;
                            for (int wi = 0; wi < V; wi++) {
                                int j = (int) whash[wi] & nmask;
                                while (nt[j] >= 0) j = (j + 1) & nmask;
                                nt[j] = wi;
                            }
                            wtab = nt; wcap = ncap; wmask = nmask;
                        }
                        break;
                    }
                    if (whash[id] == mh && wlen[id] == len) {
                        int off = woff[id];
                        boolean eq = true;
                        for (int k = 0; k < len; k++) {
                            if (arena[off + k] != (byte) (data[start + k] | 32)) { eq = false; break; }
                        }
                        if (eq) break;
                    }
                    idx = (idx + 1) & wmask;
                }
                W++;
                if (prev >= 0) {
                    if (pc == pairs.length) pairs = Arrays.copyOf(pairs, pairs.length << 1);
                    pairs[pc++] = ((long) prev << 32) | (id & 0xFFFFFFFFL);
                }
                prev = id;
            } else {
                if (b == '.' || b == '!' || b == '?') prev = -1;
                i++;
            }
        }
        long T = pc;
        data = null;

        // rank
        Integer[] ids = new Integer[V];
        for (int k = 0; k < V; k++) ids[k] = k;
        final byte[] ar = arena;
        final int[] wo = woff, wl = wlen;
        Arrays.sort(ids, (a, b) -> {
            int la = wl[a], lb = wl[b], oa = wo[a], ob = wo[b];
            int m = la < lb ? la : lb;
            for (int k = 0; k < m; k++) {
                int diff = (ar[oa + k] & 0xFF) - (ar[ob + k] & 0xFF);
                if (diff != 0) return diff;
            }
            return la - lb;
        });
        int[] rankv = new int[V];
        for (int k = 0; k < V; k++) rankv[ids[k]] = k;

        int[] topC = new int[20], topA = new int[20], topB = new int[20];
        int topN = 0, worst = 0;
        long D = 0;

        if (pc > 0 && V <= 65536) {
            int[] keys = new int[pc];
            for (int k = 0; k < pc; k++) { long v = pairs[k]; keys[k] = ((int) (v >> 32) << 16) | (int) v; }
            pairs = null;
            int[] aux = new int[pc];
            int[] src = keys, dst = aux;
            int[] cnt = new int[65536];
            for (int shift = 0; shift < 32; shift += 16) {
                Arrays.fill(cnt, 0);
                for (int k = 0; k < pc; k++) cnt[(src[k] >>> shift) & 0xFFFF]++;
                int sum = 0;
                for (int k = 0; k < 65536; k++) { int t = cnt[k]; cnt[k] = sum; sum += t; }
                for (int k = 0; k < pc; k++) { int v = src[k]; dst[cnt[(v >>> shift) & 0xFFFF]++] = v; }
                int[] tmp = src; src = dst; dst = tmp;
            }
            int k = 0;
            while (k < pc) {
                int j = k + 1;
                int v = src[k];
                while (j < pc && src[j] == v) j++;
                int c = j - k;
                D++;
                int a = v >>> 16, bb = v & 0xFFFF;
                if (topN < 20) {
                    topC[topN] = c; topA[topN] = a; topB[topN] = bb; topN++;
                    if (topN == 20) worst = findWorst(topC, topA, topB, topN, rankv);
                } else if (better(c, a, bb, topC[worst], topA[worst], topB[worst], rankv)) {
                    topC[worst] = c; topA[worst] = a; topB[worst] = bb;
                    worst = findWorst(topC, topA, topB, topN, rankv);
                }
                k = j;
            }
        } else if (pc > 0) {
            long[] aux = new long[pc];
            long[] src = pairs, dst = aux;
            int[] cnt = new int[65536];
            for (int shift = 0; shift < 64; shift += 16) {
                Arrays.fill(cnt, 0);
                for (int k = 0; k < pc; k++) cnt[(int) (src[k] >>> shift) & 0xFFFF]++;
                int sum = 0;
                for (int k = 0; k < 65536; k++) { int t = cnt[k]; cnt[k] = sum; sum += t; }
                for (int k = 0; k < pc; k++) { long v = src[k]; dst[cnt[(int) (v >>> shift) & 0xFFFF]++] = v; }
                long[] tmp = src; src = dst; dst = tmp;
            }
            int k = 0;
            while (k < pc) {
                int j = k + 1;
                long v = src[k];
                while (j < pc && src[j] == v) j++;
                int c = j - k;
                D++;
                int a = (int) (v >> 32), bb = (int) v;
                if (topN < 20) {
                    topC[topN] = c; topA[topN] = a; topB[topN] = bb; topN++;
                    if (topN == 20) worst = findWorst(topC, topA, topB, topN, rankv);
                } else if (better(c, a, bb, topC[worst], topA[worst], topB[worst], rankv)) {
                    topC[worst] = c; topA[worst] = a; topB[worst] = bb;
                    worst = findWorst(topC, topA, topB, topN, rankv);
                }
                k = j;
            }
        }
        // sort top descending by better order (insertion sort, <=20)
        for (int a = 1; a < topN; a++) {
            int c = topC[a], x = topA[a], y = topB[a], b = a - 1;
            while (b >= 0 && better(c, x, y, topC[b], topA[b], topB[b], rankv)) {
                topC[b + 1] = topC[b]; topA[b + 1] = topA[b]; topB[b + 1] = topB[b]; b--;
            }
            topC[b + 1] = c; topA[b + 1] = x; topB[b + 1] = y;
        }

        StringBuilder sb = new StringBuilder(1024);
        sb.append("words ").append(W).append('\n');
        sb.append("pairs ").append(T).append('\n');
        sb.append("distinct ").append(D).append('\n');
        for (int k2 = 0; k2 < topN; k2++) {
            sb.append(topC[k2]).append(' ');
            int a = topA[k2], b = topB[k2];
            for (int q = 0; q < wl[a]; q++) sb.append((char) ar[wo[a] + q]);
            sb.append(' ');
            for (int q = 0; q < wl[b]; q++) sb.append((char) ar[wo[b] + q]);
            sb.append('\n');
        }
        System.out.print(sb.toString());
    }

    static boolean better(int c1, int a1, int b1, int c2, int a2, int b2, int[] rk) {
        if (c1 != c2) return c1 > c2;
        if (rk[a1] != rk[a2]) return rk[a1] < rk[a2];
        return rk[b1] < rk[b2];
    }

    static int findWorst(int[] C, int[] A, int[] B, int n, int[] rk) {
        int w = 0;
        for (int q = 1; q < n; q++) if (better(C[w], A[w], B[w], C[q], A[q], B[q], rk)) w = q;
        return w;
    }
}
