import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// Ledger: fast single-pass JSON Lines aggregator.
// Hand-rolled byte scanner over the whole input (no DOM), no per-line line splitting.
public class Main {
    private static byte[] buf;
    private static int i;
    private static int n;

    private static int sStart;
    private static int sEnd;
    private static boolean sEsc;

    public static void main(String[] args) throws IOException {
        buf = Files.readAllBytes(Paths.get(args[0]));
        n = buf.length;

        HashMap<String, Long> rates = new HashMap<>();
        HashMap<String, long[]> channels = new HashMap<>(); // [count, net]
        HashMap<String, long[]> accounts = new HashMap<>(); // [net]

        // ---- first line: rates ----
        skipWs();
        i++; // '{'
        while (true) {
            skipWs();
            scanString();
            int ks = sStart, ke = sEnd;
            boolean kesc = sEsc;
            skipWs();
            i++; // ':'
            skipWs();
            if (!kesc && ke - ks == 5 && eq(ks, ke, "rates")) {
                i++; // '{'
                while (true) {
                    skipWs();
                    if (buf[i] == '}') {
                        i++;
                        break;
                    }
                    scanString();
                    String cur = strValue();
                    skipWs();
                    i++; // ':'
                    skipWs();
                    long r = 0;
                    while (buf[i] >= '0' && buf[i] <= '9') {
                        r = r * 10 + (buf[i] - '0');
                        i++;
                    }
                    rates.put(cur, r);
                    skipWs();
                    if (buf[i] == ',') i++;
                }
            } else {
                skipValue();
            }
            skipWs();
            if (buf[i] == ',') {
                i++;
                continue;
            }
            i++;
            break;
        }

        // ---- transactions ----
        long totalCount = 0;
        long totalNet = 0;

        while (true) {
            skipWs();
            if (i >= n) break;
            i++; // '{'

            int typeCode = 0; // 1 credit, 2 debit, 3 refund, 4 void
            boolean testTag = false;
            long hund = 0;
            String currency = null;
            String account = null;
            String channel = null;

            while (true) {
                skipWs();
                scanString();
                int ks = sStart, ke = sEnd;
                int klen = ke - ks;
                boolean kesc = sEsc;
                skipWs();
                i++; // ':'
                skipWs();
                if (!kesc) {
                    char c0 = klen > 0 ? (char) buf[ks] : 0;
                    if (klen == 4 && c0 == 't' && eq(ks, ke, "type")) {
                        scanString();
                        typeCode = typeCode();
                    } else if (klen == 6 && eq(ks, ke, "amount")) {
                        scanString();
                        hund = parseAmount(sStart, sEnd, sEsc);
                    } else if (klen == 8 && eq(ks, ke, "currency")) {
                        scanString();
                        currency = strValue();
                    } else if (klen == 7 && eq(ks, ke, "account")) {
                        scanString();
                        account = strValue();
                    } else if (klen == 4 && c0 == 't' && eq(ks, ke, "tags")) {
                        testTag = parseTags();
                    } else if (klen == 4 && c0 == 'm' && eq(ks, ke, "meta")) {
                        channel = parseMeta();
                    } else {
                        skipValue();
                    }
                } else {
                    // escaped key: decode and compare (rare)
                    String k = decodeString(ks, ke);
                    switch (k) {
                        case "type":
                            scanString();
                            typeCode = typeCode();
                            break;
                        case "amount":
                            scanString();
                            hund = parseAmount(sStart, sEnd, sEsc);
                            break;
                        case "currency":
                            scanString();
                            currency = strValue();
                            break;
                        case "account":
                            scanString();
                            account = strValue();
                            break;
                        case "tags":
                            testTag = parseTags();
                            break;
                        case "meta":
                            channel = parseMeta();
                            break;
                        default:
                            skipValue();
                            break;
                    }
                }
                skipWs();
                if (buf[i] == ',') {
                    i++;
                    continue;
                }
                i++; // '}'
                break;
            }

            if (typeCode == 4 || testTag) continue;

            Long rate = rates.get(currency);
            if (rate == null) continue;
            long usd = (hund * rate) / 1000000;
            long v = typeCode == 2 ? -usd : usd;

            totalCount++;
            totalNet += v;

            long[] c = channels.get(channel);
            if (c == null) {
                channels.put(channel, new long[] {1, v});
            } else {
                c[0]++;
                c[1] += v;
            }
            long[] a = accounts.get(account);
            if (a == null) {
                accounts.put(account, new long[] {v});
            } else {
                a[0] += v;
            }
        }

        // ---- output ----
        StringBuilder sb = new StringBuilder(1 << 16);
        sb.append("counted ").append(totalCount).append('\n');
        sb.append("net ").append(totalNet).append('\n');

        List<Map.Entry<String, long[]>> chs = new ArrayList<>(channels.entrySet());
        chs.sort(Map.Entry.comparingByKey());
        for (Map.Entry<String, long[]> e : chs) {
            sb.append("channel ").append(e.getKey()).append(' ')
              .append(e.getValue()[0]).append(' ').append(e.getValue()[1]).append('\n');
        }

        List<Map.Entry<String, long[]>> accs = new ArrayList<>(accounts.entrySet());
        accs.sort((x, y) -> {
            int c = Long.compare(y.getValue()[0], x.getValue()[0]);
            return c != 0 ? c : x.getKey().compareTo(y.getKey());
        });
        int lim = Math.min(10, accs.size());
        for (int k = 0; k < lim; k++) {
            sb.append("account ").append(accs.get(k).getKey()).append(' ').append(accs.get(k).getValue()[0]).append('\n');
        }
        System.out.print(sb);
    }

