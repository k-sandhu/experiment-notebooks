using System.Runtime.InteropServices;
using System.Text;

unsafe sealed class NBuf
{
    public byte* P;
    public int Cap;

    public NBuf(int cap)
    {
        Cap = cap;
        P = (byte*)NativeMemory.Alloc((nuint)cap);
    }

    public void Ensure(int n)
    {
        if (n <= Cap) return;
        int nc = Math.Max(n, Cap * 2);
        P = (byte*)NativeMemory.Realloc(P, (nuint)nc);
        Cap = nc;
    }
}

unsafe sealed class Interner
{
    int[] table = new int[1024];
    int mask = 1023;
    byte* pool;
    int poolCap = 1 << 16;
    int poolLen;
    int[] off = new int[256];
    int[] len = new int[256];
    int[] hash = new int[256];
    public long[] Sum = new long[256];
    public long[] Cnt = new long[256];
    public int Count;

    public Interner()
    {
        pool = (byte*)NativeMemory.Alloc((nuint)poolCap);
    }

    static int HashOf(byte* s, int n)
    {
        uint h = 2166136261u;
        for (int i = 0; i < n; i++)
            h = (h ^ s[i]) * 16777619u;
        return (int)(h ^ (h >> 15));
    }

    void GrowIds()
    {
        int nc = off.Length * 2;
        Array.Resize(ref off, nc);
        Array.Resize(ref len, nc);
        Array.Resize(ref hash, nc);
        Array.Resize(ref Sum, nc);
        Array.Resize(ref Cnt, nc);
    }

    void Rehash()
    {
        int ns = table.Length * 2;
        var nt = new int[ns];
        int nm = ns - 1;
        for (int id = 0; id < Count; id++)
        {
            int idx = hash[id] & nm;
            while (nt[idx] != 0) idx = (idx + 1) & nm;
            nt[idx] = id + 1;
        }
        table = nt;
        mask = nm;
    }

    int Lookup(byte* s, int n, bool add)
    {
        int h = HashOf(s, n);
        int idx = h & mask;
        while (true)
        {
            int v = table[idx];
            if (v == 0) break;
            int id = v - 1;
            if (hash[id] == h && len[id] == n &&
                new ReadOnlySpan<byte>(pool + off[id], n).SequenceEqual(new ReadOnlySpan<byte>(s, n)))
                return id;
            idx = (idx + 1) & mask;
        }
        if (!add) return -1;

        int nid = Count++;
        if (nid >= off.Length) GrowIds();
        if (poolLen + n > poolCap)
        {
            poolCap = Math.Max(poolCap * 2, poolLen + n);
            pool = (byte*)NativeMemory.Realloc(pool, (nuint)poolCap);
        }
        Buffer.MemoryCopy(s, pool + poolLen, poolCap - poolLen, n);
        off[nid] = poolLen;
        len[nid] = n;
        hash[nid] = h;
        poolLen += n;
        table[idx] = nid + 1;
        if (Count * 2 > table.Length) Rehash();
        return nid;
    }

    public int Find(byte* s, int n) => Lookup(s, n, false);

    public int GetOrAdd(byte* s, int n) => Lookup(s, n, true);

    public ReadOnlySpan<byte> KeyOf(int id) => new ReadOnlySpan<byte>(pool + off[id], len[id]);
}

unsafe sealed class Ledger
{
    const int K_OTHER = 0, K_TYPE = 1, K_AMOUNT = 2, K_CURRENCY = 3, K_ACCOUNT = 4, K_TAGS = 5, K_META = 6;

    byte* p, e;
    byte* cs, ce;
    bool hasEsc;
    bool first = true;

    readonly NBuf tmpBuf = new NBuf(256);
    readonly NBuf accBuf = new NBuf(256);
    readonly NBuf chBuf = new NBuf(256);
    readonly NBuf curBuf = new NBuf(256);

    public readonly Interner Currencies = new Interner();
    public readonly Interner Accounts = new Interner();
    public readonly Interner Channels = new Interner();
    public long Counted;
    public long Net;

    public void ProcessRange(byte* start, byte* end)
    {
        byte* q = start;
        while (q < end)
        {
            int rem = (int)(end - q);
            int idx = new ReadOnlySpan<byte>(q, rem).IndexOf((byte)'\n');
            byte* le = idx < 0 ? end : q + idx;
            ParseLine(q, le);
            q = le + 1;
        }
    }

    void ParseLine(byte* s, byte* en)
    {
        p = s;
        e = en;
        SkipWs();
        if (p >= e) return;
        if (first)
        {
            first = false;
            ParseRates();
        }
        else
        {
            ParseTxn();
        }
    }

