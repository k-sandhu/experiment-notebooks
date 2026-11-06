using System;
using System.IO;
using System.Text;

// Open-addressing map byte-string -> {net, cnt}; keys copied once into an arena.
sealed class StrMap
{
    public ulong[] Hash;
    public int[] Off, KLen;
    public long[] Net, Cnt;
    public bool[] Used;
    public byte[] Arena = new byte[1 << 16];
    public int ArenaLen;
    int mask;
    public int UsedCnt;

    public StrMap(int capHint)
    {
        int c = 16;
        while (c < capHint) c <<= 1;
        Hash = new ulong[c]; Off = new int[c]; KLen = new int[c];
        Net = new long[c]; Cnt = new long[c]; Used = new bool[c];
        mask = c - 1;
    }

    void Grow()
    {
        var oh = Hash; var oo = Off; var ol = KLen;
        var on = Net; var oc = Cnt; var ou = Used;
        int c = oh.Length * 2;
        Hash = new ulong[c]; Off = new int[c]; KLen = new int[c];
        Net = new long[c]; Cnt = new long[c]; Used = new bool[c];
        mask = c - 1;
        for (int i = 0; i < oh.Length; i++) if (ou[i])
        {
            int j = (int)oh[i] & mask;
            while (Used[j]) j = (j + 1) & mask;
            Used[j] = true; Hash[j] = oh[i]; Off[j] = oo[i]; KLen[j] = ol[i];
            Net[j] = on[i]; Cnt[j] = oc[i];
        }
    }

    static ulong HashBytes(ReadOnlySpan<byte> b)
    {
        ulong h = 1469598103934665603UL;
        foreach (byte c in b) { h ^= c; h *= 1099511628211UL; }
        h ^= h >> 33; h *= 0xff51afd7ed558ccdUL; h ^= h >> 33;
        return h;
    }

    public int FindOrInsert(ReadOnlySpan<byte> key)
    {
        if ((UsedCnt + 1) * 10 > Hash.Length * 7) Grow();
        ulong h = HashBytes(key);
        int i = (int)h & mask;
        while (true)
        {
            if (!Used[i])
            {
                Used[i] = true; Hash[i] = h;
                if (ArenaLen + key.Length > Arena.Length)
                {
                    int nc = Arena.Length;
                    while (nc < ArenaLen + key.Length) nc <<= 1;
                    Array.Resize(ref Arena, nc);
                }
                Off[i] = ArenaLen; KLen[i] = key.Length;
                key.CopyTo(Arena.AsSpan(ArenaLen));
                ArenaLen += key.Length;
                Net[i] = 0; Cnt[i] = 0; UsedCnt++;
                return i;
            }
            if (Hash[i] == h && KLen[i] == key.Length &&
                Arena.AsSpan(Off[i], key.Length).SequenceEqual(key)) return i;
            i = (i + 1) & mask;
        }
    }

    public int Find(ReadOnlySpan<byte> key)
    {
        ulong h = HashBytes(key);
        int i = (int)h & mask;
        while (true)
        {
            if (!Used[i]) return -1;
            if (Hash[i] == h && KLen[i] == key.Length &&
                Arena.AsSpan(Off[i], key.Length).SequenceEqual(key)) return i;
            i = (i + 1) & mask;
        }
    }
}

static class Program
{
    static byte[] d = Array.Empty<byte>();
    static int n, pos;
    static byte[] keyDec = new byte[64], acctDec = new byte[64],
                  chanDec = new byte[64], miscDec = new byte[64];

    static void SkipWs()
    {
        while (pos < n)
        {
            byte c = d[pos];
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') pos++; else break;
        }
    }

    static void SkipStringRaw()
    {
        pos++;
        while (pos < n)
        {
            byte c = d[pos];
            if (c == '"') { pos++; return; }
            pos += c == '\\' ? 2 : 1;
        }
    }

    static uint Hex4(ref int i, int end)
    {
        uint v = 0;
        for (int k = 0; k < 4 && i < end; k++, i++)
        {
            byte c = d[i];
            v <<= 4;
            if (c >= '0' && c <= '9') v |= (uint)(c - '0');
            else if (c >= 'a' && c <= 'f') v |= (uint)(c - 'a' + 10);
            else if (c >= 'A' && c <= 'F') v |= (uint)(c - 'A' + 10);
        }
        return v;
    }

