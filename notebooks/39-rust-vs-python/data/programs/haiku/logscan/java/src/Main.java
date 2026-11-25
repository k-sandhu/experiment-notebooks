import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;

// Log scan: status-class counts and latency percentiles of the busiest path templates (see SPEC.md).
//
// The file is streamed in 1 MiB chunks. Each line is checked by a hand-written matcher that accepts
// exactly the language of the SPEC regex. Path templates are interned in an open-addressing table keyed
// by bytes, so no String is created per line. Only the ten busiest templates have their latencies sorted.
public class Main {
    static final int CHUNK_SIZE = 1 << 20;
    static final int TOP_N = 10;

    // Characters allowed in the path group: [A-Za-z0-9_/-], indexed by unsigned byte value.
    static final boolean[] PATH_CHAR = new boolean[256];
    static final byte[] TIMESTAMP = "dddd-dd-ddTdd:dd:dd.dddZ".getBytes(StandardCharsets.US_ASCII);

    static {
        for (int c = 0; c < 256; c++) {
            PATH_CHAR[c] = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
                    || c == '_' || c == '/' || c == '-';
        }
    }

    static final class Template {
        final byte[] name;
        final int hash;
        long count;
        long[] latencies = new long[4];  // tenths of a millisecond
        int size;

        Template(byte[] name, int hash) {
            this.name = name;
            this.hash = hash;
        }
    }

    static final class LogScanner {
        long total;
        long malformed;
        final long[] statusCount = new long[10];

        // Fields set by parseLine for the line that matched.
        private int pathStart;
        private int pathEnd;
        private int statusClass;
        private long tenths;

        private byte[] tmpl = new byte[1024];
        private int tmplLen;

        private final ArrayList<Template> templates = new ArrayList<>();
        private int[] table = new int[1 << 12];  // stores template index + 1; 0 means empty

        void add(byte[] b, int p, int e) {
            total++;
            if (!parseLine(b, p, e)) {
                malformed++;
                return;
            }
            statusCount[statusClass]++;
            buildTemplate(b);
            int h = hash(tmpl, tmplLen);
            Template t = find(h);
            t.count++;
            if (t.size == t.latencies.length) t.latencies = Arrays.copyOf(t.latencies, t.size * 2);
            t.latencies[t.size++] = tenths;
        }

        // Finds the template for tmpl[0..tmplLen), creating it if needed.
        private Template find(int h) {
            int mask = table.length - 1;
            int i = h & mask;
            for (int v = table[i]; v != 0; v = table[i]) {
                Template t = templates.get(v - 1);
                if (t.hash == h && t.name.length == tmplLen
                        && Arrays.equals(t.name, 0, tmplLen, tmpl, 0, tmplLen)) {
                    return t;
                }
                i = (i + 1) & mask;
            }
            Template t = new Template(Arrays.copyOf(tmpl, tmplLen), h);
            templates.add(t);
            table[i] = templates.size();
            if (templates.size() * 2 > table.length) grow();
            return t;
        }

        private void grow() {
            int[] bigger = new int[table.length * 2];
            int mask = bigger.length - 1;
            for (int k = 0; k < templates.size(); k++) {
                int i = templates.get(k).hash & mask;
                while (bigger[i] != 0) i = (i + 1) & mask;
                bigger[i] = k + 1;
            }
            table = bigger;
        }

        static int hash(byte[] b, int n) {
            int h = 0x811c9dc5;  // FNV-1a
            for (int i = 0; i < n; i++) h = (h ^ b[i]) * 0x01000193;
            h ^= h >>> 16;
            h *= 0x85ebca6b;
            return h ^ (h >>> 13);
        }

        // Path template: each non-empty all-digit segment becomes {id}. Writes into tmpl.
        private void buildTemplate(byte[] b) {
            int len = pathEnd - pathStart;
            if (tmpl.length < 4 * len + 4) tmpl = new byte[4 * len + 4];
            byte[] out = tmpl;
            int n = 0;
            int s = pathStart;
            for (;;) {
                int e = s;
                boolean digits = true;
                while (e < pathEnd && b[e] != '/') {
                    digits &= isDigit(b[e]);
                    e++;
                }
                if (e > s && digits) {
                    out[n++] = '{';
                    out[n++] = 'i';
                    out[n++] = 'd';
                    out[n++] = '}';
                } else {
                    System.arraycopy(b, s, out, n, e - s);
                    n += e - s;
                }
                if (e == pathEnd) break;
                out[n++] = '/';
                s = e + 1;
            }
            tmplLen = n;
        }

