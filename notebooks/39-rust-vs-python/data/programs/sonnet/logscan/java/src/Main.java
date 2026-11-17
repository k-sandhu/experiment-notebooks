import java.io.FileInputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.util.Arrays;

public class Main {
    static byte[] arena = new byte[1 << 16];
    static int arenaLen = 0;
    static int[] eOff = new int[256], eLen = new int[256], eCount = new int[256];
    static long[] eHash = new long[256];
    static int nEntries = 0;
    static int[] table;
    static int tableMask;
    static int[] recTid = new int[1 << 16];
    static long[] recLat = new long[1 << 16];
    static int nRec = 0;
    static byte[] tmpl = new byte[1024];

    static long lines = 0, malformed = 0;
    static final long[] statusCount = new long[10];

    static void growTable() {
        int cap = table == null ? 1024 : table.length * 2;
        table = new int[cap];
        Arrays.fill(table, -1);
        tableMask = cap - 1;
        for (int i = 0; i < nEntries; i++) {
            int h = (int) eHash[i] & tableMask;
            while (table[h] >= 0) h = (h + 1) & tableMask;
            table[h] = i;
        }
    }

    static int lookup(byte[] t, int len) {
        long h = 0xcbf29ce484222325L;
        for (int i = 0; i < len; i++) h = (h ^ (t[i] & 0xff)) * 0x100000001b3L;
        h ^= h >>> 29;
        int slot = (int) h & tableMask;
        while (true) {
            int id = table[slot];
            if (id < 0) break;
            if (eHash[id] == h && eLen[id] == len && Arrays.equals(arena, eOff[id], eOff[id] + len, t, 0, len)) return id;
            slot = (slot + 1) & tableMask;
        }
        if (nEntries == eOff.length) {
            int c = nEntries * 2;
            eOff = Arrays.copyOf(eOff, c);
            eLen = Arrays.copyOf(eLen, c);
            eCount = Arrays.copyOf(eCount, c);
            eHash = Arrays.copyOf(eHash, c);
        }
        if (arenaLen + len > arena.length) arena = Arrays.copyOf(arena, Math.max(arena.length * 2, arenaLen + len));
        System.arraycopy(t, 0, arena, arenaLen, len);
        int id = nEntries++;
        eOff[id] = arenaLen;
        eLen[id] = len;
        eCount[id] = 0;
        eHash[id] = h;
        arenaLen += len;
        if (nEntries * 2 > table.length) growTable();
        else table[slot] = id;
        return id;
    }

    static boolean dig(byte c) {
        return (c - '0') >= 0 && (c - '0') < 10;
    }

    static boolean pathChar(int c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-';
    }

    static boolean match(byte[] b, int p, String w) {
        for (int i = 0; i < w.length(); i++) if (b[p + i] != w.charAt(i)) return false;
        return true;
    }

    static void processLine(byte[] b, int s, int e) {
        lines++;
        int p = s;
        if (e - s < 40) { malformed++; return; }
        if (!(dig(b[p]) && dig(b[p + 1]) && dig(b[p + 2]) && dig(b[p + 3]) && b[p + 4] == '-' && dig(b[p + 5]) &&
              dig(b[p + 6]) && b[p + 7] == '-' && dig(b[p + 8]) && dig(b[p + 9]) && b[p + 10] == 'T' && dig(b[p + 11]) &&
              dig(b[p + 12]) && b[p + 13] == ':' && dig(b[p + 14]) && dig(b[p + 15]) && b[p + 16] == ':' && dig(b[p + 17]) &&
              dig(b[p + 18]) && b[p + 19] == '.' && dig(b[p + 20]) && dig(b[p + 21]) && dig(b[p + 22]) && b[p + 23] == 'Z' &&
              b[p + 24] == ' ')) { malformed++; return; }
        p += 25;
        int q = p;
        while (q < e && b[q] >= 'a' && b[q] <= 'z') q++;
        if (q == p || q >= e || b[q] != '-') { malformed++; return; }
        q++;
        p = q;
        while (q < e && dig(b[q])) q++;
        if (q == p || q >= e || b[q] != ' ') { malformed++; return; }
        p = q + 1;
        if (e - p < 8) { malformed++; return; }
        byte m = b[p];
        if (m == 'G' && match(b, p, "GET ")) p += 4;
        else if (m == 'P' && match(b, p, "PUT ")) p += 4;
        else if (m == 'P' && match(b, p, "POST ")) p += 5;
        else if (m == 'P' && match(b, p, "PATCH ")) p += 6;
        else if (m == 'D' && match(b, p, "DELETE ")) p += 7;
        else { malformed++; return; }
        if (p >= e || b[p] != '/') { malformed++; return; }
        int pathStart = p;
        p++;
        while (p < e && pathChar(b[p])) p++;
        int pathEnd = p;
        if (p >= e) { malformed++; return; }
        if (b[p] == '?') {
            p++;
            while (p < e && b[p] != ' ') p++;
            if (p >= e) { malformed++; return; }
        }
        if (b[p] != ' ') { malformed++; return; }
        p++;
        if (e - p < 5 || !(dig(b[p]) && dig(b[p + 1]) && dig(b[p + 2]) && b[p + 3] == ' ')) { malformed++; return; }
        int cls = b[p] - '0';
        p += 4;
        q = p;
        while (q < e && dig(b[q])) q++;
        if (q == p || e - q < 2 || b[q] != 'B' || b[q + 1] != ' ') { malformed++; return; }
        p = q + 2;
        long lat = 0;
        q = p;
        while (q < e && dig(b[q])) { lat = lat * 10 + (b[q] - '0'); q++; }
        if (q == p || e - q < 6 || b[q] != '.' || !dig(b[q + 1]) || b[q + 2] != 'm' || b[q + 3] != 's' || b[q + 4] != ' ' || b[q + 5] != '"') {
            malformed++;
            return;
        }
        lat = lat * 10 + (b[q + 1] - '0');
        p = q + 6;
        int last = e - 1;
        if (p > last || b[last] != '"') { malformed++; return; }
        for (int i = p; i < last; i++) if (b[i] == '"') { malformed++; return; }

        statusCount[cls]++;
        int plen = pathEnd - pathStart;
        if (tmpl.length < plen * 4 + 8) tmpl = new byte[plen * 4 + 8];
        byte[] t = tmpl;
        int out = 0;
        t[out++] = '/';
        int segStart = out;
        boolean allDigits = true;
        for (int c = pathStart + 1; ; c++) {
            if (c == pathEnd || b[c] == '/') {
                if (allDigits && out > segStart) {
                    out = segStart;
                    t[out++] = '{'; t[out++] = 'i'; t[out++] = 'd'; t[out++] = '}';
                }
                if (c == pathEnd) break;
                t[out++] = '/';
                segStart = out;
                allDigits = true;
            } else {
                byte ch = b[c];
                t[out++] = ch;
                allDigits &= dig(ch);
            }
        }
        int id = lookup(t, out);
        eCount[id]++;
        if (nRec == recTid.length) {
            recTid = Arrays.copyOf(recTid, nRec * 2);
            recLat = Arrays.copyOf(recLat, nRec * 2);
        }
        recTid[nRec] = id;
        recLat[nRec++] = lat;
    }

