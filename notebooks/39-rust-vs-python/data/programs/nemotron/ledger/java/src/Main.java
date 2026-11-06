import java.nio.file.*;
import java.util.*;
import java.util.Map.Entry;

public class Main {
    static byte[] file;
    static int pos;
    static int limit;
    static int flen;

    static boolean isWS(int b) {
        return b == ' ' || b == '\t' || b == '\r' || b == '\n';
    }

    static void skipWS() { while (pos < limit && isWS(file[pos])) pos++; }

    // Scans a JSON string starting at buf[pos]=='"'. Appends unescaped chars to out.
    // Sets pos to just after closing quote. Returns false on malformed input.
    static boolean scanString(StringBuilder out) {
        out.setLength(0);
        int i = pos + 1;
        while (i < limit) {
            int c = file[i++] & 0xFF;
            if (c == '"') { pos = i; return true; }
            if (c == '\\') {
                if (i >= limit) return false;
                int e = file[i++] & 0xFF;
                switch (e) {
                    case '"': out.append('"'); break;
                    case '\\': out.append('\\'); break;
                    case '/': out.append('/'); break;
                    case 'n': out.append('\n'); break;
                    case 'r': out.append('\r'); break;
                    case 't': out.append('\t'); break;
                    case 'b': out.append('\b'); break;
                    case 'f': out.append('\f'); break;
                    case 'u': {
                        if (i + 6 >= limit) return false;
                        int cp = 0;
                        for (int k = 0; k < 4; k++) {
                            int h = file[i++] & 0xFF; cp <<= 4;
                            if (h >= '0' && h <= '9') cp += h - '0';
                            else if (h >= 'a' && h <= 'f') cp += h - 'a' + 10;
                            else if (h >= 'A' && h <= 'F') cp += h - 'A' + 10;
                            else return false;
                        }
                        if (cp >= 0xD800 && cp <= 0xDBFF && file[i] == '\\' && file[i + 1] == 'u') {
                            i += 2;
                            int cp2 = 0;
                            for (int k = 0; k < 4; k++) {
                                int h = file[i++] & 0xFF; cp2 <<= 4;
                                if (h >= '0' && h <= '9') cp2 += h - '0';
                                else if (h >= 'a' && h <= 'f') cp2 += h - 'a' + 10;
                                else if (h >= 'A' && h <= 'F') cp2 += h - 'A' + 10;
                                else return false;
                            }
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (cp2 - 0xDC00);
                        }
                        out.appendCodePoint(cp);
                        break;
                    }
                    default: return false;
                }
            } else {
                out.append((char) c);
            }
        }
        return false;
    }

    static void skipScalar() {
        while (pos < limit) {
            int b = file[pos] & 0xFF;
            if (b == ',' || b == '}' || b == ']' || isWS(b)) return;
            pos++;
        }
    }

    enum Kind { RATES, COUNTED, SKIPPED, BAD }

    // Fields filled by parseLine
    static String acct, typ, amt, cur, chan;
    static boolean hasTest;
    static long usd;

