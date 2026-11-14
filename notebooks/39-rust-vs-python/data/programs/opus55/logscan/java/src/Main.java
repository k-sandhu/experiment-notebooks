import java.io.IOException;
import java.io.PrintStream;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

// Log scan: reads the file in large chunks into a byte[], matches each line with a
// hand-written parser and interns path templates in an open-addressing hash table.
public class Main {
    private static final byte C_DIGIT = 1, C_LOWER = 2, C_PATH = 4;
    private static final byte[] CT = new byte[256];
    private static final VarHandle LONGS = MethodHandles.byteArrayViewVarHandle(long[].class, ByteOrder.LITTLE_ENDIAN);

    static {
        for (int c = '0'; c <= '9'; c++) CT[c] |= C_DIGIT | C_PATH;
        for (int c = 'a'; c <= 'z'; c++) CT[c] |= C_LOWER | C_PATH;
        for (int c = 'A'; c <= 'Z'; c++) CT[c] |= C_PATH;
        CT['_'] |= C_PATH;
        CT['-'] |= C_PATH;
        CT['/'] |= C_PATH;
    }

    // Template table
    private static byte[] arena = new byte[1 << 16];
    private static int arenaLen = 0;
    private static int[] tOff = new int[256], tLen = new int[256], tCount = new int[256];
    private static int nTemplates = 0;
    private static int[] slotId; // id + 1, 0 = empty
    private static int[] slotHash;
    private static int mask;

    // Per well-formed line
    private static int[] ids = new int[1 << 20];
    private static long[] lats = new long[1 << 20];
    private static int nGood = 0;

    private static long lines = 0, malformed = 0;
    private static final long[] status = new long[10];

    private static byte[] tbuf;

    private static boolean isDigit(int c) {
        return c >= '0' && c <= '9';
    }

    private static int intern(byte[] key, int len, int h) {
        int i = h & mask;
        for (;;) {
            int s = slotId[i];
            if (s == 0) break;
            if (slotHash[i] == h) {
                int id = s - 1;
                if (tLen[id] == len && Arrays.equals(arena, tOff[id], tOff[id] + len, key, 0, len)) {
                    tCount[id]++;
                    return id;
                }
            }
            i = (i + 1) & mask;
        }
        int id = nTemplates++;
        if (id == tOff.length) {
            tOff = Arrays.copyOf(tOff, id * 2);
            tLen = Arrays.copyOf(tLen, id * 2);
            tCount = Arrays.copyOf(tCount, id * 2);
        }
        if (arenaLen + len > arena.length) arena = Arrays.copyOf(arena, Math.max(arena.length * 2, arenaLen + len));
        System.arraycopy(key, 0, arena, arenaLen, len);
        tOff[id] = arenaLen;
        tLen[id] = len;
        tCount[id] = 1;
        arenaLen += len;
        slotId[i] = id + 1;
        slotHash[i] = h;
        if (nTemplates * 2 > slotId.length) grow();
        return id;
    }

    private static void grow() {
        int[] oldId = slotId, oldHash = slotHash;
        slotId = new int[oldId.length * 2];
        slotHash = new int[oldId.length * 2];
        mask = slotId.length - 1;
        for (int j = 0; j < oldId.length; j++) {
            if (oldId[j] == 0) continue;
            int i = oldHash[j] & mask;
            while (slotId[i] != 0) i = (i + 1) & mask;
            slotId[i] = oldId[j];
            slotHash[i] = oldHash[j];
        }
    }

