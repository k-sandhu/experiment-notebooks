import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;

public class Main {
    static byte[] data;
    static int n;

    static byte[] scratch = new byte[1024];

    static byte[][] tmpl = new byte[1024][];
    static int[] tmplLen = new int[1024];
    static int[] count = new int[1024];
    static long[][] lat = new long[1024][];
    static int[] latN = new int[1024];
    static int nEntries;

    static int[] table = new int[2048];

    // parse outputs
    static int stStatus;
    static long stLat;

    static boolean isDig(byte c) { return (c & 0xFF) >= '0' && (c & 0xFF) <= '9'; }

    static void ensureScratch(int need) {
        if (need > scratch.length) scratch = new byte[need];
    }

    static void addEntry(int len) {
        if (nEntries == tmpl.length) {
            int cap = nEntries * 2;
            tmpl = Arrays.copyOf(tmpl, cap);
            tmplLen = Arrays.copyOf(tmplLen, cap);
            count = Arrays.copyOf(count, cap);
            lat = Arrays.copyOf(lat, cap);
            latN = Arrays.copyOf(latN, cap);
        }
        int e = nEntries++;
        tmpl[e] = Arrays.copyOf(scratch, len);
        tmplLen[e] = len;
        lat[e] = new long[16];
        if ((long) nEntries * 2 >= table.length) {
            int[] t = new int[table.length * 2];
            int mask = t.length - 1;
            for (int i = 0; i < nEntries; i++) {
                int h = hash(tmpl[i], tmplLen[i]);
                int idx = h & mask;
                while (t[idx] != 0) idx = (idx + 1) & mask;
                t[idx] = i + 1;
            }
            table = t;
        } else {
            int mask = table.length - 1;
            int h = hash(tmpl[e], len);
            int idx = h & mask;
            while (table[idx] != 0) idx = (idx + 1) & mask;
            table[idx] = e + 1;
        }
    }

    static int hash(byte[] b, int len) {
        int h = 0x811c9dc5;
        for (int i = 0; i < len; i++) h = (h ^ (b[i] & 0xFF)) * 16777619;
        h ^= h >>> 16;
        return h;
    }

    static int findEntry(int len) {
        int mask = table.length - 1;
        int idx = hash(scratch, len) & mask;
        while (true) {
            int s = table[idx];
            if (s == 0) return -1;
            int e = s - 1;
            if (tmplLen[e] == len) {
                byte[] t = tmpl[e];
                int i = 0;
                while (i < len && t[i] == scratch[i]) i++;
                if (i == len) return e;
            }
            idx = (idx + 1) & mask;
        }
    }

