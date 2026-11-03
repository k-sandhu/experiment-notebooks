import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Main {
    // ---- byte-keyed aggregation table ----
    static final class Table {
        int[] index = new int[1 << 12];
        int mask = (1 << 12) - 1;
        int n = 0;
        int[] hashes = new int[1024];
        int[] keyOff = new int[1024];
        int[] keyLen = new int[1024];
        long[] sums = new long[1024];
        long[] counts = new long[1024];
        byte[] arena = new byte[1 << 14];
        int arenaLen = 0;

        Table() {
            Arrays.fill(index, -1);
        }

        void add(byte[] k, int off, int len, long v) {
            int hash = 0x811C9DC5;
            for (int i = 0; i < len; i++) hash = (hash ^ (k[off + i] & 0xFF)) * 16777619;
            hash ^= hash >>> 15;
            int h = hash & mask;
            for (;;) {
                int ix = index[h];
                if (ix < 0) break;
                if (hashes[ix] == hash && keyLen[ix] == len
                        && Arrays.equals(arena, keyOff[ix], keyOff[ix] + len, k, off, off + len)) {
                    sums[ix] += v;
                    counts[ix]++;
                    return;
                }
                h = (h + 1) & mask;
            }
            if (n == hashes.length) {
                int c = n * 2;
                hashes = Arrays.copyOf(hashes, c);
                keyOff = Arrays.copyOf(keyOff, c);
                keyLen = Arrays.copyOf(keyLen, c);
                sums = Arrays.copyOf(sums, c);
                counts = Arrays.copyOf(counts, c);
            }
            if (arenaLen + len > arena.length) arena = Arrays.copyOf(arena, Math.max(arena.length * 2, arenaLen + len));
            System.arraycopy(k, off, arena, arenaLen, len);
            int ix = n++;
            hashes[ix] = hash;
            keyOff[ix] = arenaLen;
            keyLen[ix] = len;
            arenaLen += len;
            sums[ix] = v;
            counts[ix] = 1;
            index[h] = ix;
            if (n * 2 > index.length) grow();
        }

        void grow() {
            int cap = index.length * 2;
            index = new int[cap];
            Arrays.fill(index, -1);
            mask = cap - 1;
            for (int i = 0; i < n; i++) {
                int h = hashes[i] & mask;
                while (index[h] >= 0) h = (h + 1) & mask;
                index[h] = i;
            }
        }

        String key(int i) {
            return new String(arena, keyOff[i], keyLen[i], StandardCharsets.ISO_8859_1);
        }
    }

    // ---- parser state ----
    static byte[] buf;
    static int p;

    // last parsed string
    static byte[] sArr;
    static int sOff, sLen;

    static final Table accounts = new Table();
    static final Table channels = new Table();
    static long totalCount = 0, totalNet = 0;

    static byte[][] rateKeys = new byte[0][];
    static long[] rateVals = new long[0];

    static void appendUtf8(byte[][] holder, int[] len, int cp) {
        byte[] b = holder[0];
        if (len[0] + 4 > b.length) b = holder[0] = Arrays.copyOf(b, b.length * 2 + 8);
        int l = len[0];
        if (cp < 0x80) {
            b[l++] = (byte) cp;
        } else if (cp < 0x800) {
            b[l++] = (byte) (0xC0 | (cp >> 6));
            b[l++] = (byte) (0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            b[l++] = (byte) (0xE0 | (cp >> 12));
            b[l++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
            b[l++] = (byte) (0x80 | (cp & 0x3F));
        } else {
            b[l++] = (byte) (0xF0 | (cp >> 18));
            b[l++] = (byte) (0x80 | ((cp >> 12) & 0x3F));
            b[l++] = (byte) (0x80 | ((cp >> 6) & 0x3F));
            b[l++] = (byte) (0x80 | (cp & 0x3F));
        }
        len[0] = l;
    }

    static int hex4(byte[] b, int q) {
        int v = 0;
        for (int i = 0; i < 4; i++) {
            int c = b[q + i];
            v <<= 4;
            if (c >= '0' && c <= '9') v |= c - '0';
            else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
            else v |= c - 'A' + 10;
        }
        return v;
    }

    // p at opening quote; sets sArr/sOff/sLen, leaves p after closing quote
    static void parseStr() {
        final byte[] b = buf;
        int q = p + 1;
        final int s = q;
        for (;;) {
            byte c = b[q];
            if (c == '"') {
                sArr = b;
                sOff = s;
                sLen = q - s;
                p = q + 1;
                return;
            }
            if (c == '\\') break;
            q++;
        }
        parseStrSlow(s, q);
    }

    static void parseStrSlow(int s, int q) {
        final byte[] b = buf;
        byte[][] holder = {new byte[q - s + 16]};
        int[] len = {q - s};
        System.arraycopy(b, s, holder[0], 0, q - s);
        for (;;) {
            byte c = b[q];
            if (c == '"') {
                q++;
                break;
            }
            if (c == '\\') {
                byte e = b[q + 1];
                q += 2;
                switch (e) {
                    case 'n': appendUtf8(holder, len, '\n'); break;
                    case 't': appendUtf8(holder, len, '\t'); break;
                    case 'r': appendUtf8(holder, len, '\r'); break;
                    case 'b': appendUtf8(holder, len, '\b'); break;
                    case 'f': appendUtf8(holder, len, '\f'); break;
                    case 'u': {
                        int cp = hex4(b, q);
                        q += 4;
                        if (cp >= 0xD800 && cp < 0xDC00 && b[q] == '\\' && b[q + 1] == 'u') {
                            int lo = hex4(b, q + 2);
                            if (lo >= 0xDC00 && lo < 0xE000) {
                                cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                q += 6;
                            }
                        }
                        appendUtf8(holder, len, cp);
                        break;
                    }
                    default: appendUtf8(holder, len, e); break;
                }
            } else {
                if (len[0] + 4 > holder[0].length) holder[0] = Arrays.copyOf(holder[0], holder[0].length * 2 + 8);
                holder[0][len[0]++] = c;
                q++;
            }
        }
        sArr = holder[0];
        sOff = 0;
        sLen = len[0];
        p = q;
    }

    static void skipWs() {
        final byte[] b = buf;
        int q = p;
        for (;;) {
            byte c = b[q];
            if (c == ' ' || c == '\n' || c == '\t' || c == '\r') q++;
            else break;
        }
        p = q;
    }

    static int skipString(int q) {
        final byte[] b = buf;
        q++;
        for (;;) {
            byte c = b[q];
            if (c == '"') break;
            if (c == '\\') q++;
            q++;
        }
        return q + 1;
    }

    static void skipValue() {
        final byte[] b = buf;
        int q = p;
        byte c = b[q];
        if (c == '"') {
            p = skipString(q);
            return;
        }
        if (c == '{' || c == '[') {
            int depth = 0;
            for (;;) {
                c = b[q];
                if (c == '"') {
                    q = skipString(q);
                    continue;
                }
                q++;
                if (c == '{' || c == '[') depth++;
                else if (c == '}' || c == ']') {
                    if (--depth == 0) break;
                }
            }
            p = q;
            return;
        }
        while (c != ',' && c != '}' && c != ']' && c != ' ' && c != '\n' && c != '\r' && c != '\t') c = b[++q];
        p = q;
    }

    static long parseInt() {
        long v = 0;
        final byte[] b = buf;
        int q = p;
        while (b[q] >= '0' && b[q] <= '9') v = v * 10 + (b[q++] - '0');
        p = q;
        return v;
    }

    static boolean eq(byte[] a, int off, int len, String lit) {
        if (len != lit.length()) return false;
        for (int i = 0; i < len; i++) if (a[off + i] != lit.charAt(i)) return false;
        return true;
    }

    static void parseRates() {
        p++;
        for (;;) {
            skipWs();
            parseStr();
            boolean isRates = eq(sArr, sOff, sLen, "rates");
            skipWs();
            p++;
            skipWs();
            if (isRates) {
                p++;
                List<byte[]> keys = new ArrayList<>();
                List<Long> vals = new ArrayList<>();
                for (;;) {
                    skipWs();
                    if (buf[p] == '}') {
                        p++;
                        break;
                    }
                    parseStr();
                    keys.add(Arrays.copyOfRange(sArr, sOff, sOff + sLen));
                    skipWs();
                    p++;
                    skipWs();
                    vals.add(parseInt());
                    skipWs();
                    if (buf[p] == ',') p++;
                }
                rateKeys = keys.toArray(new byte[0][]);
                rateVals = new long[vals.size()];
                for (int i = 0; i < rateVals.length; i++) rateVals[i] = vals.get(i);
            } else {
                skipValue();
            }
            skipWs();
            if (buf[p] == ',') {
                p++;
                continue;
            }
            p++;
            break;
        }
    }

    static byte[] accArr, chanArr;
    static int accOff, accLen, chanOff, chanLen;

    static void parseTx() {
        p++;
        accArr = null;
        accLen = 0;
        chanArr = null;
        chanLen = 0;
        int type = 0;
        long hund = 0, rate = 0;
        boolean test = false;
        for (;;) {
            skipWs();
            if (buf[p] == '}') {
                p++;
                break;
            }
            parseStr();
            final byte[] ka = sArr;
            final int ko = sOff, kl = sLen;
            skipWs();
            p++;
            skipWs();
            int kind = 0;
            if (kl == 4) {
                if (ka[ko] == 't' && ka[ko + 1] == 'y' && ka[ko + 2] == 'p' && ka[ko + 3] == 'e') kind = 2;
                else if (ka[ko] == 't' && ka[ko + 1] == 'a' && ka[ko + 2] == 'g' && ka[ko + 3] == 's') kind = 5;
                else if (ka[ko] == 'm' && ka[ko + 1] == 'e' && ka[ko + 2] == 't' && ka[ko + 3] == 'a') kind = 6;
            } else if (kl == 6) {
                if (eq(ka, ko, kl, "amount")) kind = 3;
            } else if (kl == 7) {
                if (eq(ka, ko, kl, "account")) kind = 1;
            } else if (kl == 8) {
                if (eq(ka, ko, kl, "currency")) kind = 4;
            }
            switch (kind) {
                case 1:
                    parseStr();
                    accArr = sArr;
                    accOff = sOff;
                    accLen = sLen;
                    break;
                case 2:
                    parseStr();
                    type = sLen > 0 ? sArr[sOff] : 0;
                    break;
                case 3: {
                    parseStr();
                    final byte[] a = sArr;
                    int q = sOff;
                    final int e = q + sLen;
                    long ip = 0;
                    while (q < e && a[q] != '.') ip = ip * 10 + (a[q++] - '0');
                    long fr = 0;
                    if (q < e) {
                        q++;
                        if (q < e) {
                            fr = (a[q++] - '0') * 10;
                            if (q < e) fr += a[q] - '0';
                        }
                    }
                    hund = ip * 100 + fr;
                    break;
                }
                case 4: {
                    parseStr();
                    for (int i = 0; i < rateKeys.length; i++) {
                        byte[] rk = rateKeys[i];
                        if (Arrays.equals(rk, 0, rk.length, sArr, sOff, sOff + sLen)) {
                            rate = rateVals[i];
                            break;
                        }
                    }
                    break;
                }
                case 5: {
                    p++;
                    skipWs();
                    if (buf[p] == ']') {
                        p++;
                        break;
                    }
                    for (;;) {
                        skipWs();
                        parseStr();
                        if (sLen == 4 && sArr[sOff] == 't' && sArr[sOff + 1] == 'e' && sArr[sOff + 2] == 's'
                                && sArr[sOff + 3] == 't') test = true;
                        skipWs();
                        if (buf[p] == ',') {
                            p++;
                            continue;
                        }
                        p++;
                        break;
                    }
                    break;
                }
                case 6: {
                    p++;
                    for (;;) {
                        skipWs();
                        if (buf[p] == '}') {
                            p++;
                            break;
                        }
                        parseStr();
                        boolean isChannel = eq(sArr, sOff, sLen, "channel");
                        skipWs();
                        p++;
                        skipWs();
                        if (isChannel && buf[p] == '"') {
                            parseStr();
                            chanArr = sArr;
                            chanOff = sOff;
                            chanLen = sLen;
                        } else {
                            skipValue();
                        }
                        skipWs();
                        if (buf[p] == ',') {
                            p++;
                            continue;
                        }
                        p++;
                        break;
                    }
                    break;
                }
                default:
                    skipValue();
            }
            skipWs();
            if (buf[p] == ',') {
                p++;
                continue;
            }
            p++;
            break;
        }
        if (type == 'v' || test) return;
        long usd = hund * rate / 1000000L;
        long v = type == 'd' ? -usd : usd;
        totalCount++;
        totalNet += v;
        accounts.add(accArr, accOff, accLen, v);
        channels.add(chanArr, chanOff, chanLen, v);
    }

    static boolean accBefore(int a, int b) {
        long sa = accounts.sums[a], sb = accounts.sums[b];
        if (sa != sb) return sa > sb;
        int ao = accounts.keyOff[a], bo = accounts.keyOff[b];
        return Arrays.compareUnsigned(accounts.arena, ao, ao + accounts.keyLen[a], accounts.arena, bo,
                bo + accounts.keyLen[b]) < 0;
    }

    static boolean ratesDone = false;

    static void processChunk(int end) {
        p = 0;
        for (;;) {
            skipWs();
            if (p >= end) break;
            if (!ratesDone) {
                parseRates();
                ratesDone = true;
            } else {
                parseTx();
            }
        }
    }

    public static void main(String[] args) throws IOException {
        int cap = 1 << 22;
        buf = new byte[cap + 16];
        int have = 0;
        boolean eof = false;
        try (InputStream in = new FileInputStream(args[0])) {
            while (!eof) {
                int n = in.read(buf, have, cap - have);
                if (n <= 0) eof = true;
                else have += n;
                int end;
                if (eof) {
                    if (have > 0 && buf[have - 1] != '\n') buf[have++] = '\n';
                    end = have;
                    buf[end] = 0;
                } else {
                    int i = have;
                    while (i > 0 && buf[i - 1] != '\n') i--;
                    if (i == 0) {
                        if (have == cap) {
                            cap *= 2;
                            buf = Arrays.copyOf(buf, cap + 16);
                        }
                        continue;
                    }
                    end = i;
                }
                processChunk(end);
                if (!eof) {
                    System.arraycopy(buf, end, buf, 0, have - end);
                    have -= end;
                }
            }
        }

        StringBuilder out = new StringBuilder();
        out.append("counted ").append(totalCount).append('\n');
        out.append("net ").append(totalNet).append('\n');
        Integer[] ch = new Integer[channels.n];
        for (int i = 0; i < ch.length; i++) ch[i] = i;
        Arrays.sort(ch, (a, b) -> channels.key(a).compareTo(channels.key(b)));
        for (int i : ch) {
            out.append("channel ").append(channels.key(i)).append(' ').append(channels.counts[i]).append(' ')
                    .append(channels.sums[i]).append('\n');
        }
        int[] top = new int[Math.min(10, accounts.n)];
        int tn = 0;
        for (int i = 0; i < accounts.n; i++) {
            if (tn == top.length && !accBefore(i, top[tn - 1])) continue;
            int j = tn < top.length ? tn++ : tn - 1;
            while (j > 0 && accBefore(i, top[j - 1])) {
                top[j] = top[j - 1];
                j--;
            }
            top[j] = i;
        }
        for (int i = 0; i < tn; i++) {
            out.append("account ").append(accounts.key(top[i])).append((char) 32).append(accounts.sums[top[i]]).append((char) 10);
        }
        PrintStream ps = new PrintStream(System.out, false, "ISO-8859-1");
        ps.print(out);
        ps.flush();
    }
}