    // Parses the line starting at p (terminated by '\n'). Returns true if well-formed.
    private static int parseLine(byte[] b, int p) {
        // Fixed-position checks use non-short-circuit '&' so that C2 sees one branch instead of
        // many rarely-taken ones (each of which would otherwise cost a deoptimization). Reading a
        // few bytes past a short line is safe: the buffer is padded, and the line's '\n' always
        // fails one of the checks.
        if (!(isDigit(b[p]) & isDigit(b[p + 1]) & isDigit(b[p + 2]) & isDigit(b[p + 3]) & b[p + 4] == '-'
                & isDigit(b[p + 5]) & isDigit(b[p + 6]) & b[p + 7] == '-' & isDigit(b[p + 8])
                & isDigit(b[p + 9]) & b[p + 10] == 'T' & isDigit(b[p + 11]) & isDigit(b[p + 12])
                & b[p + 13] == ':' & isDigit(b[p + 14]) & isDigit(b[p + 15]) & b[p + 16] == ':'
                & isDigit(b[p + 17]) & isDigit(b[p + 18]) & b[p + 19] == '.' & isDigit(b[p + 20])
                & isDigit(b[p + 21]) & isDigit(b[p + 22]) & b[p + 23] == 'Z' & b[p + 24] == ' '))
            return ~p;
        p += 25;
        // Host: [a-z]+-\d+
        if ((CT[b[p] & 0xFF] & C_LOWER) == 0) return ~p;
        do p++; while ((CT[b[p] & 0xFF] & C_LOWER) != 0);
        if (b[p] != '-') return ~p;
        p++;
        if (!isDigit(b[p])) return ~p;
        do p++; while (isDigit(b[p]));
        if (b[p] != ' ') return ~p;
        p++;
        // Method
        switch (b[p]) {
            case 'G':
                if (!(b[p + 1] == 'E' & b[p + 2] == 'T')) return ~p;
                p += 3;
                break;
            case 'P':
                if (b[p + 1] == 'U' & b[p + 2] == 'T') p += 3;
                else if (b[p + 1] == 'O' & b[p + 2] == 'S' & b[p + 3] == 'T') p += 4;
                else if (b[p + 1] == 'A' & b[p + 2] == 'T' & b[p + 3] == 'C' & b[p + 4] == 'H') p += 5;
                else return ~p;
                break;
            case 'D':
                if (!(b[p + 1] == 'E' & b[p + 2] == 'L' & b[p + 3] == 'E' & b[p + 4] == 'T' & b[p + 5] == 'E'))
                    return ~p;
                p += 6;
                break;
            default:
                return ~p;
        }
        if (b[p] != ' ') return ~p;
        p++;
        // Path, building the template as we go.
        if (b[p] != '/') return ~p;
        p++;
        byte[] t = tbuf;
        int o = 0;
        t[o++] = '/';
        int c;
        for (;;) {
            int seg = p;
            boolean allDigit = true;
            while (((CT[(c = b[p] & 0xFF)] & C_PATH) != 0) && c != '/') {
                allDigit &= isDigit(c);
                p++;
            }
            int n = p - seg;
            if (o + n + 13 > t.length) tbuf = t = Arrays.copyOf(t, (o + n + 13) * 2);
            if (n != 0 && allDigit) {
                t[o] = '{';
                t[o + 1] = 'i';
                t[o + 2] = 'd';
                t[o + 3] = '}';
                o += 4;
            } else {
                System.arraycopy(b, seg, t, o, n);
                o += n;
            }
            if (c != '/') break;
            t[o++] = '/';
            p++;
        }
        if (c == '?') {
            do p++; while (b[p] != ' ' && b[p] != '\n');
        }
        if (b[p] != ' ') return ~p;
        p++;
        // Status
        if (!(isDigit(b[p]) & isDigit(b[p + 1]) & isDigit(b[p + 2]) & b[p + 3] == ' ')) return ~p;
        int cls = b[p] - '0';
        p += 4;
        // Size
        if (!isDigit(b[p])) return ~p;
        do p++; while (isDigit(b[p]));
        if (!(b[p] == 'B' & b[p + 1] == ' ')) return ~p;
        p += 2;
        // Latency
        if (!isDigit(b[p])) return ~p;
        long lat = 0;
        do lat = lat * 10 + (b[p++] - '0'); while (isDigit(b[p]));
        if (!(b[p] == '.' & isDigit(b[p + 1]) & b[p + 2] == 'm' & b[p + 3] == 's' & b[p + 4] == ' '
                & b[p + 5] == '"'))
            return ~p;
        lat = lat * 10 + (b[p + 1] - '0');
        p += 6;
        // User agent
        while (b[p] != '"' && b[p] != '\n') p++;
        if (!(b[p] == '"' & b[p + 1] == '\n')) return ~p;

        // Hash 8 bytes at a time; tbuf always has at least 8 bytes of slack after o.
        long hh = 0x9E3779B97F4A7C15L ^ o;
        int i = 0;
        for (; i + 8 <= o; i += 8) {
            hh = (hh ^ (long) LONGS.get(t, i)) * 0xFF51AFD7ED558CCDL;
            hh ^= hh >>> 29;
        }
        if (i < o) {
            long w = (long) LONGS.get(t, i) & (-1L >>> (64 - 8 * (o - i)));
            hh = (hh ^ w) * 0xFF51AFD7ED558CCDL;
            hh ^= hh >>> 29;
        }
        hh *= 0xC4CEB9FE1A85EC53L;
        int h = (int) (hh ^ (hh >>> 32));
        int id = intern(t, o, h);
        status[cls]++;
        if (nGood == ids.length) {
            ids = Arrays.copyOf(ids, nGood * 2);
            lats = Arrays.copyOf(lats, nGood * 2);
        }
        ids[nGood] = id;
        lats[nGood] = lat;
        nGood++;
        return p + 2;
    }

    // Processes all lines in buf[0..lastNl]; returns the start of the unprocessed tail.
    private static int processLines(byte[] buf, int lastNl) {
        int p = 0;
        long nLines = 0, nBad = 0;
        while (p <= lastNl) {
            nLines++;
            int r = parseLine(buf, p);
            if (r >= 0) {
                p = r;
            } else {
                nBad++;
                p = ~r;
                while (buf[p] != '\n') p++;
                p++;
            }
        }
        lines += nLines;
        malformed += nBad;
        return p;
    }

