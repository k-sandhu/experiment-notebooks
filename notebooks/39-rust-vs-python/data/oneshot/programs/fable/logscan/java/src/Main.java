import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;

public class Main {
    private static final VarHandle LONG =
            MethodHandles.byteArrayViewVarHandle(long[].class, ByteOrder.LITTLE_ENDIAN);

    private static final int PAD = 64;

    private static final String TS = "dddd-dd-ddTdd:dd:dd.dddZ";

    private static final long M0 = tsConst(0, 0), E0 = tsConst(0, 1), L0 = tsConst(0, 2), S0 = tsConst(0, 3), C0 = tsConst(0, 4);
    private static final long M1 = tsConst(1, 0), E1 = tsConst(1, 1), L1 = tsConst(1, 2), S1 = tsConst(1, 3), C1 = tsConst(1, 4);
    private static final long M2 = tsConst(2, 0), E2 = tsConst(2, 1), L2 = tsConst(2, 2), S2 = tsConst(2, 3), C2 = tsConst(2, 4);

    private static final long GET = lit("GET "), PUT = lit("PUT "), POST = lit("POST "),
            PATCH = lit("PATCH "), DELETE = lit("DELETE ");

    private static final long ONES = 0x0101010101010101L;
    private static final long HIGHS = 0x8080808080808080L;
    private static final long QUOTES = 0x2222222222222222L;
    private static final long NLS = 0x0A0A0A0A0A0A0A0AL;

    private static final byte[] CLS = new byte[256];

    static {
        for (int c = '0'; c <= '9'; c++) CLS[c] = 1;
        for (int c = 'a'; c <= 'z'; c++) CLS[c] = 2;
        for (int c = 'A'; c <= 'Z'; c++) CLS[c] = 2;
        CLS['_'] = 2;
        CLS['-'] = 2;
    }

    private static long tsConst(int word, int kind) {
        long r = 0;
        for (int i = 0; i < 8; i++) {
            char ch = TS.charAt(word * 8 + i);
            boolean d = ch == 'd';
            long b;
            switch (kind) {
                case 0: b = d ? 0xF0 : 0xFF; break;
                case 1: b = d ? 0x30 : ch; break;
                case 2: b = d ? 0x0F : 0; break;
                case 3: b = d ? 0x06 : 0; break;
                default: b = d ? 0x10 : 0; break;
            }
            r |= b << (8 * i);
        }
        return r;
    }

    private static long lit(String s) {
        long r = 0;
        for (int i = 0; i < s.length(); i++) r |= ((long) s.charAt(i)) << (8 * i);
        return r;
    }

    // ---- state ----
    private static long lines, malformed;
    private static final long[] statusCount = new long[10];

    private static int[] table = new int[1 << 10];
    private static long[] hashes = new long[256];
    private static long[][] keys = new long[256][];
    private static int[] keyLen = new int[256];
    private static int[] counts = new int[256];
    private static int nTemplates;

    private static int[] latId = new int[1 << 20];
    private static long[] latVal = new long[1 << 20];
    private static int nLat;

    private static int lookup(byte[] tb, int t) {
        LONG.set(tb, t, 0L);
        int nw = (t + 7) >>> 3;
        long h = 0;
        for (int i = 0; i < nw; i++) {
            h = (h ^ (long) LONG.get(tb, i << 3)) * 0x9E3779B97F4A7C15L;
            h ^= h >>> 32;
        }
        int[] tab = table;
        int mask = tab.length - 1;
        int slot = (int) h & mask;
        for (;;) {
            int id = tab[slot] - 1;
            if (id < 0) return insert(tb, t, nw, h, slot);
            if (hashes[id] == h) {
                long[] kw = keys[id];
                if (kw.length == nw) {
                    int i = 0;
                    while (i < nw && kw[i] == (long) LONG.get(tb, i << 3)) i++;
                    if (i == nw) return id;
                }
            }
            slot = (slot + 1) & mask;
        }
    }

    private static int insert(byte[] tb, int t, int nw, long h, int slot) {
        int id = nTemplates;
        if (id == keys.length) {
            int nl = id * 2;
            keys = Arrays.copyOf(keys, nl);
            hashes = Arrays.copyOf(hashes, nl);
            keyLen = Arrays.copyOf(keyLen, nl);
            counts = Arrays.copyOf(counts, nl);
        }
        long[] kw = new long[nw];
        for (int i = 0; i < nw; i++) kw[i] = (long) LONG.get(tb, i << 3);
        keys[id] = kw;
        hashes[id] = h;
        keyLen[id] = t;
        counts[id] = 0;
        table[slot] = id + 1;
        nTemplates = id + 1;
        if (nTemplates * 2 > table.length) rehash();
        return id;
    }

    private static void rehash() {
        int[] nt = new int[table.length * 2];
        int mask = nt.length - 1;
        for (int id = 0; id < nTemplates; id++) {
            int s = (int) hashes[id] & mask;
            while (nt[s] != 0) s = (s + 1) & mask;
            nt[s] = id + 1;
        }
        table = nt;
    }

