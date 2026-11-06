import java.io.*;
import java.nio.file.*;
import java.util.Arrays;

public class Main {
    // ---- open-addressing hash map: template -> stats ----
    static byte[][] keys = new byte[64][];
    static long[] hashes = new long[64];
    static long[] counts = new long[64];
    static int[][] lats = new int[64][];
    static int[] latLens = new int[64];
    static int numEntries = 0;
    static int[] table = new int[1024];
    static int tmask = 1023;
    static int used = 0;

    static void putEntry(byte[] buf, int len, long h) {
        if (numEntries == keys.length) {
            keys = Arrays.copyOf(keys, numEntries * 2);
            hashes = Arrays.copyOf(hashes, numEntries * 2);
            counts = Arrays.copyOf(counts, numEntries * 2);
            lats = Arrays.copyOf(lats, numEntries * 2);
            latLens = Arrays.copyOf(latLens, numEntries * 2);
        }
        keys[numEntries] = Arrays.copyOf(buf, len);
        hashes[numEntries] = h;
        lats[numEntries] = new int[16];
        numEntries++;
    }

    static int lookup(byte[] buf, int len, long h) {
        int i = (int) (h & tmask);
        while (table[i] != 0) {
            int e = table[i] - 1;
            if (hashes[e] == h) {
                byte[] k = keys[e];
                if (k.length == len) {
                    boolean eq = true;
                    for (int z = 0; z < len; z++) {
                        if (k[z] != buf[z]) { eq = false; break; }
                    }
                    if (eq) return e;
                }
            }
            i = (i + 1) & tmask;
        }
        putEntry(buf, len, h);
        table[i] = numEntries;
        used++;
        if (used * 10 >= table.length * 7) rehash();
        return numEntries - 1;
    }

    static void rehash() {
        int ncap = table.length * 2;
        table = new int[ncap];
        tmask = ncap - 1;
        for (int e = 0; e < numEntries; e++) {
            int i = (int) (hashes[e] & tmask);
            while (table[i] != 0) i = (i + 1) & tmask;
            table[i] = e + 1;
        }
    }

    static boolean isd(byte c) { return c >= '0' && c <= '9'; }

    private static final java.lang.invoke.VarHandle LONG_VIEW =
            java.lang.invoke.MethodHandles.byteArrayViewVarHandle(long[].class, java.nio.ByteOrder.LITTLE_ENDIAN);
    private static final long NL_MASK  = 0x0a0a0a0a0a0a0a0aL;
    private static final long ONE_MASK = 0x0101010101010101L;
    private static final long HI_MASK  = 0x8080808080808080L;

    // index of first '\n' in d[from:n), or n if none (SWAR, 8 bytes at a time)
    static int findNl(byte[] d, int from, int n) {
        int i = from;
        int lim = n - 8;
        while (i <= lim) {
            long chunk = (long) LONG_VIEW.get(d, i);
            long x = chunk ^ NL_MASK;
            long has = (x - ONE_MASK) & ~x & HI_MASK;
            if (has != 0) {
                return i + (Long.numberOfTrailingZeros(has) >> 3);
            }
            i += 8;
        }
        while (i < n && d[i] != '\n') i++;
        return i;
    }

    public static void main(String[] args) throws IOException {
        byte[] d = Files.readAllBytes(Paths.get(args[0]));
        int n = d.length;

        long lines = 0, malformed = 0;
        long[] clsCount = new long[10];

        int i = 0;
        while (i < n) {
            // find end of line
            int le = findNl(d, i, n);
            int len = le - i;
            lines++;

            if (parse(d, i, len)) {
                int t = tlen;
                long h = 2166136261L;
                byte[] tb = tbGlobal;
                for (int z = 0; z < t; z++) { h ^= (tb[z] & 0xFFL); h *= 16777619L; }
                int e = lookup(tb, t, h);
                counts[e]++;
                int[] la = lats[e];
                if (latLens[e] == la.length) lats[e] = la = Arrays.copyOf(la, la.length * 2);
                la[latLens[e]++] = tenths;
                clsCount[cls]++;
            } else {
                malformed++;
            }
            i = le + 1;
        }

        Integer[] ord = new Integer[numEntries];
        for (int e = 0; e < numEntries; e++) ord[e] = e;
        Arrays.sort(ord, (a, b) -> {
            if (counts[a] != counts[b]) return counts[a] > counts[b] ? -1 : 1;
            byte[] ka = keys[a], kb = keys[b];
            int c = compareUnsigned(ka, kb);
            return c;
        });

        StringBuilder sb = new StringBuilder(512);
        sb.append("lines ").append(lines).append('\n');
        sb.append("malformed ").append(malformed).append('\n');
        for (int dd = 0; dd < 10; dd++)
            if (clsCount[dd] > 0) sb.append("status ").append(dd).append("xx ").append(clsCount[dd]).append('\n');
        int top = Math.min(10, numEntries);
        for (int r = 0; r < top; r++) {
            int e = ord[r];
            int[] la = Arrays.copyOf(lats[e], latLens[e]);
            Arrays.sort(la);
            int nn = la.length;
            int p50 = la[(50 * nn + 99) / 100 - 1];
            int p95 = la[(95 * nn + 99) / 100 - 1];
            int mx = la[nn - 1];
            sb.append("path ").append(new String(keys[e], 0, keys[e].length, java.nio.charset.StandardCharsets.ISO_8859_1))
              .append(' ').append(counts[e]).append(' ')
              .append(p50 / 10).append('.').append(p50 % 10).append(' ')
              .append(p95 / 10).append('.').append(p95 % 10).append(' ')
              .append(mx / 10).append('.').append(mx % 10).append('\n');
        }
        byte[] out = sb.toString().getBytes(java.nio.charset.StandardCharsets.ISO_8859_1);
        System.out.write(out, 0, out.length);
        System.out.flush();
    }