    // Parses one line (buf[pos..limit-1]). Returns its kind.
    static Kind parseLine() {
        skipWS();
        if (pos >= limit || file[pos] != '{') return Kind.BAD;
        pos++; // skip outer {

        int depth = 1;
        String key = null;
        boolean haveKey = false;
        int keyDepth = 0;

        boolean inRates = false;
        int ratesDepth = 0;
        boolean inMeta = false;
        int metaDepth = 0;
        boolean inTags = false;
        int tagsDepth = 0;

        acct = null; typ = null; amt = null; cur = null; chan = null;
        hasTest = false;
        boolean isRates = false;
        StringBuilder sb = new StringBuilder();

        while (pos < limit && depth > 0) {
            int c = file[pos] & 0xFF;
            if (c == '"') {
                if (!scanString(sb)) return Kind.BAD;
                skipWS();
                if (pos < limit && file[pos] == ':') {
                    key = sb.toString();
                    keyDepth = depth;
                    haveKey = true;
                    pos++; skipWS();
                    if (pos >= limit) return Kind.BAD;
                    int nxt = file[pos] & 0xFF;
                    if (nxt == '"') {
                        if (!scanString(sb)) return Kind.BAD;
                        if (haveKey) {
                            if (keyDepth == 1) {
                                if (key.equals("account")) acct = sb.toString();
                                else if (key.equals("type")) typ = sb.toString();
                                else if (key.equals("currency")) cur = sb.toString();
                                else if (key.equals("amount")) amt = sb.toString();
                            } else if (inMeta && depth == metaDepth && key.equals("channel")) {
                                chan = sb.toString();
                            }
                        }
                        haveKey = false;
                    } else if (nxt == '{') {
                        depth++; pos++;
                        if (haveKey && keyDepth == 1 && key.equals("rates")) { inRates = true; ratesDepth = depth; isRates = true; }
                        else if (haveKey && keyDepth == 1 && key.equals("meta")) { metaDepth = depth; inMeta = true; }
                        haveKey = false;
                    } else if (nxt == '[') {
                        depth++; pos++;
                        if (haveKey && keyDepth == 1 && key.equals("tags")) { inTags = true; tagsDepth = depth; }
                        haveKey = false;
                    } else {
                        if (inRates && depth == ratesDepth && haveKey) {
                            long v = 0; boolean any = false;
                            while (pos < limit) {
                                int h = file[pos] & 0xFF;
                                if (h < '0' || h > '9') break;
                                v = v * 10 + (h - '0'); pos++; any = true;
                            }
                            if (!any) return Kind.BAD;
                            rates.put(key, v);
                        } else {
                            skipScalar();
                        }
                        haveKey = false;
                    }
                } else {
                    // string value without key -> array element
                    if (inTags && depth == tagsDepth) {
                        if (sb.toString().equals("test")) hasTest = true;
                    }
                    haveKey = false;
                }
            } else if (c == '{' || c == '[') {
                depth++; pos++;
                haveKey = false;
            } else if (c == '}' || c == ']') {
                depth--; pos++;
                if (inMeta && depth == metaDepth - 1) inMeta = false;
                if (inTags && depth == tagsDepth - 1) inTags = false;
                haveKey = false;
            } else {
                pos++;
            }
        }

        if (isRates) return Kind.RATES;
        if (typ != null && typ.equals("void")) return Kind.SKIPPED;
        if (hasTest) return Kind.SKIPPED;

        long dollars = 0;
        int j = 0;
        while (j < amt.length() && amt.charAt(j) >= '0' && amt.charAt(j) <= '9') {
            dollars = dollars * 10 + (amt.charAt(j) - '0'); j++;
        }
        long cents = 0;
        if (j < amt.length() && amt.charAt(j) == '.') {
            j++;
            int nd = 0;
            while (j < amt.length() && amt.charAt(j) >= '0' && amt.charAt(j) <= '9' && nd < 2) {
                cents = cents * 10 + (amt.charAt(j) - '0'); j++; nd++;
            }
            while (nd < 2) { cents *= 10; nd++; }
        }
        long hundredths = dollars * 100 + cents;

        Long rate = rates.get(cur);
        if (rate == null) return Kind.BAD;
        usd = (hundredths * rate) / 1000000L;
        if (typ.equals("debit")) usd = -usd;
        return Kind.COUNTED;
    }

    static final Map<String, Long> rates = new HashMap<>();
    static final Map<String, long[]> channels = new HashMap<>();
    static final Map<String, Long> accounts = new HashMap<>();
    static long totalCount = 0;
    static long totalNet = 0;

    public static void main(String[] args) throws Exception {
        file = Files.readAllBytes(Path.of(args[0]));
        flen = file.length;
        pos = 0;

        while (pos < flen) {
            int lineStart = pos;
            while (pos < flen && file[pos] != '\n') pos++;
            limit = pos;
            if (pos < flen) pos++; // skip newline

            int ln = limit - lineStart;
            if (ln == 0) continue;

            pos = lineStart;
            Kind k = parseLine();
            if (k == Kind.RATES) { }
            else if (k == Kind.BAD) { }
            else if (k == Kind.SKIPPED) { }
            else {
                totalCount++;
                totalNet += usd;
                long[] c = channels.computeIfAbsent(chan, ign -> new long[2]);
                c[0]++; c[1] += usd;
                accounts.merge(acct, usd, Long::sum);
            }
        }

        StringBuilder o = new StringBuilder();
        o.append("counted ").append(totalCount).append('\n');
        o.append("net ").append(totalNet).append('\n');

        List<String> chNames = new ArrayList<>(channels.keySet());
        Collections.sort(chNames);
        for (String name : chNames) {
            long[] c = channels.get(name);
            o.append("channel ").append(name).append(' ').append(c[0]).append(' ').append(c[1]).append('\n');
        }

        List<Entry<String,Long>> accts = new ArrayList<>(accounts.entrySet());
        accts.sort((a,b) -> {
            int cmp = Long.compare(b.getValue(), a.getValue());
            if (cmp != 0) return cmp;
            return a.getKey().compareTo(b.getKey());
        });
        int lim = Math.min(10, accts.size());
        for (int k = 0; k < lim; k++) {
            o.append("account ").append(accts.get(k).getKey()).append(' ').append(accts.get(k).getValue()).append('\n');
        }

        System.out.print(o);
    }
}
