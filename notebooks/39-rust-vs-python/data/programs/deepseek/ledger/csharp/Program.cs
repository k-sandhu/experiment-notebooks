using System;
using System.IO;
using System.Text;
using System.Collections.Generic;

static class Solution
{
    static byte[] B;
    static int LEN, P;

    // -----------------------------------------------------------------------
    // Open addressing hash map keyed by spans of the input buffer.
    // -----------------------------------------------------------------------
    sealed class SpanMap
    {
        public int[] off;
        public int[] klen;
        public long[] v1;
        public long[] v2;
        public int cap;
        public int cnt;

        public SpanMap(int c) { Init(c); }

        public void Init(int c)
        {
            cap = c; cnt = 0;
            off = new int[c];
            klen = new int[c];
            v1 = new long[c];
            v2 = new long[c];
            for (int i = 0; i < c; i++) klen[i] = -1;
        }

        static ulong Hash(int s, int n)
        {
            ulong h = 1469598103934665603UL;
            for (int i = 0; i < n; i++)
            {
                h ^= B[s + i];
                h *= 1099511628211UL;
            }
            return h;
        }

        void Grow()
        {
            int nc = cap * 2;
            var no = new int[nc];
            var nl = new int[nc];
            var n1 = new long[nc];
            var n2 = new long[nc];
            for (int i = 0; i < nc; i++) nl[i] = -1;
            int mask = nc - 1;
            for (int j = 0; j < cap; j++)
            {
                if (klen[j] < 0) continue;
                int i = (int)(Hash(off[j], klen[j]) & (ulong)mask);
                while (nl[i] >= 0) i = (i + 1) & mask;
                no[i] = off[j];
                nl[i] = klen[j];
                n1[i] = v1[j];
                n2[i] = v2[j];
            }
            off = no; klen = nl; v1 = n1; v2 = n2; cap = nc;
        }

        public int Find(int s, int n)
        {
            int mask = cap - 1;
            int i = (int)(Hash(s, n) & (ulong)mask);
            while (klen[i] >= 0)
            {
                if (klen[i] == n && SpanEq(off[i], off[i] + n, s, s + n)) return i;
                i = (i + 1) & mask;
            }
            return -1;
        }

