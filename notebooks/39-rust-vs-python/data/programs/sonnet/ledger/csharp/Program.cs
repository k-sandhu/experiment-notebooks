using System.Runtime.InteropServices;
using System.Text;

unsafe class Scratch
{
    public byte* Ptr;
    public int Cap;
    public int Len;

    public Scratch()
    {
        Cap = 256;
        Ptr = (byte*)NativeMemory.Alloc((nuint)Cap);
    }

    public void Reserve(int extra)
    {
        if (Len + extra > Cap)
        {
            while (Len + extra > Cap) Cap *= 2;
            Ptr = (byte*)NativeMemory.Realloc(Ptr, (nuint)Cap);
        }
    }

    public void Push(byte b)
    {
        Reserve(1);
        Ptr[Len++] = b;
    }

    public void PushUtf8(uint cp)
    {
        Reserve(4);
        byte* b = Ptr + Len;
        if (cp < 0x80) { b[0] = (byte)cp; Len += 1; }
        else if (cp < 0x800) { b[0] = (byte)(0xC0 | (cp >> 6)); b[1] = (byte)(0x80 | (cp & 0x3F)); Len += 2; }
        else if (cp < 0x10000)
        {
            b[0] = (byte)(0xE0 | (cp >> 12)); b[1] = (byte)(0x80 | ((cp >> 6) & 0x3F)); b[2] = (byte)(0x80 | (cp & 0x3F));
            Len += 3;
        }
        else
        {
            b[0] = (byte)(0xF0 | (cp >> 18)); b[1] = (byte)(0x80 | ((cp >> 12) & 0x3F));
            b[2] = (byte)(0x80 | ((cp >> 6) & 0x3F)); b[3] = (byte)(0x80 | (cp & 0x3F));
            Len += 4;
        }
    }
}

unsafe struct Str
{
    public byte* P;
    public int N;
}

sealed class Table
{
    public int[] Index = new int[1 << 12];
    public int Mask = (1 << 12) - 1;
    public int N;
    public uint[] Hashes = new uint[1024];
    public int[] KeyOff = new int[1024];
    public int[] KeyLen = new int[1024];
    public long[] Sums = new long[1024];
    public long[] Counts = new long[1024];
    public byte[] Arena = new byte[1 << 14];
    public int ArenaLen;

    public Table() { Array.Fill(Index, -1); }

    public unsafe void Add(Str k, long v)
    {
        uint hash = 2166136261u;
        for (int i = 0; i < k.N; i++) hash = (hash ^ k.P[i]) * 16777619u;
        hash ^= hash >> 15;
        int h = (int)(hash & (uint)Mask);
        var key = new ReadOnlySpan<byte>(k.P, k.N);
        for (; ; )
        {
            int ix = Index[h];
            if (ix < 0) break;
            if (Hashes[ix] == hash && KeyLen[ix] == k.N && key.SequenceEqual(new ReadOnlySpan<byte>(Arena, KeyOff[ix], k.N)))
            {
                Sums[ix] += v;
                Counts[ix]++;
                return;
            }
            h = (h + 1) & Mask;
        }
        if (N == Hashes.Length)
        {
            int c = N * 2;
            Array.Resize(ref Hashes, c);
            Array.Resize(ref KeyOff, c);
            Array.Resize(ref KeyLen, c);
            Array.Resize(ref Sums, c);
            Array.Resize(ref Counts, c);
        }
        if (ArenaLen + k.N > Arena.Length) Array.Resize(ref Arena, Math.Max(Arena.Length * 2, ArenaLen + k.N));
        key.CopyTo(new Span<byte>(Arena, ArenaLen, k.N));
        int id = N++;
        Hashes[id] = hash;
        KeyOff[id] = ArenaLen;
        KeyLen[id] = k.N;
        ArenaLen += k.N;
        Sums[id] = v;
        Counts[id] = 1;
        Index[h] = id;
        if (N * 2 > Index.Length) Grow();
    }

