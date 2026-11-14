import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

public class Main {

    // Mutable (scratch) or owned template key: bytes in a[0..len)
    static final class Key {
        byte[] a;
        int len;

        Key(byte[] a, int len) {
            this.a = a;
            this.len = len;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (!(o instanceof Key k)) return false;
            if (k.len != len) return false;
            byte[] x = a, y = k.a;
            for (int i = 0; i < len; i++) if (x[i] != y[i]) return false;
            return true;
        }

        @Override
        public int hashCode() {
            byte[] x = a;
            int h = 0;
            for (int i = 0; i < len; i++) h = h * 31 + (x[i] & 0xff);
            return h;
        }
    }

    static final class Agg {
        long count;
        long[] lats = new long[16];
        int n;

        void add(long v) {
            if (n == lats.length) lats = Arrays.copyOf(lats, n << 1);
            lats[n++] = v;
        }
    }

    static byte[] scratch = new byte[512];
    static Key lookupKey = new Key(scratch, 0);
    static int parsedCls;
    static long parsedLat;

    static final long NL_MASK = 0x0A0A0A0A0A0A0A0AL;

    // SWAR search for '\n' in buf[from..n); returns index or -1
    static int findNl(byte[] buf, int from, int n) {
        int p = from;
        while (p + 8 <= n) {
            long w = (buf[p] & 0xffL)
                | (buf[p + 1] & 0xffL) << 8
                | (buf[p + 2] & 0xffL) << 16
                | (buf[p + 3] & 0xffL) << 24
                | (buf[p + 4] & 0xffL) << 32
                | (buf[p + 5] & 0xffL) << 40
                | (buf[p + 6] & 0xffL) << 48
                | (buf[p + 7] & 0xffL) << 56;
            long x = w ^ NL_MASK;
            long m = (x - 0x0101010101010101L) & ~x & 0x8080808080808080L;
            if (m != 0) {
                int off = Long.numberOfTrailingZeros(m) >>> 3;
                return p + off;
            }
            p += 8;
        }
        while (p < n) {
            if (buf[p] == '\n') return p;
            p++;
        }
        return -1;
    }

    public static void main(String[] args) throws IOException {
        byte[] buf = Files.readAllBytes(Paths.get(args[0]));
        int n = buf.length;

        long lines = 0, malformed = 0;
        long[] statusCnt = new long[10];
        HashMap<Key, Agg> aggs = new HashMap<>(256);

        int i = 0;
        while (i < n) {
            int j = findNl(buf, i, n);
            if (j < 0) j = n;
            lines++;
            if (parseLine(buf, i, j)) {
                statusCnt[parsedCls]++;
                Key k = lookupKey;
                Agg a = aggs.get(k);
                if (a == null) {
                    byte[] cp = Arrays.copyOf(scratch, k.len);
                    a = new Agg();
                    a.count = 1;
                    a.lats[0] = parsedLat;
                    a.n = 1;
                    aggs.put(new Key(cp, k.len), a);
                } else {
                    a.count++;
                    a.add(parsedLat);
                }
            } else {
                malformed++;
            }
            i = j + 1;
        }

        StringBuilder out = new StringBuilder(4096);
        out.append("lines ").append(lines).append('\n');
        out.append("malformed ").append(malformed).append('\n');
        for (int d = 0; d < 10; d++) {
            if (statusCnt[d] == 0) continue;
            out.append("status ").append(d).append("xx ").append(statusCnt[d]).append('\n');
        }
        ArrayList<Key> keys = new ArrayList<>(aggs.size());
        keys.addAll(aggs.keySet());
        keys.sort((x, y) -> {
            Agg ax = aggs.get(x), ay = aggs.get(y);
            if (ax.count != ay.count) return ax.count > ay.count ? -1 : 1;
            return compareKeys(x, y);
        });
        int top = Math.min(10, keys.size());
        for (int t = 0; t < top; t++) {
            Key k = keys.get(t);
            Agg a = aggs.get(k);
            long[] l = Arrays.copyOf(a.lats, a.n);
            Arrays.sort(l);
            int m = l.length;
            out.append("path ").append(new String(k.a, 0, k.len))
               .append(' ').append(a.count)
               .append(' ').append(tenths(l[(50 * m + 99) / 100 - 1]))
               .append(' ').append(tenths(l[(95 * m + 99) / 100 - 1]))
               .append(' ').append(tenths(l[m - 1])).append('\n');
        }
        System.out.print(out);
    }

    static String tenths(long v) {
        return (v / 10) + "." + (v % 10);
    }

    static int compareKeys(Key x, Key y) {
        int lim = Math.min(x.len, y.len);
        byte[] a = x.a, b = y.a;
        for (int i = 0; i < lim; i++) {
            int c = (a[i] & 0xff) - (b[i] & 0xff);
            if (c != 0) return c;
        }
        return x.len - y.len;
    }

