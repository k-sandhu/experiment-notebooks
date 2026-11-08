import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    static byte[] B;
    static int LEN, P;

    // -----------------------------------------------------------------------
    // Open addressing hash map keyed by spans of the input buffer.
    // -----------------------------------------------------------------------
    static final class SpanMap {
        int[] off;
        int[] klen;
        long[] v1;
        long[] v2;
        int cap;
        int cnt;

        SpanMap(int c) { init(c); }

        void init(int c) {
            cap = c;
            cnt = 0;
            off = new int[c];
            klen = new int[c];
            v1 = new long[c];
            v2 = new long[c];
            for (int i = 0; i < c; i++) klen[i] = -1;
        }

        static long hash(int s, int n) {
            long h = 1469598103934665603L;
            for (int i = 0; i < n; i++) {
                h ^= (B[s + i] & 0xFF);
                h *= 1099511628211L;
            }
            return h;
        }

        void grow() {
            int nc = cap * 2;
            int[] no = new int[nc];
            int[] nl = new int[nc];
            long[] n1 = new long[nc];
            long[] n2 = new long[nc];
            for (int i = 0; i < nc; i++) nl[i] = -1;
            int mask = nc - 1;
            for (int j = 0; j < cap; j++) {
                if (klen[j] < 0) continue;
                int i = (int) (hash(off[j], klen[j]) & mask);
                while (nl[i] >= 0) i = (i + 1) & mask;
                no[i] = off[j];
                nl[i] = klen[j];
                n1[i] = v1[j];
                n2[i] = v2[j];
            }
            off = no; klen = nl; v1 = n1; v2 = n2; cap = nc;
        }

        int find(int s, int n) {
            int mask = cap - 1;
            int i = (int) (hash(s, n) & mask);
            while (klen[i] >= 0) {
                if (klen[i] == n && spanEq(off[i], off[i] + n, s, s + n)) return i;
                i = (i + 1) & mask;
            }
            return -1;
        }

        int getOrInsert(int s, int n) {
            if ((cnt + 1) * 10 > cap * 7) grow();
            int mask = cap - 1;
            int i = (int) (hash(s, n) & mask);
            while (klen[i] >= 0) {
                if (klen[i] == n && spanEq(off[i], off[i] + n, s, s + n)) return i;
                i = (i + 1) & mask;
            }
            off[i] = s;
            klen[i] = n;
            v1[i] = 0;
            v2[i] = 0;
            cnt++;
            return i;
        }
    }

    static SpanMap rates, channels, accounts;

    static void skipWs() {
        while (P < LEN) {
            byte c = B[P];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') P++;
            else break;
        }
    }

    static int parseStringS, parseStringE;
    static boolean parseStringEsc;

    static void parseString() {
        P++;
        int s = P;
        boolean esc = false;
        while (true) {
            byte c = B[P];
            if (c == '"') {
                parseStringS = s;
                parseStringE = P;
                parseStringEsc = esc;
                P++;
                return;
            }
            if (c == '\\') { esc = true; P += 2; }
            else P++;
        }
    }

    static int hex4(int p) {
        int v = 0;
        for (int i = 0; i < 4; i++) {
            int c = B[p + i];
            int d;
            if (c >= '0' && c <= '9') d = c - '0';
            else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
            else d = c - 'A' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static int decode(int s, int e) {
        int w = s, r = s;
        while (r < e) {
            byte c = B[r++];
            if (c != '\\') { B[w++] = c; continue; }
            byte x = B[r++];
            switch (x) {
                case '"': B[w++] = '"'; break;
                case '\\': B[w++] = '\\'; break;
                case '/': B[w++] = '/'; break;
                case 'b': B[w++] = 8; break;
                case 'f': B[w++] = 12; break;
                case 'n': B[w++] = '\n'; break;
                case 'r': B[w++] = '\r'; break;
                case 't': B[w++] = '\t'; break;
                case 'u': {
                    int cp = hex4(r);
                    r += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && r + 6 <= e &&
                        B[r] == '\\' && B[r + 1] == 'u') {
                        int lo = hex4(r + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            r += 6;
                        }
                    }
                    if (cp < 0x80) {
                        B[w++] = (byte) cp;
                    } else if (cp < 0x800) {
                        B[w++] = (byte) (0xC0 | (cp >> 6));
                        B[w++] = (byte) (0x80 | (cp & 0x3F));
                    } else if (cp < 0x10000) {
                        B[w++] = (byte) (0xE0 | (cp >> 12));
                        B[w++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                        B[w++] = (byte) (0x80 | (cp & 0x3F));
                    } else {
                        B[w++] = (byte) (0xF0 | (cp >> 18));
                        B[w++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
                        B[w++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
                        B[w++] = (byte) (0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default: B[w++] = x; break;
            }
        }
        return w;
    }

    // Returns encoded start/end in parseStringS/E.
    static void parseStringValue() {
        parseString();
        if (parseStringEsc) parseStringE = decode(parseStringS, parseStringE);
    }

    static boolean spanEq(int s, int e, String lit) {
        int n = e - s;
        if (n != lit.length()) return false;
        for (int i = 0; i < n; i++)
            if (B[s + i] != (byte) lit.charAt(i)) return false;
        return true;
    }

    static boolean spanEq(int s1, int e1, int s2, int e2) {
        int n = e1 - s1;
        if (n != e2 - s2) return false;
        for (int i = 0; i < n; i++)
            if (B[s1 + i] != B[s2 + i]) return false;
        return true;
    }

    static int spanCompare(int o1, int l1, int o2, int l2) {
        int n = l1 < l2 ? l1 : l2;
        for (int i = 0; i < n; i++) {
            int d = (B[o1 + i] & 0xFF) - (B[o2 + i] & 0xFF);
            if (d != 0) return d;
        }
        return l1 - l2;
    }

    static void skipValue() {
        skipWs();
        byte c = B[P];
        if (c == '"') {
            parseString();
            return;
        }
        if (c == '{' || c == '[') {
            int depth = 0;
            while (true) {
                c = B[P];
                if (c == '"') {
                    parseString();
                } else {
                    P++;
                    if (c == '{' || c == '[') depth++;
                    else if (c == '}' || c == ']') {
                        if (--depth == 0) return;
                    }
                }
            }
        }
        while (P < LEN) {
            c = B[P];
            if (c == ',' || c == '}' || c == ']' || c == ' ' || c == '\t' ||
                c == '\n' || c == '\r') return;
            P++;
        }
    }

    static long parseAmount(int s, int e) {
        long ip = 0;
        int i = s;
        while (i < e && B[i] != '.') {
            ip = ip * 10 + (B[i] - '0');
            i++;
        }
        long frac = 0;
        if (i < e) {
            i++;
            int digits = 0;
            while (i < e) {
                frac = frac * 10 + (B[i] - '0');
                i++;
                digits++;
            }
            if (digits == 1) frac *= 10;
        }
        return ip * 100 + frac;
    }

    static int typeKind(int s, int e) {
        int n = e - s;
        if (n == 6) {
            if (spanEq(s, e, "credit")) return 0;
            if (spanEq(s, e, "refund")) return 2;
        } else if (n == 5) {
            if (spanEq(s, e, "debit")) return 1;
        } else if (n == 4) {
            if (spanEq(s, e, "void")) return 3;
        }
        return -1;
    }

    static boolean parseTags() {
        P++;
        boolean hasTest = false;
        while (true) {
            skipWs();
            if (B[P] == ']') { P++; return hasTest; }
            parseStringValue();
            if (parseStringE - parseStringS == 4 &&
                spanEq(parseStringS, parseStringE, "test")) hasTest = true;
            skipWs();
            if (B[P] == ',') { P++; continue; }
            if (B[P] == ']') { P++; return hasTest; }
        }
    }

    static int metaChS, metaChE;

    static void parseMeta() {
        P++;
        metaChS = 0;
        metaChE = 0;
        while (true) {
            skipWs();
            if (B[P] == '}') { P++; return; }
            parseString();
            int ks = parseStringS, ke = parseStringE;
            if (parseStringEsc) ke = decode(ks, ke);
            skipWs();
            P++;
            skipWs();
            if (spanEq(ks, ke, "channel")) {
                parseStringValue();
                metaChS = parseStringS;
                metaChE = parseStringE;
            } else {
                skipValue();
            }
            skipWs();
            if (B[P] == ',') { P++; continue; }
            if (B[P] == '}') { P++; return; }
        }
    }

    static void parseRatesObject() {
        P++;
        while (true) {
            skipWs();
            if (B[P] == '}') { P++; return; }
            parseString();
            int ks = parseStringS, ke = parseStringE;
            if (parseStringEsc) ke = decode(ks, ke);
            skipWs();
            P++;
            skipWs();
            long v = 0;
            boolean neg = false;
            if (B[P] == '-') { neg = true; P++; }
            while (P < LEN) {
                byte c = B[P];
                if (c < '0' || c > '9') break;
                v = v * 10 + (c - '0');
                P++;
            }
            if (neg) v = -v;
            int idx = rates.getOrInsert(ks, ke - ks);
            rates.v1[idx] = v;
            skipWs();
            if (B[P] == ',') { P++; continue; }
            if (B[P] == '}') { P++; return; }
        }
    }

    static long totalNet;
    static long totalCount;

    static void parseTransaction() {
        P++;
        int accS = 0, accE = 0;
        int chS = 0, chE = 0;
        long hundredths = 0;
        long rate = 0;
        int type = -1;
        boolean hasTest = false;

        while (true) {
            skipWs();
            if (B[P] == '}') { P++; break; }
            parseString();
            int ks = parseStringS, ke = parseStringE;
            if (parseStringEsc) ke = decode(ks, ke);
            skipWs();
            P++;
            skipWs();

            if (spanEq(ks, ke, "account")) {
                parseStringValue();
                accS = parseStringS;
                accE = parseStringE;
            } else if (spanEq(ks, ke, "type")) {
                parseStringValue();
                type = typeKind(parseStringS, parseStringE);
            } else if (spanEq(ks, ke, "amount")) {
                parseStringValue();
                hundredths = parseAmount(parseStringS, parseStringE);
            } else if (spanEq(ks, ke, "currency")) {
                parseStringValue();
                int ri = rates.find(parseStringS, parseStringE - parseStringS);
                rate = ri >= 0 ? rates.v1[ri] : 0;
            } else if (spanEq(ks, ke, "tags")) {
                hasTest = parseTags();
            } else if (spanEq(ks, ke, "meta")) {
                parseMeta();
                chS = metaChS;
                chE = metaChE;
            } else {
                skipValue();
            }

            skipWs();
            if (B[P] == ',') { P++; continue; }
            if (B[P] == '}') { P++; break; }
        }

        if (type == 3 || type == -1 || hasTest) return;

        long usd = (hundredths * rate) / 1000000L;
        long signed = type == 1 ? -usd : usd;
        totalNet += signed;
        totalCount++;

        int ci = channels.getOrInsert(chS, chE - chS);
        channels.v1[ci]++;
        channels.v2[ci] += signed;

        int ai = accounts.getOrInsert(accS, accE - accS);
        accounts.v1[ai] += signed;
    }

    public static void main(String[] args) {
        if (args.length < 1) return;
        try {
            B = Files.readAllBytes(Path.of(args[0]));
        } catch (IOException ex) {
            return;
        }
        LEN = B.length;

        rates = new SpanMap(64);
        channels = new SpanMap(64);
        accounts = new SpanMap(1 << 14);

        P = 0;
        skipWs();
        P++;
        while (true) {
            skipWs();
            if (B[P] == '}') { P++; break; }
            parseString();
            int ks = parseStringS, ke = parseStringE;
            if (parseStringEsc) ke = decode(ks, ke);
            skipWs();
            P++;
            skipWs();
            if (spanEq(ks, ke, "rates")) parseRatesObject();
            else skipValue();
            skipWs();
            if (B[P] == ',') { P++; continue; }
            if (B[P] == '}') { P++; break; }
        }

        while (true) {
            skipWs();
            if (P >= LEN) break;
            parseTransaction();
        }

        // Channels, insertion sorted by name.
        int[] chIdx = new int[channels.cnt];
        int nc = 0;
        for (int i = 0; i < channels.cap; i++)
            if (channels.klen[i] >= 0) chIdx[nc++] = i;
        for (int i = 1; i < nc; i++) {
            int v = chIdx[i];
            int j = i - 1;
            while (j >= 0 && spanCompare(channels.off[chIdx[j]], channels.klen[chIdx[j]],
                                         channels.off[v], channels.klen[v]) > 0) {
                chIdx[j + 1] = chIdx[j];
                j--;
            }
            chIdx[j + 1] = v;
        }

        // Accounts: keep the best 10 in order.
        int[] best = new int[10];
        int nb = 0;
        for (int i = 0; i < accounts.cap; i++) {
            if (accounts.klen[i] < 0) continue;
            int idx = i;
            int pos = nb;
            while (pos > 0 && betterAcc(idx, best[pos - 1])) pos--;
            if (pos < 10) {
                if (nb < 10) nb++;
                for (int j = nb - 1; j > pos; j--) best[j] = best[j - 1];
                best[pos] = idx;
            }
        }

        StringBuilder sb = new StringBuilder(8192);
        sb.append("counted ").append(totalCount).append('\n');
        sb.append("net ").append(totalNet).append('\n');
        for (int j = 0; j < nc; j++) {
            int idx = chIdx[j];
            sb.append("channel ");
            sb.append(new String(B, channels.off[idx], channels.klen[idx], StandardCharsets.UTF_8));
            sb.append(' ').append(channels.v1[idx]).append(' ').append(channels.v2[idx]).append('\n');
        }
        for (int j = 0; j < nb; j++) {
            int idx = best[j];
            sb.append("account ");
            sb.append(new String(B, accounts.off[idx], accounts.klen[idx], StandardCharsets.UTF_8));
            sb.append(' ').append(accounts.v1[idx]).append('\n');
        }

        byte[] out = sb.toString().getBytes(StandardCharsets.UTF_8);
        try {
            System.out.write(out);
            System.out.flush();
        } catch (IOException ex) {
            // ignore
        }
    }

    static boolean betterAcc(int a, int b) {
        if (accounts.v1[a] != accounts.v1[b]) return accounts.v1[a] > accounts.v1[b];
        return spanCompare(accounts.off[a], accounts.klen[a],
                           accounts.off[b], accounts.klen[b]) < 0;
    }
}