    static void fmtLat(StringBuilder o, long v) {
        o.append(v / 10).append('.').append((char) ('0' + v % 10));
    }

    static int cmpEntries(int a, int b) {
        if (eCount[a] != eCount[b]) return eCount[a] > eCount[b] ? -1 : 1;
        return Arrays.compareUnsigned(arena, eOff[a], eOff[a] + eLen[a], arena, eOff[b], eOff[b] + eLen[b]);
    }

    public static void main(String[] args) throws IOException {
        growTable();
        int cap = 1 << 22, have = 0;
        byte[] buf = new byte[cap];
        try (FileInputStream in = new FileInputStream(args[0])) {
            while (true) {
                int n = in.read(buf, have, cap - have);
                boolean eof = n <= 0;
                if (!eof) have += n;
                int cur = 0;
                while (cur < have) {
                    int nl = cur;
                    while (nl < have && buf[nl] != '\n') nl++;
                    if (nl == have) break;
                    processLine(buf, cur, nl);
                    cur = nl + 1;
                }
                int rest = have - cur;
                if (eof) {
                    if (rest > 0) processLine(buf, cur, have);
                    break;
                }
                if (cur > 0) System.arraycopy(buf, cur, buf, 0, rest);
                have = rest;
                if (have == cap) {
                    cap *= 2;
                    buf = Arrays.copyOf(buf, cap);
                }
            }
        }

        StringBuilder o = new StringBuilder();
        o.append("lines ").append(lines).append('\n');
        o.append("malformed ").append(malformed).append('\n');
        for (int c = 0; c < 10; c++)
            if (statusCount[c] != 0) o.append("status ").append((char) ('0' + c)).append("xx ").append(statusCount[c]).append('\n');
        Integer[] order = new Integer[nEntries];
        for (int i = 0; i < nEntries; i++) order[i] = i;
        Arrays.sort(order, Main::cmpEntries);
        int top = Math.min(10, nEntries);
        long[] v = new long[0];
        for (int k = 0; k < top; k++) {
            int id = order[k];
            int cnt = eCount[id];
            if (v.length < cnt) v = new long[cnt];
            int j = 0;
            long mx = 0;
            for (int i = 0; i < nRec; i++) {
                if (recTid[i] == id) {
                    long x = recLat[i];
                    v[j++] = x;
                    if (x > mx) mx = x;
                }
            }
            int r50 = (int) ((50L * cnt + 99) / 100), r95 = (int) ((95L * cnt + 99) / 100);
            long p50 = -1, p95 = -1;
            if (mx < (1 << 22)) {
                int[] hist = new int[(int) mx + 1];
                for (int i = 0; i < cnt; i++) hist[(int) v[i]]++;
                long acc = 0;
                for (int b = 0; b <= mx; b++) {
                    acc += hist[b];
                    if (p50 < 0 && acc >= r50) p50 = b;
                    if (acc >= r95) { p95 = b; break; }
                }
            } else {
                Arrays.sort(v, 0, cnt);
                p50 = v[r50 - 1];
                p95 = v[r95 - 1];
            }
            o.append("path ").append(new String(arena, eOff[id], eLen[id], java.nio.charset.StandardCharsets.ISO_8859_1));
            o.append(' ').append(cnt).append(' ');
            fmtLat(o, p50);
            o.append(' ');
            fmtLat(o, p95);
            o.append(' ');
            fmtLat(o, mx);
            o.append('\n');
        }
        PrintStream ps = new PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), false);
        ps.print(o);
        ps.flush();
    }
}