    void SkipWs()
    {
        byte* q = p;
        while (q < e)
        {
            byte c = *q;
            if (c != ' ' && c != '\n' && c != '\r' && c != '\t') break;
            q++;
        }
        p = q;
    }

    // p must be at the opening quote; afterwards p is past the closing quote.
    void ScanString()
    {
        byte* s = p + 1;
        byte* q = s;
        bool esc = false;
        while (*q != '"')
        {
            if (*q == '\\')
            {
                esc = true;
                q += 2;
            }
            else
            {
                q++;
            }
        }
        cs = s;
        ce = q;
        hasEsc = esc;
        p = q + 1;
    }

    void SkipValue()
    {
        byte c = *p;
        if (c == '"')
        {
            ScanString();
            return;
        }
        if (c == '{' || c == '[')
        {
            int depth = 0;
            byte* q = p;
            do
            {
                byte d = *q;
                if (d == '"')
                {
                    p = q;
                    ScanString();
                    q = p;
                    continue;
                }
                if (d == '{' || d == '[') depth++;
                else if (d == '}' || d == ']') depth--;
                q++;
            } while (depth > 0);
            p = q;
            return;
        }
        byte* r = p;
        while (r < e)
        {
            byte d = *r;
            if (d == ',' || d == '}' || d == ']' || d == ' ' || d == '\n' || d == '\r' || d == '\t') break;
            r++;
        }
        p = r;
    }

    // Yields the decoded contents of the last scanned string.
    void Resolve(NBuf b, out byte* rp, out int rn)
    {
        int n = (int)(ce - cs);
        if (!hasEsc)
        {
            rp = cs;
            rn = n;
            return;
        }
        b.Ensure(n);
        rn = Decode(cs, ce, b.P);
        rp = b.P;
    }

    long ParseInt()
    {
        bool neg = false;
        if (*p == '-')
        {
            neg = true;
            p++;
        }
        long v = 0;
        while (p < e)
        {
            byte c = *p;
            if (c < '0' || c > '9') break;
            v = v * 10 + (c - '0');
            p++;
        }
        return neg ? -v : v;
    }

    static int Hex4(byte* s)
    {
        int v = 0;
        for (int i = 0; i < 4; i++)
        {
            int c = s[i];
            int dv = c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10;
            v = (v << 4) | dv;
        }
        return v;
    }

    static byte* WriteUtf8(byte* w, int cp)
    {
        if (cp < 0x80)
        {
            *w++ = (byte)cp;
        }
        else if (cp < 0x800)
        {
            *w++ = (byte)(0xC0 | (cp >> 6));
            *w++ = (byte)(0x80 | (cp & 0x3F));
        }
        else if (cp < 0x10000)
        {
            *w++ = (byte)(0xE0 | (cp >> 12));
            *w++ = (byte)(0x80 | ((cp >> 6) & 0x3F));
            *w++ = (byte)(0x80 | (cp & 0x3F));
        }
        else
        {
            *w++ = (byte)(0xF0 | (cp >> 18));
            *w++ = (byte)(0x80 | ((cp >> 12) & 0x3F));
            *w++ = (byte)(0x80 | ((cp >> 6) & 0x3F));
            *w++ = (byte)(0x80 | (cp & 0x3F));
        }
        return w;
    }

