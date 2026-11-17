// Word pairs: count adjacent word pairs within sentences, report the top 20.
//
// 1. Scan the input once. Words are found 8 bytes at a time (SWAR) and interned
//    to dense ids by an open-addressing table whose slots hold the first 8 bytes
//    of the word. The scan records the id sequence, with a flag on each word that
//    starts a sentence, and counts pairs per first word.
// 2. Counting-sort the pairs by first word (second words only).
// 3. For each first word, count its second words in a dense counter array that
//    stays in cache, and keep the 20 best pairs. Ties are broken by each word's
//    lexicographic rank, so the selection compares integers only.
import java.io.IOException;
import java.io.PrintStream;
import java.io.FileOutputStream;
import java.io.FileDescriptor;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;

public class Main {
    static final long ONES = 0x0101010101010101L;
    static final long HIGH = 0x8080808080808080L;
    static final long FOLD = 0x2020202020202020L;
    static final int START = 0x80000000; // flag: word starts a sentence

    static final VarHandle LONGS = MethodHandles.byteArrayViewVarHandle(long[].class, ByteOrder.LITTLE_ENDIAN);

    // 1 = letter, 2 = sentence end, 0 = other.
    static final byte[] CLASS = new byte[256];
    static {
        for (int c = 'a'; c <= 'z'; c++) {
            CLASS[c] = 1;
            CLASS[c - 32] = 1;
        }
        CLASS['.'] = 2;
        CLASS['!'] = 2;
        CLASS['?'] = 2;
    }

    static byte[] buf;
    // Word table: slot s holds prefix (first 8 lower-case bytes, zero padded) at
    // 2s and (hash << 32 | id) at 2s+1; id 0 = empty.
    static long[] slots;
    static int bits;
    static int mask;
    static int[] wOff = new int[1 << 16];
    static int[] wLen = new int[1 << 16];
    static int nextId = 1;

    // High bit set in each byte of v (bytes < 0x80) that is an ASCII letter.
    static long letterMask(long v) {
        long x = v | FOLD;
        long geA = x + 0x1FL * ONES; // >= 0x80 iff x >= 'a'
        long gtZ = x + 0x05L * ONES; // >= 0x80 iff x > 'z'
        return geA & ~gtZ & HIGH;
    }

    // Mask covering the low n bytes.
    static long lowBytes(int n) {
        return n >= 8 ? -1L : (1L << (8 * n)) - 1;
    }

    static long load(int i) {
        return (long) LONGS.get(buf, i);
    }

    static void resize(int b) {
        long[] old = slots;
        slots = new long[2 << b];
        bits = b;
        mask = (1 << b) - 1;
        if (old == null) return;
        for (int j = 0; j < old.length; j += 2) {
            long hi = old[j + 1];
            if ((int) hi == 0) continue;
            int i = (int) (hi >>> 32) >>> (32 - b);
            while ((int) slots[2 * i + 1] != 0) i = (i + 1) & mask;
            slots[2 * i] = old[j];
            slots[2 * i + 1] = hi;
        }
    }

    // Bytes 8..n at a (lower case) and b (any case) are equal, ignoring case.
    static boolean tailEq(int a, int b, int n) {
        for (int j = 8; j < n; j += 8) {
            long m = lowBytes(n - j);
            if (((load(a + j) ^ (load(b + j) | FOLD)) & m) != 0) return false;
        }
        return true;
    }

    static int intern(int start, int n, long prefix, int h) {
        long[] sl = slots;
        int i = h >>> (32 - bits);
        long tag = (long) h << 32;
        for (;;) {
            long hi = sl[2 * i + 1];
            int id = (int) hi;
            if (id == 0) break;
            if ((hi & 0xFFFFFFFF00000000L) == tag && sl[2 * i] == prefix
                    && (n < 8 || (wLen[id] == n && tailEq(wOff[id], start, n))))
                return id;
            i = (i + 1) & mask;
        }
        return add(start, n, prefix, h, i);
    }

    static int add(int start, int n, long prefix, int h, int i) {
        int id = nextId++;
        for (int j = start; j < start + n; j++) buf[j] |= 0x20; // lower-case the stored copy
        if (id == wOff.length) {
            wOff = Arrays.copyOf(wOff, id * 2);
            wLen = Arrays.copyOf(wLen, id * 2);
        }
        wOff[id] = start;
        wLen[id] = n;
        slots[2 * i] = prefix;
        slots[2 * i + 1] = ((long) h << 32) | id;
        if ((long) id * 2 > (slots.length >> 1)) resize(bits + 1);
        return id;
    }

    static int[] seq;
    static int nseq;
    static int[] deg = new int[1 << 16]; // pairs per first word
    static long totalPairs;

