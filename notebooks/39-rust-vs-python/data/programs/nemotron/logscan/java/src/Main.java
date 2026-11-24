import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    // Latencies for one path template (tenths of a ms).
    static final class Stats {
        int count;
        int[] lat = new int[16];
        int len;

        void add(int v) {
            if (len == lat.length) {
                int[] nw = new int[lat.length * 2];
                System.arraycopy(lat, 0, nw, 0, len);
                lat = nw;
            }
            lat[len++] = v;
        }
    }

    // Open-addressing map from path template -> Stats.
    // Keys are interned: lookup compares the raw char buffer against stored
    // strings, so only unique templates are ever allocated as String objects.
    static final class TMap {
        String[] keys;
        Stats[] vals;
        int mask;
        int size;

        TMap(int cap) {
            keys = new String[cap];
            vals = new Stats[cap];
            mask = cap - 1;
        }

        Stats findOrAdd(char[] buf, int start, int len) {
            int h = 0;
            for (int i = 0; i < len; i++) h = 31 * h + buf[start + i];
            h &= 0x7fffffff;
            for (int slot = h & mask; ; slot = (slot + 1) & mask) {
                String k = keys[slot];
                if (k == null) {
                    keys[slot] = new String(buf, start, len);
                    Stats v = new Stats();
                    vals[slot] = v;
                    if (++size * 4 > keys.length * 3) grow();
                    return v;
                }
                if (k.length() == len && same(k, buf, start, len)) return vals[slot];
            }
        }

        private static boolean same(String k, char[] buf, int start, int len) {
            for (int i = 0; i < len; i++) {
                if (k.charAt(i) != buf[start + i]) return false;
            }
            return true;
        }

        @SuppressWarnings("unused")
        private static int hashString(String s) {
            int h = 0;
            for (int i = 0; i < s.length(); i++) h = 31 * h + s.charAt(i);
            return h;
        }

        private void grow() {
            String[] oldK = keys;
            Stats[] oldV = vals;
            int cap = oldK.length * 2;
            keys = new String[cap];
            vals = new Stats[cap];
            mask = cap - 1;
            size = 0;
            for (int i = 0; i < oldK.length; i++) {
                String k = oldK[i];
                if (k != null) put0(k, oldV[i]);
            }
        }

        private void put0(String k, Stats v) {
            int h = 0;
            for (int i = 0; i < k.length(); i++) h = 31 * h + k.charAt(i);
            h &= 0x7fffffff;
            for (int slot = h & mask; ; slot = (slot + 1) & mask) {
                if (keys[slot] == null) {
                    keys[slot] = k;
                    vals[slot] = v;
                    ++size;
                    return;
                }
            }
        }
    }

    // Result of parsing one line.
    static final class Res {
        int cls;
        int lat; // tenths of a ms
        int pathStart;
        int pathEnd;
    }

    static final char[] DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};

    static boolean isDig(char c) {
        return c >= '0' && c <= '9';
    }

    // Validates one line (without its newline) against the SPEC.md regex.
    static boolean parseLine(String s, int start, int end, Res r) {
        int len = end - start;
        if (len < 49) return false; // shortest possible well-formed line

        // timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<sp>
        if (s.charAt(start + 4) != '-' || s.charAt(start + 7) != '-' ||
            s.charAt(start + 10) != 'T' || s.charAt(start + 13) != ':' ||
            s.charAt(start + 16) != ':' || s.charAt(start + 19) != '.' ||
            s.charAt(start + 23) != 'Z' || s.charAt(start + 24) != ' ')
            return false;
        if (!isDig(s.charAt(start)) || !isDig(s.charAt(start + 1)) ||
            !isDig(s.charAt(start + 2)) || !isDig(s.charAt(start + 3)) ||
            !isDig(s.charAt(start + 5)) || !isDig(s.charAt(start + 6)) ||
            !isDig(s.charAt(start + 8)) || !isDig(s.charAt(start + 9)) ||
            !isDig(s.charAt(start + 11)) || !isDig(s.charAt(start + 12)) ||
            !isDig(s.charAt(start + 14)) || !isDig(s.charAt(start + 15)) ||
            !isDig(s.charAt(start + 17)) || !isDig(s.charAt(start + 18)) ||
            !isDig(s.charAt(start + 20)) || !isDig(s.charAt(start + 21)) ||
            !isDig(s.charAt(start + 22)))
            return false;

        // host: [a-z]+-\d+<sp>
        int h = start + 25;
        if (h >= end || s.charAt(h) < 'a' || s.charAt(h) > 'z') return false;
        do { ++h; } while (h < end && s.charAt(h) >= 'a' && s.charAt(h) <= 'z');
        if (h >= end || s.charAt(h) != '-') return false;
        ++h;
        if (h >= end || !isDig(s.charAt(h))) return false;
        do { ++h; } while (h < end && isDig(s.charAt(h)));
        if (h >= end || s.charAt(h) != ' ') return false;
        ++h; // method

        int mlen = 0;
        int rem = end - h;
        if (rem >= 3 && (region(s, h, "GET") || region(s, h, "PUT"))) mlen = 3;
        else if (rem >= 4 && region(s, h, "POST")) mlen = 4;
        else if (rem >= 6 && region(s, h, "DELETE")) mlen = 6;
        else if (rem >= 5 && region(s, h, "PATCH")) mlen = 5;
        if (mlen == 0) return false;
        h += mlen;
        if (h >= end || s.charAt(h) != ' ') return false;
        ++h;

        // path: /[A-Za-z0-9_/-]* then optional \?[^ ]* then <sp>
        if (h >= end || s.charAt(h) != '/') return false;
        int pathStart = h;
        ++h;
        while (h < end) {
            char c = s.charAt(h);
            if (c == ' ' || c == '?') break;
            if (!pathChar(c)) return false;
            ++h;
        }
        int pathEnd = h;
        if (h < end && s.charAt(h) == '?') {
            ++h;
            while (h < end && s.charAt(h) != ' ') ++h;
        }
        if (h >= end || s.charAt(h) != ' ') return false;
        ++h;

        // status: \d{3}<sp>
        if (end - h < 3 || !isDig(s.charAt(h)) || !isDig(s.charAt(h + 1)) || !isDig(s.charAt(h + 2)))
            return false;
        r.cls = s.charAt(h) - '0';
        h += 3;
        if (h >= end || s.charAt(h) != ' ') return false;
        ++h;

        // size: \d+B<sp>
        if (h >= end || !isDig(s.charAt(h))) return false;
        do { ++h; } while (h < end && isDig(s.charAt(h)));
        if (h >= end || s.charAt(h) != 'B') return false;
        ++h;
        if (h >= end || s.charAt(h) != ' ') return false;
        ++h;

        // latency: \d+.\dms "<ua>"<end>
        long lat = 0;
        if (h >= end || !isDig(s.charAt(h))) return false;
        do { lat = lat * 10 + (s.charAt(h) - '0'); ++h; } while (h < end && isDig(s.charAt(h)));
        if (h >= end || s.charAt(h) != '.') return false;
        ++h;
        if (h >= end || !isDig(s.charAt(h))) return false;
        lat = lat * 10 + (s.charAt(h) - '0');
        ++h;
        if (end - h < 4 || s.charAt(h) != 'm' || s.charAt(h + 1) != 's' || s.charAt(h + 2) != ' ' ||
            s.charAt(h + 3) != '"')
            return false;
        h += 4;
        while (h < end && s.charAt(h) != '"') ++h;
        if (h >= end || s.charAt(h) != '"') return false;
        ++h;
        if (h != end) return false;

        r.pathStart = pathStart;
        r.pathEnd = pathEnd;
        r.lat = (int) lat;
        return true;
    }

    static boolean region(String s, int pos, String lit) {
        for (int i = 0; i < lit.length(); i++) {
            if (s.charAt(pos + i) != lit.charAt(i)) return false;
        }
        return true;
    }

    static boolean pathChar(char c) {
        return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
               c == '_' || c == '/' || c == '-';
    }

    public static void main(String[] args) throws Exception {
        String data = Files.readString(Path.of(args[0]), StandardCharsets.US_ASCII);
        int n = data.length();
        int p = 0;
        long nLines = 0, nMalformed = 0;
        int[] statusCount = new int[10];
        TMap map = new TMap(1 << 14);
        char[] tmpl = new char[128];
        Res res = new Res();

        while (p < n) {
            ++nLines;
            int lineStart = p;
            int e = p;
            while (e < n && data.charAt(e) != '\n') ++e;
            // line is [lineStart, e)
            if (parseLine(data, lineStart, e, res)) {
                ++statusCount[res.cls];

                // path template
                int tlen = 1;
                tmpl[0] = '/';
                int segStart = res.pathStart + 1;
                int i = segStart;
                for (;;) {
                    if (i == res.pathEnd || data.charAt(i) == '/') {
                        int seglen = i - segStart;
                        if (seglen > 0) {
                            boolean allDig = true;
                            for (int j = segStart; j < i; j++) {
                                if (!isDig(data.charAt(j))) { allDig = false; break; }
                            }
                            if (allDig) {
                                tmpl[tlen++] = '{';
                                tmpl[tlen++] = 'i';
                                tmpl[tlen++] = 'd';
                                tmpl[tlen++] = '}';
                            } else {
                                for (int j = segStart; j < i; j++) tmpl[tlen++] = data.charAt(j);
                            }
                        }
                        if (i < res.pathEnd) tmpl[tlen++] = '/';
                        segStart = i + 1;
                    }
                    if (i == res.pathEnd) break;
                    ++i;
                }

                Stats st = map.findOrAdd(tmpl, 0, tlen);
                ++st.count;
                st.add(res.lat);
            } else {
                ++nMalformed;
            }
            p = e + 1;
        }

        // collect items
        int m = 0;
        for (int slot = 0; slot < map.keys.length; slot++) {
            if (map.keys[slot] != null) m++;
        }
        String[] names = new String[m];
        Stats[] stats = new Stats[m];
        int k = 0;
        for (int slot = 0; slot < map.keys.length; slot++) {
            if (map.keys[slot] != null) { names[k] = map.keys[slot]; stats[k] = map.vals[slot]; k++; }
        }
        Integer[] order = new Integer[m];
        for (int i = 0; i < m; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> {
            int ca = stats[a].count, cb = stats[b].count;
            if (ca != cb) return cb - ca;
            return names[a].compareTo(names[b]); // byte order (ASCII)
        });

        StringBuilder sb = new StringBuilder(8192);
        sb.append("lines ").append(nLines).append('\n');
        sb.append("malformed ").append(nMalformed).append('\n');
        for (int c = 0; c < 10; c++) {
            if (statusCount[c] != 0) {
                sb.append("status ").append((char) ('0' + c)).append("xx ").append(statusCount[c]).append('\n');
            }
        }
        int top = m < 10 ? m : 10;
        for (int i = 0; i < top; i++) {
            Stats st = stats[order[i]];
            int[] lat = st.lat;
            Arrays.sort(lat, 0, st.len);
            int nn = st.len;
            java.util.function.IntUnaryOperator kth = pct -> lat[(int) (((long) pct * nn + 99) / 100 - 1)];
            sb.append("path ").append(names[order[i]]).append(' ').append(st.count).append(' ');
            appendLat(sb, kth.applyAsInt(50));
            sb.append(' ');
            appendLat(sb, kth.applyAsInt(95));
            sb.append(' ');
            appendLat(sb, lat[nn - 1]);
            sb.append('\n');
        }

        System.out.write(sb.toString().getBytes(StandardCharsets.US_ASCII));
    }

    static void appendLat(StringBuilder sb, int t) {
        sb.append(t / 10).append('.').append(t % 10);
    }
}