    private static int compareTemplates(int a, int b) {
        if (tCount[a] != tCount[b]) return tCount[a] > tCount[b] ? -1 : 1;
        return Arrays.compareUnsigned(arena, tOff[a], tOff[a] + tLen[a], arena, tOff[b], tOff[b] + tLen[b]);
    }

    // Quickselect: places the k-th smallest at a[k], partitions around it.
    private static void select(long[] a, int lo, int hi, int k) {
        while (hi > lo) {
            int mid = (lo + hi) >>> 1;
            // median of three
            if (a[mid] < a[lo]) swap(a, mid, lo);
            if (a[hi] < a[lo]) swap(a, hi, lo);
            if (a[hi] < a[mid]) swap(a, hi, mid);
            long pivot = a[mid];
            int i = lo, j = hi;
            while (i <= j) {
                while (a[i] < pivot) i++;
                while (a[j] > pivot) j--;
                if (i <= j) {
                    swap(a, i, j);
                    i++;
                    j--;
                }
            }
            if (k <= j) hi = j;
            else if (k >= i) lo = i;
            else return;
        }
    }

    private static void swap(long[] a, int i, int j) {
        long t = a[i];
        a[i] = a[j];
        a[j] = t;
    }

    private static void fmtLat(StringBuilder sb, long v) {
        sb.append(v / 10).append('.').append((char) ('0' + v % 10));
    }

    public static void main(String[] args) throws IOException {
        slotId = new int[1024];
        slotHash = new int[1024];
        mask = 1023;

        int cap = 1 << 22;
        byte[] buf = new byte[cap + 64];
        tbuf = new byte[4096];
        int have = 0;
        // FileChannel reuses a cached native buffer; FileInputStream would malloc one per large read.
        try (FileChannel in = FileChannel.open(Path.of(args[0]))) {
            ByteBuffer bb = ByteBuffer.wrap(buf);
            for (;;) {
                if (bb.array() != buf) bb = ByteBuffer.wrap(buf);
                bb.limit(cap).position(have);
                int n = in.read(bb);
                if (n < 0) n = 0;
                have += n;
                if (have == 0) break;
                int lastNl = -1;
                for (int q = have - 1; q >= 0; q--) {
                    if (buf[q] == '\n') {
                        lastNl = q;
                        break;
                    }
                }
                if (lastNl < 0) {
                    if (n == 0) {
                        buf[have] = '\n';
                        lastNl = have;
                        have++;
                    } else {
                        if (have < cap) continue;
                        cap *= 2;
                        buf = Arrays.copyOf(buf, cap + 64);
                        continue;
                    }
                }
                int p = processLines(buf, lastNl);
                int rest = have - p;
                System.arraycopy(buf, p, buf, 0, rest);
                have = rest;
                if (n == 0 && have == 0) break;
            }
        }

        int[] top = new int[10];
        int nTop = 0;
        for (int id = 0; id < nTemplates; id++) {
            if (nTop == 10 && compareTemplates(id, top[9]) >= 0) continue;
            int pos = nTop < 10 ? nTop++ : 9;
            while (pos > 0 && compareTemplates(id, top[pos - 1]) < 0) {
                top[pos] = top[pos - 1];
                pos--;
            }
            top[pos] = id;
        }

        int[] rank = new int[nTemplates];
        Arrays.fill(rank, -1);
        long[][] buckets = new long[nTop][];
        int[] fill = new int[nTop];
        for (int r = 0; r < nTop; r++) {
            rank[top[r]] = r;
            buckets[r] = new long[tCount[top[r]]];
        }
        for (int i = 0; i < nGood; i++) {
            int r = rank[ids[i]];
            if (r >= 0) buckets[r][fill[r]++] = lats[i];
        }

        StringBuilder sb = new StringBuilder(1024);
        sb.append("lines ").append(lines).append('\n');
        sb.append("malformed ").append(malformed).append('\n');
        for (int c = 0; c < 10; c++)
            if (status[c] != 0) sb.append("status ").append(c).append("xx ").append(status[c]).append('\n');
        for (int r = 0; r < nTop; r++) {
            long[] v = buckets[r];
            int n = v.length;
            int k50 = (int) ((50L * n + 99) / 100 - 1), k95 = (int) ((95L * n + 99) / 100 - 1);
            select(v, 0, n - 1, k50);
            long p50 = v[k50];
            select(v, k50, n - 1, k95);
            long p95 = v[k95];
            long mx = p95;
            for (int i = k95 + 1; i < n; i++) if (v[i] > mx) mx = v[i];
            int id = top[r];
            sb.append("path ").append(new String(arena, tOff[id], tLen[id], StandardCharsets.ISO_8859_1))
                    .append(' ').append(n).append(' ');
            fmtLat(sb, p50);
            sb.append(' ');
            fmtLat(sb, p95);
            sb.append(' ');
            fmtLat(sb, mx);
            sb.append('\n');
        }
        PrintStream out = System.out;
        out.write(sb.toString().getBytes(StandardCharsets.ISO_8859_1));
        out.flush();
    }
}