    static boolean parseLine(byte[] buf, int s, int e) {
        int p = s;
        if (e - p < 26) return false;
        if (buf[p + 4] != '-' || buf[p + 7] != '-' || buf[p + 10] != 'T' || buf[p + 13] != ':'
                || buf[p + 16] != ':' || buf[p + 19] != '.' || buf[p + 23] != 'Z' || buf[p + 24] != ' ')
            return false;
        for (int idx : TS_DIGITS) if (!isDig(buf[p + idx])) return false;
        p += 25;
        int s0 = p;
        while (p < e && buf[p] >= 'a' && buf[p] <= 'z') p++;
        if (p == s0 || p + 1 >= e || buf[p] != '-') return false;
        p++;
        int d0 = p;
        while (p < e && isDig(buf[p])) p++;
        if (p == d0 || p + 1 >= e || buf[p] != ' ') return false;
        p++;
        // method
        if (e - p >= 4 && buf[p] == 'G' && buf[p + 1] == 'E' && buf[p + 2] == 'T' && buf[p + 3] == ' ') p += 4;
        else if (e - p >= 5 && buf[p] == 'P' && buf[p + 1] == 'O' && buf[p + 2] == 'S' && buf[p + 3] == 'T' && buf[p + 4] == ' ') p += 5;
        else if (e - p >= 4 && buf[p] == 'P' && buf[p + 1] == 'U' && buf[p + 2] == 'T' && buf[p + 3] == ' ') p += 4;
        else if (e - p >= 7 && buf[p] == 'D' && buf[p + 1] == 'E' && buf[p + 2] == 'L' && buf[p + 3] == 'E' && buf[p + 4] == 'T' && buf[p + 5] == 'E' && buf[p + 6] == ' ') p += 7;
        else if (e - p >= 6 && buf[p] == 'P' && buf[p + 1] == 'A' && buf[p + 2] == 'T' && buf[p + 3] == 'C' && buf[p + 4] == 'H' && buf[p + 5] == ' ') p += 6;
        else return false;
        // path
        if (buf[p] != '/') return false;
        int tl = 0;
        int need = ((e - p) << 2) + 16;
        if (scratch.length < need) {
            int cap = scratch.length;
            while (cap < need) cap <<= 1;
            scratch = new byte[cap];
            lookupKey.a = scratch;
        }
        while (true) {
            int segStart = tl;
            while (p < e && isSeg(buf[p])) { scratch[tl++] = buf[p]; p++; }
            boolean allDig = tl > segStart;
            for (int q = segStart; allDig && q < tl; q++) allDig = isDig(scratch[q]);
            if (allDig) {
                tl = segStart;
                scratch[tl++] = '{'; scratch[tl++] = 'i'; scratch[tl++] = 'd'; scratch[tl++] = '}';
            }
            if (p < e && buf[p] == '/') { scratch[tl++] = '/'; p++; continue; }
            break;
        }
        if (p < e && buf[p] == '?') { p++; while (p < e && buf[p] != ' ') p++; }
        if (p + 1 >= e || buf[p] != ' ') return false;
        p++;
        // status
        if (e - p < 4 || !isDig(buf[p]) || !isDig(buf[p + 1]) || !isDig(buf[p + 2])) return false;
        int cls = buf[p] - '0';
        p += 3;
        if (p + 1 >= e || buf[p] != ' ') return false;
        p++;
        // size
        int b0 = p;
        while (p < e && isDig(buf[p])) p++;
        if (p == b0 || e - p < 2 || buf[p] != 'B' || buf[p + 1] != ' ') return false;
        p += 2;
        // latency
        int l0 = p;
        while (p < e && isDig(buf[p])) p++;
        if (p == l0 || e - p < 5 || buf[p] != '.' || !isDig(buf[p + 1]) || buf[p + 2] != 'm' || buf[p + 3] != 's' || buf[p + 4] != ' ')
            return false;
        long v;
        if (p - l0 > 18) {
            v = 1_000_000_000_000_000L;  // saturate absurdly large latencies
        } else {
            v = 0;
            while (l0 < p) v = v * 10 + (buf[l0++] - '0');
            v = v * 10 + (buf[p + 1] - '0');
            if (v > 1_000_000_000_000_000L) v = 1_000_000_000_000_000L;
        }
        p += 5;
        // user agent
        if (buf[p] != '"') return false;
        p++;
        while (p < e && buf[p] != '"') p++;
        if (p != e - 1) return false;
        // ensure scratch capacity for next use was fine; set key
        lookupKey.len = tl;
        parsedCls = cls;
        parsedLat = v;
        return true;
    }

    static final int[] TS_DIGITS = {0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22};

    static boolean isDig(byte c) { return c >= '0' && c <= '9'; }

    static boolean isSeg(byte c) {
        return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-';
    }
}
