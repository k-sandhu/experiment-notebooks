import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {
    // ---- byte-string slice result (reused, no allocation in the hot loop) ----
    static final class StrBuf {
        byte[] dec = new byte[64];
        byte[] a;
        int off, len;
    }

    // ---- open-addressing map byte-string -> {net, cnt}; keys copied once into an arena ----
    static final class StrMap {
        long[] hash;
        int[] off, klen;
        long[] net, cnt;
        boolean[] used;
        byte[] arena = new byte[1 << 16];
        int arenaLen = 0;
        int mask, usedCnt = 0;

        StrMap(int capHint) {
            int c = 16;
            while (c < capHint) c <<= 1;
            hash = new long[c]; off = new int[c]; klen = new int[c];
            net = new long[c]; cnt = new long[c]; used = new boolean[c];
            mask = c - 1;
        }

        void grow() {
            long[] oh = hash; int[] oo = off, ol = klen;
            long[] on = net, oc = cnt; boolean[] ou = used;
            int c = oh.length * 2;
            hash = new long[c]; off = new int[c]; klen = new int[c];
            net = new long[c]; cnt = new long[c]; used = new boolean[c];
            mask = c - 1;
            for (int i = 0; i < oh.length; i++) if (ou[i]) {
                int j = (int) oh[i] & mask;
                while (used[j]) j = (j + 1) & mask;
                used[j] = true; hash[j] = oh[i]; off[j] = oo[i]; klen[j] = ol[i];
                net[j] = on[i]; cnt[j] = oc[i];
            }
        }

        int findOrInsert(byte[] a, int o, int len) {
            if ((usedCnt + 1) * 10 > hash.length * 7) grow();
            long h = hashBytes(a, o, len);
            int i = (int) h & mask;
            while (true) {
                if (!used[i]) {
                    used[i] = true; hash[i] = h;
                    if (arenaLen + len > arena.length) {
                        int nc = arena.length;
                        while (nc < arenaLen + len) nc <<= 1;
                        arena = Arrays.copyOf(arena, nc);
                    }
                    off[i] = arenaLen; klen[i] = len;
                    System.arraycopy(a, o, arena, arenaLen, len);
                    arenaLen += len;
                    net[i] = 0; cnt[i] = 0; usedCnt++;
                    return i;
                }
                if (hash[i] == h && klen[i] == len &&
                        Arrays.equals(arena, off[i], off[i] + len, a, o, o + len)) return i;
                i = (i + 1) & mask;
            }
        }

        int find(byte[] a, int o, int len) {
            long h = hashBytes(a, o, len);
            int i = (int) h & mask;
            while (true) {
                if (!used[i]) return -1;
                if (hash[i] == h && klen[i] == len &&
                        Arrays.equals(arena, off[i], off[i] + len, a, o, o + len)) return i;
                i = (i + 1) & mask;
            }
        }
    }

    static long hashBytes(byte[] a, int o, int len) {
        long h = 1469598103934665603L;
        for (int i = 0; i < len; i++) {
            h ^= a[o + i] & 0xFFL;
            h *= 1099511628211L;
        }
        h ^= h >>> 33; h *= 0xff51afd7ed558ccdL; h ^= h >>> 33;
        return h;
    }

    static byte[] d;
    static int n, pos;
    static final StrBuf keyS = new StrBuf(), acctS = new StrBuf(), chanS = new StrBuf(), miscS = new StrBuf();

    static final byte[] K_ACCOUNT = ascii("account"), K_TYPE = ascii("type"),
            K_AMOUNT = ascii("amount"), K_CURRENCY = ascii("currency"),
            K_TAGS = ascii("tags"), K_META = ascii("meta"), K_RATES = ascii("rates"),
            K_CHANNEL = ascii("channel"), V_VOID = ascii("void"),
            V_DEBIT = ascii("debit"), V_TEST = ascii("test");

    static byte[] ascii(String s) { return s.getBytes(StandardCharsets.US_ASCII); }

    static boolean eq(StrBuf s, byte[] lit) {
        if (s.len != lit.length) return false;
        for (int i = 0; i < lit.length; i++) if (s.a[s.off + i] != lit[i]) return false;
        return true;
    }

    static void skipWs() {
        while (pos < n) {
            byte c = d[pos];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') pos++; else break;
        }
    }

    static void skipStringRaw() {
        pos++;
        while (pos < n) {
            byte c = d[pos];
            if (c == '"') { pos++; return; }
            pos += (c == '\\') ? 2 : 1;
        }
    }

    static int hex4(int i, int end, int[] io) {
        int v = 0;
        for (int k = 0; k < 4 && i < end; k++, i++) {
            byte c = d[i];
            v <<= 4;
            if (c >= '0' && c <= '9') v |= c - '0';
            else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') v |= c - 'A' + 10;
        }
        io[0] = i;
        return v;
    }

    static int appendUtf8(byte[] out, int w, int cp) {
        if (cp < 0x80) {
            out[w++] = (byte) cp;
        } else if (cp < 0x800) {
            out[w++] = (byte) (0xC0 | (cp >> 6));
            out[w++] = (byte) (0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            out[w++] = (byte) (0xE0 | (cp >> 12));
            out[w++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
            out[w++] = (byte) (0x80 | (cp & 0x3F));
        } else {
            out[w++] = (byte) (0xF0 | (cp >> 18));
            out[w++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
            out[w++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
            out[w++] = (byte) (0x80 | (cp & 0x3F));
        }
        return w;
    }

    // d[pos]=='"'; fills out with a slice of data, or of out.dec when escapes present.
    static void parseString(StrBuf out) {
        pos++;
        int start = pos;
        boolean esc = false;
        while (pos < n) {
            byte c = d[pos];
            if (c == '"') break;
            if (c == '\\') { esc = true; pos += 2; } else pos++;
        }
        int end = pos;
        if (pos < n) pos++;
        if (!esc) { out.a = d; out.off = start; out.len = end - start; return; }
        if (out.dec.length < end - start) {
            int nc = out.dec.length;
            while (nc < end - start) nc <<= 1;
            out.dec = new byte[nc];
        }
        byte[] o = out.dec;
        int w = 0;
        int i = start;
        int[] io = new int[1];
        while (i < end) {
            byte c = d[i];
            if (c != '\\') { o[w++] = c; i++; continue; }
            i++;
            if (i >= end) break;
            byte e = d[i++];
            switch (e) {
                case '"': o[w++] = '"'; break;
                case '\\': o[w++] = '\\'; break;
                case '/': o[w++] = '/'; break;
                case 'b': o[w++] = '\b'; break;
                case 'f': o[w++] = '\f'; break;
                case 'n': o[w++] = '\n'; break;
                case 'r': o[w++] = '\r'; break;
                case 't': o[w++] = '\t'; break;
                case 'u': {
                    int cp = hex4(i, end, io); i = io[0];
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 1 < end && d[i] == '\\' && d[i + 1] == 'u') {
                        i += 2;
                        int lo = hex4(i, end, io); i = io[0];
                        if (lo >= 0xDC00 && lo <= 0xDFFF) cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        else { w = appendUtf8(o, w, cp); cp = lo; }
                    }
                    w = appendUtf8(o, w, cp);
                    break;
                }
                default: o[w++] = e; break;
            }
        }
        out.a = o; out.off = 0; out.len = w;
    }

    static void skipValue() {
        skipWs();
        if (pos >= n) return;
        byte c = d[pos];
        if (c == '"') { skipStringRaw(); return; }
        if (c == '{' || c == '[') {
            int depth = 0;
            while (pos < n) {
                byte ch = d[pos];
                if (ch == '"') { skipStringRaw(); continue; }
                if (ch == '{' || ch == '[') { depth++; pos++; }
                else if (ch == '}' || ch == ']') { depth--; pos++; if (depth == 0) return; }
                else pos++;
            }
            return;
        }
        while (pos < n) {
            byte ch = d[pos];
            if (ch == ',' || ch == '}' || ch == ']' || ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r') break;
            pos++;
        }
    }

    static long parseInt64() {
        skipWs();
        boolean neg = false;
        if (pos < n && d[pos] == '-') { neg = true; pos++; }
        long v = 0;
        while (pos < n && d[pos] >= '0' && d[pos] <= '9') v = v * 10 + (d[pos++] - '0');
        return neg ? -v : v;
    }

    static long parseAmount(StrBuf s) {
        int i = s.off, end = s.off + s.len;
        long ip = 0;
        while (i < end && s.a[i] != '.') { ip = ip * 10 + (s.a[i] - '0'); i++; }
        long h = ip * 100;
        if (i < end) {
            i++;
            if (i < end) { h += (s.a[i] - '0') * 10L; i++; }
            if (i < end) h += s.a[i] - '0';
        }
        return h;
    }

    public static void main(String[] args) throws Exception {
        d = Files.readAllBytes(Path.of(args[0]));
        n = d.length;
        pos = 0;
        StrMap rates = new StrMap(64), channels = new StrMap(64), accounts = new StrMap(1 << 16);

        // First object: rates.
        skipWs();
        if (pos < n && d[pos] == '{') {
            pos++; skipWs();
            if (pos < n && d[pos] == '}') pos++;
            else {
                outer:
                while (true) {
                    skipWs();
                    parseString(keyS);
                    skipWs(); pos++;
                    skipWs();
                    if (eq(keyS, K_RATES)) {
                        pos++; skipWs();
                        if (pos < n && d[pos] == '}') pos++;
                        else while (true) {
                            skipWs();
                            parseString(miscS);
                            skipWs(); pos++;
                            long rv = parseInt64();
                            rates.net[rates.findOrInsert(miscS.a, miscS.off, miscS.len)] = rv;
                            skipWs();
                            if (pos < n && d[pos] == ',') { pos++; continue; }
                            if (pos < n && d[pos] == '}') pos++;
                            break;
                        }
                    } else skipValue();
                    skipWs();
                    if (pos < n && d[pos] == ',') { pos++; continue; }
                    if (pos < n && d[pos] == '}') pos++;
                    break outer;
                }
            }
        }

        long counted = 0, net = 0;
        while (true) {
            skipWs();
            if (pos >= n) break;
            long sign = 1;
            boolean isVoid = false, hasTest = false;
            long hundredths = 0, rate = 0;
            acctS.a = null; acctS.len = 0; chanS.a = null; chanS.len = 0;
            pos++; skipWs();
            if (pos < n && d[pos] == '}') pos++;
            else {
                tx:
                while (true) {
                    skipWs();
                    parseString(keyS);
                    skipWs(); pos++;
                    skipWs();
                    if (eq(keyS, K_ACCOUNT)) {
                        parseString(acctS);
                    } else if (eq(keyS, K_TYPE)) {
                        parseString(miscS);
                        if (eq(miscS, V_VOID)) isVoid = true;
                        else if (eq(miscS, V_DEBIT)) sign = -1;
                        else sign = 1;
                    } else if (eq(keyS, K_AMOUNT)) {
                        parseString(miscS);
                        hundredths = parseAmount(miscS);
                    } else if (eq(keyS, K_CURRENCY)) {
                        parseString(miscS);
                        int sl = rates.find(miscS.a, miscS.off, miscS.len);
                        rate = sl >= 0 ? rates.net[sl] : 0;
                    } else if (eq(keyS, K_TAGS)) {
                        pos++; skipWs();
                        if (pos < n && d[pos] == ']') pos++;
                        else while (true) {
                            skipWs();
                            if (pos < n && d[pos] == '"') {
                                parseString(miscS);
                                if (eq(miscS, V_TEST)) hasTest = true;
                            } else skipValue();
                            skipWs();
                            if (pos < n && d[pos] == ',') { pos++; continue; }
                            if (pos < n && d[pos] == ']') pos++;
                            break;
                        }
                    } else if (eq(keyS, K_META)) {
                        pos++; skipWs();
                        if (pos < n && d[pos] == '}') pos++;
                        else while (true) {
                            skipWs();
                            parseString(keyS);
                            skipWs(); pos++;
                            skipWs();
                            if (eq(keyS, K_CHANNEL)) parseString(chanS);
                            else skipValue();
                            skipWs();
                            if (pos < n && d[pos] == ',') { pos++; continue; }
                            if (pos < n && d[pos] == '}') pos++;
                            break;
                        }
                    } else {
                        skipValue();
                    }
                    skipWs();
                    if (pos < n && d[pos] == ',') { pos++; continue; }
                    if (pos < n && d[pos] == '}') pos++;
                    break tx;
                }
            }
            if (isVoid || hasTest) continue;
            long usd = (hundredths * rate) / 1000000L;
            long signed = sign < 0 ? -usd : usd;
            counted++;
            net += signed;
            accounts.net[accounts.findOrInsert(acctS.a, acctS.off, acctS.len)] += signed;
            int cs = channels.findOrInsert(chanS.a, chanS.off, chanS.len);
            channels.net[cs] += signed;
            channels.cnt[cs]++;
        }

        Integer[] chans = sortedSlots(channels);
        Arrays.sort(chans, (x, y) -> Arrays.compareUnsigned(
                channels.arena, channels.off[x], channels.off[x] + channels.klen[x],
                channels.arena, channels.off[y], channels.off[y] + channels.klen[y]));
        Integer[] accts = sortedSlots(accounts);
        Arrays.sort(accts, (x, y) -> {
            if (accounts.net[x] != accounts.net[y]) return accounts.net[x] > accounts.net[y] ? -1 : 1;
            return Arrays.compareUnsigned(
                    accounts.arena, accounts.off[x], accounts.off[x] + accounts.klen[x],
                    accounts.arena, accounts.off[y], accounts.off[y] + accounts.klen[y]);
        });

        StringBuilder sb = new StringBuilder(4096);
        sb.append("counted ").append(counted).append('\n');
        sb.append("net ").append(net).append('\n');
        for (int s : chans) {
            sb.append("channel ")
              .append(new String(channels.arena, channels.off[s], channels.klen[s], StandardCharsets.UTF_8))
              .append(' ').append(channels.cnt[s]).append(' ').append(channels.net[s]).append('\n');
        }
        int top = Math.min(10, accts.length);
        for (int i = 0; i < top; i++) {
            int s = accts[i];
            sb.append("account ")
              .append(new String(accounts.arena, accounts.off[s], accounts.klen[s], StandardCharsets.UTF_8))
              .append(' ').append(accounts.net[s]).append('\n');
        }
        System.out.print(sb.toString());
    }

    static Integer[] sortedSlots(StrMap m) {
        Integer[] r = new Integer[m.usedCnt];
        int k = 0;
        for (int i = 0; i < m.used.length; i++) if (m.used[i]) r[k++] = i;
        return r;
    }
}
