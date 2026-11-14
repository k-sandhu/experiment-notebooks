import java.io.FileInputStream;
import java.util.ArrayList;
import java.util.Arrays;

public class Main {

    static final class IntList {
        int[] a = new int[8];
        int n = 0;

        void add(int v) {
            if (n == a.length) a = Arrays.copyOf(a, n << 1);
            a[n++] = v;
        }
    }

    static final class Table {
        long[] hash;
        int[] id;
        byte[][] keys;
        int mask;
        int size;

        Table(int cap) {
            int c = 16;
            while (c < cap) c <<= 1;
            hash = new long[c];
            id = new int[c];
            keys = new byte[c][];
            Arrays.fill(id, -1);
            mask = c - 1;
        }

        private void resize() {
            int nc = id.length << 1;
            long[] nh = new long[nc];
            int[] ni = new int[nc];
            byte[][] nk = new byte[nc][];
            Arrays.fill(ni, -1);
            int nm = nc - 1;
            for (int i = 0; i < id.length; i++) {
                if (id[i] >= 0) {
                    int p = (int) hash[i] & nm;
                    while (ni[p] >= 0) p = (p + 1) & nm;
                    ni[p] = id[i];
                    nh[p] = hash[i];
                    nk[p] = keys[i];
                }
            }
            hash = nh;
            id = ni;
            keys = nk;
            mask = nm;
        }

        int find(byte[] s, int len, long h) {
            int p = (int) h & mask;
            while (true) {
                int v = id[p];
                if (v < 0) return -1;
                if (hash[p] == h) {
                    byte[] k = keys[p];
                    if (k.length == len) {
                        int i = 0;
                        while (i < len && k[i] == s[i]) i++;
                        if (i == len) return v;
                    }
                }
                p = (p + 1) & mask;
            }
        }

        void put(byte[] key, int len, long h, int v) {
            if ((size + 1) << 1 > id.length) resize();
            int p = (int) h & mask;
            while (id[p] >= 0) p = (p + 1) & mask;
            id[p] = v;
            hash[p] = h;
            keys[p] = Arrays.copyOf(key, len);
            size++;
        }
    }

    static ArrayList<byte[]> names;
    static ArrayList<IntList> lists;
    static IntList maxes;
    static Table table;
    static byte[] scratch;
    static long lines, malformed;
    static long[] statusCount;

    static long hashBytes(byte[] s, int len) {
        long h = 0xcbf29ce484222325L;
        for (int i = 0; i < len; i++) {
            h ^= (s[i] & 0xff);
            h *= 0x100000001b3L;
        }
        return h;
    }

    static boolean tsOk(byte[] b, int p) {
        return b[p] >= '0' && b[p] <= '9'
                && b[p + 1] >= '0' && b[p + 1] <= '9'
                && b[p + 2] >= '0' && b[p + 2] <= '9'
                && b[p + 3] >= '0' && b[p + 3] <= '9'
                && b[p + 4] == '-'
                && b[p + 5] >= '0' && b[p + 5] <= '9'
                && b[p + 6] >= '0' && b[p + 6] <= '9'
                && b[p + 7] == '-'
                && b[p + 8] >= '0' && b[p + 8] <= '9'
                && b[p + 9] >= '0' && b[p + 9] <= '9'
                && b[p + 10] == 'T'
                && b[p + 11] >= '0' && b[p + 11] <= '9'
                && b[p + 12] >= '0' && b[p + 12] <= '9'
                && b[p + 13] == ':'
                && b[p + 14] >= '0' && b[p + 14] <= '9'
                && b[p + 15] >= '0' && b[p + 15] <= '9'
                && b[p + 16] == ':'
                && b[p + 17] >= '0' && b[p + 17] <= '9'
                && b[p + 18] >= '0' && b[p + 18] <= '9'
                && b[p + 19] == '.'
                && b[p + 20] >= '0' && b[p + 20] <= '9'
                && b[p + 21] >= '0' && b[p + 21] <= '9'
                && b[p + 22] >= '0' && b[p + 22] <= '9'
                && b[p + 23] == 'Z';
    }