    // Decodes JSON string contents [s, t) into d as UTF-8. Output never exceeds input length.
    static int Decode(byte* s, byte* t, byte* d)
    {
        byte* w = d;
        while (s < t)
        {
            byte c = *s;
            if (c != '\\')
            {
                *w++ = c;
                s++;
                continue;
            }
            int x = s[1];
            s += 2;
            switch (x)
            {
                case 'u':
                {
                    int cp = Hex4(s);
                    s += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && t - s >= 6 && s[0] == '\\' && s[1] == 'u')
                    {
                        int lo = Hex4(s + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF)
                        {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            s += 6;
                        }
                    }
                    w = WriteUtf8(w, cp);
                    break;
                }
                case 'n': *w++ = 10; break;
                case 't': *w++ = 9; break;
                case 'r': *w++ = 13; break;
                case 'b': *w++ = 8; break;
                case 'f': *w++ = 12; break;
                default: *w++ = (byte)x; break;
            }
        }
        return (int)(w - d);
    }

    static long ParseAmount(byte* s, byte* t)
    {
        long ip = 0;
        int frac = 0, fd = 0;
        bool dot = false;
        for (; s < t; s++)
        {
            byte c = *s;
            if (c == '.')
            {
                dot = true;
                continue;
            }
            int dg = c - '0';
            if (!dot)
            {
                ip = ip * 10 + dg;
            }
            else if (fd < 2)
            {
                frac = frac * 10 + dg;
                fd++;
            }
        }
        while (fd < 2)
        {
            frac *= 10;
            fd++;
        }
        return ip * 100 + frac;
    }

    static int KeyCode(ReadOnlySpan<byte> k)
    {
        switch (k.Length)
        {
            case 4:
                if (k.SequenceEqual("type"u8)) return K_TYPE;
                if (k.SequenceEqual("tags"u8)) return K_TAGS;
                if (k.SequenceEqual("meta"u8)) return K_META;
                break;
            case 6:
                if (k.SequenceEqual("amount"u8)) return K_AMOUNT;
                break;
            case 7:
                if (k.SequenceEqual("account"u8)) return K_ACCOUNT;
                break;
            case 8:
                if (k.SequenceEqual("currency"u8)) return K_CURRENCY;
                break;
        }
        return K_OTHER;
    }

    // credit 0, debit 1, refund 2, void 3, unknown -1
    static int TypeCode(ReadOnlySpan<byte> t)
    {
        if (t.SequenceEqual("credit"u8)) return 0;
        if (t.SequenceEqual("debit"u8)) return 1;
        if (t.SequenceEqual("refund"u8)) return 2;
        if (t.SequenceEqual("void"u8)) return 3;
        return -1;
    }

    void ParseRates()
    {
        if (*p != '{')
        {
            p = e;
            return;
        }
        p++;
        while (true)
        {
            SkipWs();
            byte c = *p;
            if (c == '}')
            {
                p++;
                break;
            }
            if (c == ',')
            {
                p++;
                continue;
            }
            ScanString();
            Resolve(tmpBuf, out byte* kp, out int kn);
            bool isRates = new ReadOnlySpan<byte>(kp, kn).SequenceEqual("rates"u8);
            SkipWs();
            p++;
            SkipWs();
            if (isRates && *p == '{')
            {
                p++;
                while (true)
                {
                    SkipWs();
                    byte d = *p;
                    if (d == '}')
                    {
                        p++;
                        break;
                    }
                    if (d == ',')
                    {
                        p++;
                        continue;
                    }
                    ScanString();
                    Resolve(tmpBuf, out byte* cp, out int cn);
                    int id = Currencies.GetOrAdd(cp, cn);
                    SkipWs();
                    p++;
                    SkipWs();
                    long v = ParseInt();
                    Currencies.Sum[id] = v;
                }
            }
            else
            {
                SkipValue();
            }
        }
    }

    void ParseTxn()
    {
        if (*p != '{')
        {
            p = e;
            return;
        }
        p++;

        int typ = -1;
        long hundredths = 0;
        bool test = false;
        byte* accP = accBuf.P;
        int accN = 0;
        byte* chP = chBuf.P;
        int chN = 0;
        byte* curP = curBuf.P;
        int curN = 0;

        SkipWs();
        if (*p == '}')
        {
            p++;
        }
        else
        {
            while (true)
            {
                SkipWs();
                ScanString();
                Resolve(tmpBuf, out byte* kp, out int kn);
                int kc = KeyCode(new ReadOnlySpan<byte>(kp, kn));
                SkipWs();
                p++;
                SkipWs();

                switch (kc)
                {
                    case K_TYPE:
                    {
                        if (*p == '"')
                        {
                            ScanString();
                            Resolve(tmpBuf, out byte* tp, out int tn);
                            typ = TypeCode(new ReadOnlySpan<byte>(tp, tn));
                        }
                        else
                        {
                            SkipValue();
                        }
                        break;
                    }
                    case K_AMOUNT:
                    {
                        if (*p == '"')
                        {
                            ScanString();
                            hundredths = ParseAmount(cs, ce);
                        }
                        else
                        {
                            SkipValue();
                        }
                        break;
                    }
                    case K_CURRENCY:
                    {
                        if (*p == '"')
                        {
                            ScanString();
                            Resolve(curBuf, out curP, out curN);
                        }
                        else
                        {
                            SkipValue();
                        }
                        break;
                    }
                    case K_ACCOUNT:
                    {
                        if (*p == '"')
                        {
                            ScanString();
                            Resolve(accBuf, out accP, out accN);
                        }
                        else
                        {
                            SkipValue();
                        }
                        break;
                    }
                    case K_TAGS:
                    {
                        if (*p == '[')
                        {
                            p++;
                            while (true)
                            {
                                SkipWs();
                                byte b = *p;
                                if (b == ']')
                                {
                                    p++;
                                    break;
                                }
                                if (b == ',')
                                {
                                    p++;
                                    continue;
                                }
                                if (b == '"')
                                {
                                    ScanString();
                                    Resolve(tmpBuf, out byte* gp, out int gn);
                                    if (new ReadOnlySpan<byte>(gp, gn).SequenceEqual("test"u8)) test = true;
                                }
                                else
                                {
                                    SkipValue();
                                }
                            }
                        }
                        else
                        {
                            SkipValue();
                        }
                        break;
                    }
                    case K_META:
                    {
                        if (*p == '{')
                        {
                            p++;
                            while (true)
                            {
                                SkipWs();
                                byte b = *p;
                                if (b == '}')
                                {
                                    p++;
                                    break;
                                }
                                if (b == ',')
                                {
                                    p++;
                                    continue;
                                }
                                ScanString();
                                Resolve(tmpBuf, out byte* mp, out int mn);
                                bool isChannel = new ReadOnlySpan<byte>(mp, mn).SequenceEqual("channel"u8);
                                SkipWs();
                                p++;
                                SkipWs();
                                if (isChannel && *p == '"')
                                {
                                    ScanString();
                                    Resolve(chBuf, out chP, out chN);
                                }
                                else
                                {
                                    SkipValue();
                                }
                            }
                        }
                        else
                        {
                            SkipValue();
                        }
                        break;
                    }
                    default:
                    {
                        SkipValue();
                        break;
                    }
                }

                SkipWs();
                if (*p == ',')
                {
                    p++;
                    continue;
                }
                p++;
                break;
            }
        }

        if (typ < 0 || typ == 3 || test) return;

        int cid = Currencies.Find(curP, curN);
        long rate = cid >= 0 ? Currencies.Sum[cid] : 0;
        long usd = hundredths * rate / 1000000;
        long sv = typ == 1 ? -usd : usd;

        int aid = Accounts.GetOrAdd(accP, accN);
        Accounts.Sum[aid] += sv;
        int chid = Channels.GetOrAdd(chP, chN);
        Channels.Sum[chid] += sv;
        Channels.Cnt[chid]++;
        Counted++;
        Net += sv;
    }
}