    static int AppendUtf8(byte[] outp, int w, uint cp)
    {
        if (cp < 0x80) outp[w++] = (byte)cp;
        else if (cp < 0x800)
        {
            outp[w++] = (byte)(0xC0 | (cp >> 6));
            outp[w++] = (byte)(0x80 | (cp & 0x3F));
        }
        else if (cp < 0x10000)
        {
            outp[w++] = (byte)(0xE0 | (cp >> 12));
            outp[w++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
            outp[w++] = (byte)(0x80 | (cp & 0x3F));
        }
        else
        {
            outp[w++] = (byte)(0xF0 | (cp >> 18));
            outp[w++] = (byte)(0x80 | ((cp >> 12) & 0x3F));
            outp[w++] = (byte)(0x80 | ((cp >> 6) & 0x3F));
            outp[w++] = (byte)(0x80 | (cp & 0x3F));
        }
        return w;
    }

    // d[pos]=='"'; result is a slice of data, or of dec when escapes present.
    static void ParseString(ref byte[] dec, out byte[] arr, out int off, out int len)
    {
        pos++;
        int start = pos;
        bool esc = false;
        while (pos < n)
        {
            byte c = d[pos];
            if (c == '"') break;
            if (c == '\\') { esc = true; pos += 2; } else pos++;
        }
        int end = pos;
        if (pos < n) pos++;
        if (!esc) { arr = d; off = start; len = end - start; return; }
        if (dec.Length < end - start)
        {
            int nc = dec.Length;
            while (nc < end - start) nc <<= 1;
            dec = new byte[nc];
        }
        int w = 0, i = start;
        while (i < end)
        {
            byte c = d[i];
            if (c != '\\') { dec[w++] = c; i++; continue; }
            i++;
            if (i >= end) break;
            byte e = d[i++];
            switch (e)
            {
                case (byte)'"': dec[w++] = (byte)'"'; break;
                case (byte)'\\': dec[w++] = (byte)'\\'; break;
                case (byte)'/': dec[w++] = (byte)'/'; break;
                case (byte)'b': dec[w++] = (byte)'\b'; break;
                case (byte)'f': dec[w++] = (byte)'\f'; break;
                case (byte)'n': dec[w++] = (byte)'\n'; break;
                case (byte)'r': dec[w++] = (byte)'\r'; break;
                case (byte)'t': dec[w++] = (byte)'\t'; break;
                case (byte)'u':
                {
                    uint cp = Hex4(ref i, end);
                    if (cp >= 0xD800 && cp <= 0xDBFF && i + 1 < end && d[i] == '\\' && d[i + 1] == 'u')
                    {
                        i += 2;
                        uint lo = Hex4(ref i, end);
                        if (lo >= 0xDC00 && lo <= 0xDFFF) cp = 0x10000u + ((cp - 0xD800u) << 10) + (lo - 0xDC00u);
                        else { w = AppendUtf8(dec, w, cp); cp = lo; }
                    }
                    w = AppendUtf8(dec, w, cp);
                    break;
                }
                default: dec[w++] = e; break;
            }
        }
        arr = dec; off = 0; len = w;
    }

    static void SkipValue()
    {
        SkipWs();
        if (pos >= n) return;
        byte c = d[pos];
        if (c == '"') { SkipStringRaw(); return; }
        if (c == '{' || c == '[')
        {
            int depth = 0;
            while (pos < n)
            {
                byte ch = d[pos];
                if (ch == '"') { SkipStringRaw(); continue; }
                if (ch == '{' || ch == '[') { depth++; pos++; }
                else if (ch == '}' || ch == ']') { depth--; pos++; if (depth == 0) return; }
                else pos++;
            }
            return;
        }
        while (pos < n)
        {
            byte ch = d[pos];
            if (ch == ',' || ch == '}' || ch == ']' || ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r') break;
            pos++;
        }
    }

    static long ParseInt64()
    {
        SkipWs();
        bool neg = false;
        if (pos < n && d[pos] == '-') { neg = true; pos++; }
        long v = 0;
        while (pos < n && d[pos] >= '0' && d[pos] <= '9') v = v * 10 + (d[pos++] - '0');
        return neg ? -v : v;
    }

    static long ParseAmount(ReadOnlySpan<byte> v)
    {
        int i = 0;
        long ip = 0;
        while (i < v.Length && v[i] != '.') { ip = ip * 10 + (v[i] - '0'); i++; }
        long h = ip * 100;
        if (i < v.Length)
        {
            i++;
            if (i < v.Length) { h += (v[i] - '0') * 10L; i++; }
            if (i < v.Length) h += v[i] - '0';
        }
        return h;
    }

    static int[] Slots(StrMap m)
    {
        var r = new int[m.UsedCnt];
        int k = 0;
        for (int i = 0; i < m.Used.Length; i++) if (m.Used[i]) r[k++] = i;
        return r;
    }

    static void Main(string[] args)
    {
        d = File.ReadAllBytes(args[0]);
        n = d.Length;
        pos = 0;
        var rates = new StrMap(64);
        var channels = new StrMap(64);
        var accounts = new StrMap(1 << 16);

        // First object: rates.
        SkipWs();
        if (pos < n && d[pos] == '{')
        {
            pos++; SkipWs();
            if (pos < n && d[pos] == '}') pos++;
            else
            {
                while (true)
                {
                    SkipWs();
                    ParseString(ref keyDec, out var ka, out int ko, out int kl);
                    bool isRates = ka.AsSpan(ko, kl).SequenceEqual("rates"u8);
                    SkipWs(); pos++;
                    SkipWs();
                    if (isRates)
                    {
                        pos++; SkipWs();
                        if (pos < n && d[pos] == '}') pos++;
                        else while (true)
                        {
                            SkipWs();
                            ParseString(ref miscDec, out var cka, out int cko, out int ckl);
                            SkipWs(); pos++;
                            long rv = ParseInt64();
                            rates.Net[rates.FindOrInsert(cka.AsSpan(cko, ckl))] = rv;
                            SkipWs();
                            if (pos < n && d[pos] == ',') { pos++; continue; }
                            if (pos < n && d[pos] == '}') pos++;
                            break;
                        }
                    }
                    else SkipValue();
                    SkipWs();
                    if (pos < n && d[pos] == ',') { pos++; continue; }
                    if (pos < n && d[pos] == '}') pos++;
                    break;
                }
            }
        }

        long counted = 0, net = 0;
        while (true)
        {
            SkipWs();
            if (pos >= n) break;
            long sign = 1;
            bool isVoid = false, hasTest = false;
            long hundredths = 0, rate = 0;
            // Keep acct/chan as spans via backing arrays + ranges, since spans
            // cannot be fields; record (array, off, len).
            byte[] acctArr = d, chanArr = d;
            int acctOff = 0, acctLen = 0, chanOff = 0, chanLen = 0;
            pos++; SkipWs();
            if (pos < n && d[pos] == '}') pos++;
            else
            {
                while (true)
                {
                    SkipWs();
                    ParseString(ref keyDec, out var ka, out int ko, out int kl);
                    var key = ka.AsSpan(ko, kl);
                    int kind =
                        key.SequenceEqual("account"u8) ? 1 :
                        key.SequenceEqual("type"u8) ? 2 :
                        key.SequenceEqual("amount"u8) ? 3 :
                        key.SequenceEqual("currency"u8) ? 4 :
                        key.SequenceEqual("tags"u8) ? 5 :
                        key.SequenceEqual("meta"u8) ? 6 : 0;
                    SkipWs(); pos++;
                    SkipWs();
                    switch (kind)
                    {
                        case 1:
                            ParseString(ref acctDec, out acctArr, out acctOff, out acctLen);
                            break;
                        case 2:
                        {
                            ParseString(ref miscDec, out var va, out int vo, out int vl);
                            var v = va.AsSpan(vo, vl);
                            if (v.SequenceEqual("void"u8)) isVoid = true;
                            else if (v.SequenceEqual("debit"u8)) sign = -1;
                            else sign = 1;
                            break;
                        }
                        case 3:
                        {
                            ParseString(ref miscDec, out var va, out int vo, out int vl);
                            hundredths = ParseAmount(va.AsSpan(vo, vl));
                            break;
                        }
                        case 4:
                        {
                            ParseString(ref miscDec, out var va, out int vo, out int vl);
                            int sl = rates.Find(va.AsSpan(vo, vl));
                            rate = sl >= 0 ? rates.Net[sl] : 0;
                            break;
                        }
                        case 5:
                        {
                            pos++; SkipWs();
                            if (pos < n && d[pos] == ']') pos++;
                            else while (true)
                            {
                                SkipWs();
                                if (pos < n && d[pos] == '"')
                                {
                                    ParseString(ref miscDec, out var va, out int vo, out int vl);
                                    if (va.AsSpan(vo, vl).SequenceEqual("test"u8)) hasTest = true;
                                }
                                else SkipValue();
                                SkipWs();
                                if (pos < n && d[pos] == ',') { pos++; continue; }
                                if (pos < n && d[pos] == ']') pos++;
                                break;
                            }
                            break;
                        }
                        case 6:
                        {
                            pos++; SkipWs();
                            if (pos < n && d[pos] == '}') pos++;
                            else while (true)
                            {
                                SkipWs();
                                ParseString(ref keyDec, out var k2a, out int k2o, out int k2l);
                                bool isChan = k2a.AsSpan(k2o, k2l).SequenceEqual("channel"u8);
                                SkipWs(); pos++;
                                SkipWs();
                                if (isChan)
                                {
                                    ParseString(ref chanDec, out chanArr, out chanOff, out chanLen);
                                }
                                else SkipValue();
                                SkipWs();
                                if (pos < n && d[pos] == ',') { pos++; continue; }
                                if (pos < n && d[pos] == '}') pos++;
                                break;
                            }
                            break;
                        }
                        default:
                            SkipValue();
                            break;
                    }
                    SkipWs();
                    if (pos < n && d[pos] == ',') { pos++; continue; }
                    if (pos < n && d[pos] == '}') pos++;
                    break;
                }
            }
            if (isVoid || hasTest) continue;
            long usd = (hundredths * rate) / 1000000L;
            long signed = sign < 0 ? -usd : usd;
            counted++;
            net += signed;
            accounts.Net[accounts.FindOrInsert(acctArr.AsSpan(acctOff, acctLen))] += signed;
            int cs = channels.FindOrInsert(chanArr.AsSpan(chanOff, chanLen));
            channels.Net[cs] += signed;
            channels.Cnt[cs]++;
        }

        var chans = Slots(channels);
        Array.Sort(chans, (x, y) => channels.Arena.AsSpan(channels.Off[x], channels.KLen[x])
            .SequenceCompareTo(channels.Arena.AsSpan(channels.Off[y], channels.KLen[y])));
        var accts = Slots(accounts);
        Array.Sort(accts, (x, y) =>
        {
            if (accounts.Net[x] != accounts.Net[y]) return accounts.Net[x] > accounts.Net[y] ? -1 : 1;
            return accounts.Arena.AsSpan(accounts.Off[x], accounts.KLen[x])
                .SequenceCompareTo(accounts.Arena.AsSpan(accounts.Off[y], accounts.KLen[y]));
        });

        var sb = new StringBuilder(4096);
        sb.Append("counted ").Append(counted).Append('\n');
        sb.Append("net ").Append(net).Append('\n');
        foreach (int s in chans)
            sb.Append("channel ").Append(Encoding.UTF8.GetString(channels.Arena, channels.Off[s], channels.KLen[s]))
              .Append(' ').Append(channels.Cnt[s]).Append(' ').Append(channels.Net[s]).Append('\n');
        int top = Math.Min(10, accts.Length);
        for (int i = 0; i < top; i++)
        {
            int s = accts[i];
            sb.Append("account ").Append(Encoding.UTF8.GetString(accounts.Arena, accounts.Off[s], accounts.KLen[s]))
              .Append(' ').Append(accounts.Net[s]).Append('\n');
        }
        Console.Out.Write(sb.ToString());
    }

}