    static int cmpBytes(byte[] a, byte[] b) {
        int n = Math.min(a.length, b.length);
        for (int i = 0; i < n; i++) {
            int x = a[i] & 0xff, y = b[i] & 0xff;
            if (x != y) return x - y;
        }
        return a.length - b.length;
    }

    static void process(byte[] data, int pos, int e) {
        lines++;
        boolean ok = true;
        int statusClass = 0;
        int lat = 0;
        int pathStart = 0, pathEnd = 0;

        parse:
        {
            int p = pos;
            int end = e;
            if (end - p < 25 || !tsOk(data, p)) { ok = false; break parse; }
            p += 24;
            if (data[p] != ' ') { ok = false; break parse; }
            p++;
            if (p >= end || data[p] < 'a' || data[p] > 'z') { ok = false; break parse; }
            p++;
            while (p < end && data[p] >= 'a' && data[p] <= 'z') p++;
            if (p >= end || data[p] != '-') { ok = false; break parse; }
            p++;
            if (p >= end || data[p] < '0' || data[p] > '9') { ok = false; break parse; }
            while (p < end && data[p] >= '0' && data[p] <= '9') p++;
            if (p >= end || data[p] != ' ') { ok = false; break parse; }
            p++;
            int rem = end - p;
            if (rem >= 4 && data[p] == 'G' && data[p + 1] == 'E' && data[p + 2] == 'T' && data[p + 3] == ' ') {
                p += 4;
            } else if (rem >= 5 && data[p] == 'P' && data[p + 1] == 'O' && data[p + 2] == 'S' && data[p + 3] == 'T' && data[p + 4] == ' ') {
                p += 5;
            } else if (rem >= 4 && data[p] == 'P' && data[p + 1] == 'U' && data[p + 2] == 'T' && data[p + 3] == ' ') {
                p += 4;
            } else if (rem >= 7 && data[p] == 'D' && data[p + 1] == 'E' && data[p + 2] == 'L' && data[p + 3] == 'E' && data[p + 4] == 'T' && data[p + 5] == 'E' && data[p + 6] == ' ') {
                p += 7;
            } else if (rem >= 6 && data[p] == 'P' && data[p + 1] == 'A' && data[p + 2] == 'T' && data[p + 3] == 'C' && data[p + 4] == 'H' && data[p + 5] == ' ') {
                p += 6;
            } else { ok = false; break parse; }

            if (p >= end || data[p] != '/') { ok = false; break parse; }
            pathStart = p;
            while (p < end) {
                int c = data[p];
                if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
                        || c == '_' || c == '-' || c == '/') {
                    p++;
                } else {
                    break;
                }
            }
            pathEnd = p;
            if (p < end && data[p] == '?') {
                p++;
                while (p < end && data[p] != ' ') p++;
            }
            if (p >= end || data[p] != ' ') { ok = false; break parse; }
            p++;
            if (end - p < 4 || data[p] < '0' || data[p] > '9' || data[p + 1] < '0' || data[p + 1] > '9'
                    || data[p + 2] < '0' || data[p + 2] > '9' || data[p + 3] != ' ') {
                ok = false;
                break parse;
            }
            statusClass = data[p] - '0';
            p += 4;
            if (p >= end || data[p] < '0' || data[p] > '9') { ok = false; break parse; }
            while (p < end && data[p] >= '0' && data[p] <= '9') p++;
            if (p >= end || data[p] != 'B') { ok = false; break parse; }
            p++;
            if (p >= end || data[p] != ' ') { ok = false; break parse; }
            p++;
            if (p >= end || data[p] < '0' || data[p] > '9') { ok = false; break parse; }
            int v = 0;
            while (p < end && data[p] >= '0' && data[p] <= '9') {
                v = v * 10 + (data[p] - '0');
                p++;
            }
            if (p >= end || data[p] != '.') { ok = false; break parse; }
            p++;
            if (p >= end || data[p] < '0' || data[p] > '9') { ok = false; break parse; }
            v = v * 10 + (data[p] - '0');
            p++;
            if (end - p < 3 || data[p] != 'm' || data[p + 1] != 's' || data[p + 2] != ' ') {
                ok = false;
                break parse;
            }
            p += 3;
            if (p >= end || data[p] != '"') { ok = false; break parse; }
            p++;
            while (p < end && data[p] != '"') p++;
            if (p >= end) { ok = false; break parse; }
            p++;
            if (p != end) { ok = false; break parse; }
            lat = v;
        }