unsafe static class Program
{
    static void Main(string[] args)
    {
        var ledger = new Ledger();

        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16, FileOptions.SequentialScan))
        {
            int cap = 1 << 22;
            byte* buf = (byte*)NativeMemory.Alloc((nuint)cap);
            int filled = 0;
            bool eof = false;

            while (true)
            {
                if (filled == cap)
                {
                    cap *= 2;
                    buf = (byte*)NativeMemory.Realloc(buf, (nuint)cap);
                }

                int n = fs.Read(new Span<byte>(buf + filled, cap - filled));
                if (n <= 0) eof = true;
                else filled += n;

                int procEnd;
                if (eof)
                {
                    procEnd = filled;
                }
                else
                {
                    int i = filled - 1;
                    while (i >= 0 && buf[i] != (byte)'\n') i--;
                    procEnd = i + 1;
                }

                if (procEnd > 0) ledger.ProcessRange(buf, buf + procEnd);

                int rest = filled - procEnd;
                if (procEnd > 0 && rest > 0)
                {
                    new Span<byte>(buf + procEnd, rest).CopyTo(new Span<byte>(buf, rest));
                }
                filled = rest;

                if (eof) break;
            }

            NativeMemory.Free(buf);
        }

        var sb = new StringBuilder();
        sb.Append("counted ").Append(ledger.Counted).Append('\n');
        sb.Append("net ").Append(ledger.Net).Append('\n');

        var ch = ledger.Channels;
        int nc = ch.Count;
        int[] order = new int[nc];
        for (int i = 0; i < nc; i++) order[i] = i;
        Array.Sort(order, (a, b) => ch.KeyOf(a).SequenceCompareTo(ch.KeyOf(b)));
        foreach (int id in order)
        {
            sb.Append("channel ").Append(Encoding.UTF8.GetString(ch.KeyOf(id)))
              .Append(' ').Append(ch.Cnt[id])
              .Append(' ').Append(ch.Sum[id])
              .Append('\n');
        }

        var ac = ledger.Accounts;
        int na = ac.Count;
        bool[] used = new bool[na];
        int take = Math.Min(10, na);
        for (int k = 0; k < take; k++)
        {
            int best = -1;
            for (int i = 0; i < na; i++)
            {
                if (used[i]) continue;
                if (best < 0)
                {
                    best = i;
                    continue;
                }
                long si = ac.Sum[i];
                long sBest = ac.Sum[best];
                if (si > sBest || (si == sBest && ac.KeyOf(i).SequenceCompareTo(ac.KeyOf(best)) < 0))
                    best = i;
            }
            used[best] = true;
            sb.Append("account ").Append(Encoding.UTF8.GetString(ac.KeyOf(best)))
              .Append(' ').Append(ac.Sum[best])
              .Append('\n');
        }

        byte[] outBytes = Encoding.UTF8.GetBytes(sb.ToString());
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(outBytes, 0, outBytes.Length);
        stdout.Flush();
    }
}
