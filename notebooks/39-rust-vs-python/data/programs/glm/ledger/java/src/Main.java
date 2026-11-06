import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Main {

    // ---------- open-addressing hash table keyed by byte ranges ----------
    // Keys are copied into a private byte pool; lookups hash the raw slice.
    static final class Table {
        int cap = 1024;          // power of two
        int mask = cap - 1;
        int[] slot = new int[cap];      // entry index + 1, 0 = empty
        int[] keyOff = new int[cap];
        int[] keyLen = new int[cap];
        long[] a = new long[cap];       // count (channels) / unused
        long[] b = new long[cap];       // net
        int size = 0;
        byte[] pool = new byte[1 << 16];
        int poolLen = 0;

        long hash(byte[] d, int off, int len) {
            long h = 0xcbf29ce484222325L;
            for (int i = 0; i < len; i++) {
                h ^= d[off + i] & 0xffL;
                h *= 0x100000001b3L;
            }
            return h;
        }

        void ensurePool(int n) {
            if (poolLen + n > pool.length) {
                pool = Arrays.copyOf(pool, Math.max(pool.length * 2, poolLen + n));
            }
        }

        int find(byte[] d, int off, int len) {
            int h = (int) hash(d, off, len);
            int i = h & mask;
            while (slot[i] != 0) {
                int e = slot[i] - 1;
                if (keyLen[e] == len) {
                    byte[] p = pool;
                    int po = keyOff[e];
                    int k = 0;
                    while (k < len && p[po + k] == d[off + k]) k++;
                    if (k == len) return e;
                }
                i = (i + 1) & mask;
            }
            return -1;
        }

        int findOrInsert(byte[] d, int off, int len) {
            if (size * 10 >= cap * 7) grow();
            int h = (int) hash(d, off, len);
            int i = h & mask;
            while (slot[i] != 0) {
                int e = slot[i] - 1;
                int kl = keyLen[e];
                if (kl == len) {
                    byte[] p = pool;
                    int po = keyOff[e];
                    int k = 0;
                    while (k < len && p[po + k] == d[off + k]) k++;
                    if (k == len) return e;
                }
                i = (i + 1) & mask;
            }
            int e = size++;
            ensurePool(len);
            System.arraycopy(d, off, pool, poolLen, len);
            keyOff[e] = poolLen;
            keyLen[e] = len;
            poolLen += len;
            a[e] = 0;
            b[e] = 0;
            slot[i] = e + 1;
            return e;
        }

        private void grow() {
            cap <<= 1;
            mask = cap - 1;
            slot = new int[cap];
            int[] nKeyOff = new int[cap];
            int[] nKeyLen = new int[cap];
            long[] na = new long[cap];
            long[] nb = new long[cap];
            for (int e = 0; e < size; e++) {
                int h = (int) hash(pool, keyOff[e], keyLen[e]);
                int i = h & mask;
                while (slot[i] != 0) i = (i + 1) & mask;
                slot[i] = e + 1;
                nKeyOff[e] = keyOff[e];
                nKeyLen[e] = keyLen[e];
                na[e] = a[e];
                nb[e] = b[e];
            }
            keyOff = nKeyOff;
            keyLen = nKeyLen;
            a = na;
            b = nb;
        }

        int size() { return size; }
    }

    static byte[] data;
    static byte[] scratch = new byte[256];
    static int scratchLen;

    // ---------- JSON scanning helpers ----------
    static boolean isWS(byte c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    }

    static int skipWS(int i) {
        while (i < data.length && isWS(data[i])) i++;
        return i;
    }

    // parses string starting at '"'; result in sVal (start), eVal (end), i advanced past quote
    static int sVal, eVal;
    static boolean escVal;

    static void parseString(int i) {
        i++;
        sVal = i;
        boolean esc = false;
        while (i < data.length) {
            byte c = data[i];
            if (c == '"') break;
            if (c == '\\') {
                esc = true;
                i++;
                if (i < data.length && data[i] == 'u') i += 4;
            }
            i++;
        }
        eVal = i;
        escVal = esc;
        sNext = i + 1;
    }

    static int sNext;

    static int skipValue(int i) {
        int n = data.length;
        if (i < n && data[i] == '"') {
            parseString(i);
            return sNext;
        }
        if (i < n && (data[i] == '{' || data[i] == '[')) {
            int depth = 0;
            while (i < n) {
                byte c = data[i];
                if (c == '"') {
                    parseString(i);
                    i = sNext;
                    continue;
                }
                if (c == '{' || c == '[') depth++;
                else if (c == '}' || c == ']') {
                    if (--depth == 0) return i + 1;
                }
                i++;
            }
            return i;
        }
        while (i < n) {
            byte c = data[i];
            if (c == ',' || c == '}' || c == ']') break;
            i++;
        }
        return i;
    }

    static boolean strEq(int s, int e, boolean esc, String lit) {
        if (!esc) {
            int len = e - s;
            if (len != lit.length()) return false;
            for (int k = 0; k < len; k++) {
                if (data[s + k] != lit.charAt(k)) return false;
            }
            return true;
        }
        decodeString(s, e);
        if (scratchLen != lit.length()) return false;
        for (int k = 0; k < scratchLen; k++) {
            if (scratch[k] != lit.charAt(k)) return false;
        }
        return true;
    }

    static void decodeString(int s, int e) {
        if (scratch.length < (e - s) * 4 + 16) scratch = new byte[(e - s) * 4 + 16];
        scratchLen = 0;
        for (int i = s; i < e; i++) {
            byte c = data[i];
            if (c != '\\') {
                scratch[scratchLen++] = c;
                continue;
            }
            i++;
            byte x = data[i];
            switch (x) {
                case '"': scratch[scratchLen++] = '"'; break;
                case '\\': scratch[scratchLen++] = '\\'; break;
                case '/': scratch[scratchLen++] = '/'; break;
                case 'b': scratch[scratchLen++] = '\b'; break;
                case 'f': scratch[scratchLen++] = '\f'; break;
                case 'n': scratch[scratchLen++] = '\n'; break;
                case 'r': scratch[scratchLen++] = '\r'; break;
                case 't': scratch[scratchLen++] = '\t'; break;
                case 'u': {
                    int cp = hex4(i + 1);
                    i += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 2 < e
                            && data[i + 1] == '\\' && data[i + 2] == 'u') {
                        int lo = hex4(i + 3);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            i += 6;
                        }
                    }
                    scratchLen = appendRune(cp);
                    break;
                }
                default: scratch[scratchLen++] = x; break;
            }
        }
    }

    static int hex4(int i) {
        int v = 0;
        for (int k = 0; k < 4; k++) {
            byte c = data[i + k];
            v <<= 4;
            if (c >= '0' && c <= '9') v |= c - '0';
            else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') v |= c - 'A' + 10;
        }
        return v;
    }

    static int appendRune(int cp) {
        if (cp < 0x80) {
            scratch[scratchLen++] = (byte) cp;
        } else if (cp < 0x800) {
            scratch[scratchLen++] = (byte) (0xC0 | cp >> 6);
            scratch[scratchLen++] = (byte) (0x80 | cp & 0x3F);
        } else if (cp < 0x10000) {
            scratch[scratchLen++] = (byte) (0xE0 | cp >> 12);
            scratch[scratchLen++] = (byte) (0x80 | (cp >> 6) & 0x3F);
            scratch[scratchLen++] = (byte) (0x80 | cp & 0x3F);
        } else {
            scratch[scratchLen++] = (byte) (0xF0 | cp >> 18);
            scratch[scratchLen++] = (byte) (0x80 | (cp >> 12) & 0x3F);
            scratch[scratchLen++] = (byte) (0x80 | (cp >> 6) & 0x3F);
            scratch[scratchLen++] = (byte) (0x80 | cp & 0x3F);
        }
        return scratchLen;
    }

    // "12", "12.5", "12.05" -> integer hundredths
    static long parseAmount(int s, int e) {
        long whole = 0;
        int i = s;
        while (i < e && data[i] >= '0' && data[i] <= '9') {
            whole = whole * 10 + (data[i] - '0');
            i++;
        }
        long frac = 0;
        if (i < e && data[i] == '.') {
            i++;
            frac = (data[i] - '0') * 10L;
            i++;
            if (i < e) frac += data[i] - '0';
        }
        return whole * 100 + frac;
    }

    // key into table: raw slice if unescaped, else decoded copy
    static int keyTempStart, keyTempLen;
    static byte[] keyArr;      // points to data or to a temp copy
    static int keyOff, keyLen;

    static void makeKey(int s, int e, boolean esc) {
        if (!esc) {
            keyArr = data;
            keyOff = s;
            keyLen = e - s;
        } else {
            decodeString(s, e);
            keyArr = scratch;
            keyOff = 0;
            keyLen = scratchLen;
        }
    }

    public static void main(String[] args) throws IOException {
        data = Files.readAllBytes(Path.of(args[0]));
        Table rates = new Table();
        Table channels = new Table();
        Table accounts = new Table();
        int n = data.length;

        // First line: rates.
        int i = skipWS(0);
        int eol = indexOf(i, (byte) 10);
        if (eol < 0) eol = n;
        // parse rates object
        int p = skipWS(i);
        if (p < n && data[p] == '{') {
            p++;
            while (p < n) {
                p = skipWS(p);
                if (p >= n || data[p] == '}') break;
                if (data[p] == ',') { p++; continue; }
                parseString(p);
                int ks = sVal, ke = eVal; boolean kesc = escVal;
                p = skipWS(sNext);
                p++; // ':'
                p = skipWS(p);
                if (strEq(ks, ke, kesc, "rates")) {
                    p = skipWS(p);
                    p++; // '{'
                    while (p < n) {
                        p = skipWS(p);
                        if (p >= n || data[p] == '}') break;
                        if (data[p] == ',') { p++; continue; }
                        parseString(p);
                        int cs = sVal, ce = eVal; boolean cesc = escVal;
                        p = skipWS(sNext);
                        p++; // ':'
                        p = skipWS(p);
                        boolean neg = data[p] == '-';
                        if (neg) p++;
                        long rate = 0;
                        while (p < n && data[p] >= '0' && data[p] <= '9') {
                            rate = rate * 10 + (data[p] - '0');
                            p++;
                        }
                        if (neg) rate = -rate;
                        makeKey(cs, ce, cesc);
                        int eIdx = rates.findOrInsert(keyArr, keyOff, keyLen);
                        rates.b[eIdx] = rate;
                    }
                    p++; // '}'
                } else {
                    p = skipValue(p);
                }
            }
        }
        i = eol < n ? eol + 1 : n;

        long totalCount = 0, totalNet = 0;
        while (i < n) {
            int q = skipWS(i);
            eol = indexOf(i, (byte) 10);
            if (eol < 0) eol = n;
            if (q < eol && data[q] == '{') {
                q++;
                long sign = 0, rate = 0, amount = 0;
                boolean hasRate = false;
                int accS = -1, accE = 0, chanS = -1, chanE = 0;
                boolean accEsc = false, chanEsc = false, isTest = false;
                while (true) {
                    q = skipWS(q);
                    if (q >= n || data[q] == '}') { q++; break; }
                    if (data[q] == ',') { q++; continue; }
                    parseString(q);
                    int ks = sVal, ke = eVal; boolean kesc = escVal;
                    q = skipWS(sNext);
                    q++; // ':'
                    q = skipWS(q);
                    if (!kesc) {
                        int kl = ke - ks;
                        byte k0 = kl > 0 ? data[ks] : 0;
                        if (k0 == 't' && kl == 4 && data[ks] == 't' && data[ks + 1] == 'y'
                                && data[ks + 2] == 'p' && data[ks + 3] == 'e') {
                            parseString(q);
                            int vs = sVal, ve = eVal; boolean vesc = escVal;
                            q = sNext;
                            if (strEq(vs, ve, vesc, "credit") || strEq(vs, ve, vesc, "refund")) sign = 1;
                            else if (strEq(vs, ve, vesc, "debit")) sign = -1;
                            continue;
                        } else if (k0 == 'a' && kl == 6 && data[ks + 1] == 'm'
                                && data[ks + 2] == 'o' && data[ks + 3] == 'u'
                                && data[ks + 4] == 'n' && data[ks + 5] == 't') {
                            parseString(q);
                            int vs = sVal, ve = eVal;
                            q = sNext;
                            amount = parseAmount(vs, ve);
                            continue;
                        } else if (k0 == 'c' && kl == 8 && data[ks + 1] == 'u'
                                && data[ks + 2] == 'r' && data[ks + 3] == 'r'
                                && data[ks + 4] == 'e' && data[ks + 5] == 'n'
                                && data[ks + 6] == 'c' && data[ks + 7] == 'y') {
                            parseString(q);
                            int vs = sVal, ve = eVal; boolean vesc = escVal;
                            q = sNext;
                            makeKey(vs, ve, vesc);
                            int ri = rates.find(keyArr, keyOff, keyLen);
                            if (ri >= 0) {
                                rate = rates.b[ri];
                                hasRate = true;
                            } else {
                                hasRate = false;
                            }
                            continue;
                        } else if (k0 == 'a' && kl == 7 && data[ks + 1] == 'c'
                                && data[ks + 2] == 'c' && data[ks + 3] == 'o'
                                && data[ks + 4] == 'u' && data[ks + 5] == 'n'
                                && data[ks + 6] == 't') {
                            parseString(q);
                            accS = sVal; accE = eVal; accEsc = escVal;
                            q = sNext;
                            continue;
                        } else if (k0 == 't' && kl == 4 && data[ks + 1] == 'a'
                                && data[ks + 2] == 'g' && data[ks + 3] == 's') {
                            q++; // '['
                            while (true) {
                                q = skipWS(q);
                                if (q >= n || data[q] == ']') { q++; break; }
                                if (data[q] == ',') { q++; continue; }
                                if (data[q] == '"') {
                                    parseString(q);
                                    int vs = sVal, ve = eVal; boolean vesc = escVal;
                                    q = sNext;
                                    if (!isTest && strEq(vs, ve, vesc, "test")) isTest = true;
                                } else {
                                    q = skipValue(q);
                                }
                            }
                            continue;
                        } else if (k0 == 'm' && kl == 4 && data[ks + 1] == 'e'
                                && data[ks + 2] == 't' && data[ks + 3] == 'a') {
                            q++; // '{'
                            while (true) {
                                q = skipWS(q);
                                if (q >= n || data[q] == '}') { q++; break; }
                                if (data[q] == ',') { q++; continue; }
                                parseString(q);
                                int mks = sVal, mke = eVal; boolean mkesc = escVal;
                                q = skipWS(sNext);
                                q++; // ':'
                                q = skipWS(q);
                                if (strEq(mks, mke, mkesc, "channel")) {
                                    parseString(q);
                                    chanS = sVal; chanE = eVal; chanEsc = escVal;
                                    q = sNext;
                                } else {
                                    q = skipValue(q);
                                }
                            }
                            continue;
                        }
                    }
                    q = skipValue(q);
                }
                if (sign != 0 && !isTest && hasRate && accS >= 0 && chanS >= 0) {
                    long val = sign * ((amount * rate) / 1_000_000L);
                    totalCount++;
                    totalNet += val;
                    makeKey(chanS, chanE, chanEsc);
                    int ci = channels.findOrInsert(keyArr, keyOff, keyLen);
                    channels.a[ci]++;
                    channels.b[ci] += val;
                    makeKey(accS, accE, accEsc);
                    int ai = accounts.findOrInsert(keyArr, keyOff, keyLen);
                    accounts.b[ai] += val;
                }
            }
            i = eol < n ? eol + 1 : n;
        }

        StringBuilder out = new StringBuilder(4096);
        out.append("counted ").append(totalCount).append('\n');
        out.append("net ").append(totalNet).append('\n');

        // Channel lines sorted by name ascending (byte order).
        int nc = channels.size();
        Integer[] cIdx = new Integer[nc];
        for (int e = 0; e < nc; e++) cIdx[e] = e;
        java.util.Arrays.sort(cIdx, (x, y) -> {
            int lx = channels.keyLen[x], ly = channels.keyLen[y];
            int ox = channels.keyOff[x], oy = channels.keyOff[y];
            int m = Math.min(lx, ly);
            for (int k = 0; k < m; k++) {
                int d = (channels.pool[ox + k] & 0xff) - (channels.pool[oy + k] & 0xff);
                if (d != 0) return d;
            }
            return lx - ly;
        });
        for (int e : cIdx) {
            out.append("channel ").append(new String(channels.pool, channels.keyOff[e],
                    channels.keyLen[e], StandardCharsets.ISO_8859_1));
            out.append(' ').append(channels.a[e]).append(' ').append(channels.b[e]).append('\n');
        }

        // Top 10 accounts by net desc, then id asc.
        int na = accounts.size();
        int[] aIdx = new int[na];
        for (int e = 0; e < na; e++) aIdx[e] = e;
        int take = Math.min(10, na);
        // partial selection: place the 10 best in aIdx[0..take)
        for (int pos = 0; pos < take; pos++) {
            int best = pos;
            for (int j = pos + 1; j < na; j++) {
                if (accountBetter(accounts, aIdx[j], aIdx[best])) best = j;
            }
            int t = aIdx[pos]; aIdx[pos] = aIdx[best]; aIdx[best] = t;
        }
        // sort those 10
        int[] top = Arrays.copyOfRange(aIdx, 0, take);
        Integer[] topBox = new Integer[take];
        for (int k = 0; k < take; k++) topBox[k] = top[k];
        java.util.Arrays.sort(topBox, (x, y) -> accountBetter(accounts, x, y) ? -1
                : accountBetter(accounts, y, x) ? 1 : 0);
        for (int e : topBox) {
            out.append("account ").append(new String(accounts.pool, accounts.keyOff[e],
                    accounts.keyLen[e], StandardCharsets.ISO_8859_1));
            out.append(' ').append(accounts.b[e]).append('\n');
        }

        FileOutputStream fos = new FileOutputStream(java.io.FileDescriptor.out);
        fos.write(out.toString().getBytes(StandardCharsets.ISO_8859_1));
        fos.flush();
    }

    static boolean accountBetter(Table t, int x, int y) {
        long nx = t.b[x], ny = t.b[y];
        if (nx != ny) return nx > ny;
        int lx = t.keyLen[x], ly = t.keyLen[y];
        int ox = t.keyOff[x], oy = t.keyOff[y];
        int m = Math.min(lx, ly);
        for (int k = 0; k < m; k++) {
            int d = (t.pool[ox + k] & 0xff) - (t.pool[oy + k] & 0xff);
            if (d != 0) return d < 0;
        }
        return lx < ly;
    }

    static int indexOf(int from, byte c) {
        byte[] d = data;
        for (int i = from; i < d.length; i++) {
            if (d[i] == c) return i;
        }
        return -1;
    }
}
