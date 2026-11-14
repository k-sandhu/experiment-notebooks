using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Text;

internal struct Entry
{
    public ulong Hash;
    public long Sum;
    public long Count;
    public int KeyOff;
    public int KeyLen;
}

internal sealed unsafe class Table
{
    public Entry[] Entries = new Entry[64];
    public byte[] Arena = new byte[1024];
    public int Count;
    private int arenaPos;
    private int[] slots = new int[128];
    private int mask = 127;

    private const ulong K1 = 0x9E3779B97F4A7C15UL;
    private const ulong K2 = 0xD6E8FEB86659FD93UL;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ulong Mum(ulong a, ulong b)
    {
        ulong hi = Math.BigMul(a, b, out ulong lo);
        return hi ^ lo;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ulong Hash(byte* p, int len)
    {
        if (len <= 8)
        {
            ulong a = Unsafe.ReadUnaligned<ulong>(p);
            if (len < 8) a &= (1UL << (len << 3)) - 1;
            return Mum(a ^ K1, (ulong)len ^ K2);
        }
        return HashLong(p, len);
    }

    [MethodImpl(MethodImplOptions.NoInlining | MethodImplOptions.AggressiveOptimization)]
    private static ulong HashLong(byte* p, int len)
    {
        ulong h = (ulong)len * K2;
        int i = 0;
        for (; i + 8 < len; i += 8) h = Mum(h ^ Unsafe.ReadUnaligned<ulong>(p + i), K1);
        h = Mum(h ^ Unsafe.ReadUnaligned<ulong>(p + len - 8), K1);
        return h;
    }

    public ReadOnlySpan<byte> Key(int idx)
    {
        return new ReadOnlySpan<byte>(Arena, Entries[idx].KeyOff, Entries[idx].KeyLen);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public int GetOrAdd(byte* k, int len)
    {
        ulong h = Hash(k, len);
        int[] sl = slots;
        Entry[] es = Entries;
        int m = mask;
        int i = (int)h & m;
        while (true)
        {
            int idx = sl[i];
            if (idx == 0) return Insert(k, len, h);
            ref Entry e = ref es[idx - 1];
            if (e.Hash == h && e.KeyLen == len &&
                new ReadOnlySpan<byte>(k, len).SequenceEqual(new ReadOnlySpan<byte>(Arena, e.KeyOff, len)))
                return idx - 1;
            i = (i + 1) & m;
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public int Find(byte* k, int len)
    {
        ulong h = Hash(k, len);
        int[] sl = slots;
        Entry[] es = Entries;
        int m = mask;
        int i = (int)h & m;
        while (true)
        {
            int idx = sl[i];
            if (idx == 0) return -1;
            ref Entry e = ref es[idx - 1];
            if (e.Hash == h && e.KeyLen == len &&
                new ReadOnlySpan<byte>(k, len).SequenceEqual(new ReadOnlySpan<byte>(Arena, e.KeyOff, len)))
                return idx - 1;
            i = (i + 1) & m;
        }
    }

    [MethodImpl(MethodImplOptions.NoInlining | MethodImplOptions.AggressiveOptimization)]
    private int Insert(byte* k, int len, ulong h)
    {
        if (Count == Entries.Length) Array.Resize(ref Entries, Count * 2);
        if (arenaPos + len > Arena.Length) Array.Resize(ref Arena, Math.Max(Arena.Length * 2, arenaPos + len));
        new ReadOnlySpan<byte>(k, len).CopyTo(new Span<byte>(Arena, arenaPos, len));
        int idx = Count++;
        ref Entry e = ref Entries[idx];
        e.Hash = h;
        e.Sum = 0;
        e.Count = 0;
        e.KeyOff = arenaPos;
        e.KeyLen = len;
        arenaPos += len;
        if (Count * 2 > slots.Length)
        {
            Rehash();
        }
        else
        {
            int i = (int)h & mask;
            while (slots[i] != 0) i = (i + 1) & mask;
            slots[i] = idx + 1;
        }
        return idx;
    }

    private void Rehash()
    {
        int size = slots.Length * 2;
        int[] ns = new int[size];
        int m = size - 1;
        for (int j = 0; j < Count; j++)
        {
            int i = (int)Entries[j].Hash & m;
            while (ns[i] != 0) i = (i + 1) & m;
            ns[i] = j + 1;
        }
        slots = ns;
        mask = m;
    }
}

internal static unsafe class Program
{
    private const int PAD = 64;

    private const uint K_TYPE = (uint)'t' | ((uint)'y' << 8) | ((uint)'p' << 16) | ((uint)'e' << 24);
    private const uint K_TAGS = (uint)'t' | ((uint)'a' << 8) | ((uint)'g' << 16) | ((uint)'s' << 24);
    private const uint K_META = (uint)'m' | ((uint)'e' << 8) | ((uint)'t' << 16) | ((uint)'a' << 24);
    private const uint K_TEST = (uint)'t' | ((uint)'e' << 8) | ((uint)'s' << 16) | ((uint)'t' << 24);
    private const uint K_AMOU = (uint)'a' | ((uint)'m' << 8) | ((uint)'o' << 16) | ((uint)'u' << 24);
    private const ushort K_NT = (ushort)('n' | ('t' << 8));
    private const uint K_ACCO = (uint)'a' | ((uint)'c' << 8) | ((uint)'c' << 16) | ((uint)'o' << 24);
    private const uint K_OUNT = (uint)'o' | ((uint)'u' << 8) | ((uint)'n' << 16) | ((uint)'t' << 24);
    private const ulong K_CURRENCY = (ulong)'c' | ((ulong)'u' << 8) | ((ulong)'r' << 16) | ((ulong)'r' << 24)
                                     | ((ulong)'e' << 32) | ((ulong)'n' << 40) | ((ulong)'c' << 48) | ((ulong)'y' << 56);
    private const uint K_CHAN = (uint)'c' | ((uint)'h' << 8) | ((uint)'a' << 16) | ((uint)'n' << 24);
    private const uint K_NNEL = (uint)'n' | ((uint)'n' << 8) | ((uint)'e' << 16) | ((uint)'l' << 24);
    private const uint K_CRED = (uint)'c' | ((uint)'r' << 8) | ((uint)'e' << 16) | ((uint)'d' << 24);
    private const ushort K_IT = (ushort)('i' | ('t' << 8));
    private const uint K_REFU = (uint)'r' | ((uint)'e' << 8) | ((uint)'f' << 16) | ((uint)'u' << 24);
    private const ushort K_ND = (ushort)('n' | ('d' << 8));
    private const uint K_DEBI = (uint)'d' | ((uint)'e' << 8) | ((uint)'b' << 16) | ((uint)'i' << 24);
    private const uint K_RATE = (uint)'r' | ((uint)'a' << 8) | ((uint)'t' << 16) | ((uint)'e' << 24);

    private static byte* scratch;
    private static int scratchPos;
    private static byte* slowS;
    private static int slowLen;
    private static long counted;
    private static long net;
    private static Table rates;
    private static Table channels;
    private static Table accounts;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static uint Read32(byte* p) => Unsafe.ReadUnaligned<uint>(p);

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ushort Read16(byte* p) => Unsafe.ReadUnaligned<ushort>(p);

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static ulong Read64(byte* p) => Unsafe.ReadUnaligned<ulong>(p);

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static byte* Ws(byte* p)
    {
        while (*p <= 32 && *p != (byte)'\n') p++;
        return p;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static byte* FindQuoteOrBackslash(byte* p)
    {
        if (Vector256.IsHardwareAccelerated)
        {
            Vector256<byte> q = Vector256.Create((byte)'"');
            Vector256<byte> b = Vector256.Create((byte)'\\');
            while (true)
            {
                Vector256<byte> v = Vector256.Load(p);
                uint m = (Vector256.Equals(v, q) | Vector256.Equals(v, b)).ExtractMostSignificantBits();
                if (m != 0) return p + BitOperations.TrailingZeroCount(m);
                p += 32;
            }
        }
        else if (Vector128.IsHardwareAccelerated)
        {
            Vector128<byte> q = Vector128.Create((byte)'"');
            Vector128<byte> b = Vector128.Create((byte)'\\');
            while (true)
            {
                Vector128<byte> v = Vector128.Load(p);
                uint m = (Vector128.Equals(v, q) | Vector128.Equals(v, b)).ExtractMostSignificantBits();
                if (m != 0) return p + BitOperations.TrailingZeroCount(m);
                p += 16;
            }
        }
        else
        {
            while (*p != (byte)'"' && *p != (byte)'\\') p++;
            return p;
        }
    }

    // p points just after the opening quote; returns pointer just after the closing quote.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static byte* ReadString(byte* p, out byte* s, out int len)
    {
        byte* e = FindQuoteOrBackslash(p);
        if (*e == (byte)'"')
        {
            s = p;
            len = (int)(e - p);
            return e + 1;
        }
        byte* r = ReadStringSlow(p, e);
        s = slowS;
        len = slowLen;
        return r;
    }

    private static int Hex4(byte* p)
    {
        int v = 0;
        for (int i = 0; i < 4; i++)
        {
            int c = p[i];
            int d;
            if (c >= '0' && c <= '9') d = c - '0';
            else
            {
                c |= 0x20;
                d = (c >= 'a' && c <= 'f') ? c - 'a' + 10 : 0;
            }
            v = (v << 4) | d;
        }
        return v;
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    private static byte* ReadStringSlow(byte* p, byte* e)
    {
        byte* d0 = scratch + scratchPos;
        byte* d = d0;
        while (true)
        {
            long n = e - p;
            if (n > 0)
            {
                Buffer.MemoryCopy(p, d, n, n);
                d += n;
            }
            if (*e == (byte)'"') break;
            byte c = e[1];
            p = e + 2;
            switch (c)
            {
                case (byte)'n': *d++ = (byte)'\n'; break;
                case (byte)'t': *d++ = (byte)'\t'; break;
                case (byte)'r': *d++ = (byte)'\r'; break;
                case (byte)'b': *d++ = 8; break;
                case (byte)'f': *d++ = 12; break;
                case (byte)'u':
                {
                    int cp = Hex4(p);
                    p += 4;
                    if (cp >= 0xD800 && cp <= 0xDBFF && p[0] == (byte)'\\' && p[1] == (byte)'u')
                    {
                        int lo = Hex4(p + 2);
                        if (lo >= 0xDC00 && lo <= 0xDFFF)
                        {
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                            p += 6;
                        }
                    }
                    if (cp < 0x80)
                    {
                        *d++ = (byte)cp;
                    }
                    else if (cp < 0x800)
                    {
                        *d++ = (byte)(0xC0 | (cp >> 6));
                        *d++ = (byte)(0x80 | (cp & 0x3F));
                    }
                    else if (cp < 0x10000)
                    {
                        *d++ = (byte)(0xE0 | (cp >> 12));
                        *d++ = (byte)(0x80 | ((cp >> 6) & 0x3F));
                        *d++ = (byte)(0x80 | (cp & 0x3F));
                    }
                    else
                    {
                        *d++ = (byte)(0xF0 | (cp >> 18));
                        *d++ = (byte)(0x80 | ((cp >> 12) & 0x3F));
                        *d++ = (byte)(0x80 | ((cp >> 6) & 0x3F));
                        *d++ = (byte)(0x80 | (cp & 0x3F));
                    }
                    break;
                }
                default: *d++ = c; break;
            }
            e = FindQuoteOrBackslash(p);
        }
        int len = (int)(d - d0);
        slowS = d0;
        slowLen = len;
        scratchPos += len;
        return e + 1;
    }

    // p points just after the opening quote; returns pointer just after the closing quote.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static byte* SkipString(byte* p)
    {
        while (true)
        {
            p = FindQuoteOrBackslash(p);
            if (*p == (byte)'"') return p + 1;
            p += 2;
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static byte* SkipScalar(byte* p)
    {
        byte c = *p;
        while (!(c == (byte)',' || c == (byte)'}' || c == (byte)']' || c <= 32)) c = *++p;
        return p;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static byte* SkipValue(byte* p)
    {
        byte c = *p;
        if (c == (byte)'"') return SkipString(p + 1);
        if ((c | 0x20) == 0x7B)
        {
            int depth = 1;
            p++;
            while (true)
            {
                c = *p++;
                if (c == (byte)'"') p = SkipString(p);
                else if ((c | 0x20) == 0x7B) depth++;
                else if ((c | 0x20) == 0x7D)
                {
                    if (--depth == 0) return p;
                }
            }
        }
        return SkipScalar(p);
    }

    private static byte* ProcessRates(byte* p)
    {
        if (p[0] == 0xEF && p[1] == 0xBB && p[2] == 0xBF) p += 3;
        scratchPos = 0;
        byte* s;
        int n;
        p = Ws(p);
        if (*p == (byte)'{')
        {
            p++;
            while (true)
            {
                p = Ws(p);
                byte c = *p;
                if (c == (byte)'"')
                {
                    p = ReadString(p + 1, out s, out n);
                    p = Ws(p);
                    if (*p == (byte)':') p++;
                    p = Ws(p);
                    if (n == 5 && Read32(s) == K_RATE && s[4] == (byte)'s' && *p == (byte)'{')
                    {
                        p++;
                        while (true)
                        {
                            p = Ws(p);
                            c = *p;
                            if (c == (byte)'"')
                            {
                                p = ReadString(p + 1, out s, out n);
                                p = Ws(p);
                                if (*p == (byte)':') p++;
                                p = Ws(p);
                                c = *p;
                                if (c == (byte)'-' || (uint)(c - '0') <= 9)
                                {
                                    bool neg = false;
                                    if (c == (byte)'-') { neg = true; p++; }
                                    long v = 0;
                                    while ((uint)(*p - '0') <= 9)
                                    {
                                        v = v * 10 + (*p - '0');
                                        p++;
                                    }
                                    p = SkipScalar(p);
                                    int idx = rates.GetOrAdd(s, n);
                                    rates.Entries[idx].Sum = neg ? -v : v;
                                }
                                else
                                {
                                    p = SkipValue(p);
                                }
                            }
                            else if (c == (byte)',') p++;
                            else
                            {
                                if (c == (byte)'}') p++;
                                break;
                            }
                        }
                    }
                    else
                    {
                        p = SkipValue(p);
                    }
                }
                else if (c == (byte)',') p++;
                else
                {
                    if (c == (byte)'}') p++;
                    break;
                }
            }
        }
        while (*p != (byte)'\n') p++;
        return p + 1;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static byte* ProcessLine(byte* p)
    {
        p = Ws(p);
        if (*p != (byte)'{')
        {
            while (*p != (byte)'\n') p++;
            return p + 1;
        }
        p++;
        scratchPos = 0;

        int kind = 0;
        bool test = false;
        long hundredths = 0, rate = 0;
        byte* acc = p; int accLen = 0;
        byte* ch = p; int chLen = 0;
        byte* k; int klen;
        byte* s; int n;

        while (true)
        {
            p = Ws(p);
            byte c = *p;
            if (c == (byte)'"')
            {
                p = ReadString(p + 1, out k, out klen);
                p = Ws(p);
                if (*p == (byte)':') p++;
                p = Ws(p);
                c = *p;
                switch (klen)
                {
                    case 4:
                    {
                        uint w = Read32(k);
                        if (w == K_TYPE)
                        {
                            if (c == (byte)'"')
                            {
                                p = ReadString(p + 1, out s, out n);
                                int kd = 0;
                                if (n == 6)
                                {
                                    uint a = Read32(s);
                                    ushort b = Read16(s + 4);
                                    if ((a == K_CRED && b == K_IT) || (a == K_REFU && b == K_ND)) kd = 1;
                                }
                                else if (n == 5)
                                {
                                    if (Read32(s) == K_DEBI && s[4] == (byte)'t') kd = 2;
                                }
                                kind = kd;
                                continue;
                            }
                        }
                        else if (w == K_TAGS)
                        {
                            if (c == (byte)'[')
                            {
                                p++;
                                test = false;
                                while (true)
                                {
                                    p = Ws(p);
                                    c = *p;
                                    if (c == (byte)'"')
                                    {
                                        p = ReadString(p + 1, out s, out n);
                                        if (n == 4 && Read32(s) == K_TEST) test = true;
                                    }
                                    else if (c == (byte)',') p++;
                                    else if (c == (byte)']') { p++; break; }
                                    else if (c == (byte)'\n' || c == (byte)'}') break;
                                    else p = SkipValue(p);
                                }
                                continue;
                            }
                        }
                        else if (w == K_META)
                        {
                            if (c == (byte)'{')
                            {
                                p++;
                                while (true)
                                {
                                    p = Ws(p);
                                    c = *p;
                                    if (c == (byte)'"')
                                    {
                                        p = ReadString(p + 1, out s, out n);
                                        p = Ws(p);
                                        if (*p == (byte)':') p++;
                                        p = Ws(p);
                                        if (n == 7 && Read32(s) == K_CHAN && Read32(s + 3) == K_NNEL && *p == (byte)'"')
                                        {
                                            p = ReadString(p + 1, out ch, out chLen);
                                        }
                                        else
                                        {
                                            p = SkipValue(p);
                                        }
                                    }
                                    else if (c == (byte)',') p++;
                                    else
                                    {
                                        if (c == (byte)'}') p++;
                                        break;
                                    }
                                }
                                continue;
                            }
                        }
                        break;
                    }
                    case 6:
                    {
                        if (Read32(k) == K_AMOU && Read16(k + 4) == K_NT && c == (byte)'"')
                        {
                            p = ReadString(p + 1, out s, out n);
                            byte* q = s;
                            byte* qe = s + n;
                            long v = 0;
                            while (q < qe)
                            {
                                uint d = (uint)(*q - '0');
                                if (d > 9) break;
                                v = v * 10 + d;
                                q++;
                            }
                            v *= 100;
                            if (q < qe && *q == (byte)'.')
                            {
                                q++;
                                if (q < qe)
                                {
                                    v += (*q - '0') * 10;
                                    q++;
                                    if (q < qe) v += *q - '0';
                                }
                            }
                            hundredths = v;
                            continue;
                        }
                        break;
                    }
                    case 7:
                    {
                        if (Read32(k) == K_ACCO && Read32(k + 3) == K_OUNT && c == (byte)'"')
                        {
                            p = ReadString(p + 1, out acc, out accLen);
                            continue;
                        }
                        break;
                    }
                    case 8:
                    {
                        if (Read64(k) == K_CURRENCY && c == (byte)'"')
                        {
                            p = ReadString(p + 1, out s, out n);
                            int ri = rates.Find(s, n);
                            rate = ri >= 0 ? rates.Entries[ri].Sum : 0;
                            continue;
                        }
                        break;
                    }
                }
                p = SkipValue(p);
            }
            else if (c == (byte)',')
            {
                p++;
            }
            else
            {
                if (c == (byte)'}') p++;
                break;
            }
        }

        if (kind != 0 && !test)
        {
            long prod = hundredths * rate;
            long usd = prod / 1000000;
            if (prod < 0 && usd * 1000000 != prod) usd--;
            if (kind == 2) usd = -usd;
            counted++;
            net += usd;
            Table ct = channels;
            int ci = ct.GetOrAdd(ch, chLen);
            ref Entry ce = ref ct.Entries[ci];
            ce.Sum += usd;
            ce.Count++;
            Table at = accounts;
            int ai = at.GetOrAdd(acc, accLen);
            ref Entry ae = ref at.Entries[ai];
            ae.Sum += usd;
            ae.Count++;
        }

        while (*p != (byte)'\n') p++;
        return p + 1;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static void Run(string path)
    {
        int cap = 1 << 20;
        byte* buf = (byte*)NativeMemory.Alloc((nuint)(cap + PAD));
        scratch = (byte*)NativeMemory.Alloc((nuint)(cap + PAD));

        using var h = File.OpenHandle(path, FileMode.Open, FileAccess.Read, FileShare.Read, FileOptions.SequentialScan);

        int have = 0;
        long off = 0;
        bool first = true;
        bool eof = false;
        while (true)
        {
            if (have == cap)
            {
                cap *= 2;
                buf = (byte*)NativeMemory.Realloc(buf, (nuint)(cap + PAD));
                scratch = (byte*)NativeMemory.Realloc(scratch, (nuint)(cap + PAD));
            }
            int n = RandomAccess.Read(h, new Span<byte>(buf + have, cap - have), off);
            if (n <= 0)
            {
                if (have == 0) break;
                eof = true;
                if (buf[have - 1] != (byte)'\n') buf[have++] = (byte)'\n';
            }
            else
            {
                off += n;
                have += n;
            }
            int last = new ReadOnlySpan<byte>(buf, have).LastIndexOf((byte)'\n');
            if (last < 0) continue;
            byte* end = buf + last + 1;
            byte* p = buf;
            if (first)
            {
                p = ProcessRates(p);
                first = false;
            }
            while (p < end) p = ProcessLine(p);
            int rem = have - (last + 1);
            if (rem > 0) new Span<byte>(end, rem).CopyTo(new Span<byte>(buf, rem));
            have = rem;
            if (eof) break;
        }

        NativeMemory.Free(buf);
        NativeMemory.Free(scratch);
        scratch = null;
    }

    private static bool Better(Table t, int x, int y)
    {
        long sx = t.Entries[x].Sum, sy = t.Entries[y].Sum;
        if (sx != sy) return sx > sy;
        return t.Key(x).SequenceCompareTo(t.Key(y)) < 0;
    }

    private static int Main(string[] args)
    {
        rates = new Table();
        channels = new Table();
        accounts = new Table();
        counted = 0;
        net = 0;

        Run(args[0]);

        var sb = new StringBuilder(1024);
        sb.Append("counted ").Append(counted).Append('\n');
        sb.Append("net ").Append(net).Append('\n');

        Table ct = channels;
        int cn = ct.Count;
        int[] order = new int[cn];
        for (int i = 0; i < cn; i++) order[i] = i;
        Array.Sort(order, (x, y) => ct.Key(x).SequenceCompareTo(ct.Key(y)));
        for (int i = 0; i < cn; i++)
        {
            int idx = order[i];
            ref Entry e = ref ct.Entries[idx];
            sb.Append("channel ")
              .Append(Encoding.Latin1.GetString(ct.Arena, e.KeyOff, e.KeyLen))
              .Append(' ').Append(e.Count)
              .Append(' ').Append(e.Sum)
              .Append('\n');
        }

        Table at = accounts;
        int an = at.Count;
        int[] best = new int[10];
        int bc = 0;
        for (int i = 0; i < an; i++)
        {
            if (bc == 10 && !Better(at, i, best[9])) continue;
            int j = bc < 10 ? bc++ : 9;
            while (j > 0 && Better(at, i, best[j - 1]))
            {
                best[j] = best[j - 1];
                j--;
            }
            best[j] = i;
        }
        for (int i = 0; i < bc; i++)
        {
            ref Entry e = ref at.Entries[best[i]];
            sb.Append("account ")
              .Append(Encoding.Latin1.GetString(at.Arena, e.KeyOff, e.KeyLen))
              .Append(' ').Append(e.Sum)
              .Append('\n');
        }

        byte[] bytes = Encoding.Latin1.GetBytes(sb.ToString());
        using (Stream o = Console.OpenStandardOutput())
        {
            o.Write(bytes, 0, bytes.Length);
            o.Flush();
        }
        return 0;
    }
}