    static int compareUnsigned(byte[] a, byte[] b) {
        int la = a.length, lb = b.length, mn = Math.min(la, lb);
        for (int z = 0; z < mn; z++) {
            int ca = a[z] & 0xFF, cb = b[z] & 0xFF;
            if (ca != cb) return ca < cb ? -1 : 1;
        }
        return Integer.compare(la, lb);
    }

    static int tlen;
    static int tenths;
    static int cls;
    static int ps, pe;
    static byte[] tbGlobal = new byte[512];

    static boolean parse(byte[] d, int base, int n) {
        byte[] tb = tbGlobal;
        if (n < 50) return false;
        int i = base;
        // timestamp: dddd-dd-ddTdd:dd:dd.dddZ
        int[] digs = {0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22};
        for (int j : digs) if (!isd(d[i + j])) return false;
        if (d[i + 4] != '-' || d[i + 7] != '-' || d[i + 10] != 'T' || d[i + 13] != ':'
                || d[i + 16] != ':' || d[i + 19] != '.' || d[i + 23] != 'Z') return false;
        i += 24;
        if (d[i++] != ' ') return false;
        // host [a-z]+-\d+
        int st = i;
        while (i < base + n && d[i] >= 'a' && d[i] <= 'z') i++;
        if (i == st || i >= base + n || d[i] != '-') return false;
        i++;
        st = i;
        while (i < base + n && isd(d[i])) i++;
        if (i == st || i >= base + n || d[i] != ' ') return false;
        i++;
        int rem = base + n - i;
        if (rem >= 4 && d[i] == 'G' && d[i + 1] == 'E' && d[i + 2] == 'T' && d[i + 3] == ' ') i += 4;
        else if (rem >= 4 && d[i] == 'P' && d[i + 1] == 'U' && d[i + 2] == 'T' && d[i + 3] == ' ') i += 4;
        else if (rem >= 5 && d[i] == 'P' && d[i + 1] == 'O' && d[i + 2] == 'S' && d[i + 3] == 'T' && d[i + 4] == ' ') i += 5;
        else if (rem >= 6 && d[i] == 'P' && d[i + 1] == 'A' && d[i + 2] == 'T' && d[i + 3] == 'C' && d[i + 4] == 'H' && d[i + 5] == ' ') i += 6;
        else if (rem >= 7 && d[i] == 'D' && d[i + 1] == 'E' && d[i + 2] == 'L' && d[i + 3] == 'E' && d[i + 4] == 'T' && d[i + 5] == 'E' && d[i + 6] == ' ') i += 7;
        else return false;
        if (base + n - i < 17) return false;
        if (d[i] != '/') return false;
        ps = i;
        i++;
        while (i < base + n) {
            byte c = d[i];
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || isd(c) || c == '_' || c == '-' || c == '/') i++;
            else break;
        }
        pe = i;
        if (i < base + n && d[i] == '?') {
            i++;
            while (i < base + n && d[i] != ' ') i++;
        }
        if (i >= base + n || d[i] != ' ') return false;
        i++;
        if (base + n - i < 15) return false;
        if (!isd(d[i]) || !isd(d[i + 1]) || !isd(d[i + 2])) return false;
        cls = d[i] - '0';
        i += 3;
        if (d[i++] != ' ') return false;
        if (base + n - i < 11) return false;
        st = i;
        while (i < base + n && isd(d[i])) i++;
        if (i == st || d[i] != 'B') return false;
        i++;
        if (d[i++] != ' ') return false;
        st = i;
        long v = 0;
        int nd = 0;
        while (i < base + n && isd(d[i])) {
            if (nd < 15) v = v * 10 + (d[i] - '0');
            i++; nd++;
        }
        if (i == st || d[i] != '.') return false;
        i++;
        if (!isd(d[i])) return false;
        v = v * 10 + (d[i] - '0');
        i++;
        if (d[i] != 'm' || d[i + 1] != 's' || d[i + 2] != ' ') return false;
        tenths = (int) Math.min(v, 0xFFFFFFFFL);
        i += 3;
        if (d[i] != '"') return false;
        i++;
        while (i < base + n && d[i] != '"') i++;
        if (i + 1 != base + n) return false;

        // build template
        int need = (pe - ps) * 5 + 8;
        if (tb.length < need) tbGlobal = tb = new byte[need * 2];
        int t = 0;
        int k = ps;
        int peA = pe;
        while (k < peA) {
            tb[t++] = '/';
            k++;
            int s0 = k;
            while (k < peA && d[k] != '/') k++;
            int slen = k - s0;
            boolean dig = slen > 0;
            for (int z = 0; dig && z < slen; z++) if (!isd(d[s0 + z])) { dig = false; break; }
            if (dig) {
                tb[t] = '{'; tb[t + 1] = 'i'; tb[t + 2] = 'd'; tb[t + 3] = '}';
                t += 4;
            } else {
                System.arraycopy(d, s0, tb, t, slen);
                t += slen;
            }
        }
        tlen = t;
        return true;
    }
}
