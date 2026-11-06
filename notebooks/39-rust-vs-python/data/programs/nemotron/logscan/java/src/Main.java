import java.io.BufferedOutputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// Log scan: summarise an access log by status class and path-template latency percentiles.
// Java 23, SE classes only (Jackson provided but not needed).

public class Main {
    static final class Stats {
        int count;
        int maxT; // max latency in tenths of a ms
        int[] lats = new int[16];
        int len;

        void add(int t) {
            count++;
            if (t > maxT) maxT = t;
            if (len == lats.length) {
                int[] n = new int[lats.length * 2];
                System.arraycopy(lats, 0, n, 0, len);
                lats = n;
            }
            lats[len++] = t;
        }
    }

    static final class Res {
        int statusClass;
        int latencyT;
        int tlen;
    }

    private static boolean isDigit(int c) {
        return c >= '0' && c <= '9';
    }

    private static boolean isUpper(int c) {
        return c >= 'A' && c <= 'Z';
    }

    private static boolean isLower(int c) {
        return c >= 'a' && c <= 'z';
    }

    // Strictly validates one line and, if well-formed, extracts the status class,
    // the latency in tenths of a ms, and the path template into tb[0..tlen).
    // Returns the (possibly grown) template buffer.
    static char[] parseLine(byte[] b, int p, int end, char[] tb, Res r) {
        // 1. timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<space>
        if (end - p < 25) return null;
        if (!isDigit(b[p]) || !isDigit(b[p + 1]) || !isDigit(b[p + 2]) || !isDigit(b[p + 3])) return null;
        if (b[p + 4] != '-') return null;
        if (!isDigit(b[p + 5]) || !isDigit(b[p + 6])) return null;
        if (b[p + 7] != '-') return null;
        if (!isDigit(b[p + 8]) || !isDigit(b[p + 9])) return null;
        if (b[p + 10] != 'T') return null;
        if (!isDigit(b[p + 11]) || !isDigit(b[p + 12])) return null;
        if (b[p + 13] != ':') return null;
        if (!isDigit(b[p + 14]) || !isDigit(b[p + 15])) return null;
        if (b[p + 16] != ':') return null;
        if (!isDigit(b[p + 17]) || !isDigit(b[p + 18])) return null;
        if (b[p + 19] != '.') return null;
        if (!isDigit(b[p + 20]) || !isDigit(b[p + 21]) || !isDigit(b[p + 22])) return null;
        if (b[p + 23] != 'Z' || b[p + 24] != ' ') return null;
        p += 25;

        // 2. host: [a-z]+-\d+<space>
        if (p >= end || !isLower(b[p])) return null;
        do { p++; } while (p < end && isLower(b[p]));
        if (p >= end || b[p] != '-') return null;
        p++;
        if (p >= end || !isDigit(b[p])) return null;
        do { p++; } while (p < end && isDigit(b[p]));
        if (p >= end || b[p] != ' ') return null;
        p++;

        // 3. method: GET/POST/PUT/DELETE/PATCH followed by <space>
        boolean ok = false;
        if (!ok && end - p > 3 && b[p] == 'G' && b[p + 1] == 'E' && b[p + 2] == 'T' && b[p + 3] == ' ') { p += 4; ok = true; }
        if (!ok && end - p > 4 && b[p] == 'P' && b[p + 1] == 'O' && b[p + 2] == 'S' && b[p + 3] == 'T' && b[p + 4] == ' ') { p += 5; ok = true; }
        if (!ok && end - p > 3 && b[p] == 'P' && b[p + 1] == 'U' && b[p + 2] == 'T' && b[p + 3] == ' ') { p += 4; ok = true; }
        if (!ok && end - p > 6 && b[p] == 'D' && b[p + 1] == 'E' && b[p + 2] == 'L' && b[p + 3] == 'E' && b[p + 4] == 'T' && b[p + 5] == 'E' && b[p + 6] == ' ') { p += 7; ok = true; }
        if (!ok && end - p > 5 && b[p] == 'P' && b[p + 1] == 'A' && b[p + 2] == 'T' && b[p + 3] == 'C' && b[p + 4] == 'H' && b[p + 5] == ' ') { p += 6; ok = true; }
        if (!ok) return null;

        // 4. path: '/' [A-Za-z0-9_/-]* [ '?' [^ ]* ] <space> ; build template
        r.tlen = 0;
        if (p >= end || b[p] != '/') return null;
        int segStart = 0;
        boolean segDigits = true;
        int segLen = 0;
        for (;;) {
            if (p >= end) return null; // path must end with space
            int c = b[p] & 0xFF;
            if (c == '/') {
                if (segLen > 0 && segDigits) {
                    if (r.tlen == tb.length) tb = grow(tb);
                    r.tlen = segStart;
                    tb[r.tlen++] = '{';
                    tb[r.tlen++] = 'i';
                    tb[r.tlen++] = 'd';
                    tb[r.tlen++] = '}';
                }
                if (r.tlen == tb.length) tb = grow(tb);
                tb[r.tlen++] = '/';
                segStart = r.tlen;
                segDigits = true;
                segLen = 0;
                p++;
            } else if (c == ' ') {
                if (segLen > 0 && segDigits) {
                    if (r.tlen == tb.length) tb = grow(tb);
                    r.tlen = segStart;
                    tb[r.tlen++] = '{';
                    tb[r.tlen++] = 'i';
                    tb[r.tlen++] = 'd';
                    tb[r.tlen++] = '}';
                }
                p++;
                break;
            } else if (c == '?') {
                if (segLen > 0 && segDigits) {
                    if (r.tlen == tb.length) tb = grow(tb);
                    r.tlen = segStart;
                    tb[r.tlen++] = '{';
                    tb[r.tlen++] = 'i';
                    tb[r.tlen++] = 'd';
                    tb[r.tlen++] = '}';
                }
                p++;
                while (p < end && b[p] != ' ') p++;
                if (p >= end) return null;
                p++;
                break;
            } else {
                if (!isDigit(c) && !isUpper(c) && !isLower(c) && c != '_' && c != '-') return null;
                if (segLen == 0) segDigits = isDigit(c);
                else if (segDigits && !isDigit(c)) segDigits = false;
                segLen++;
                if (r.tlen == tb.length) tb = grow(tb);
                tb[r.tlen++] = (char) c;
                p++;
            }
        }

        // 5. status: \d{3}<space>
        if (end - p < 4) return null;
        if (!isDigit(b[p]) || !isDigit(b[p + 1]) || !isDigit(b[p + 2])) return null;
        if (b[p + 3] != ' ') return null;
        r.statusClass = b[p] - '0';
        p += 4;

        // 6. size: \d+B<space>
        if (p >= end || !isDigit(b[p])) return null;
        do { p++; } while (p < end && isDigit(b[p]));
        if (p >= end || b[p] != 'B') return null;
        p++;
        if (p >= end || b[p] != ' ') return null;
        p++;

        // 7. latency: \d+.\d ms<space>
        int ls = p;
        long ip = 0;
        while (p < end && isDigit(b[p])) { ip = ip * 10 + (b[p] - '0'); p++; }
        if (p == ls || p >= end || b[p] != '.') return null;
        p++;
        if (p >= end || !isDigit(b[p])) return null;
        int frac = b[p] - '0';
        p++;
        if (end - p < 3 || b[p] != 'm' || b[p + 1] != 's' || b[p + 2] != ' ') return null;
        p += 3;
        r.latencyT = (int) (ip * 10 + frac);

        // 8. "..." then end of line
        if (p >= end || b[p] != '"') return null;
        p++;
        while (p < end && b[p] != '"') p++;
        if (p >= end) return null;
        p++;
        if (p != end) return null;
        return tb;
    }