        if (!ok) {
            malformed++;
        } else {
            statusCount[statusClass]++;
            int need = (pathEnd - pathStart) * 4 + 4;
            if (need > scratch.length) scratch = new byte[need];
            int tlen = 0;
            int q = pathStart;
            byte[] data2 = data;
            byte[] sc = scratch;
            while (q < pathEnd) {
                sc[tlen++] = '/';
                q++;
                int s = q;
                boolean digits = true, nonempty = false;
                while (q < pathEnd && data2[q] != '/') {
                    int c = data2[q];
                    if (c < '0' || c > '9') digits = false;
                    nonempty = true;
                    q++;
                }
                if (nonempty && digits) {
                    sc[tlen++] = '{';
                    sc[tlen++] = 'i';
                    sc[tlen++] = 'd';
                    sc[tlen++] = '}';
                } else {
                    int cnt = q - s;
                    System.arraycopy(data2, s, sc, tlen, cnt);
                    tlen += cnt;
                }
            }
            long h = hashBytes(sc, tlen);
            int id = table.find(sc, tlen, h);
            if (id < 0) {
                id = names.size();
                byte[] key = Arrays.copyOf(sc, tlen);
                table.put(key, tlen, h, id);
                names.add(key);
                lists.add(new IntList());
                maxes.add(0);
            }
            IntList il = lists.get(id);
            il.add(lat);
            if (lat > maxes.a[id]) maxes.a[id] = lat;
        }
    }

    public static void main(String[] args) throws Exception {
        names = new ArrayList<>();
        lists = new ArrayList<>();
        maxes = new IntList();
        table = new Table(1024);
        scratch = new byte[2048];
        statusCount = new long[10];

        byte[] buf = new byte[1 << 22];
        int len = 0;
        boolean eof = false;
        try (FileInputStream in = new FileInputStream(args[0])) {
            while (!eof) {
                if (len == buf.length) buf = Arrays.copyOf(buf, len << 1);
                int r = in.read(buf, len, buf.length - len);
                if (r <= 0) {
                    eof = true;
                } else {
                    len += r;
                }
                int s = 0;
                while (s < len) {
                    int nl = -1;
                    for (int i = s; i < len; i++) {
                        if (buf[i] == '\n') { nl = i; break; }
                    }
                    if (nl < 0) break;
                    process(buf, s, nl);
                    s = nl + 1;
                }
                if (s > 0) {
                    System.arraycopy(buf, s, buf, 0, len - s);
                    len -= s;
                }
            }
        }
        if (len > 0) process(buf, 0, len);

        StringBuilder sb = new StringBuilder(512);
        sb.append("lines ").append(lines).append('\n');
        sb.append("malformed ").append(malformed).append('\n');
        for (int d = 0; d < 10; d++) {
            if (statusCount[d] != 0) {
                sb.append("status ").append(d).append("xx ").append(statusCount[d]).append('\n');
            }
        }

        int m = names.size();
        Integer[] order = new Integer[m];
        for (int i = 0; i < m; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> {
            int ca = lists.get(a).n, cb = lists.get(b).n;
            if (ca != cb) return Integer.compare(cb, ca);
            return cmpBytes(names.get(a), names.get(b));
        });

        int top = Math.min(10, m);
        for (int k = 0; k < top; k++) {
            int idx = order[k];
            IntList il = lists.get(idx);
            Arrays.sort(il.a, 0, il.n);
            long cnt = il.n;
            int i50 = (int) ((50L * cnt + 99) / 100) - 1;
            int i95 = (int) ((95L * cnt + 99) / 100) - 1;
            int p50 = il.a[i50], p95 = il.a[i95], mx = il.a[il.n - 1];
            sb.append("path ").append(new String(names.get(idx), java.nio.charset.StandardCharsets.ISO_8859_1))
              .append(' ').append(cnt)
              .append(' ').append(p50 / 10).append('.').append(p50 % 10)
              .append(' ').append(p95 / 10).append('.').append(p95 % 10)
              .append(' ').append(mx / 10).append('.').append(mx % 10)
              .append('\n');
        }

        System.out.print(sb);
    }
}