    // ---- scanner helpers ----

    private static void skipWs() {
        while (i < n) {
            byte c = buf[i];
            if (c == ' ' || c == '\t' || c == '\r' || c == '\n') i++;
            else break;
        }
    }

    private static void skipString() { // i at opening quote; leaves i past closing quote
        i++;
        while (true) {
            byte c = buf[i];
            if (c == '\\') {
                i += 2; // the escape char (and hex digits of a unicode escape) hold no quote or backslash
                continue;
            }
            if (c == '"') {
                i++;
                return;
            }
            i++;
        }
    }

    private static void scanString() { // i at opening quote; leaves i past closing quote
        i++;
        sStart = i;
        sEsc = false;
        while (true) {
            byte c = buf[i];
            if (c == '\\') {
                sEsc = true;
                i += 2;
                continue;
            }
            if (c == '"') {
                sEnd = i;
                i++;
                return;
            }
            i++;
        }
    }

    private static void skipValue() {
        byte c = buf[i];
        if (c == '"') {
            skipString();
            return;
        }
        if (c == '{' || c == '[') {
            int depth = 0;
            while (i < n) {
                byte d = buf[i];
                if (d == '"') {
                    skipString();
                    continue;
                }
                if (d == '{' || d == '[') depth++;
                else if (d == '}' || d == ']') {
                    depth--;
                    if (depth == 0) {
                        i++;
                        return;
                    }
                }
                i++;
            }
            return;
        }
        while (i < n) {
            byte d = buf[i];
            if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n') return;
            i++;
        }
    }

    private static boolean eq(int a, int b, String lit) {
        if (b - a != lit.length()) return false;
        for (int j = 0; j < lit.length(); j++) {
            if (buf[a + j] != lit.charAt(j)) return false;
        }
        return true;
    }

    // value string at sStart..sEnd (sEsc set) as a Java String
    private static String strValue() {
        if (!sEsc) {
            // account IDs / channel names / currencies are ASCII: ISO-8859-1 decode is a raw widening copy
            return new String(buf, sStart, sEnd - sStart, StandardCharsets.ISO_8859_1);
        }
        return decodeString(sStart, sEnd);
    }