    void Grow()
    {
        int cap = Index.Length * 2;
        Index = new int[cap];
        Array.Fill(Index, -1);
        Mask = cap - 1;
        for (int i = 0; i < N; i++)
        {
            int h = (int)(Hashes[i] & (uint)Mask);
            while (Index[h] >= 0) h = (h + 1) & Mask;
            Index[h] = i;
        }
    }

    public string Key(int i) => Encoding.Latin1.GetString(Arena, KeyOff[i], KeyLen[i]);
}

static unsafe class Parser
{
    static byte* p;
    static readonly Scratch sT = new(), sA = new(), sC = new();
    public static readonly Table Accounts = new(), Channels = new();
    public static long TotalCount, TotalNet;
    static byte[][] rateKeys = Array.Empty<byte[]>();
    static long[] rateVals = Array.Empty<long>();
    static bool ratesDone;

    static uint Hex4(byte* q)
    {
        uint v = 0;
        for (int i = 0; i < 4; i++)
        {
            uint c = q[i];
            v <<= 4;
            if (c >= '0' && c <= '9') v |= c - '0';
            else if (c >= 'a' && c <= 'f') v |= c - 'a' + 10;
            else v |= c - 'A' + 10;
        }
        return v;
    }

    static Str ParseStr(Scratch buf)
    {
        byte* q = p + 1;
        byte* s = q;
        for (; ; )
        {
            byte c = *q;
            if (c == (byte)'"')
            {
                p = q + 1;
                return new Str { P = s, N = (int)(q - s) };
            }
            if (c == (byte)'\\') break;
            q++;
        }
        return ParseStrSlow(buf, s, q);
    }

    static Str ParseStrSlow(Scratch buf, byte* s, byte* q)
    {
        buf.Len = 0;
        buf.Reserve((int)(q - s));
        Buffer.MemoryCopy(s, buf.Ptr, buf.Cap, (long)(q - s));
        buf.Len = (int)(q - s);
        for (; ; )
        {
            byte c = *q;
            if (c == (byte)'"') { q++; break; }
            if (c == (byte)'\\')
            {
                byte e = q[1];
                q += 2;
                switch (e)
                {
                    case (byte)'n': buf.Push(10); break;
                    case (byte)'t': buf.Push(9); break;
                    case (byte)'r': buf.Push(13); break;
                    case (byte)'b': buf.Push(8); break;
                    case (byte)'f': buf.Push(12); break;
                    case (byte)'u':
                        {
                            uint cp = Hex4(q);
                            q += 4;
                            if (cp >= 0xD800 && cp < 0xDC00 && q[0] == (byte)'\\' && q[1] == (byte)'u')
                            {
                                uint lo = Hex4(q + 2);
                                if (lo >= 0xDC00 && lo < 0xE000)
                                {
                                    cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                    q += 6;
                                }
                            }
                            buf.PushUtf8(cp);
                            break;
                        }
                    default: buf.Push(e); break;
                }
            }
            else
            {
                buf.Push(c);
                q++;
            }
        }
        p = q;
        return new Str { P = buf.Ptr, N = buf.Len };
    }

    static void SkipWs()
    {
        byte* q = p;
        while (*q == ' ' || *q == '\n' || *q == '\t' || *q == '\r') q++;
        p = q;
    }

    static byte* SkipString(byte* q)
    {
        q++;
        for (; ; )
        {
            byte c = *q;
            if (c == (byte)'"') break;
            if (c == (byte)'\\') q++;
            q++;
        }
        return q + 1;
    }

    static void SkipValue()
    {
        byte* q = p;
        byte c = *q;
        if (c == (byte)'"') { p = SkipString(q); return; }
        if (c == (byte)'{' || c == (byte)'[')
        {
            int depth = 0;
            for (; ; )
            {
                c = *q;
                if (c == (byte)'"') { q = SkipString(q); continue; }
                q++;
                if (c == (byte)'{' || c == (byte)'[') depth++;
                else if (c == (byte)'}' || c == (byte)']') { if (--depth == 0) break; }
            }
            p = q;
            return;
        }
        while (c != ',' && c != '}' && c != ']' && c != ' ' && c != '\n' && c != '\r' && c != '\t') c = *++q;
        p = q;
    }