    private static void growLat() {
        int n = latId.length;
        int nl = n < (1 << 30) ? n * 2 : Integer.MAX_VALUE - 8;
        latId = Arrays.copyOf(latId, nl);
        latVal = Arrays.copyOf(latVal, nl);
    }

    private static void record(int id, long lat) {
        int n = nLat;
        if (n == latId.length) growLat();
        latId[n] = id;
        latVal[n] = lat;
        nLat = n + 1;
        counts[id]++;
    }

    // buf[end-1] == '\n'; buf has at least PAD readable bytes after end
    private static void process(byte[] buf, byte[] tb, int end) {
        final byte[] cls = CLS;
        final long[] sc = statusCount;
        long nl = 0, mal = 0;
        int p = 0;
        while (p < end) {
            nl++;
            int q = p;
            bad:
            {
                long w0 = (long) LONG.get(buf, p);
                long w1 = (long) LONG.get(buf, p + 8);
                long w2 = (long) LONG.get(buf, p + 16);
                if ((((w0 & M0) ^ E0) | ((w1 & M1) ^ E1) | ((w2 & M2) ^ E2)
                        | (((w0 & L0) + S0) & C0) | (((w1 & L1) + S1) & C1) | (((w2 & L2) + S2) & C2)) != 0
                        || buf[p + 24] != ' ') {
                    break bad;
                }
                q = p + 25;
                byte c = buf[q];
                if (c < 'a' || c > 'z') break bad;
                do {
                    c = buf[++q];
                } while (c >= 'a' && c <= 'z');
                if (c != '-') break bad;
                c = buf[++q];
                if (c < '0' || c > '9') break bad;
                do {
                    c = buf[++q];
                } while (c >= '0' && c <= '9');
                if (c != ' ') break bad;
                q++;

                long w = (long) LONG.get(buf, q);
                long w4 = w & 0xFFFFFFFFL;
                if (w4 == GET || w4 == PUT) q += 4;
                else if ((w & 0xFFFFFFFFFFL) == POST) q += 5;
                else if ((w & 0xFFFFFFFFFFFFL) == PATCH) q += 6;
                else if ((w & 0xFFFFFFFFFFFFFFL) == DELETE) q += 7;
                else break bad;

                if (buf[q] != '/') break bad;
                int t = 0;
                do {
                    tb[t++] = '/';
                    int segStart = t;
                    int acc = 0, k;
                    while ((k = cls[(c = buf[++q]) & 0xFF]) != 0) {
                        tb[t++] = c;
                        acc |= k;
                    }
                    if (acc == 1) {
                        tb[segStart] = '{';
                        tb[segStart + 1] = 'i';
                        tb[segStart + 2] = 'd';
                        tb[segStart + 3] = '}';
                        t = segStart + 4;
                    }
                } while (c == '/');

                if (c == '?') {
                    do {
                        c = buf[++q];
                    } while (c != ' ' && c != '\n');
                }
                if (c != ' ') break bad;

                int s1 = buf[q + 1] - '0', s2 = buf[q + 2] - '0', s3 = buf[q + 3] - '0';
                if ((s1 | s2 | s3) < 0 || s1 > 9 || s2 > 9 || s3 > 9 || buf[q + 4] != ' ') break bad;
                q += 5;

                c = buf[q];
                if (c < '0' || c > '9') break bad;
                do {
                    c = buf[++q];
                } while (c >= '0' && c <= '9');
                if (c != 'B' || buf[q + 1] != ' ') break bad;
                q += 2;

                c = buf[q];
                if (c < '0' || c > '9') break bad;
                long lat = 0;
                do {
                    lat = lat * 10 + (c - '0');
                    c = buf[++q];
                } while (c >= '0' && c <= '9');
                if (c != '.') break bad;
                int d = buf[q + 1] - '0';
                if (d < 0 || d > 9 || buf[q + 2] != 'm' || buf[q + 3] != 's'
                        || buf[q + 4] != ' ' || buf[q + 5] != '"') break bad;
                lat = lat * 10 + d;
                q += 6;

                for (;;) {
                    long u = (long) LONG.get(buf, q);
                    long x = u ^ QUOTES;
                    long y = u ^ NLS;
                    long m = (((x - ONES) & ~x) | ((y - ONES) & ~y)) & HIGHS;
                    if (m != 0) {
                        q += Long.numberOfTrailingZeros(m) >>> 3;
                        break;
                    }
                    q += 8;
                }
                if (buf[q] != '"') break bad;
                if (buf[q + 1] != '\n') {
                    q++;
                    break bad;
                }

                sc[s1]++;
                int id = lookup(tb, t);
                record(id, lat);
                p = q + 2;
                continue;
            }
            mal++;
            while (buf[q] != '\n') q++;
            p = q + 1;
        }
        lines += nl;
        malformed += mal;
    }

