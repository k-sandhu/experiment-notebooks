import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    static final long PM = 0x9E3779B97F4A7C15L;
    static final long EMPTY = -1L;
    static final int NONE = -1;
    static final int BATCH = 512;

    static byte[] data;

    // words
    static int[] wstart = new int[1 << 15], wlen = new int[1 << 15];
    static long[] whash = new long[1 << 15];
    static int wcount = 0;
    static int[] wtab = new int[1 << 16];  // id+1, 0 = empty
    static int wmask = (1 << 16) - 1;

    // pairs: interleaved [key, count]
    static long[] ptab;
    static int pmask;       // slot mask
    static int pshift;
    static long distinct = 0, tcount = 0;

    static void growWords() {
        int ncap = wtab.length * 2;
        int[] nt = new int[ncap];
        int nmask = ncap - 1;
        for (int id = 0; id < wcount; id++) {
            int p = (int) (whash[id] >>> 20) & nmask;
            while (nt[p] != 0) p = (p + 1) & nmask;
            nt[p] = id + 1;
        }
        wtab = nt;
        wmask = nmask;
    }

    static int lookupWord(int start, int len, long h) {
        final byte[] d = data;
        int p = (int) (h >>> 20) & wmask;
        for (;;) {
            int e = wtab[p];
            if (e == 0) break;
            int id = e - 1;
            if (whash[id] == h && wlen[id] == len) {
                int t = wstart[id];
                int k = 0;
                while (k < len && ((d[start + k] ^ d[t + k]) | 0x20) == 0x20) k++;
                if (k == len) return id;
            }
            p = (p + 1) & wmask;
        }
        int id = wcount++;
        if (id == wstart.length) {
            wstart = java.util.Arrays.copyOf(wstart, id * 2);
            wlen = java.util.Arrays.copyOf(wlen, id * 2);
            whash = java.util.Arrays.copyOf(whash, id * 2);
        }
        wstart[id] = start;
        wlen[id] = len;
        whash[id] = h;
        wtab[p] = id + 1;
        if (wcount * 2 > wtab.length) growWords();
        return id;
    }

    static void growPairs() {
        int ncap = (ptab.length >> 1) * 2;
        int nshift = pshift - 1;
        long[] nt = new long[ncap * 2];
        for (int i = 0; i < ncap; i++) nt[2 * i] = EMPTY;
        int nmask = ncap - 1;
        long[] ot = ptab;
        for (int q = 0; q < ot.length; q += 2) {
            long key = ot[q];
            if (key == EMPTY) continue;
            int p = (int) ((key * PM) >>> nshift);
            while (nt[2 * p] != EMPTY) p = (p + 1) & nmask;
            nt[2 * p] = key;
            nt[2 * p + 1] = ot[q + 1];
        }
        ptab = nt;
        pshift = nshift;
        pmask = nmask;
    }

    static long sink;

    // ids[0] is the previous word (or NONE); NONE marks a sentence end.
    static void flush(int[] ids, int cnt) {
        long acc = 0;
        long[] tab = ptab;
        int sh = pshift;
        for (int k = 1; k <= cnt; k++) {
            long key = ((long) ids[k - 1] << 32) | (ids[k] & 0xFFFFFFFFL);
            acc += tab[(int) ((key * PM) >>> sh) << 1];
        }
        sink += acc;
        for (int k = 1; k <= cnt; k++) {
            int a = ids[k - 1], b = ids[k];
            if (a == NONE || b == NONE) continue;
            tcount++;
            long key = ((long) a << 32) | b;
            long[] t = ptab;
            int p = (int) ((key * PM) >>> pshift);
            for (;;) {
                long kk = t[2 * p];
                if (kk == key) {
                    t[2 * p + 1]++;
                    break;
                }
                if (kk == EMPTY) {
                    t[2 * p] = key;
                    t[2 * p + 1] = 1;
                    distinct++;
                    if (distinct * 10 > (long) (t.length >> 1) * 7) growPairs();
                    break;
                }
                p = (p + 1) & pmask;
            }
        }
    }

    static int cmpWords(int x, int y) {
        if (x == y) return 0;
        int sx = wstart[x], sy = wstart[y], lx = wlen[x], ly = wlen[y];
        int n = Math.min(lx, ly);
        for (int i = 0; i < n; i++) {
            int cx = data[sx + i] | 0x20, cy = data[sy + i] | 0x20;
            if (cx != cy) return cx < cy ? -1 : 1;
        }
        return Integer.compare(lx, ly);
    }

    static boolean better(long cx, int ax, int bx, long cy, int ay, int by) {
        if (cx != cy) return cx > cy;
        int c = cmpWords(ax, ay);
        if (c != 0) return c < 0;
        return cmpWords(bx, by) < 0;
    }

    static void appendWord(StringBuilder sb, int id) {
        int s = wstart[id], l = wlen[id];
        for (int i = 0; i < l; i++) sb.append((char) (data[s + i] | 0x20));
    }

    public static void main(String[] args) throws IOException {
        byte[] raw = Files.readAllBytes(Paths.get(args[0]));
        int n = raw.length;
        data = java.util.Arrays.copyOf(raw, n + 1);
        raw = null;
        data[n] = '\n';
        final byte[] d = data;

        int pcap = 1 << 16;
        while (pcap < n / 12 && pcap < (1 << 27)) pcap <<= 1;
        pshift = 64 - Integer.numberOfTrailingZeros(pcap);
        pmask = pcap - 1;
        ptab = new long[pcap * 2];
        for (int i = 0; i < pcap; i++) ptab[2 * i] = EMPTY;

        long W = 0;
        int[] ids = new int[BATCH + 1];
        ids[0] = NONE;
        int cnt = 0;
        int i = 0;
        while (i < n) {
            int c = d[i];
            int lc = c | 0x20;
            if (lc >= 'a' && lc <= 'z') {
                int st = i;
                long h = 0xcbf29ce484222325L;
                do {
                    h = (h ^ lc) * 0x100000001b3L;
                    lc = d[++i] | 0x20;
                } while (lc >= 'a' && lc <= 'z');
                h ^= h >>> 29;
                h *= PM;
                h ^= h >>> 32;
                ids[++cnt] = lookupWord(st, i - st, h);
                W++;
                if (cnt == BATCH) {
                    flush(ids, cnt);
                    ids[0] = ids[BATCH];
                    cnt = 0;
                }
            } else {
                if (c == '.' || c == '!' || c == '?') {
                    if (ids[cnt] != NONE) {
                        ids[++cnt] = NONE;
                        if (cnt == BATCH) {
                            flush(ids, cnt);
                            ids[0] = ids[BATCH];
                            cnt = 0;
                        }
                    }
                }
                i++;
            }
        }
        flush(ids, cnt);

        long[] tc = new long[21];
        int[] ta = new int[21], tb = new int[21];
        int nt = 0;
        long[] t = ptab;
        for (int q = 0; q < t.length; q += 2) {
            long key = t[q];
            if (key == EMPTY) continue;
            long count = t[q + 1];
            if (nt == 20 && count < tc[19]) continue;
            int a = (int) (key >>> 32), b = (int) key;
            if (nt == 20 && !better(count, a, b, tc[19], ta[19], tb[19])) continue;
            int j = nt < 20 ? nt++ : 19;
            while (j > 0 && better(count, a, b, tc[j - 1], ta[j - 1], tb[j - 1])) {
                tc[j] = tc[j - 1]; ta[j] = ta[j - 1]; tb[j] = tb[j - 1];
                j--;
            }
            tc[j] = count; ta[j] = a; tb[j] = b;
        }

        StringBuilder sb = new StringBuilder();
        sb.append("words ").append(W).append("\npairs ").append(tcount).append("\ndistinct ").append(distinct).append('\n');
        for (int k = 0; k < nt; k++) {
            sb.append(tc[k]).append(' ');
            appendWord(sb, ta[k]);
            sb.append(' ');
            appendWord(sb, tb[k]);
            sb.append('\n');
        }
        PrintStream out = new PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), false);
        out.write(sb.toString().getBytes(java.nio.charset.StandardCharsets.US_ASCII));
        out.flush();
        if (sink == 42) System.err.println();
    }
}