    static bool Eq(Str s, string lit)
    {
        if (s.N != lit.Length) return false;
        for (int i = 0; i < s.N; i++) if (s.P[i] != lit[i]) return false;
        return true;
    }

    static long ParseInt()
    {
        long v = 0;
        byte* q = p;
        while (*q >= '0' && *q <= '9') v = v * 10 + (*q++ - '0');
        p = q;
        return v;
    }

    static void ParseRates()
    {
        p++;
        for (; ; )
        {
            SkipWs();
            Str k = ParseStr(sT);
            bool isRates = Eq(k, "rates");
            SkipWs(); p++; SkipWs();
            if (isRates)
            {
                p++;
                var keys = new List<byte[]>();
                var vals = new List<long>();
                for (; ; )
                {
                    SkipWs();
                    if (*p == '}') { p++; break; }
                    Str c = ParseStr(sT);
                    keys.Add(new ReadOnlySpan<byte>(c.P, c.N).ToArray());
                    SkipWs(); p++; SkipWs();
                    vals.Add(ParseInt());
                    SkipWs();
                    if (*p == ',') p++;
                }
                rateKeys = keys.ToArray();
                rateVals = vals.ToArray();
            }
            else SkipValue();
            SkipWs();
            if (*p == ',') { p++; continue; }
            p++;
            break;
        }
    }

    static void ParseTx()
    {
        p++;
        Str acc = default, chan = default;
        int type = 0;
        long hund = 0, rate = 0;
        bool test = false;
        for (; ; )
        {
            SkipWs();
            if (*p == '}') { p++; break; }
            Str k = ParseStr(sT);
            SkipWs(); p++; SkipWs();
            int kind = 0;
            byte* kp = k.P;
            switch (k.N)
            {
                case 4:
                    if (kp[0] == 't' && kp[1] == 'y' && kp[2] == 'p' && kp[3] == 'e') kind = 2;
                    else if (kp[0] == 't' && kp[1] == 'a' && kp[2] == 'g' && kp[3] == 's') kind = 5;
                    else if (kp[0] == 'm' && kp[1] == 'e' && kp[2] == 't' && kp[3] == 'a') kind = 6;
                    break;
                case 6: if (Eq(k, "amount")) kind = 3; break;
                case 7: if (Eq(k, "account")) kind = 1; break;
                case 8: if (Eq(k, "currency")) kind = 4; break;
            }
            switch (kind)
            {
                case 1:
                    acc = ParseStr(sA);
                    break;
                case 2:
                    {
                        Str t = ParseStr(sT);
                        type = t.N > 0 ? t.P[0] : 0;
                        break;
                    }
                case 3:
                    {
                        Str a = ParseStr(sT);
                        byte* q = a.P;
                        byte* e = q + a.N;
                        long ip = 0;
                        while (q < e && *q != '.') ip = ip * 10 + (*q++ - '0');
                        long fr = 0;
                        if (q < e)
                        {
                            q++;
                            if (q < e)
                            {
                                fr = (*q++ - '0') * 10;
                                if (q < e) fr += *q - '0';
                            }
                        }
                        hund = ip * 100 + fr;
                        break;
                    }
                case 4:
                    {
                        Str c = ParseStr(sT);
                        var cs = new ReadOnlySpan<byte>(c.P, c.N);
                        for (int i = 0; i < rateKeys.Length; i++)
                        {
                            if (cs.SequenceEqual(rateKeys[i])) { rate = rateVals[i]; break; }
                        }
                        break;
                    }
                case 5:
                    {
                        p++;
                        SkipWs();
                        if (*p == ']') { p++; break; }
                        for (; ; )
                        {
                            SkipWs();
                            Str s = ParseStr(sT);
                            if (s.N == 4 && s.P[0] == 't' && s.P[1] == 'e' && s.P[2] == 's' && s.P[3] == 't') test = true;
                            SkipWs();
                            if (*p == ',') { p++; continue; }
                            p++;
                            break;
                        }
                        break;
                    }
                case 6:
                    {
                        p++;
                        for (; ; )
                        {
                            SkipWs();
                            if (*p == '}') { p++; break; }
                            Str mk = ParseStr(sT);
                            bool isChannel = Eq(mk, "channel");
                            SkipWs(); p++; SkipWs();
                            if (isChannel && *p == '"') chan = ParseStr(sC);
                            else SkipValue();
                            SkipWs();
                            if (*p == ',') { p++; continue; }
                            p++;
                            break;
                        }
                        break;
                    }
                default:
                    SkipValue();
                    break;
            }
            SkipWs();
            if (*p == ',') { p++; continue; }
            p++;
            break;
        }
        if (type == 'v' || test) return;
        long usd = hund * rate / 1000000L;
        long v = type == 'd' ? -usd : usd;
        TotalCount++;
        TotalNet += v;
        Accounts.Add(acc, v);
        Channels.Add(chan, v);
    }

