import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    static byte[] d;
    static int n, i, pathS, pathE, statusDigit, latency;
    static final boolean[] pathCharTab = new boolean[256];
    static {
        for (int c = 0; c < 256; c++)
            pathCharTab[c] = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-';
    }
    static boolean isDigit(byte c) { return c >= '0' && c <= '9'; }

    static boolean parseLine() {
        int i = Main.i;
        byte[] d = Main.d; int n = Main.n;
        if (i + 25 > n) { Main.i = i; return false; }
        if (!(isDigit(d[i]) && isDigit(d[i+1]) && isDigit(d[i+2]) && isDigit(d[i+3]) && d[i+4] == '-' &&
              isDigit(d[i+5]) && isDigit(d[i+6]) && d[i+7] == '-' && isDigit(d[i+8]) && isDigit(d[i+9]) &&
              d[i+10] == 'T' && isDigit(d[i+11]) && isDigit(d[i+12]) && d[i+13] == ':' && isDigit(d[i+14]) &&
              isDigit(d[i+15]) && d[i+16] == ':' && isDigit(d[i+17]) && isDigit(d[i+18]) && d[i+19] == '.' &&
              isDigit(d[i+20]) && isDigit(d[i+21]) && isDigit(d[i+22]) && d[i+23] == 'Z' && d[i+24] == ' ')) { Main.i = i; return false; }
        i += 25;
        { int s = i; while (i < n && d[i] >= 'a' && d[i] <= 'z') i++; if (i == s) { Main.i = i; return false; } }
        if (i >= n || d[i] != '-') { Main.i = i; return false; } i++;
        { int s = i; while (i < n && isDigit(d[i])) i++; if (i == s) { Main.i = i; return false; } }
        if (i >= n || d[i] != ' ') { Main.i = i; return false; } i++;
        if (i >= n) { Main.i = i; return false; }
        switch (d[i]) {
            case 'G':
                if (i + 4 <= n && d[i+1] == 'E' && d[i+2] == 'T' && d[i+3] == ' ') i += 4; else { Main.i = i; return false; } break;
            case 'D':
                if (i + 7 <= n && d[i+1] == 'E' && d[i+2] == 'L' && d[i+3] == 'E' && d[i+4] == 'T' && d[i+5] == 'E' && d[i+6] == ' ') i += 7; else { Main.i = i; return false; } break;
            case 'P':
                if (i + 1 >= n) { Main.i = i; return false; }
                if (d[i+1] == 'O') { if (i + 5 <= n && d[i+2] == 'S' && d[i+3] == 'T' && d[i+4] == ' ') i += 5; else { Main.i = i; return false; } }
                else if (d[i+1] == 'U') { if (i + 4 <= n && d[i+2] == 'T' && d[i+3] == ' ') i += 4; else { Main.i = i; return false; } }
                else if (d[i+1] == 'A') { if (i + 6 <= n && d[i+2] == 'T' && d[i+3] == 'C' && d[i+4] == 'H' && d[i+5] == ' ') i += 6; else { Main.i = i; return false; } }
                else { Main.i = i; return false; }
                break;
            default: Main.i = i; return false;
        }
        if (i >= n || d[i] != '/') { Main.i = i; return false; }
        pathS = i; i++;
        while (i < n && pathCharTab[d[i] & 0xFF]) i++;
        pathE = i;
        if (i < n && d[i] == '?') { i++; while (i < n && d[i] != ' ' && d[i] != '\n') i++; }
        if (i >= n || d[i] != ' ') { Main.i = i; return false; } i++;
        if (i + 3 > n || !isDigit(d[i]) || !isDigit(d[i+1]) || !isDigit(d[i+2])) { Main.i = i; return false; }
        statusDigit = d[i] - '0'; i += 3;
        if (i >= n || d[i] != ' ') { Main.i = i; return false; } i++;
        { int s = i; while (i < n && isDigit(d[i])) i++; if (i == s) { Main.i = i; return false; } }
        if (i >= n || d[i] != 'B') { Main.i = i; return false; } i++;
        if (i >= n || d[i] != ' ') { Main.i = i; return false; } i++;
        { int s = i; long v = 0; while (i < n && isDigit(d[i])) { v = v * 10 + (d[i] - '0'); i++; } if (i == s) { Main.i = i; return false; }
          if (i >= n || d[i] != '.') { Main.i = i; return false; } i++;
          if (i >= n || !isDigit(d[i])) { Main.i = i; return false; } v = v * 10 + (d[i] - '0'); i++;
          latency = (int) v; }
        if (i + 2 > n || d[i] != 'm' || d[i+1] != 's') { Main.i = i; return false; } i += 2;
        if (i >= n || d[i] != ' ') { Main.i = i; return false; } i++;
        if (i >= n || d[i] != '"') { Main.i = i; return false; } i++;
        while (i < n && d[i] != '"' && d[i] != '\n') i++;
        if (i >= n || d[i] != '"') { Main.i = i; return false; } i++;
        if (i < n && d[i] != '\n') { Main.i = i; return false; }
        Main.i = i; return true;
    }

    static long hashBytes(byte[] s, int off, int len) {
        long h = 1469598103934665603L;
        for (int k = 0; k < len; k++) { h ^= (s[off + k] & 0xFFL); h *= 1099511628211L; }
        h ^= h >>> 33; h *= 0xff51afd7ed558ccdL; h ^= h >>> 33; h *= 0xc4ceb9fe1a85ec53L; h ^= h >>> 33;
        return h;
    }

    static int compareTemplates(byte[] arena, int offA, int lenA, int offB, int lenB) {
        int m = Math.min(lenA, lenB);
        for (int k = 0; k < m; k++) {
            int a = arena[offA + k] & 0xFF, b = arena[offB + k] & 0xFF;
            if (a != b) return a - b;
        }
        return lenA - lenB;
    }

    public static void main(String[] args) throws IOException {
        d = Files.readAllBytes(Path.of(args[0]));
        n = d.length; i = 0;
        long lines = 0, malformed = 0;
        long[] statusCnt = new long[10];

        byte[] arena = new byte[1 << 16]; int arenaLen = 0;
        int[] offs = new int[1024], lens = new int[1024], counts = new int[1024];
        long[] hashes = new long[1024];
        int templates = 0;
        int tableSize = 1024; int[] table = new int[tableSize]; Arrays.fill(table, -1); int mask = tableSize - 1;

        int est = n / 100 + 16;
        int[] lats = new int[est], ids = new int[est]; int pairs = 0;
        byte[] scratch = new byte[256];

        while (i < n) {
            lines++;
            if (parseLine()) {
                statusCnt[statusDigit]++;
                int pathLen = pathE - pathS;
                int need = pathLen * 3 + 8;
                if (scratch.length < need) scratch = new byte[need];
                int sl = 0; int j = pathS;
                while (true) {
                    int segS = j; boolean allDig = true;
                    while (j < pathE && d[j] != '/') { if (!isDigit(d[j])) allDig = false; j++; }
                    if (j > segS && allDig) { scratch[sl++] = '{'; scratch[sl++] = 'i'; scratch[sl++] = 'd'; scratch[sl++] = '}'; }
                    else if (j > segS) { System.arraycopy(d, segS, scratch, sl, j - segS); sl += j - segS; }
                    if (j >= pathE) break;
                    scratch[sl++] = '/'; j++;
                }
                long h = hashBytes(scratch, 0, sl);
                int hidx = (int) h & mask; int id = -1;
                while (true) {
                    int t = table[hidx];
                    if (t == -1) break;
                    if (hashes[t] == h && lens[t] == sl && Arrays.equals(arena, offs[t], offs[t] + sl, scratch, 0, sl)) { id = t; break; }
                    hidx = (hidx + 1) & mask;
                }
                if (id == -1) {
                    if ((templates + 1) * 10 > tableSize * 7) {
                        int ns = tableSize * 2; int[] nt = new int[ns]; Arrays.fill(nt, -1); int nm = ns - 1;
                        for (int t = 0; t < templates; t++) { int hh = (int) hashes[t] & nm; while (nt[hh] != -1) hh = (hh + 1) & nm; nt[hh] = t; }
                        table = nt; tableSize = ns; mask = nm;
                        hidx = (int) h & mask; while (table[hidx] != -1) hidx = (hidx + 1) & mask;
                    }
                    if (templates == offs.length) {
                        int nc = offs.length * 2;
                        offs = Arrays.copyOf(offs, nc); lens = Arrays.copyOf(lens, nc); counts = Arrays.copyOf(counts, nc); hashes = Arrays.copyOf(hashes, nc);
                    }
                    if (arenaLen + sl > arena.length) arena = Arrays.copyOf(arena, Math.max(arena.length * 2, arenaLen + sl));
                    id = templates++;
                    table[hidx] = id;
                    offs[id] = arenaLen; System.arraycopy(scratch, 0, arena, arenaLen, sl); arenaLen += sl;
                    lens[id] = sl; counts[id] = 0; hashes[id] = h;
                }
                counts[id]++;
                if (pairs == lats.length) { int nc = lats.length * 2; lats = Arrays.copyOf(lats, nc); ids = Arrays.copyOf(ids, nc); }
                lats[pairs] = latency; ids[pairs] = id; pairs++;
                if (i < n) i++;
            } else {
                malformed++;
                while (i < n && d[i] != '\n') i++;
                if (i < n) i++;
            }
        }
        d = null;

        Integer[] order = new Integer[templates];
        for (int k = 0; k < templates; k++) order[k] = k;
        final byte[] ar = arena; final int[] of = offs, ln = lens, ct = counts;
        Arrays.sort(order, (a, b) -> {
            if (ct[a] != ct[b]) return ct[b] - ct[a];
            return compareTemplates(ar, of[a], ln[a], of[b], ln[b]);
        });
        int K = Math.min(templates, 10);
        int[][] tops = new int[K][];
        int[] slot = new int[templates]; Arrays.fill(slot, -1);
        for (int k = 0; k < K; k++) { slot[order[k]] = k; tops[k] = new int[counts[order[k]]]; }
        int[] fill = new int[K];
        for (int q = 0; q < pairs; q++) { int s = slot[ids[q]]; if (s >= 0) tops[s][fill[s]++] = lats[q]; }
        for (int k = 0; k < K; k++) Arrays.sort(tops[k]);

        StringBuilder out = new StringBuilder(1024);
        out.append("lines ").append(lines).append('\n');
        out.append("malformed ").append(malformed).append('\n');
        for (int dig = 0; dig < 10; dig++) if (statusCnt[dig] > 0)
            out.append("status ").append(dig).append("xx ").append(statusCnt[dig]).append('\n');
        for (int k = 0; k < K; k++) {
            int id = order[k]; int[] vec = tops[k]; long nn = vec.length;
            int p50 = vec[(int) ((50 * nn + 99) / 100 - 1)];
            int p95 = vec[(int) ((95 * nn + 99) / 100 - 1)];
            int mx = vec[vec.length - 1];
            out.append("path ");
            out.append(new String(arena, offs[id], lens[id], StandardCharsets.US_ASCII));
            out.append(' ').append(counts[id]).append(' ');
            appendLat(out, p50); out.append(' '); appendLat(out, p95); out.append(' '); appendLat(out, mx); out.append('\n');
        }
        OutputStream os = System.out;
        os.write(out.toString().getBytes(StandardCharsets.US_ASCII));
        os.flush();
    }
    static void appendLat(StringBuilder out, int v) { out.append(v / 10).append('.').append(v % 10); }
}
