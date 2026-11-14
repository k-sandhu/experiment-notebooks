using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Text;

[StructLayout(LayoutKind.Sequential)]
struct Entry
{
    public ulong K0;
    public ulong K1;
    public int Id;
    public int Len;
}

static unsafe class Program
{
    const ulong C1 = 0x9E3779B97F4A7C15UL;
    const ulong C2 = 0xC2B2AE3D27D4EB4FUL;

    static Entry* tab;
    static int capBits;
    static int cap;
    static int limit;
    static int count;

    static byte* pool;
    static long poolLen;
    static long poolCap;

    static long[] wordOff;
    static int[] wordLen;
    static int* firstCnt;
    static int regCap;

    static int[] topC;
    static int[] topF;
    static int[] topS;
    static int topN;

    static int Main(string[] args)
    {
        Run(args[0]);
        return 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static uint Slot(ulong x, int shift)
    {
        return (uint)(((x ^ (x >> 32)) * C1) >> shift);
    }

    static void EnsurePool(long need)
    {
        if (poolLen + need + 32 > poolCap)
        {
            long nc = poolCap * 2;
            if (nc < poolLen + need + 32) nc = poolLen + need + 32;
            pool = (byte*)NativeMemory.Realloc(pool, (nuint)nc);
            poolCap = nc;
        }
    }

    static void Grow()
    {
        int oldCap = cap;
        Entry* old = tab;
        capBits++;
        cap <<= 1;
        limit = cap - (cap >> 2) - (cap >> 4);
        tab = (Entry*)NativeMemory.AllocZeroed((nuint)cap, (nuint)sizeof(Entry));
        int shift = 64 - capBits;
        uint mask = (uint)cap - 1;
        for (int i = 0; i < oldCap; i++)
        {
            Entry* o = old + i;
            if (o->Len == 0) continue;
            ulong x = o->Len <= 15 ? (o->K0 ^ (o->K1 * C2)) : o->K0;
            uint idx = Slot(x, shift);
            while (tab[idx].Len != 0) idx = (idx + 1) & mask;
            tab[idx] = *o;
        }
        NativeMemory.Free(old);
    }

    static void GrowReg()
    {
        int nc = regCap * 2;
        Array.Resize(ref wordOff, nc);
        Array.Resize(ref wordLen, nc);
        firstCnt = (int*)NativeMemory.Realloc(firstCnt, (nuint)nc * 4);
        new Span<int>(firstCnt + regCap, nc - regCap).Clear();
        regCap = nc;
    }

    static int AddEntry(ulong k0, ulong k1, int len, ulong x, long off)
    {
        if (count >= limit) Grow();
        int id = count;
        if (id >= regCap) GrowReg();
        wordOff[id] = off;
        wordLen[id] = len;
        uint mask = (uint)cap - 1;
        uint idx = Slot(x, 64 - capBits);
        Entry* e = tab + idx;
        while (e->Len != 0)
        {
            idx = (idx + 1) & mask;
            e = tab + idx;
        }
        e->K0 = k0;
        e->K1 = k1;
        e->Len = len;
        e->Id = id;
        count = id + 1;
        return id;
    }

    static int InsertShort(ulong k0, ulong k1, int wl)
    {
        EnsurePool(16);
        long off = poolLen;
        *(ulong*)(pool + off) = k0;
        *(ulong*)(pool + off + 8) = k1;
        poolLen += wl;
        return AddEntry(k0, k1, wl, k0 ^ (k1 * C2), off);
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static int LookupLong(byte* p, int wl)
    {
        ulong h = 0xCBF29CE484222325UL;
        for (int i = 0; i < wl; i++) h = (h ^ (uint)(p[i] | 0x20)) * 0x100000001B3UL;
        uint mask = (uint)cap - 1;
        uint idx = Slot(h, 64 - capBits);
        Entry* e = tab + idx;
        while (true)
        {
            int el = e->Len;
            if (el == 0) break;
            if (el == wl && e->K0 == h)
            {
                byte* w = pool + (long)e->K1;
                int i = 0;
                while (i < wl && w[i] == (p[i] | 0x20)) i++;
                if (i == wl) return e->Id;
            }
            idx = (idx + 1) & mask;
            e = tab + idx;
        }
        EnsurePool(wl);
        long off = poolLen;
        byte* dst = pool + off;
        for (int i = 0; i < wl; i++) dst[i] = (byte)(p[i] | 0x20);
        poolLen += wl;
        return AddEntry(h, (ulong)off, wl, h, off);
    }

    static int CmpWord(int a, int b)
    {
        return new ReadOnlySpan<byte>(pool + wordOff[a], wordLen[a])
            .SequenceCompareTo(new ReadOnlySpan<byte>(pool + wordOff[b], wordLen[b]));
    }

    static bool Better(int c1, int f1, int s1, int c2, int f2, int s2)
    {
        if (c1 != c2) return c1 > c2;
        if (f1 != f2) return CmpWord(f1, f2) < 0;
        return CmpWord(s1, s2) < 0;
    }

    static int Consider(int cc, int f, int s)
    {
        int n = topN;
        if (n == 20)
        {
            if (!Better(cc, f, s, topC[19], topF[19], topS[19])) return topC[19];
            n = 19;
        }
        int i = n;
        while (i > 0 && Better(cc, f, s, topC[i - 1], topF[i - 1], topS[i - 1]))
        {
            topC[i] = topC[i - 1];
            topF[i] = topF[i - 1];
            topS[i] = topS[i - 1];
            i--;
        }
        topC[i] = cc;
        topF[i] = f;
        topS[i] = s;
        topN = n + 1;
        return topN == 20 ? topC[19] : 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void Run(string path)
    {
        long len;
        byte* buf;
        using (var fh = File.OpenHandle(path, FileMode.Open, FileAccess.Read, FileShare.Read, FileOptions.SequentialScan))
        {
            len = RandomAccess.GetLength(fh);
            buf = (byte*)NativeMemory.Alloc((nuint)(len + 64));
            long got = 0;
            while (got < len)
            {
                int want = (int)Math.Min(len - got, 1 << 30);
                int r = RandomAccess.Read(fh, new Span<byte>(buf + got, want), got);
                if (r <= 0) break;
                got += r;
            }
            len = got;
        }
        new Span<byte>(buf + len, 64).Clear();

        byte* cls = stackalloc byte[256];
        for (int i = 0; i < 256; i++) cls[i] = 0;
        for (int i = 'a'; i <= 'z'; i++) { cls[i] = 1; cls[i - 32] = 1; }
        cls['.'] = 0x80;
        cls['!'] = 0x80;
        cls['?'] = 0x80;

        byte* mt = stackalloc byte[32];
        for (int i = 0; i < 16; i++) { mt[i] = 0xFF; mt[16 + i] = 0; }

        // state init
        capBits = 16;
        cap = 1 << capBits;
        limit = cap - (cap >> 2) - (cap >> 4);
        tab = (Entry*)NativeMemory.AllocZeroed((nuint)cap, (nuint)sizeof(Entry));
        count = 0;
        poolCap = 1 << 20;
        pool = (byte*)NativeMemory.Alloc((nuint)poolCap);
        poolLen = 0;
        regCap = 1 << 16;
        wordOff = new long[regCap];
        wordLen = new int[regCap];
        firstCnt = (int*)NativeMemory.AllocZeroed((nuint)regCap, 4);
        topC = new int[20];
        topF = new int[20];
        topS = new int[20];
        topN = 0;

        int* seq = (int*)NativeMemory.Alloc((nuint)(len / 2 + 2) * 4);

        Vector128<byte> v20 = Vector128.Create((byte)0x20);
        Vector128<byte> vA = Vector128.Create((byte)'a');
        Vector128<byte> v25 = Vector128.Create((byte)25);

        byte* p = buf;
        byte* end = buf + len;
        int* sp = seq;
        uint flag = 0x80;
        int prev = 0;
        Entry* t = tab;
        int shift = 64 - capBits;
        uint mask = (uint)cap - 1;
        int* fc = firstCnt;

        while (true)
        {
            while (true)
            {
                if (p >= end) goto Done;
                uint c = cls[*p];
                if (c == 1) break;
                flag |= c;
                p++;
            }

            Vector128<byte> v = Vector128.Load(p) | v20;
            uint m = Vector128.GreaterThan(v - vA, v25).ExtractMostSignificantBits();
            int id;
            if (m != 0)
            {
                int wl = BitOperations.TrailingZeroCount(m);
                Vector128<ulong> kv = (v & Vector128.Load(mt + 16 - wl)).AsUInt64();
                ulong k0 = kv.ToScalar();
                ulong k1 = kv.GetElement(1);
                ulong x = k0 ^ (k1 * C2);
                uint idx = (uint)(((x ^ (x >> 32)) * C1) >> shift);
                Entry* e = t + idx;
                while (true)
                {
                    int el = e->Len;
                    if (el == 0)
                    {
                        id = InsertShort(k0, k1, wl);
                        t = tab;
                        shift = 64 - capBits;
                        mask = (uint)cap - 1;
                        fc = firstCnt;
                        break;
                    }
                    if (e->K0 == k0 && e->K1 == k1 && el == wl)
                    {
                        id = e->Id;
                        break;
                    }
                    idx = (idx + 1) & mask;
                    e = t + idx;
                }
                p += wl;
            }
            else
            {
                byte* q = p + 16;
                while ((uint)((*q | 0x20) - 'a') < 26u) q++;
                int wl = (int)(q - p);
                id = LookupLong(p, wl);
                t = tab;
                shift = 64 - capBits;
                mask = (uint)cap - 1;
                fc = firstCnt;
                p = q;
            }

            fc[prev] += (int)(1 - (flag >> 7));
            prev = id;
            *sp++ = id | (int)(flag << 24);
            flag = 0;
        }
    Done:;

        long W = sp - seq;
        int V = count;
        fc = firstCnt;

        int* pos = (int*)NativeMemory.AllocZeroed((nuint)(V + 1), 4);
        long T = 0;
        for (int v2 = 0; v2 < V; v2++)
        {
            pos[v2] = (int)T;
            T += fc[v2];
        }

        int* second = (int*)NativeMemory.Alloc((nuint)Math.Max(T, 1) * 4);
        if (W > 0)
        {
            int pr = seq[0] & 0x7FFFFFFF;
            for (long i = 1; i < W; i++)
            {
                int s = seq[i];
                if (s >= 0)
                {
                    second[pos[pr]++] = s;
                    pr = s;
                }
                else
                {
                    pr = s & 0x7FFFFFFF;
                }
            }
        }

        int* cnt = (int*)NativeMemory.AllocZeroed((nuint)(V + 1), 4);
        long distinct = 0;
        int minCnt = 0;
        int lo = 0;
        for (int f = 0; f < V; f++)
        {
            int hi = pos[f];
            for (int j = lo; j < hi; j++) cnt[second[j]]++;
            for (int j = lo; j < hi; j++)
            {
                int id2 = second[j];
                int cc = cnt[id2];
                if (cc != 0)
                {
                    cnt[id2] = 0;
                    distinct++;
                    if (cc >= minCnt) minCnt = Consider(cc, f, id2);
                }
            }
            lo = hi;
        }

        var sb = new StringBuilder(2048);
        sb.Append("words ").Append(W).Append('\n');
        sb.Append("pairs ").Append(T).Append('\n');
        sb.Append("distinct ").Append(distinct).Append('\n');
        for (int i = 0; i < topN; i++)
        {
            int f = topF[i];
            int s = topS[i];
            sb.Append(topC[i]).Append(' ');
            sb.Append(Encoding.ASCII.GetString(pool + wordOff[f], wordLen[f])).Append(' ');
            sb.Append(Encoding.ASCII.GetString(pool + wordOff[s], wordLen[s])).Append('\n');
        }
        byte[] ob = Encoding.ASCII.GetBytes(sb.ToString());
        using (Stream o = Console.OpenStandardOutput())
        {
            o.Write(ob, 0, ob.Length);
            o.Flush();
        }
    }
}