        public int GetOrInsert(int s, int n)
        {
            if ((cnt + 1) * 10 > cap * 7) Grow();
            int mask = cap - 1;
            int i = (int)(Hash(s, n) & (ulong)mask);
            while (klen[i] >= 0)
            {
                if (klen[i] == n && SpanEq(off[i], off[i] + n, s, s + n)) return i;
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

    static void SkipWs()
    {
        while (P < LEN)
        {
            byte c = B[P];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') P++;
            else break;
        }
    }

    static void ParseString(out int s, out int e, out bool esc)
    {
        P++;
        s = P;
        esc = false;
        while (true)
        {
            byte c = B[P];
            if (c == (byte)'"') { e = P; P++; return; }
            if (c == (byte)'\\') { esc = true; P += 2; }
            else P++;
        }
    }

    static uint Hex4(int p)
    {
        uint v = 0;
        for (int i = 0; i < 4; i++)
        {
            uint c = B[p + i];
            uint d;
            if (c >= '0' && c <= '9') d = c - '0';
            else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
            else d = c - 'A' + 10;
            v = (v << 4) | d;
        }
        return v;
    }

    static int Decode(int s, int e)
    {
        int w = s, r = s;
        while (r < e)
        {
            byte c = B[r++];
            if (c != (byte)'\\') { B[w++] = c; continue; }
            byte x = B[r++];
            switch (x)
            {
                case (byte)'"': B[w++] = (byte)'"'; break;
                case (byte)'\\': B[w++] = (byte)'\\'; break;
                case (byte)'/': B[w++] = (byte)'/'; break;
                case (byte)'b': B[w++] = 8; break;
                case (byte)'f': B[w++] = 12; break;
                case (byte)'n': B[w++] = (byte)'\n'; break;
                case (byte)'r': B[w++] = (byte)'\r'; break;
                case (byte)'t': B[w++] = (byte)'\t'; break;
                case (byte)'u':
                {
                    uint cp = Hex4(r);
                    r += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && r + 6 <= e &&
                        B[r] == (byte)'\\' && B[r + 1] == (byte)'u')
                    {
                        uint lo = Hex4(r + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF)
                        {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            r += 6;
                        }
                    }
                    if (cp < 0x80) B[w++] = (byte)cp;
                    else if (cp < 0x800)
                    {
                        B[w++] = (byte)(0xC0 | (cp >> 6));
                        B[w++] = (byte)(0x80 | (cp & 0x3F));
                    }
                    else if (cp < 0x10000)
                    {
                        B[w++] = (byte)(0xE0 | (cp >> 12));
                        B[w++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                        B[w++] = (byte)(0x80 | (cp & 0x3F));
                    }
                    else
                    {
                        B[w++] = (byte)(0xF0 | (cp >> 18));
                        B[w++] = (byte)(0x80 | ((cp >> 12) & 0x3F));
                        B[w++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
                        B[w++] = (byte)(0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default: B[w++] = x; break;
            }
        }
        return w;
    }

    static void ParseStringValue(out int s, out int e)
    {
        ParseString(out s, out e, out bool esc);
        if (esc) e = Decode(s, e);
    }

    static bool SpanEq(int s, int e, string lit)
    {
        int n = e - s;
        if (n != lit.Length) return false;
        for (int i = 0; i < n; i++)
            if (B[s + i] != (byte)lit[i]) return false;
        return true;
    }

    static bool SpanEq(int s1, int e1, int s2, int e2)
    {
        int n = e1 - s1;
        if (n != e2 - s2) return false;
        for (int i = 0; i < n; i++)
            if (B[s1 + i] != B[s2 + i]) return false;
        return true;
    }

    static int SpanCompare(int o1, int l1, int o2, int l2)
    {
        int n = l1 < l2 ? l1 : l2;
        for (int i = 0; i < n; i++)
        {
            int d = B[o1 + i] - B[o2 + i];
            if (d != 0) return d;
        }
        return l1 - l2;
    }

    static void SkipValue()
    {
        SkipWs();
        byte c = B[P];
        if (c == (byte)'"')
        {
            ParseString(out _, out _, out _);
            return;
        }
        if (c == (byte)'{' || c == (byte)'[')
        {
            int depth = 0;
            while (true)
            {
                c = B[P];
                if (c == (byte)'"')
                {
                    ParseString(out _, out _, out _);
                }
                else
                {
                    P++;
                    if (c == (byte)'{' || c == (byte)'[') depth++;
                    else if (c == (byte)'}' || c == (byte)']')
                    {
                        if (--depth == 0) return;
                    }
                }
            }
        }
        while (P < LEN)
        {
            c = B[P];
            if (c == (byte)',' || c == (byte)'}' || c == (byte)']' ||
                c == (byte)' ' || c == (byte)'\t' || c == (byte)'\n' || c == (byte)'\r')
                return;
            P++;
        }
    }

    static long ParseAmount(int s, int e)
    {
        long ip = 0;
        int i = s;
        while (i < e && B[i] != (byte)'.')
        {
            ip = ip * 10 + (B[i] - '0');
            i++;
        }
        long frac = 0;
        if (i < e)
        {
            i++;
            int digits = 0;
            while (i < e)
            {
                frac = frac * 10 + (B[i] - '0');
                i++;
                digits++;
            }
            if (digits == 1) frac *= 10;
        }
        return ip * 100 + frac;
    }

    static int TypeKind(int s, int e)
    {
        int n = e - s;
        if (n == 6)
        {
            if (SpanEq(s, e, "credit")) return 0;
            if (SpanEq(s, e, "refund")) return 2;
        }
        else if (n == 5)
        {
            if (SpanEq(s, e, "debit")) return 1;
        }
        else if (n == 4)
        {
            if (SpanEq(s, e, "void")) return 3;
        }
        return -1;
    }

    static bool ParseTags()
    {
        P++;
        bool hasTest = false;
        while (true)
        {
            SkipWs();
            if (B[P] == (byte)']') { P++; return hasTest; }
            ParseStringValue(out int s, out int e);
            if (e - s == 4 && SpanEq(s, e, "test")) hasTest = true;
            SkipWs();
            if (B[P] == (byte)',') { P++; continue; }
            if (B[P] == (byte)']') { P++; return hasTest; }
        }
    }

    static void ParseMeta(out int chS, out int chE, out bool chSet)
    {
        P++;
        chS = 0; chE = 0; chSet = false;
        while (true)
        {
            SkipWs();
            if (B[P] == (byte)'}') { P++; return; }
            ParseString(out int ks, out int ke, out bool esc);
            if (esc) ke = Decode(ks, ke);
            SkipWs();
            P++;
            SkipWs();
            if (SpanEq(ks, ke, "channel"))
            {
                ParseStringValue(out chS, out chE);
                chSet = true;
            }
            else SkipValue();
            SkipWs();
            if (B[P] == (byte)',') { P++; continue; }
            if (B[P] == (byte)'}') { P++; return; }
        }
    }

    static void ParseRatesObject()
    {
        P++;
        while (true)
        {
            SkipWs();
            if (B[P] == (byte)'}') { P++; return; }
            ParseString(out int ks, out int ke, out bool esc);
            if (esc) ke = Decode(ks, ke);
            SkipWs();
            P++;
            SkipWs();
            long v = 0;
            bool neg = false;
            if (B[P] == (byte)'-') { neg = true; P++; }
            while (P < LEN)
            {
                byte c = B[P];
                if (c < '0' || c > '9') break;
                v = v * 10 + (c - '0');
                P++;
            }
            if (neg) v = -v;
            int idx = rates.GetOrInsert(ks, ke - ks);
            rates.v1[idx] = v;
            SkipWs();
            if (B[P] == (byte)',') { P++; continue; }
            if (B[P] == (byte)'}') { P++; return; }
        }
    }

    static long totalNet;
    static long totalCount;

    static void ParseTransaction()
    {
        P++;
        int accS = 0, accE = 0;
        int chS = 0, chE = 0;
        long hundredths = 0;
        long rate = 0;
        int type = -1;
        bool hasTest = false;

        while (true)
        {
            SkipWs();
            if (B[P] == (byte)'}') { P++; break; }
            ParseString(out int ks, out int ke, out bool esc);
            if (esc) ke = Decode(ks, ke);
            SkipWs();
            P++;
            SkipWs();

            if (SpanEq(ks, ke, "account"))
            {
                ParseStringValue(out accS, out accE);
            }
            else if (SpanEq(ks, ke, "type"))
            {
                ParseStringValue(out int s, out int e);
                type = TypeKind(s, e);
            }
            else if (SpanEq(ks, ke, "amount"))
            {
                ParseStringValue(out int s, out int e);
                hundredths = ParseAmount(s, e);
            }
            else if (SpanEq(ks, ke, "currency"))
            {
                ParseStringValue(out int s, out int e);
                int ri = rates.Find(s, e - s);
                rate = ri >= 0 ? rates.v1[ri] : 0;
            }
            else if (SpanEq(ks, ke, "tags"))
            {
                hasTest = ParseTags();
            }
            else if (SpanEq(ks, ke, "meta"))
            {
                ParseMeta(out chS, out chE, out _);
            }
            else
            {
                SkipValue();
            }

            SkipWs();
            if (B[P] == (byte)',') { P++; continue; }
            if (B[P] == (byte)'}') { P++; break; }
        }

        if (type == 3 || type == -1 || hasTest) return;

        long usd = (hundredths * rate) / 1000000L;
        long signed = type == 1 ? -usd : usd;
        totalNet += signed;
        totalCount++;

        int ci = channels.GetOrInsert(chS, chE - chS);
        channels.v1[ci]++;
        channels.v2[ci] += signed;

        int ai = accounts.GetOrInsert(accS, accE - accS);
        accounts.v1[ai] += signed;
    }

    static void Main(string[] args)
    {
        if (args.Length < 1) return;
        B = File.ReadAllBytes(args[0]);
        LEN = B.Length;

        rates = new SpanMap(64);
        channels = new SpanMap(64);
        accounts = new SpanMap(1 << 14);

        P = 0;
        SkipWs();
        P++;
        while (true)
        {
            SkipWs();
            if (B[P] == (byte)'}') { P++; break; }
            ParseString(out int ks, out int ke, out bool esc);
            if (esc) ke = Decode(ks, ke);
            SkipWs();
            P++;
            SkipWs();
            if (SpanEq(ks, ke, "rates")) ParseRatesObject();
            else SkipValue();
            SkipWs();
            if (B[P] == (byte)',') { P++; continue; }
            if (B[P] == (byte)'}') { P++; break; }
        }

        while (true)
        {
            SkipWs();
            if (P >= LEN) break;
            ParseTransaction();
        }

        var chIdx = new List<int>(channels.cnt);
        for (int i = 0; i < channels.cap; i++)
            if (channels.klen[i] >= 0) chIdx.Add(i);
        chIdx.Sort((a, b) => SpanCompare(channels.off[a], channels.klen[a],
                                          channels.off[b], channels.klen[b]));

        var accIdx = new List<int>(accounts.cnt);
        for (int i = 0; i < accounts.cap; i++)
            if (accounts.klen[i] >= 0) accIdx.Add(i);
        accIdx.Sort((a, b) =>
        {
            if (accounts.v1[a] != accounts.v1[b])
                return accounts.v1[b].CompareTo(accounts.v1[a]);
            return SpanCompare(accounts.off[a], accounts.klen[a],
                               accounts.off[b], accounts.klen[b]);
        });
        int k = accIdx.Count < 10 ? accIdx.Count : 10;

        var sb = new StringBuilder(8192);
        sb.Append("counted ").Append(totalCount).Append('\n');
        sb.Append("net ").Append(totalNet).Append('\n');
        for (int j = 0; j < chIdx.Count; j++)
        {
            int idx = chIdx[j];
            sb.Append("channel ");
            sb.Append(Encoding.UTF8.GetString(B, channels.off[idx], channels.klen[idx]));
            sb.Append(' ').Append(channels.v1[idx]).Append(' ').Append(channels.v2[idx]).Append('\n');
        }
        for (int j = 0; j < k; j++)
        {
            int idx = accIdx[j];
            sb.Append("account ");
            sb.Append(Encoding.UTF8.GetString(B, accounts.off[idx], accounts.klen[idx]));
            sb.Append(' ').Append(accounts.v1[idx]).Append('\n');
        }

        byte[] outBytes = Encoding.UTF8.GetBytes(sb.ToString());
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(outBytes, 0, outBytes.Length);
    }
}