        // Matches one line b[p, e) (without its '\n') against the SPEC regex. Returns false if malformed.
        private boolean parseLine(byte[] b, int p, int e) {
            if (e - p < 25) return false;
            for (int i = 0; i < 24; i++) {
                byte c = TIMESTAMP[i];
                if (c == 'd' ? !isDigit(b[p + i]) : b[p + i] != c) return false;
            }
            if (b[p + 24] != ' ') return false;

            // Host: [a-z]+-\d+ followed by a space.
            int q = p + 25;
            int s = q;
            while (q < e && isLower(b[q])) q++;
            if (q == s || q == e || b[q] != '-') return false;
            q++;
            s = q;
            while (q < e && isDigit(b[q])) q++;
            if (q == s || q == e || b[q] != ' ') return false;
            q++;

            // Method, then a space.
            if (startsWith(b, q, e, "GET ")) q += 4;
            else if (startsWith(b, q, e, "POST ")) q += 5;
            else if (startsWith(b, q, e, "PUT ")) q += 4;
            else if (startsWith(b, q, e, "DELETE ")) q += 7;
            else if (startsWith(b, q, e, "PATCH ")) q += 6;
            else return false;

            // Path: '/' and path characters, then an optional query running to the next space.
            if (q == e || b[q] != '/') return false;
            pathStart = q;
            q++;
            while (q < e && PATH_CHAR[b[q] & 0xFF]) q++;
            pathEnd = q;
            if (q < e && b[q] == '?') {
                while (q < e && b[q] != ' ') q++;
            }
            if (q == e || b[q] != ' ') return false;
            q++;

            // Status: three digits, then a space.
            if (e - q < 4 || !isDigit(b[q]) || !isDigit(b[q + 1]) || !isDigit(b[q + 2]) || b[q + 3] != ' ') {
                return false;
            }
            statusClass = b[q] - '0';
            q += 4;

            // Size: \d+B followed by a space.
            s = q;
            while (q < e && isDigit(b[q])) q++;
            if (q == s || q == e || b[q] != 'B') return false;
            q++;
            if (q == e || b[q] != ' ') return false;
            q++;

            // Latency: \d+ '.' \d 'ms' followed by a space, kept in tenths of a millisecond.
            s = q;
            long whole = 0;
            while (q < e && isDigit(b[q])) {
                whole = whole * 10 + (b[q] - '0');
                q++;
            }
            if (q == s || q == e || b[q] != '.') return false;
            q++;
            if (q == e || !isDigit(b[q])) return false;
            long frac = b[q] - '0';
            q++;
            if (e - q < 3 || b[q] != 'm' || b[q + 1] != 's' || b[q + 2] != ' ') return false;
            q += 3;
            tenths = whole * 10 + frac;

            // User agent: "[^"]*" which must end the line.
            if (e - q < 2 || b[q] != '"' || b[e - 1] != '"') return false;
            for (int u = q + 1; u < e - 1; u++) {
                if (b[u] == '"') return false;
            }
            return true;
        }

        private static boolean startsWith(byte[] b, int q, int e, String lit) {
            int n = lit.length();
            if (e - q < n) return false;
            for (int i = 0; i < n; i++) {
                if (b[q + i] != lit.charAt(i)) return false;
            }
            return true;
        }

        private static boolean isDigit(byte c) {
            return c >= '0' && c <= '9';
        }

        private static boolean isLower(byte c) {
            return c >= 'a' && c <= 'z';
        }

        String report() {
            StringBuilder sb = new StringBuilder();
            sb.append("lines ").append(total).append('\n');
            sb.append("malformed ").append(malformed).append('\n');
            for (int c = 0; c < 10; c++) {
                if (statusCount[c] != 0) {
                    sb.append("status ").append(c).append("xx ").append(statusCount[c]).append('\n');
                }
            }

            // Keep the TOP_N busiest templates, best first, by insertion into a small sorted array.
            ArrayList<Template> top = new ArrayList<>(TOP_N + 1);
            for (Template t : templates) {
                if (top.size() == TOP_N) {
                    if (!better(t, top.get(TOP_N - 1))) continue;
                    top.set(TOP_N - 1, t);
                } else {
                    top.add(t);
                }
                for (int k = top.size() - 1; k > 0 && better(top.get(k), top.get(k - 1)); k--) {
                    Template x = top.get(k);
                    top.set(k, top.get(k - 1));
                    top.set(k - 1, x);
                }
            }

            for (Template t : top) {
                long[] lat = Arrays.copyOf(t.latencies, t.size);
                Arrays.sort(lat);
                int n = lat.length;
                long p50 = lat[(int) ((50L * n + 99) / 100) - 1];
                long p95 = lat[(int) ((95L * n + 99) / 100) - 1];
                sb.append("path ").append(new String(t.name, StandardCharsets.US_ASCII)).append(' ')
                        .append(t.count).append(' ').append(formatTenths(p50)).append(' ')
                        .append(formatTenths(p95)).append(' ').append(formatTenths(lat[n - 1])).append('\n');
            }
            return sb.toString();
        }

        private static boolean better(Template a, Template b) {
            if (a.count != b.count) return a.count > b.count;
            return Arrays.compareUnsigned(a.name, b.name) < 0;
        }

        private static String formatTenths(long t) {
            return (t / 10) + "." + (char) ('0' + t % 10);
        }
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: Main INPUT_PATH");
            System.exit(2);
        }
        LogScanner scanner = new LogScanner();
        try (InputStream in = new FileInputStream(args[0])) {
            byte[] buf = new byte[CHUNK_SIZE];
            int start = 0;  // first byte of the unprocessed data
            int end = 0;    // one past the last byte read
            boolean eof = false;
            while (true) {
                int nl = indexOfNewline(buf, start, end);
                if (nl >= 0) {
                    scanner.add(buf, start, nl);
                    start = nl + 1;
                    continue;
                }
                if (eof) {
                    if (start < end) scanner.add(buf, start, end);  // last line without '\n'
                    break;
                }
                // No complete line in the buffer: move the partial line to the front and read more.
                if (start > 0) {
                    System.arraycopy(buf, start, buf, 0, end - start);
                    end -= start;
                    start = 0;
                }
                if (end == buf.length) buf = Arrays.copyOf(buf, buf.length * 2);  // one line longer than the buffer
                int n = in.read(buf, end, buf.length - end);
                if (n < 0) eof = true;
                else end += n;
            }
        }
        System.out.print(scanner.report());
        System.out.flush();
    }

    private static int indexOfNewline(byte[] buf, int from, int to) {
        for (int i = from; i < to; i++) {
            if (buf[i] == '\n') return i;
        }
        return -1;
    }
}