    static boolean parseLine(int p, int le) {
        byte[] d = data;
        if (le - p < 25) return false;
        if (!(isDig(d[p]) && isDig(d[p + 1]) && isDig(d[p + 2]) && isDig(d[p + 3]) && d[p + 4] == '-'
                && isDig(d[p + 5]) && isDig(d[p + 6]) && d[p + 7] == '-' && isDig(d[p + 8])
                && isDig(d[p + 9]) && d[p + 10] == 'T' && isDig(d[p + 11]) && isDig(d[p + 12])
                && d[p + 13] == ':' && isDig(d[p + 14]) && isDig(d[p + 15]) && d[p + 16] == ':'
                && isDig(d[p + 17]) && isDig(d[p + 18]) && d[p + 19] == '.' && isDig(d[p + 20])
                && isDig(d[p + 21]) && isDig(d[p + 22]) && d[p + 23] == 'Z' && d[p + 24] == ' '))
            return false;

        int i = p + 25;
        int j = i;
        while (j < le && d[j] >= 'a' && d[j] <= 'z') j++;
        if (j == i || j >= le || d[j] != '-') return false;
        j++;
        int ds = j;
        while (j < le && isDig(d[j])) j++;
        if (j == ds || j >= le || d[j] != ' ') return false;
        j++;

        // method
        if (j + 4 <= le && d[j] == 'G' && d[j + 1] == 'E' && d[j + 2] == 'T' && d[j + 3] == ' ') {
            j += 4;
        } else if (j + 5 <= le && d[j] == 'P' && d[j + 1] == 'O' && d[j + 2] == 'S'
                && d[j + 3] == 'T' && d[j + 4] == ' ') {
            j += 5;
        } else if (j + 4 <= le && d[j] == 'P' && d[j + 1] == 'U' && d[j + 2] == 'T'
                && d[j + 3] == ' ') {
            j += 4;
        } else if (j + 7 <= le && d[j] == 'D' && d[j + 1] == 'E' && d[j + 2] == 'L'
                && d[j + 3] == 'E' && d[j + 4] == 'T' && d[j + 5] == 'E' && d[j + 6] == ' ') {
            j += 7;
        } else if (j + 6 <= le && d[j] == 'P' && d[j + 1] == 'A' && d[j + 2] == 'T'
                && d[j + 3] == 'C' && d[j + 4] == 'H' && d[j + 5] == ' ') {
            j += 6;
        } else {
            return false;
        }

        if (j >= le || d[j] != '/') return false;
        int q = j + 1;
        while (q < le) {
            int c = d[q];
            if ((c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')
                    || c == '_' || c == '/' || c == '-')
                q++;
            else
                break;
        }

        int fieldEnd;
        if (q < le && d[q] == '?') {
            int r = q + 1;
            while (r < le && d[r] != ' ') r++;
            if (r >= le) return false;
            fieldEnd = r;
        } else if (q < le && d[q] == ' ') {
            fieldEnd = q;
        } else {
            return false;
        }

        // build template into scratch
        ensureScratch((q - j) * 4 + 16);
        byte[] sc = scratch;
        int t = 0;
        int s = j;
        while (s < q) {
            if (d[s] == '/') {
                sc[t++] = '/';
                s++;
                continue;
            }
            int e = s;
            boolean allDig = true;
            while (e < q && d[e] != '/') {
                if (!isDig(d[e])) allDig = false;
                e++;
            }
            if (allDig) {
                sc[t] = '{'; sc[t + 1] = 'i'; sc[t + 2] = 'd'; sc[t + 3] = '}';
                t += 4;
            } else {
                for (int k = s; k < e; k++) sc[t++] = d[k];
            }
            s = e;
        }

        int k = fieldEnd;
        if (k + 4 >= le) return false;
        if (!isDig(d[k + 1]) || !isDig(d[k + 2]) || !isDig(d[k + 3]) || d[k + 4] != ' ')
            return false;
        stStatus = d[k + 1] - '0';
        k += 5;

        int e = k;
        while (e < le && isDig(d[e])) e++;
        if (e == k) return false;
        if (e >= le || d[e] != 'B') return false;
        e++;
        if (e >= le || d[e] != ' ') return false;
        e++;

        int ls = e;
        long v = 0;
        while (e < le && isDig(d[e])) {
            v = v * 10 + (d[e] - '0');
            e++;
        }
        if (e == ls) return false;
        if (e >= le || d[e] != '.') return false;
        e++;
        if (e >= le || !isDig(d[e])) return false;
        v = v * 10 + (d[e] - '0');
        e++;
        if (e + 3 >= le) return false;
        if (d[e] != 'm' || d[e + 1] != 's' || d[e + 2] != ' ') return false;
        e += 3;
        if (d[e] != '"') return false;
        e++;
        int r = e;
        while (r < le && d[r] != '"') r++;
        if (r != le - 1) return false;

        stLat = v;
        stTlen = t;
        return true;
    }

    static int cmpBytes(byte[] a, byte[] b) {
        int m = Math.min(a.length, b.length);
        for (int i = 0; i < m; i++) {
            int x = a[i] & 0xFF, y = b[i] & 0xFF;
            if (x != y) return x - y;
        }
        return a.length - b.length;
    }

    static boolean better(int a, int b) {
        if (count[a] != count[b]) return count[a] > count[b];
        return cmpBytes(tmpl[a], tmpl[b]) < 0;
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) return;
        try (FileChannel ch = FileChannel.open(Paths.get(args[0]), StandardOpenOption.READ)) {
            long size = ch.size();
            if (size > Integer.MAX_VALUE - 8) throw new IOException("too large");
            data = new byte[(int) size];
            ByteBuffer bb = ByteBuffer.wrap(data);
            while (bb.hasRemaining()) {
                if (ch.read(bb) < 0) break;
            }
        }
        n = data.length;

        long lines = 0, malformed = 0;
        long[] statusCount = new long[10];

        int p = 0;
        while (p < n) {
            int le = p;
            while (le < n && data[le] != '\n') le++;
            lines++;
            if (parseLine(p, le)) {
                statusCount[stStatus]++;
                int len = stTlen;
                int e = findEntry(len);
                if (e < 0) {
                    addEntry(len);
                    e = nEntries - 1;
                }
                count[e]++;
                long[] a = lat[e];
                int k = latN[e];
                if (k == a.length) {
                    a = Arrays.copyOf(a, k * 2);
                    lat[e] = a;
                }
                a[k] = stLat;
                latN[e] = k + 1;
            } else {
                malformed++;
            }
            p = (le < n) ? le + 1 : n;
        }

        int[] best = new int[10];
        int bestN = 0;
        for (int e = 0; e < nEntries; e++) {
            int pos = 0;
            while (pos < bestN && better(best[pos], e)) pos++;
            if (pos < 10) {
                int lim = Math.min(bestN, 9);
                for (int k = lim; k > pos; k--) best[k] = best[k - 1];
                best[pos] = e;
                if (bestN < 10) bestN++;
            }
        }

        StringBuilder sb = new StringBuilder(8192);
        sb.append("lines ").append(lines).append('\n');
        sb.append("malformed ").append(malformed).append('\n');
        for (int c = 0; c < 10; c++) {
            if (statusCount[c] != 0) {
                sb.append("status ").append((char) ('0' + c)).append("xx ")
                        .append(statusCount[c]).append('\n');
            }
        }
        for (int bi = 0; bi < bestN; bi++) {
            int e = best[bi];
            int len = latN[e];
            Arrays.sort(lat[e], 0, len);
            int i50 = (50 * len + 99) / 100 - 1;
            int i95 = (95 * len + 99) / 100 - 1;
            sb.append("path ").append(new String(tmpl[e], StandardCharsets.ISO_8859_1)).append(' ')
                    .append(count[e]).append(' ');
            appendTenths(sb, lat[e][i50]);
            sb.append(' ');
            appendTenths(sb, lat[e][i95]);
            sb.append(' ');
            appendTenths(sb, lat[e][len - 1]);
            sb.append('\n');
        }
        System.out.print(sb);
    }

    static int stTlen;

    static void appendTenths(StringBuilder sb, long v) {
        sb.append(v / 10).append('.').append(v % 10);
    }
}