    public static void Process(byte* start, byte* end)
    {
        p = start;
        for (; ; )
        {
            SkipWs();
            if (p >= end) break;
            if (!ratesDone) { ParseRates(); ratesDone = true; }
            else ParseTx();
        }
    }
}

static unsafe class Program
{
    static bool AccBefore(int a, int b)
    {
        var t = Parser.Accounts;
        if (t.Sums[a] != t.Sums[b]) return t.Sums[a] > t.Sums[b];
        return new ReadOnlySpan<byte>(t.Arena, t.KeyOff[a], t.KeyLen[a])
            .SequenceCompareTo(new ReadOnlySpan<byte>(t.Arena, t.KeyOff[b], t.KeyLen[b])) < 0;
    }

    static void Main(string[] args)
    {
        long cap = 1 << 22;
        byte* buf = (byte*)NativeMemory.Alloc((nuint)(cap + 16));
        long have = 0;
        bool eof = false;
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.SequentialScan))
        {
            while (!eof)
            {
                int n = fs.Read(new Span<byte>(buf + have, (int)(cap - have)));
                if (n <= 0) eof = true;
                else have += n;
                long end;
                if (eof)
                {
                    if (have > 0 && buf[have - 1] != '\n') buf[have++] = (byte)'\n';
                    end = have;
                    buf[end] = 0;
                }
                else
                {
                    long i = have;
                    while (i > 0 && buf[i - 1] != '\n') i--;
                    if (i == 0)
                    {
                        if (have == cap)
                        {
                            cap *= 2;
                            buf = (byte*)NativeMemory.Realloc(buf, (nuint)(cap + 16));
                        }
                        continue;
                    }
                    end = i;
                }
                Parser.Process(buf, buf + end);
                if (!eof)
                {
                    Buffer.MemoryCopy(buf + end, buf, cap, have - end);
                    have -= end;
                }
            }
        }

        var sb = new StringBuilder();
        sb.Append("counted ").Append(Parser.TotalCount).Append('\n');
        sb.Append("net ").Append(Parser.TotalNet).Append('\n');
        var ch = Parser.Channels;
        var order = new List<int>();
        for (int i = 0; i < ch.N; i++) order.Add(i);
        order.Sort((a, b) => string.CompareOrdinal(ch.Key(a), ch.Key(b)));
        foreach (int i in order)
            sb.Append("channel ").Append(ch.Key(i)).Append(' ').Append(ch.Counts[i]).Append(' ').Append(ch.Sums[i]).Append('\n');
        var ac = Parser.Accounts;
        int[] top = new int[Math.Min(10, ac.N)];
        int tn = 0;
        for (int i = 0; i < ac.N; i++)
        {
            if (tn == top.Length && !AccBefore(i, top[tn - 1])) continue;
            int j = tn < top.Length ? tn++ : tn - 1;
            while (j > 0 && AccBefore(i, top[j - 1])) { top[j] = top[j - 1]; j--; }
            top[j] = i;
        }
        for (int i = 0; i < tn; i++)
            sb.Append("account ").Append(ac.Key(top[i])).Append(' ').Append(ac.Sums[top[i]]).Append('\n');
        using var stdout = Console.OpenStandardOutput();
        var bytes = Encoding.Latin1.GetBytes(sb.ToString());
        stdout.Write(bytes, 0, bytes.Length);
        stdout.Flush();
    }
}
