import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    static final int[] LOWER = new int[256];
    static {
        for (int c = 'a'; c <= 'z'; c++) LOWER[c] = c;
        for (int c = 'A'; c <= 'Z'; c++) LOWER[c] = c + 32;
    }

    static byte[] B;
    static int n;
    static long[] tab = new long[4096 * 3];
    static int mask = 4095;
    static int nWords = 0;
    static int[] wOff = new int[1 << 12];
    static int[] wLen = new int[1 << 12];

    static long mixKey(long p0, long p1, int len) {
        long h = p0 * 0x9E3779B97F4A7C15L;
        h ^= (p1 + len) * 0xC2B2AE3D27D4EB4FL;
        h ^= h >>> 29;
        h *= 0xBF58476D1CE4E5B9L;
        h ^= h >>> 32;
        return h;
    }

    static void rehash(int slots) {
        long[] t = new long[slots * 3];
        Arrays.fill(t, -1L);
        int m = slots - 1;
        int oldSlots = tab.length / 3;
        for (int s = 0; s < oldSlots; s++) {
            long idl = tab[s * 3 + 2];
            if ((int) idl < 0) continue;
            long p0 = tab[s * 3], p1 = tab[s * 3 + 1];
            int len = (int) (idl >>> 32);
            int idx = (int) mixKey(p0, p1, len) & m;
            while ((int) t[idx * 3 + 2] >= 0) idx = (idx + 1) & m;
            t[idx * 3] = p0;
            t[idx * 3 + 1] = p1;
            t[idx * 3 + 2] = idl;
        }
        tab = t;
        mask = m;
    }

    static void growWords() {
        int nc = wOff.length + (wOff.length >> 1) + 16;
        wOff = Arrays.copyOf(wOff, nc);
        wLen = Arrays.copyOf(wLen, nc);
    }

    static boolean eqTail(int a, int b, int len) {
        byte[] d = B;
        for (int i = 16; i < len; i++)
            if (d[a + i] != d[b + i]) return false;
        return true;
    }

    static int intern(long p0, long p1, int len, int off) {
        int idx = (int) mixKey(p0, p1, len) & mask;
        long[] t = tab;
        for (;;) {
            long idl = t[idx * 3 + 2];
            int id = (int) idl;
            if (id < 0) break;
            if ((int) (idl >>> 32) == len && t[idx * 3] == p0 && t[idx * 3 + 1] == p1) {
                if (len <= 16 || eqTail(wOff[id], off, len)) return id;
            }
            idx = (idx + 1) & mask;
        }
        if (nWords == wOff.length) growWords();
        int id = nWords++;
        wOff[id] = off;
        wLen[id] = len;
        t[idx * 3] = p0;
        t[idx * 3 + 1] = p1;
        t[idx * 3 + 2] = ((long) len << 32) | (id & 0xFFFFFFFFL);
        if (nWords * 10 > (t.length / 3) * 7) rehash((t.length / 3) * 2);
        return id;
    }

    static long getLong(byte[] b, int o) {
        return (b[o] & 0xFFL)
                | ((b[o + 1] & 0xFFL) << 8)
                | ((b[o + 2] & 0xFFL) << 16)
                | ((b[o + 3] & 0xFFL) << 24)
                | ((b[o + 4] & 0xFFL) << 32)
                | ((b[o + 5] & 0xFFL) << 40)
                | ((b[o + 6] & 0xFFL) << 48)
                | ((b[o + 7] & 0xFFL) << 56);
    }

    static int cmpWord(int x, int y) {
        int ox = wOff[x], oy = wOff[y];
        int lx = wLen[x], ly = wLen[y];
        int l = lx < ly ? lx : ly;
        byte[] d = B;
        for (int i = 0; i < l; i++) {
            int a = d[ox + i], b = d[oy + i];
            if (a != b) return a - b;
        }
        return lx - ly;
    }

    static boolean better(int c1, int a1, int a2, int c2, int b1, int b2) {
        if (c1 != c2) return c1 > c2;
        int c = cmpWord(a1, b1);
        if (c != 0) return c < 0;
        return cmpWord(a2, b2) < 0;
    }

    static boolean worse(int c1, int a1, int a2, int c2, int b1, int b2) {
        return better(c2, b1, b2, c1, a1, a2);
    }

    public static void main(String[] args) throws Exception {
        byte[] raw = Files.readAllBytes(Path.of(args[0]));
        n = raw.length;
        B = Arrays.copyOf(raw, n + 16);
        byte[] b = B;
        raw = null;

        Arrays.fill(tab, -1L);

        int cap = Math.max(1024, n / 6 + 1024);
        long[] pairs = new long[cap];
        int np = 0;
        int prev = -1;
        int i = 0;
        long W = 0, T = 0;
        int[] low = LOWER;

        while (i < n) {
            int lc = low[b[i] & 0xFF];
            if (lc != 0) {
                int start = i;
                do {
                    b[i] = (byte) lc;
                    i++;
                    lc = (i < n) ? low[b[i] & 0xFF] : 0;
                } while (lc != 0);
                int len = i - start;

                long r0 = getLong(b, start);
                long p0 = (len >= 8) ? r0 : (r0 & ((1L << (8 * len)) - 1));
                long p1 = 0;
                if (len > 8) {
                    long r1 = getLong(b, start + 8);
                    int rem = len - 8;
                    p1 = (rem >= 8) ? r1 : (r1 & ((1L << (8 * rem)) - 1));
                }

                int id = intern(p0, p1, len, start);
                W++;
                if (prev >= 0) {
                    if (np == pairs.length)
                        pairs = Arrays.copyOf(pairs, pairs.length + (pairs.length >> 1) + 64);
                    pairs[np++] = ((long) prev << 32) | (id & 0xFFFFFFFFL);
                    T++;
                }
                prev = id;
            } else {
                int c = b[i];
                if (c == '.' || c == '!' || c == '?') prev = -1;
                i++;
            }
        }

        long[] keys = pairs;
        if (np > 1) {
            long orAll = 0;
            for (int k = 0; k < np; k++) orAll |= pairs[k];
            long[] tmp = new long[np];
            long[] src = pairs, dst = tmp;
            int[] cnt = new int[256];
            for (int pass = 0; pass < 8; pass++) {
                int shift = pass * 8;
                if (((orAll >>> shift) & 0xFFL) == 0) continue;
                Arrays.fill(cnt, 0);
                for (int k = 0; k < np; k++)
                    cnt[(int) ((src[k] >>> shift) & 0xFF)]++;
                int sum = 0;
                for (int d = 0; d < 256; d++) {
                    int c = cnt[d];
                    cnt[d] = sum;
                    sum += c;
                }
                for (int k = 0; k < np; k++) {
                    long key = src[k];
                    dst[cnt[(int) ((key >>> shift) & 0xFF)]++] = key;
                }
                long[] t = src;
                src = dst;
                dst = t;
            }
            keys = src;
        }

        int[] bestC = new int[20];
        int[] bestA = new int[20];
        int[] bestB = new int[20];
        int bn = 0;
        long distinct = 0;

        int k = 0;
        while (k < np) {
            int j = k + 1;
            long key = keys[k];
            while (j < np && keys[j] == key) j++;
            int c = j - k;
            int a = (int) (key >>> 32);
            int b2 = (int) (key & 0xFFFFFFFFL);
            if (bn < 20) {
                bestC[bn] = c; bestA[bn] = a; bestB[bn] = b2;
                int idx = bn++;
                while (idx > 0) {
                    int p = (idx - 1) >> 1;
                    if (worse(bestC[idx], bestA[idx], bestB[idx],
                              bestC[p], bestA[p], bestB[p])) {
                        int t = bestC[idx]; bestC[idx] = bestC[p]; bestC[p] = t;
                        t = bestA[idx]; bestA[idx] = bestA[p]; bestA[p] = t;
                        t = bestB[idx]; bestB[idx] = bestB[p]; bestB[p] = t;
                        idx = p;
                    } else break;
                }
            } else if (better(c, a, b2, bestC[0], bestA[0], bestB[0])) {
                bestC[0] = c; bestA[0] = a; bestB[0] = b2;
                int idx = 0;
                for (;;) {
                    int l = 2 * idx + 1, r = l + 1, w = idx;
                    if (l < bn && worse(bestC[l], bestA[l], bestB[l],
                                        bestC[w], bestA[w], bestB[w])) w = l;
                    if (r < bn && worse(bestC[r], bestA[r], bestB[r],
                                        bestC[w], bestA[w], bestB[w])) w = r;
                    if (w == idx) break;
                    int t = bestC[idx]; bestC[idx] = bestC[w]; bestC[w] = t;
                    t = bestA[idx]; bestA[idx] = bestA[w]; bestA[w] = t;
                    t = bestB[idx]; bestB[idx] = bestB[w]; bestB[w] = t;
                    idx = w;
                }
            }
            distinct++;
            k = j;
        }

        for (int q = 1; q < bn; q++) {
            int cq = bestC[q], aq = bestA[q], bq = bestB[q];
            int r = q - 1;
            while (r >= 0 && better(cq, aq, bq, bestC[r], bestA[r], bestB[r])) {
                bestC[r + 1] = bestC[r]; bestA[r + 1] = bestA[r]; bestB[r + 1] = bestB[r];
                r--;
            }
            bestC[r + 1] = cq; bestA[r + 1] = aq; bestB[r + 1] = bq;
        }

        StringBuilder sb = new StringBuilder(512);
        sb.append("words ").append(W).append('\n');
        sb.append("pairs ").append(T).append('\n');
        sb.append("distinct ").append(distinct).append('\n');
        for (int q = 0; q < bn; q++) {
            sb.append(bestC[q]).append(' ');
            sb.append(new String(b, wOff[bestA[q]], wLen[bestA[q]], StandardCharsets.US_ASCII));
            sb.append(' ');
            sb.append(new String(b, wOff[bestB[q]], wLen[bestB[q]], StandardCharsets.US_ASCII));
            sb.append('\n');
        }
        System.out.write(sb.toString().getBytes(StandardCharsets.US_ASCII));
        System.out.flush();
    }
}