    private static String decodeString(int from, int to) {
        char[] out = new char[to - from];
        int o = 0, j = from;
        while (j < to) {
            char c = (char) (buf[j] & 0xFF);
            if (c != '\\') {
                out[o++] = c;
                j++;
                continue;
            }
            char e = (char) (buf[j + 1] & 0xFF);
            j += 2;
            switch (e) {
                case '"': out[o++] = '"'; break;
                case '\\': out[o++] = '\\'; break;
                case '/': out[o++] = '/'; break;
                case 'b': out[o++] = '\b'; break;
                case 'f': out[o++] = '\f'; break;
                case 'n': out[o++] = '\n'; break;
                case 'r': out[o++] = '\r'; break;
                case 't': out[o++] = '\t'; break;
                case 'u': {
                    int cp = hex4(j);
                    j += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && j + 1 < to && buf[j] == '\\' && buf[j + 1] == 'u') {
                        int lo = hex4(j + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            j += 6;
                        }
                    }
                    if (cp < 0x10000) {
                        out[o++] = (char) cp;
                    } else {
                        cp -= 0x10000;
                        out[o++] = (char) (0xD800 | (cp >> 10));
                        out[o++] = (char) (0xDC00 | (cp & 0x3FF));
                    }
                    break;
                }
                default: out[o++] = e; break;
            }
        }
        return new String(out, 0, o);
    }

    private static int hex4(int at) {
        int v = 0;
        for (int k = 0; k < 4; k++) {
            byte c = buf[at + k];
            v <<= 4;
            if (c <= '9') v += c - '0';
            else if (c <= 'F') v += c - 'A' + 10;
            else v += c - 'a' + 10;
        }
        return v;
    }

    private static boolean decodedEq(String lit) {
        return decodeString(sStart, sEnd).contentEquals(lit);
    }

    private static long parseAmount(int from, int to, boolean esc) {
        if (esc) {
            String s = decodeString(from, to);
            return parseAmountDigits(s, 0, s.length());
        }
        return parseAmountDigits(buf, from, to);
    }

    private static long parseAmountDigits(byte[] b, int from, int to) {
        long ip = 0;
        int j = from;
        while (j < to && b[j] >= '0' && b[j] <= '9') {
            ip = ip * 10 + (b[j] - '0');
            j++;
        }
        long frac = 0;
        int fd = 0;
        if (j < to && b[j] == '.') {
            j++;
            while (j < to && fd < 2 && b[j] >= '0' && b[j] <= '9') {
                frac = frac * 10 + (b[j] - '0');
                fd++;
                j++;
            }
        }
        while (fd < 2) {
            frac *= 10;
            fd++;
        }
        return ip * 100 + frac;
    }

    private static long parseAmountDigits(String s, int from, int to) {
        long ip = 0;
        int j = from;
        while (j < to && s.charAt(j) >= '0' && s.charAt(j) <= '9') {
            ip = ip * 10 + (s.charAt(j) - '0');
            j++;
        }
        long frac = 0;
        int fd = 0;
        if (j < to && s.charAt(j) == '.') {
            j++;
            while (j < to && fd < 2 && s.charAt(j) >= '0' && s.charAt(j) <= '9') {
                frac = frac * 10 + (s.charAt(j) - '0');
                fd++;
                j++;
            }
        }
        while (fd < 2) {
            frac *= 10;
            fd++;
        }
        return ip * 100 + frac;
    }

    private static boolean parseTags() {
        i++; // '['
        boolean test = false;
        while (true) {
            skipWs();
            if (buf[i] == ']') {
                i++;
                return test;
            }
            if (buf[i] == '"') {
                scanString();
                if (!test) {
                    test = sEsc ? decodedEq("test") : (sEnd - sStart == 4 && eq(sStart, sEnd, "test"));
                }
            } else {
                skipValue();
            }
            skipWs();
            if (buf[i] == ',') i++;
        }
    }

    private static String parseMeta() {
        i++; // '{'
        String channel = null;
        while (true) {
            skipWs();
            if (buf[i] == '}') {
                i++;
                return channel;
            }
            scanString();
            int ks = sStart, ke = sEnd;
            boolean kesc = sEsc;
            skipWs();
            i++; // ':'
            skipWs();
            boolean isChannel = kesc ? "channel".contentEquals(decodeString(ks, ke)) : (ke - ks == 7 && eq(ks, ke, "channel"));
            if (isChannel) {
                scanString();
                channel = strValue();
            } else {
                skipValue();
            }
            skipWs();
            if (buf[i] == ',') i++;
        }
    }

    private static int typeCode() {
        if (!sEsc) {
            int len = sEnd - sStart;
            if (len == 6 && eq(sStart, sEnd, "credit")) return 1;
            if (len == 5 && eq(sStart, sEnd, "debit")) return 2;
            if (len == 6 && eq(sStart, sEnd, "refund")) return 3;
            if (len == 4 && eq(sStart, sEnd, "void")) return 4;
            return 0;
        }
        switch (decodeString(sStart, sEnd)) {
            case "credit": return 1;
            case "debit": return 2;
            case "refund": return 3;
            case "void": return 4;
            default: return 0;
        }
    }
}
