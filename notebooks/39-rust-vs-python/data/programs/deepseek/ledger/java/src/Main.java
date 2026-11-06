import java.io.InputStream;
import java.io.FileInputStream;
import java.io.BufferedOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class Main {
    static byte[] buf;
    static int pos;
    static int end;

    // Result of the last scanString()
    static int sBeg, sLen;
    static boolean sEsc;

    // Resolved string (raw input bytes, or decoded scratch)
    static byte[] rArr;
    static int rOff, rLen;

    static byte[] scratch = new byte[256];
    static int scratchLen;

    static final byte[] K_ACCOUNT = ascii("account");
    static final byte[] K_AMOUNT = ascii("amount");
    static final byte[] K_TYPE = ascii("type");
    static final byte[] K_TAGS = ascii("tags");
    static final byte[] K_META = ascii("meta");
    static final byte[] K_CHANNEL = ascii("channel");
    static final byte[] K_CURRENCY = ascii("currency");
    static final byte[] K_RATES = ascii("rates");
    static final byte[] K_TEST = ascii("test");
    static final byte[] K_VOID = ascii("void");
    static final byte[] K_DEBIT = ascii("debit");

    static byte[] ascii(String s) {
        return s.getBytes(StandardCharsets.US_ASCII);
    }

    static void skipWs() {
        byte[] b = buf;
        int i = pos;
        int e = end;
        while (i < e) {
            byte c = b[i];
            if (c == ' ' || c == '\t' || c == '\r' || c == '\n') i++;
            else break;
        }
        pos = i;
    }

    static void scanString() {
        byte[] b = buf;
        int i = pos + 1;
        int st = i;
        boolean esc = false;
        while (b[i] != '"') {
            if (b[i] == '\\') {
                esc = true;
                i++;
                if (b[i] == 'u') i += 5; else i++;
            } else {
                i++;
            }
        }
        sBeg = st;
        sLen = i - st;
        pos = i + 1;
        sEsc = esc;
    }

    static void skipString() {
        byte[] b = buf;
        int i = pos + 1;
        while (b[i] != '"') {
            if (b[i] == '\\') {
                i++;
                if (b[i] == 'u') i += 5; else i++;
            } else {
                i++;
            }
        }
        pos = i + 1;
    }

    static int hex4(byte[] a, int off) {
        int v = 0;
        for (int i = 0; i < 4; i++) {
            byte c = a[off + i];
            int d;
            if (c >= '0' && c <= '9') d = c - '0';
            else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
            else d = c - 'A' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static void put(int b) {
        if (scratchLen == scratch.length) scratch = Arrays.copyOf(scratch, scratch.length * 2);
        scratch[scratchLen++] = (byte) b;
    }

    static void unescape() {
        scratchLen = 0;
        byte[] a = buf;
        int q = sBeg;
        int e = sBeg + sLen;
        while (q < e) {
            int c = a[q++] & 0xff;
            if (c != '\\') { put(c); continue; }
            int esc = a[q++] & 0xff;
            switch (esc) {
                case '"': put('"'); break;
                case '\\': put('\\'); break;
                case '/': put('/'); break;
                case 'b': put('\b'); break;
                case 'f': put('\f'); break;
                case 'n': put('\n'); break;
                case 'r': put('\r'); break;
                case 't': put('\t'); break;
                case 'u': {
                    int cp = hex4(a, q); q += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && q + 6 <= e && a[q] == '\\' && a[q + 1] == 'u') {
                        int lo = hex4(a, q + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            q += 6;
                        }
                    }
                    if (cp < 0x80) {
                        put(cp);
                    } else if (cp < 0x800) {
                        put(0xC0 | (cp >> 6));
                        put(0x80 | (cp & 0x3F));
                    } else if (cp < 0x10000) {
                        put(0xE0 | (cp >> 12));
                        put(0x80 | ((cp >> 6) & 0x3F));
                        put(0x80 | (cp & 0x3F));
                    } else {
                        put(0xF0 | (cp >> 18));
                        put(0x80 | ((cp >> 12) & 0x3F));
                        put(0x80 | ((cp >> 6) & 0x3F));
                        put(0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default: put(esc); break;
            }
        }
    }

    static void resolve() {
        if (sEsc) {
            unescape();
            rArr = scratch;
            rOff = 0;
            rLen = scratchLen;
        } else {
            rArr = buf;
            rOff = sBeg;
            rLen = sLen;
        }
    }

    static boolean eq(byte[] lit) {
        if (rLen != lit.length) return false;
        byte[] a = rArr;
        int o = rOff;
        for (int i = 0; i < lit.length; i++) {
            if (a[o + i] != lit[i]) return false;
        }
        return true;
    }

    static boolean bytesEq(byte[] a, int ao, byte[] b, int bo, int len) {
        for (int i = 0; i < len; i++) {
            if (a[ao + i] != b[bo + i]) return false;
        }
        return true;
    }

    // ---- skip arbitrary value (depth scan; input is valid JSON)
    static void skipValue() {
        skipWs();
        byte[] b = buf;
        int i = pos;
        int e = end;
        byte c = b[i];
        if (c == '"') {
            i++;
            while (b[i] != '"') {
                if (b[i] == '\\') { i++; if (b[i] == 'u') i += 5; else i++; }
                else i++;
            }
            pos = i + 1;
            return;
        }
        if (c == '{' || c == '[') {
            int depth = 0;
            while (true) {
                byte d = b[i];
                if (d == '"') {
                    i++;
                    while (b[i] != '"') {
                        if (b[i] == '\\') { i++; if (b[i] == 'u') i += 5; else i++; }
                        else i++;
                    }
                    i++;
                } else if (d == '{' || d == '[') { depth++; i++; }
                else if (d == '}' || d == ']') { i++; if (--depth == 0) { pos = i; return; } }
                else i++;
            }
        }
        while (i < e) {
            byte d = b[i];
            if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n') break;
            i++;
        }
        pos = i;
    }

    // ---- rates
    static byte[][] rateKeys = new byte[16][];
    static long[] rateVals = new long[16];
    static int rateN;

    static long lookupRate() {
        for (int i = 0; i < rateN; i++) {
            byte[] k = rateKeys[i];
            if (k.length == rLen && bytesEq(k, 0, rArr, rOff, rLen)) return rateVals[i];
        }
        return 0;
    }

    // ---- accounts: custom open-addressing map keyed by byte ranges
    static int[] accSlots = new int[1 << 14];
    static int[] accStart = new int[1 << 13];
    static int[] accLen = new int[1 << 13];
    static long[] accSum = new long[1 << 13];
    static int[] accCnt = new int[1 << 13];
    static int accN;
    static byte[] arena = new byte[1 << 16];
    static int arenaLen;

    static int hash(byte[] a, int off, int len) {
        int h = 0x811c9dc5;
        for (int i = 0; i < len; i++) {
            h ^= (a[off + i] & 0xff);
            h *= 0x01000193;
        }
        return h & 0x7fffffff;
    }

    static void growAccounts() {
        int cap = accStart.length * 2;
        accStart = Arrays.copyOf(accStart, cap);
        accLen = Arrays.copyOf(accLen, cap);
        accSum = Arrays.copyOf(accSum, cap);
        accCnt = Arrays.copyOf(accCnt, cap);
    }

    static void rehash() {
        int[] ns = new int[accSlots.length * 2];
        int mask = ns.length - 1;
        for (int i = 0; i < accN; i++) {
            int slot = hash(arena, accStart[i], accLen[i]) & mask;
            while (ns[slot] != 0) slot = (slot + 1) & mask;
            ns[slot] = i + 1;
        }
        accSlots = ns;
    }

    static int internAccount(byte[] a, int off, int len) {
        int mask = accSlots.length - 1;
        int slot = hash(a, off, len) & mask;
        while (true) {
            int e = accSlots[slot];
            if (e == 0) break;
            int i = e - 1;
            if (accLen[i] == len && bytesEq(arena, accStart[i], a, off, len)) return i;
            slot = (slot + 1) & mask;
        }
        if (accN == accStart.length) growAccounts();
        int idx = accN++;
        if (arenaLen + len > arena.length) {
            int cap = arena.length;
            while (cap < arenaLen + len) cap *= 2;
            arena = Arrays.copyOf(arena, cap);
        }
        accStart[idx] = arenaLen;
        accLen[idx] = len;
        System.arraycopy(a, off, arena, arenaLen, len);
        arenaLen += len;
        accSum[idx] = 0;
        accCnt[idx] = 0;
        accSlots[slot] = idx + 1;
        if (accN * 2 > accSlots.length) rehash();
        return idx;
    }

    // ---- channels (few distinct values: linear search)
    static byte[][] chName = new byte[64][];
    static long[] chCnt = new long[64];
    static long[] chNet = new long[64];
    static int chN;

    static int internChannel() {
        for (int i = 0; i < chN; i++) {
            byte[] n = chName[i];
            if (n.length == rLen && bytesEq(n, 0, rArr, rOff, rLen)) return i;
        }
        if (chN == chName.length) {
            chName = Arrays.copyOf(chName, chN * 2);
            chCnt = Arrays.copyOf(chCnt, chN * 2);
            chNet = Arrays.copyOf(chNet, chN * 2);
        }
        chName[chN] = Arrays.copyOfRange(rArr, rOff, rOff + rLen);
        chCnt[chN] = 0;
        chNet[chN] = 0;
        return chN++;
    }

    static long parseAmount(byte[] a, int off, int len) {
        long whole = 0;
        int i = off, e = off + len;
        while (i < e) {
            byte c = a[i];
            if (c < '0' || c > '9') break;
            whole = whole * 10 + (c - '0');
            i++;
        }
        int f1 = 0, f2 = 0;
        if (i < e && a[i] == '.') {
            i++;
            if (i < e) { f1 = a[i] - '0'; i++; }
            if (i < e) { f2 = a[i] - '0'; }
        }
        return whole * 100 + f1 * 10 + f2;
    }

    // ---- transaction state
    static long totalCount, totalNet;

    static boolean curHasTest;

    static void parseTags() {
        pos++; skipWs();       // '['
        if (buf[pos] == ']') { pos++; return; }
        while (true) {
            skipWs();
            if (buf[pos] == '"') {
                scanString();
                if (!curHasTest) {
                    resolve();
                    if (eq(K_TEST)) curHasTest = true;
                }
            } else {
                skipValue();
            }
            skipWs();
            if (buf[pos] == ',') { pos++; continue; }
            pos++;
            return;
        }
    }

    static int parseMeta() {
        int chIdx = -1;
        pos++; skipWs();       // '{'
        if (buf[pos] == '}') { pos++; return chIdx; }
        while (true) {
            skipWs();
            scanString();
            resolve();
            boolean isChannel = eq(K_CHANNEL);
            skipWs();
            pos++;             // ':'
            skipWs();
            if (isChannel) {
                scanString();
                resolve();
                chIdx = internChannel();
            } else {
                skipValue();
            }
            skipWs();
            if (buf[pos] == ',') { pos++; continue; }
            pos++;
            return chIdx;
        }
    }

    static void parseTransaction() {
        int acctIdx = -1;
        int chIdx = -1;
        int sign = 1;
        curHasTest = false;
        long hundredths = 0;
        long rate = 0;

        pos++;  // '{'
        skipWs();
        if (buf[pos] == '}') { pos++; return; }
        while (true) {
            skipWs();
            scanString();
            resolve();
            int first = rLen > 0 ? (rArr[rOff] & 0xff) : 0;
            skipWs();
            pos++;  // ':'
            skipWs();
            switch (first) {
                case 'a':
                    if (eq(K_ACCOUNT)) {
                        scanString(); resolve();
                        acctIdx = internAccount(rArr, rOff, rLen);
                    } else if (eq(K_AMOUNT)) {
                        scanString(); resolve();
                        hundredths = parseAmount(rArr, rOff, rLen);
                    } else {
                        skipValue();
                    }
                    break;
                case 't':
                    if (eq(K_TYPE)) {
                        scanString(); resolve();
                        if (eq(K_VOID)) sign = 0;
                        else if (eq(K_DEBIT)) sign = -1;
                        else sign = 1;
                    } else if (eq(K_TAGS)) {
                        parseTags();
                    } else {
                        skipValue();
                    }
                    break;
                case 'm':
                    if (eq(K_META)) {
                        chIdx = parseMeta();
                    } else {
                        skipValue();
                    }
                    break;
                case 'c':
                    if (eq(K_CURRENCY)) {
                        scanString(); resolve();
                        rate = lookupRate();
                    } else {
                        skipValue();
                    }
                    break;
                default:
                    skipValue();
                    break;
            }
            skipWs();
            if (buf[pos] == ',') { pos++; continue; }
            pos++;
            break;
        }

        if (sign == 0 || curHasTest) return;

        long usd = (hundredths * rate) / 1000000L;
        long val = sign > 0 ? usd : -usd;

        totalCount++;
        totalNet += val;
        if (acctIdx >= 0) {
            accSum[acctIdx] += val;
            accCnt[acctIdx]++;
        }
        if (chIdx >= 0) {
            chCnt[chIdx]++;
            chNet[chIdx] += val;
        }
    }

    static int cmpBytes(byte[] a, byte[] b) {
        int n = Math.min(a.length, b.length);
        for (int i = 0; i < n; i++) {
            int x = a[i] & 0xff, y = b[i] & 0xff;
            if (x != y) return x - y;
        }
        return a.length - b.length;
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1) return;

        buf = java.nio.file.Files.readAllBytes(java.nio.file.Path.of(args[0]));
        end = buf.length;
        pos = 0;

        // first line: {"rates": {...}}
        skipWs();
        pos++;
        skipWs();
        if (buf[pos] != '}') {
            while (true) {
                skipWs();
                scanString();
                resolve();
                boolean isRates = eq(K_RATES);
                skipWs();
                pos++;
                skipWs();
                if (isRates && buf[pos] == '{') {
                    pos++;
                    skipWs();
                    if (buf[pos] != '}') {
                        while (true) {
                            skipWs();
                            scanString();
                            resolve();
                            byte[] cur = Arrays.copyOfRange(rArr, rOff, rOff + rLen);
                            skipWs();
                            pos++;
                            skipWs();
                            boolean neg = false;
                            if (buf[pos] == '-') { neg = true; pos++; }
                            long v = 0;
                            while (buf[pos] >= '0' && buf[pos] <= '9') {
                                v = v * 10 + (buf[pos] - '0');
                                pos++;
                            }
                            if (neg) v = -v;
                            if (rateN == rateKeys.length) {
                                rateKeys = Arrays.copyOf(rateKeys, rateN * 2);
                                rateVals = Arrays.copyOf(rateVals, rateN * 2);
                            }
                            rateKeys[rateN] = cur;
                            rateVals[rateN] = v;
                            rateN++;
                            skipWs();
                            if (buf[pos] == ',') { pos++; continue; }
                            pos++;
                            break;
                        }
                    } else {
                        pos++;
                    }
                } else {
                    skipValue();
                }
                skipWs();
                if (buf[pos] == ',') { pos++; continue; }
                pos++;
                break;
            }
        } else {
            pos++;
        }

        // transactions
        while (true) {
            skipWs();
            if (pos >= end) break;
            if (buf[pos] != '{') { pos++; continue; }
            parseTransaction();
        }

        // channels sorted by byte order
        int[] ci = new int[chN];
        for (int i = 0; i < chN; i++) ci[i] = i;
        for (int i = 1; i < chN; i++) {
            int v = ci[i];
            int j = i - 1;
            while (j >= 0 && cmpBytes(chName[ci[j]], chName[v]) > 0) {
                ci[j + 1] = ci[j];
                j--;
            }
            ci[j + 1] = v;
        }

        // top ten accounts
        int[] best = new int[10];
        int bn = 0;
        for (int i = 0; i < accN; i++) {
            if (accCnt[i] == 0) continue;
            long s = accSum[i];
            int p = bn;
            while (p > 0) {
                int o = best[p - 1];
                boolean better;
                if (s != accSum[o]) better = s > accSum[o];
                else better = cmpBytes(arena, accStart[i], accLen[i], arena, accStart[o], accLen[o]) < 0;
                if (!better) break;
                p--;
            }
            if (p >= 10) continue;
            if (bn < 10) bn++;
            for (int j = bn - 1; j > p; j--) best[j] = best[j - 1];
            best[p] = i;
        }

        StringBuilder sb = new StringBuilder(4096);
        sb.append("counted ").append(totalCount).append('\n');
        sb.append("net ").append(totalNet).append('\n');
        for (int i = 0; i < chN; i++) {
            int c = ci[i];
            if (chCnt[c] == 0) continue;
            sb.append("channel ").append(new String(chName[c], StandardCharsets.UTF_8))
              .append(' ').append(chCnt[c]).append(' ').append(chNet[c]).append('\n');
        }
        for (int i = 0; i < bn; i++) {
            int a = best[i];
            sb.append("account ").append(new String(arena, accStart[a], accLen[a], StandardCharsets.UTF_8))
              .append(' ').append(accSum[a]).append('\n');
        }
        byte[] out = sb.toString().getBytes(StandardCharsets.UTF_8);
        OutputStream os = new BufferedOutputStream(System.out, 1 << 16);
        os.write(out);
        os.flush();
    }

    static int cmpBytes(byte[] a, int ao, int alen, byte[] b, int bo, int blen) {
        int n = Math.min(alen, blen);
        for (int i = 0; i < n; i++) {
            int x = a[ao + i] & 0xff, y = b[bo + i] & 0xff;
            if (x != y) return x - y;
        }
        return alen - blen;
    }
}