    static void scan(int n) {
        byte[] b = buf;
        byte[] cls = CLASS;
        int[] sq = seq;
        int ns = 0;
        long pairs = 0;
        int prev = 0; // previous word id in the current sentence, 0 = none
        int i = 0;
        while (i < n) {
            int k = cls[b[i]];
            if (k != 1) {
                if (k == 2) prev = 0;
                i++;
                continue;
            }
            // Word starting at i: fold case and hash it 8 bytes at a time.
            int start = i;
            long v = load(i);
            long nl = ~letterMask(v) & HIGH;
            long prefix, h;
            if (nl != 0) {
                int w = Long.numberOfTrailingZeros(nl) >>> 3;
                prefix = (v | FOLD) & lowBytes(w);
                h = prefix * 0x9E3779B97F4A7C15L;
                i += w;
            } else {
                prefix = v | FOLD;
                h = prefix * 0x9E3779B97F4A7C15L;
                i += 8;
                for (;;) {
                    v = load(i);
                    nl = ~letterMask(v) & HIGH;
                    if (nl != 0) {
                        int w = Long.numberOfTrailingZeros(nl) >>> 3;
                        if (w != 0) {
                            h = (h ^ ((v | FOLD) & lowBytes(w))) * 0xC2B2AE3D27D4EB4FL;
                            i += w;
                        }
                        break;
                    }
                    h = (h ^ (v | FOLD)) * 0xC2B2AE3D27D4EB4FL;
                    i += 8;
                }
            }
            int wl = i - start;
            h ^= h >>> 31;
            h += wl;
            h *= 0xBF58476D1CE4E5B9L;
            int id = intern(start, wl, prefix, (int) (h >>> 32));
            if (id == deg.length) deg = Arrays.copyOf(deg, id * 2);
            if (ns == sq.length) sq = seq = Arrays.copyOf(sq, (int) Math.min((long) ns * 3 / 2 + 16, n / 2 + 2));
            if (prev != 0) {
                deg[prev]++;
                pairs++;
                sq[ns++] = id;
            } else {
                sq[ns++] = id | START;
            }
            prev = id;
        }
        nseq = ns;
        totalPairs = pairs;
    }

    // True if (c1, r1, s1) ranks before (c2, r2, s2) in the output order.
    static boolean better(int c1, int r1, int s1, int c2, int r2, int s2) {
        if (c1 != c2) return c1 > c2;
        if (r1 != r2) return r1 < r2;
        return s1 < s2;
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: Main INPUT");
            System.exit(1);
        }
        int n;
        try (FileChannel ch = FileChannel.open(Path.of(args[0]), StandardOpenOption.READ)) {
            long size = ch.size();
            buf = new byte[(int) size + 16]; // zero padding: non-letters, safe 8-byte loads
            ByteBuffer bb = ByteBuffer.wrap(buf, 0, (int) size);
            while (bb.hasRemaining() && ch.read(bb) >= 0) {
            }
            n = bb.position();
        }

        resize(16);
        seq = new int[n / 5 + 16]; // grows on demand; zero-filling is not free in Java
        scan(n);
        long totalWords = nseq;
        int nw = nextId - 1;

        // Bucket the second word of every pair by its first word.
        int[] pos = new int[nw + 2];
        for (int id = 1; id <= nw; id++) pos[id + 1] = pos[id] + deg[id];
        int[] fill = pos.clone();
        int[] second = new int[(int) totalPairs + 1];
        int[] sq = seq;
        for (int j = 1; j < nseq; j++) {
            int x = sq[j];
            if ((x & START) == 0) second[fill[sq[j - 1] & ~START]++] = x;
        }
        seq = null;

        // Lexicographic rank of each word id.
        byte[] b = buf;
        int[] off = wOff, len = wLen;
        Integer[] order = new Integer[nw];
        for (int id = 0; id < nw; id++) order[id] = id + 1;
        Arrays.sort(order, (x, y) -> Arrays.compare(b, off[x], off[x] + len[x], b, off[y], off[y] + len[y]));
        int[] rank = new int[nw + 1];
        for (int r = 0; r < nw; r++) rank[order[r]] = r;

        // Count second words per first word; keep the 20 best pairs.
        final int K = 20;
        int[] tc = new int[K], tr1 = new int[K], tr2 = new int[K], ta = new int[K], tb = new int[K];
        int nt = 0;
        long distinct = 0;
        int[] cnt = new int[nw + 1];
        for (int a = 1; a <= nw; a++) {
            int lo = pos[a], hi = pos[a + 1];
            if (lo == hi) continue;
            for (int j = lo; j < hi; j++) cnt[second[j]]++;
            int ra = rank[a];
            for (int j = lo; j < hi; j++) {
                int s = second[j];
                int c = cnt[s];
                if (c == 0) continue;
                cnt[s] = 0;
                distinct++;
                if (nt == K && c < tc[K - 1]) continue;
                int rs = rank[s];
                if (nt == K && !better(c, ra, rs, tc[K - 1], tr1[K - 1], tr2[K - 1])) continue;
                int p = nt < K ? nt++ : K - 1;
                while (p > 0 && better(c, ra, rs, tc[p - 1], tr1[p - 1], tr2[p - 1])) {
                    tc[p] = tc[p - 1];
                    tr1[p] = tr1[p - 1];
                    tr2[p] = tr2[p - 1];
                    ta[p] = ta[p - 1];
                    tb[p] = tb[p - 1];
                    p--;
                }
                tc[p] = c;
                tr1[p] = ra;
                tr2[p] = rs;
                ta[p] = a;
                tb[p] = s;
            }
        }

        StringBuilder sb = new StringBuilder(4096);
        sb.append("words ").append(totalWords).append('\n');
        sb.append("pairs ").append(totalPairs).append('\n');
        sb.append("distinct ").append(distinct).append('\n');
        for (int t = 0; t < nt; t++) {
            sb.append(tc[t]).append(' ');
            sb.append(new String(b, off[ta[t]], len[ta[t]], StandardCharsets.ISO_8859_1)).append(' ');
            sb.append(new String(b, off[tb[t]], len[tb[t]], StandardCharsets.ISO_8859_1)).append('\n');
        }
        try (PrintStream out = new PrintStream(new FileOutputStream(FileDescriptor.out), false)) {
            out.write(sb.toString().getBytes(StandardCharsets.ISO_8859_1));
            out.flush();
        }
    }
}
