using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

// Ledger: fast single-pass JSON Lines aggregator.
// Hand-rolled byte scanner over the whole input (no DOM), unsafe pointer access.
internal static class Program {
    private static unsafe byte* p;
    private static int i;
    private static int n;

    private static int sStart;
    private static int sEnd;
    private static bool sEsc;

    private static unsafe void Main(string[] args) {
        byte[] data = File.ReadAllBytes(args[0]);
        n = data.Length;

        var rates = new Dictionary<string, long>();
        var channels = new Dictionary<string, long[]>(); // [count, net]
        var accounts = new Dictionary<string, long[]>(); // [net]

        fixed (byte* basePtr = data) {
            p = basePtr;

            // ---- first line: rates ----
            SkipWs();
            i++; // '{'
            while (true) {
                SkipWs();
                ScanString();
                int ks = sStart, ke = sEnd;
                bool kesc = sEsc;
                SkipWs();
                i++; // ':'
                SkipWs();
                if (!kesc && ke - ks == 5 && Eq(ks, ke, "rates")) {
                    i++; // '{'
                    while (true) {
                        SkipWs();
                        if (p[i] == '}') {
                            i++;
                            break;
                        }
                        ScanString();
                        string cur = StrValue();
                        SkipWs();
                        i++; // ':'
                        SkipWs();
                        long r = 0;
                        while (p[i] >= '0' && p[i] <= '9') {
                            r = r * 10 + (p[i] - '0');
                            i++;
                        }
                        rates[cur] = r;
                        SkipWs();
                        if (p[i] == ',') i++;
                    }
                } else {
                    SkipValue();
                }
                SkipWs();
                if (p[i] == ',') {
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
                SkipWs();
                if (i >= n) break;
                i++; // '{'

                int typeCode = 0; // 1 credit, 2 debit, 3 refund, 4 void
                bool testTag = false;
                long hund = 0;
                string currency = null;
                string account = null;
                string channel = null;

                while (true) {
                    SkipWs();
                    ScanString();
                    int ks = sStart, ke = sEnd;
                    int klen = ke - ks;
                    bool kesc = sEsc;
                    SkipWs();
                    i++; // ':'
                    SkipWs();
                    if (!kesc) {
                        char c0 = klen > 0 ? (char)p[ks] : '\0';
                        if (klen == 4 && c0 == 't' && Eq(ks, ke, "type")) {
                            ScanString();
                            typeCode = TypeCode();
                        } else if (klen == 6 && Eq(ks, ke, "amount")) {
                            ScanString();
                            hund = ParseAmount(sStart, sEnd, sEsc);
                        } else if (klen == 8 && Eq(ks, ke, "currency")) {
                            ScanString();
                            currency = StrValue();
                        } else if (klen == 7 && Eq(ks, ke, "account")) {
                            ScanString();
                            account = StrValue();
                        } else if (klen == 4 && c0 == 't' && Eq(ks, ke, "tags")) {
                            testTag = ParseTags();
                        } else if (klen == 4 && c0 == 'm' && Eq(ks, ke, "meta")) {
                            channel = ParseMeta();
                        } else {
                            SkipValue();
                        }
                    } else {
                        // escaped key: decode and compare (rare)
                        switch (DecodeString(ks, ke)) {
                            case "type":
                                ScanString();
                                typeCode = TypeCode();
                                break;
                            case "amount":
                                ScanString();
                                hund = ParseAmount(sStart, sEnd, sEsc);
                                break;
                            case "currency":
                                ScanString();
                                currency = StrValue();
                                break;
                            case "account":
                                ScanString();
                                account = StrValue();
                                break;
                            case "tags":
                                testTag = ParseTags();
                                break;
                            case "meta":
                                channel = ParseMeta();
                                break;
                            default:
                                SkipValue();
                                break;
                        }
                    }
                    SkipWs();
                    if (p[i] == ',') {
                        i++;
                        continue;
                    }
                    i++; // '}'
                    break;
                }

                if (typeCode == 4 || testTag) continue;

                if (!rates.TryGetValue(currency, out long rate)) continue;
                long usd = (hund * rate) / 1000000;
                long v = typeCode == 2 ? -usd : usd;

                totalCount++;
                totalNet += v;

                if (channels.TryGetValue(channel, out var c)) {
                    c[0]++;
                    c[1] += v;
                } else {
                    channels[channel] = new[] { 1L, v };
                }
                if (accounts.TryGetValue(account, out var a)) {
                    a[0] += v;
                } else {
                    accounts[account] = new[] { v };
                }
            }

            // ---- output ----
            var sb = new StringBuilder(1 << 16);
            sb.Append("counted ").Append(totalCount).Append('\n');
            sb.Append("net ").Append(totalNet).Append('\n');

            var chs = new List<KeyValuePair<string, long[]>>(channels);
            chs.Sort((x, y) => string.CompareOrdinal(x.Key, y.Key));
            foreach (var e in chs) {
                sb.Append("channel ").Append(e.Key).Append(' ')
                  .Append(e.Value[0]).Append(' ').Append(e.Value[1]).Append('\n');
            }

            var accs = new List<KeyValuePair<string, long[]>>(accounts);
            accs.Sort((x, y) => {
                int c = y.Value[0].CompareTo(x.Value[0]);
                return c != 0 ? c : string.CompareOrdinal(x.Key, y.Key);
            });
            int lim = Math.Min(10, accs.Count);
            for (int k = 0; k < lim; k++) {
                sb.Append("account ").Append(accs[k].Key).Append(' ').Append(accs[k].Value[0]).Append('\n');
            }

            using Stream stdout = Console.OpenStandardOutput();
            var bytes = Encoding.UTF8.GetBytes(sb.ToString());
            stdout.Write(bytes, 0, bytes.Length);
        }
    }

    // ---- scanner helpers ----

    private static unsafe void SkipWs() {
        while (i < n) {
            byte c = p[i];
            if (c == (byte)' ' || c == (byte)'\t' || c == (byte)'\r' || c == (byte)'\n') i++;
            else break;
        }
    }

    private static unsafe void SkipString() { // i at opening quote; leaves i past closing quote
        i++;
        while (true) {
            byte c = p[i];
            if (c == (byte)'\\') {
                i += 2; // hex digits after \u contain no '"' or '\\'
                continue;
            }
            if (c == (byte)'"') {
                i++;
                return;
            }
            i++;
        }
    }

    private static unsafe void ScanString() { // i at opening quote; leaves i past closing quote
        i++;
        sStart = i;
        sEsc = false;
        while (true) {
            byte c = p[i];
            if (c == (byte)'\\') {
                sEsc = true;
                i += 2;
                continue;
            }
            if (c == (byte)'"') {
                sEnd = i;
                i++;
                return;
            }
            i++;
        }
    }

    private static unsafe void SkipValue() {
        byte c = p[i];
        if (c == (byte)'"') {
            SkipString();
            return;
        }
        if (c == (byte)'{' || c == (byte)'[') {
            int depth = 0;
            while (i < n) {
                byte d = p[i];
                if (d == (byte)'"') {
                    SkipString();
                    continue;
                }
                if (d == (byte)'{' || d == (byte)'[') depth++;
                else if (d == (byte)'}' || d == (byte)']') {
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
            byte d = p[i];
            if (d == (byte)',' || d == (byte)'}' || d == (byte)']' || d == (byte)' ' || d == (byte)'\t' || d == (byte)'\r' || d == (byte)'\n') return;
            i++;
        }
    }

    private static unsafe bool Eq(int a, int b, string lit) {
        if (b - a != lit.Length) return false;
        for (int j = 0; j < lit.Length; j++) {
            if (p[a + j] != lit[j]) return false;
        }
        return true;
    }

    // value string at sStart..sEnd (sEsc set) as a .NET String
    private static unsafe string StrValue() {
        if (!sEsc) {
            // account IDs / channel names / currencies are ASCII: Latin1 decode is a raw widening copy
            return Encoding.Latin1.GetString(p + sStart, sEnd - sStart);
        }
        return DecodeString(sStart, sEnd);
    }

    private static unsafe string DecodeString(int from, int to) {
        var outChars = new char[to - from];
        int o = 0, j = from;
        while (j < to) {
            char c = (char)p[j];
            if (c != '\\') {
                outChars[o++] = c;
                j++;
                continue;
            }
            char e = (char)p[j + 1];
            j += 2;
            switch (e) {
                case '"': outChars[o++] = '"'; break;
                case '\\': outChars[o++] = '\\'; break;
                case '/': outChars[o++] = '/'; break;
                case 'b': outChars[o++] = '\b'; break;
                case 'f': outChars[o++] = '\f'; break;
                case 'n': outChars[o++] = '\n'; break;
                case 'r': outChars[o++] = '\r'; break;
                case 't': outChars[o++] = '\t'; break;
                case 'u': {
                    int cp = Hex4(j);
                    j += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && j + 1 < to && p[j] == (byte)'\\' && p[j + 1] == (byte)'u') {
                        int lo = Hex4(j + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            j += 6;
                        }
                    }
                    if (cp < 0x10000) {
                        outChars[o++] = (char)cp;
                    } else {
                        cp -= 0x10000;
                        outChars[o++] = (char)(0xD800 | (cp >> 10));
                        outChars[o++] = (char)(0xDC00 | (cp & 0x3FF));
                    }
                    break;
                }
                default: outChars[o++] = e; break;
            }
        }
        return new string(outChars, 0, o);
    }

    private static unsafe int Hex4(int at) {
        int v = 0;
        for (int k = 0; k < 4; k++) {
            byte c = p[at + k];
            v <<= 4;
            if (c <= (byte)'9') v += c - (byte)'0';
            else if (c <= (byte)'F') v += c - (byte)'A' + 10;
            else v += c - (byte)'a' + 10;
        }
        return v;
    }

    private static bool DecodedEq(string lit) => DecodeString(sStart, sEnd) == lit;

    private static unsafe long ParseAmount(int from, int to, bool esc) {
        if (esc) {
            string s = DecodeString(from, to);
            return ParseAmountDigits(s, 0, s.Length);
        }
        return ParseAmountDigits(from, to);
    }

    private static unsafe long ParseAmountDigits(int from, int to) {
        long ip = 0;
        int j = from;
        while (j < to && p[j] >= (byte)'0' && p[j] <= (byte)'9') {
            ip = ip * 10 + (p[j] - (byte)'0');
            j++;
        }
        long frac = 0;
        int fd = 0;
        if (j < to && p[j] == (byte)'.') {
            j++;
            while (j < to && fd < 2 && p[j] >= (byte)'0' && p[j] <= (byte)'9') {
                frac = frac * 10 + (p[j] - (byte)'0');
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

    private static long ParseAmountDigits(string s, int from, int to) {
        long ip = 0;
        int j = from;
        while (j < to && s[j] >= '0' && s[j] <= '9') {
            ip = ip * 10 + (s[j] - '0');
            j++;
        }
        long frac = 0;
        int fd = 0;
        if (j < to && s[j] == '.') {
            j++;
            while (j < to && fd < 2 && s[j] >= '0' && s[j] <= '9') {
                frac = frac * 10 + (s[j] - '0');
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

    private static unsafe bool ParseTags() {
        i++; // '['
        bool test = false;
        while (true) {
            SkipWs();
            if (p[i] == (byte)']') {
                i++;
                return test;
            }
            if (p[i] == (byte)'"') {
                ScanString();
                if (!test) {
                    test = sEsc ? DecodedEq("test") : (sEnd - sStart == 4 && Eq(sStart, sEnd, "test"));
                }
            } else {
                SkipValue();
            }
            SkipWs();
            if (p[i] == (byte)',') i++;
        }
    }

    private static unsafe string ParseMeta() {
        i++; // '{'
        string channel = null;
        while (true) {
            SkipWs();
            if (p[i] == (byte)'}') {
                i++;
                return channel;
            }
            ScanString();
            int ks = sStart, ke = sEnd;
            bool kesc = sEsc;
            SkipWs();
            i++; // ':'
            SkipWs();
            bool isChannel = kesc ? DecodeString(ks, ke) == "channel" : (ke - ks == 7 && Eq(ks, ke, "channel"));
            if (isChannel) {
                ScanString();
                channel = StrValue();
            } else {
                SkipValue();
            }
            SkipWs();
            if (p[i] == (byte)',') i++;
        }
    }

    private static unsafe int TypeCode() {
        if (!sEsc) {
            int len = sEnd - sStart;
            if (len == 6 && Eq(sStart, sEnd, "credit")) return 1;
            if (len == 5 && Eq(sStart, sEnd, "debit")) return 2;
            if (len == 6 && Eq(sStart, sEnd, "refund")) return 3;
            if (len == 4 && Eq(sStart, sEnd, "void")) return 4;
            return 0;
        }
        switch (DecodeString(sStart, sEnd)) {
            case "credit": return 1;
            case "debit": return 2;
            case "refund": return 3;
            case "void": return 4;
            default: return 0;
        }
    }
}