    private static char[] grow(char[] tb) {
        char[] n = new char[tb.length * 2];
        System.arraycopy(tb, 0, n, 0, tb.length);
        return n;
    }

    private static int pos(int pct, int nn) {
        return (pct * nn + 99) / 100 - 1; // nearest-rank, 0-based index
    }

    public static void main(String[] args) throws Exception {
        byte[] b = Files.readAllBytes(Path.of(args[0]));
        int n = b.length;
        int p = 0;
        long lines = 0, malformed = 0;
        long[] statusCount = new long[10];
        Map<String, Stats> map = new HashMap<>();
        char[] tb = new char[1024];
        Res r = new Res();

        while (p < n) {
            int nl = p;
            while (nl < n && b[nl] != '\n') nl++;
            int lineEnd = nl;
            ++lines;
            char[] nt = parseLine(b, p, lineEnd, tb, r);
            if (nt != null) {
                tb = nt;
                statusCount[r.statusClass]++;
                String key = new String(tb, 0, r.tlen);
                Stats s = map.get(key);
                if (s == null) {
                    s = new Stats();
                    map.put(key, s);
                }
                s.add(r.latencyT);
            } else {
                ++malformed;
            }
            p = lineEnd + 1;
        }

        StringBuilder sb = new StringBuilder();
        sb.append("lines ").append(lines).append('\n');
        sb.append("malformed ").append(malformed).append('\n');
        for (int d = 0; d < 10; d++) {
            if (statusCount[d] != 0) {
                sb.append("status ").append((char) ('0' + d)).append("xx ").append(statusCount[d]).append('\n');
            }
        }
        List<Map.Entry<String, Stats>> paths = new ArrayList<>(map.entrySet());
        paths.sort((x, y) -> {
            int c = Long.compare(y.getValue().count, x.getValue().count);
            if (c != 0) return c;
            return x.getKey().compareTo(y.getKey());
        });
        int lim = Math.min(paths.size(), 10);
        for (int i = 0; i < lim; i++) {
            Map.Entry<String, Stats> pe = paths.get(i);
            Stats s = pe.getValue();
            Arrays.sort(s.lats, 0, s.len);
            int nn = s.len;
            sb.append("path ").append(pe.getKey()).append(' ').append(s.count).append(' ');
            sb.append(s.lats[pos(50, nn)] / 10).append('.').append(s.lats[pos(50, nn)] % 10).append(' ');
            sb.append(s.lats[pos(95, nn)] / 10).append('.').append(s.lats[pos(95, nn)] % 10).append(' ');
            sb.append(s.maxT / 10).append('.').append(s.maxT % 10).append('\n');
        }
        OutputStream out = new BufferedOutputStream(System.out);
        out.write(sb.toString().getBytes("US-ASCII"));
        out.flush();
    }
}