    private static int cmpKey(int a, int b) {
        long[] x = keys[a], y = keys[b];
        int n = Math.min(x.length, y.length);
        for (int i = 0; i < n; i++) {
            if (x[i] != y[i]) {
                return Long.compareUnsigned(Long.reverseBytes(x[i]), Long.reverseBytes(y[i]));
            }
        }
        return x.length - y.length;
    }

    private static boolean better(int a, int b) {
        int ca = counts[a], cb = counts[b];
        if (ca != cb) return ca > cb;
        return cmpKey(a, b) < 0;
    }

    private static void fmt(StringBuilder sb, long v) {
        sb.append(v / 10).append('.').append(v % 10);
    }

    public static void main(String[] args) throws IOException {
        int cap = 1 << 18;
        byte[] buf = new byte[cap + PAD];
        byte[] tb = new byte[3 * cap + PAD];

        try (FileChannel ch = FileChannel.open(Paths.get(args[0]), StandardOpenOption.READ)) {
            ByteBuffer bb = ByteBuffer.wrap(buf);
            int carry = 0;
            for (;;) {
                if (carry == cap) {
                    cap *= 2;
                    buf = Arrays.copyOf(buf, cap + PAD);
                    tb = new byte[3 * cap + PAD];
                    bb = ByteBuffer.wrap(buf);
                }
                bb.limit(cap);
                bb.position(carry);
                int n = ch.read(bb);
                if (n < 0) break;
                if (n == 0) continue;
                int filled = carry + n;
                int e = filled;
                while (e > carry && buf[e - 1] != '\n') e--;
                if (e == carry) {
                    carry = filled;
                    continue;
                }
                process(buf, tb, e);
                carry = filled - e;
                if (carry > 0) System.arraycopy(buf, e, buf, 0, carry);
            }
        }

        StringBuilder sb = new StringBuilder(2048);
        sb.append("lines ").append(lines).append('\n');
        sb.append("malformed ").append(malformed).append('\n');
        for (int s = 0; s < 10; s++) {
            if (statusCount[s] > 0) {
                sb.append("status ").append(s).append("xx ").append(statusCount[s]).append('\n');
            }
        }

        int T = nTemplates;
        int[] top = new int[10];
        int nt = 0;
        for (int id = 0; id < T; id++) {
            if (nt == 10) {
                if (!better(id, top[9])) continue;
            } else {
                nt++;
            }
            int pos = nt - 1;
            while (pos > 0 && better(id, top[pos - 1])) {
                top[pos] = top[pos - 1];
                pos--;
            }
            top[pos] = id;
        }

        if (nt > 0) {
            int[] rank = new int[T];
            Arrays.fill(rank, -1);
            long[][] vals = new long[nt][];
            int[] fillc = new int[nt];
            for (int r = 0; r < nt; r++) {
                rank[top[r]] = r;
                vals[r] = new long[counts[top[r]]];
            }
            final int[] ids = latId;
            final long[] lv = latVal;
            final int total = nLat;
            for (int i = 0; i < total; i++) {
                int r = rank[ids[i]];
                if (r >= 0) vals[r][fillc[r]++] = lv[i];
            }

            for (int r = 0; r < nt; r++) {
                int id = top[r];
                long[] a = vals[r];
                int n = a.length;
                long max = Long.MIN_VALUE, min = Long.MAX_VALUE;
                for (int i = 0; i < n; i++) {
                    long v = a[i];
                    if (v > max) max = v;
                    if (v < min) min = v;
                }
                int k50 = (n + 1) / 2;
                int k95 = (int) ((95L * n + 99) / 100);
                long p50, p95;
                if (min >= 0 && max < 4L * n + 65536) {
                    int[] hist = new int[(int) max + 1];
                    for (int i = 0; i < n; i++) hist[(int) a[i]]++;
                    int cum = 0;
                    int v = 0;
                    while ((cum += hist[v]) < k50) v++;
                    p50 = v;
                    while (cum < k95) cum += hist[++v];
                    p95 = v;
                } else {
                    Arrays.sort(a);
                    p50 = a[k50 - 1];
                    p95 = a[k95 - 1];
                }

                sb.append("path ");
                long[] kw = keys[id];
                int len = keyLen[id];
                for (int i = 0; i < len; i++) {
                    sb.append((char) ((kw[i >>> 3] >>> ((i & 7) << 3)) & 0xFF));
                }
                sb.append(' ').append(n).append(' ');
                fmt(sb, p50);
                sb.append(' ');
                fmt(sb, p95);
                sb.append(' ');
                fmt(sb, max);
                sb.append('\n');
            }
        }

        byte[] out = sb.toString().getBytes(StandardCharsets.ISO_8859_1);
        try (FileOutputStream fos = new FileOutputStream(FileDescriptor.out)) {
            fos.write(out, 0, out.length);
            fos.flush();
        }
    }
}
