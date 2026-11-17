using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Text;
using Microsoft.Win32.SafeHandles;

sealed class Tmpl
{
    public ulong[] Words;
    public byte[] Key;
    public int Len;
    public int Count;
    public long[] Vals;
}

struct Slot
{
    public ulong Hash;
    public Tmpl T;
}

static unsafe class Program
{
    const int Pad = 64;

    const uint M_GET = (uint)('G' | ('E' << 8) | ('T' << 16) | (' ' << 24));
    const uint M_PUT = (uint)('P' | ('U' << 8) | ('T' << 16) | (' ' << 24));
    const uint M_POST = (uint)('P' | ('O' << 8) | ('S' << 16) | ('T' << 24));
    const uint M_PATC = (uint)('P' | ('A' << 8) | ('T' << 16) | ('C' << 24));
    const uint M_H_SP = (uint)('H' | (' ' << 8));
    const uint M_DELE = (uint)('D' | ('E' << 8) | ('L' << 16) | ('E' << 24));
    const uint M_ETE_SP = (uint)('E' | ('T' << 8) | ('E' << 16) | (' ' << 24));
    const uint ID_WORD = (uint)('{' | ('i' << 8) | ('d' << 16) | ('}' << 24));
    const uint B_SP = (uint)('B' | (' ' << 8));
    const uint MS_SP_QUOTE = (uint)('m' | ('s' << 8) | (' ' << 16) | ('"' << 24));
    const uint QUOTE_NL = (uint)('"' | ('\n' << 8));

    static Slot[] slots = new Slot[1024];
    static int slotShift = 64 - 10;
    static int tmplCount;
    static readonly List<Tmpl> all = new List<Tmpl>();
    static long lines, malformed;
    static long* statusCounts;
    static byte* cls;
    static byte* scratch;
    static int[] hist;

    static int Main(string[] args)
    {
        cls = (byte*)NativeMemory.AllocZeroed(256);
        for (int i = '0'; i <= '9'; i++) cls[i] = 1;
        for (int i = 'a'; i <= 'z'; i++) cls[i] = 2;
        for (int i = 'A'; i <= 'Z'; i++) cls[i] = 2;
        cls['_'] = 2;
        cls['-'] = 2;
        statusCounts = (long*)NativeMemory.AllocZeroed(10 * sizeof(long));

        int cap = 1 << 19;
        byte* buf = (byte*)NativeMemory.Alloc((nuint)((long)cap + Pad));
        scratch = (byte*)NativeMemory.Alloc((nuint)((long)cap * 3 + Pad));

        using (SafeFileHandle h = File.OpenHandle(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, FileOptions.SequentialScan))
        {
            long off = 0;
            int have = 0;
            for (;;)
            {
                if (have == cap)
                {
                    int ncap = cap * 2;
                    buf = (byte*)NativeMemory.Realloc(buf, (nuint)((long)ncap + Pad));
                    NativeMemory.Free(scratch);
                    scratch = (byte*)NativeMemory.Alloc((nuint)((long)ncap * 3 + Pad));
                    cap = ncap;
                }
                int n = RandomAccess.Read(h, new Span<byte>(buf + have, cap - have), off);
                if (n <= 0) break;
                off += n;
                int total = have + n;
                int last = new ReadOnlySpan<byte>(buf + have, n).LastIndexOf((byte)'\n');
                if (last < 0)
                {
                    have = total;
                    continue;
                }
                int endPos = have + last + 1;
                Process(buf, buf + endPos);
                have = total - endPos;
                if (have > 0) Buffer.MemoryCopy(buf + endPos, buf, cap, have);
            }
        }

        var sb = new StringBuilder(1024);
        sb.Append("lines ").Append(lines).Append('\n');
        sb.Append("malformed ").Append(malformed).Append('\n');
        for (int c = 0; c < 10; c++)
        {
            if (statusCounts[c] > 0)
                sb.Append("status ").Append((char)('0' + c)).Append("xx ").Append(statusCounts[c]).Append('\n');
        }

        all.Sort((a, b) =>
        {
            if (a.Count != b.Count) return b.Count.CompareTo(a.Count);
            return a.Key.AsSpan().SequenceCompareTo(b.Key);
        });

        int top = Math.Min(10, all.Count);
        for (int i = 0; i < top; i++)
        {
            Tmpl tm = all[i];
            Stats(tm, out long p50, out long p95, out long max);
            sb.Append("path ").Append(Encoding.ASCII.GetString(tm.Key)).Append(' ').Append(tm.Count).Append(' ');
            sb.Append(p50 / 10).Append('.').Append(p50 % 10).Append(' ');
            sb.Append(p95 / 10).Append('.').Append(p95 % 10).Append(' ');
            sb.Append(max / 10).Append('.').Append(max % 10).Append('\n');
        }

        byte[] outBytes = Encoding.ASCII.GetBytes(sb.ToString());
        using (Stream o = Console.OpenStandardOutput())
        {
            o.Write(outBytes, 0, outBytes.Length);
            o.Flush();
        }
        return 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void Stats(Tmpl tm, out long p50, out long p95, out long max)
    {
        int n = tm.Count;
        long[] vals = tm.Vals;
        long mx = 0;
        for (int i = 0; i < n; i++)
        {
            long v = vals[i];
            if (v > mx) mx = v;
        }
        max = mx;
        long r50 = (50L * n + 99) / 100;
        long r95 = (95L * n + 99) / 100;
        if (mx < (1 << 20))
        {
            int m = (int)mx;
            if (hist == null || hist.Length < m + 1) hist = new int[Math.Max(m + 1, 1 << 16)];
            else Array.Clear(hist, 0, m + 1);
            int[] hs = hist;
            for (int i = 0; i < n; i++) hs[vals[i]]++;
            long cum = hs[0];
            int x = 0;
            while (cum < r50)
            {
                x++;
                cum += hs[x];
            }
            p50 = x;
            while (cum < r95)
            {
                x++;
                cum += hs[x];
            }
            p95 = x;
        }
        else
        {
            Array.Sort(vals, 0, n);
            p50 = vals[r50 - 1];
            p95 = vals[r95 - 1];
        }
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    static long[] Grow(Tmpl tm)
    {
        long[] nv = GC.AllocateUninitializedArray<long>(tm.Vals.Length * 2);
        Array.Copy(tm.Vals, nv, tm.Count);
        tm.Vals = nv;
        return nv;
    }

    static void Place(Slot[] arr, int shift, ulong h, Tmpl t)
    {
        int mask = arr.Length - 1;
        int idx = (int)(h >> shift);
        while (arr[idx].T != null) idx = (idx + 1) & mask;
        arr[idx].Hash = h;
        arr[idx].T = t;
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    static Tmpl Insert(ulong h, int len)
    {
        int nw = (len + 7) >> 3;
        var tm = new Tmpl();
        tm.Len = len;
        tm.Words = new ulong[nw];
        tm.Key = new byte[len];
        tm.Vals = new long[16];
        ulong* w = (ulong*)scratch;
        for (int i = 0; i < nw; i++) tm.Words[i] = w[i];
        new ReadOnlySpan<byte>(scratch, len).CopyTo(tm.Key);

        if ((tmplCount + 1) * 2 > slots.Length)
        {
            Slot[] old = slots;
            Slot[] ns = new Slot[old.Length * 2];
            slotShift--;
            for (int i = 0; i < old.Length; i++)
            {
                if (old[i].T != null) Place(ns, slotShift, old[i].Hash, old[i].T);
            }
            slots = ns;
        }
        Place(slots, slotShift, h, tm);
        tmplCount++;
        all.Add(tm);
        return tm;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static void Process(byte* p, byte* end)
    {
        byte* cls = Program.cls;
        byte* scratch = Program.scratch;
        long* st = statusCounts;
        Slot[] slots = Program.slots;
        int shift = slotShift;
        int mask = slots.Length - 1;
        long nLines = 0, nMal = 0;

        Vector128<byte> zero16 = Vector128.Create((byte)'0');
        Vector128<byte> nine16 = Vector128.Create((byte)9);
        Vector128<byte> loA = Vector128.Create("0000-00-00T00:00"u8);
        Vector128<byte> loB = Vector128.Create("0T00:00:00.000Z "u8);
        Vector128<byte> rA = Vector128.Equals(loA, zero16) & nine16;
        Vector128<byte> rB = Vector128.Equals(loB, zero16) & nine16;
        Vector256<byte> q256 = Vector256.Create((byte)'"');
        Vector256<byte> nl256 = Vector256.Create((byte)'\n');
        Vector128<byte> q128 = Vector128.Create((byte)'"');
        Vector128<byte> nl128 = Vector128.Create((byte)'\n');

        while (p < end)
        {
            nLines++;

            // timestamp + space (25 bytes)
            Vector128<byte> a = Vector128.Load(p) - loA;
            Vector128<byte> b = Vector128.Load(p + 9) - loB;
            if (((Vector128.Min(a, rA) ^ a) | (Vector128.Min(b, rB) ^ b)) != Vector128<byte>.Zero) goto bad;
            p += 25;

            // host: [a-z]+-\d+ and space
            if ((uint)(*p - 'a') > 25) goto bad;
            do p++; while ((uint)(*p - 'a') <= 25);
            if (*p != '-') goto bad;
            p++;
            if ((uint)(*p - '0') > 9) goto bad;
            do p++; while ((uint)(*p - '0') <= 9);
            if (*p != ' ') goto bad;
            p++;

            // method and space
            uint m = *(uint*)p;
            if (m == M_GET || m == M_PUT) p += 4;
            else if (m == M_POST && p[4] == ' ') p += 5;
            else if (m == M_PATC && *(ushort*)(p + 4) == M_H_SP) p += 6;
            else if (m == M_DELE && *(uint*)(p + 3) == M_ETE_SP) p += 7;
            else goto bad;

            // path
            if (*p != '/') goto bad;
            byte* t = scratch;
            uint c;
            for (;;)
            {
                *t++ = (byte)'/';
                p++;
                byte* segStart = t;
                uint acc = 0, k;
                while ((k = cls[c = *p]) != 0)
                {
                    acc |= k;
                    *t++ = (byte)c;
                    p++;
                }
                if (acc == 1)
                {
                    *(uint*)segStart = ID_WORD;
                    t = segStart + 4;
                }
                if (c != '/') break;
            }
            if (c == '?')
            {
                do p++; while (*p != ' ' && *p != '\n');
                if (*p != ' ') goto bad;
            }
            else if (c != ' ') goto bad;
            p++;

            // status
            uint d0 = (uint)(p[0] - '0');
            if (d0 > 9 || (uint)(p[1] - '0') > 9 || (uint)(p[2] - '0') > 9 || p[3] != ' ') goto bad;
            p += 4;

            // size
            if ((uint)(*p - '0') > 9) goto bad;
            do p++; while ((uint)(*p - '0') <= 9);
            if (*(ushort*)p != B_SP) goto bad;
            p += 2;

            // latency
            uint d = (uint)(*p - '0');
            if (d > 9) goto bad;
            long v = d;
            p++;
            while ((d = (uint)(*p - '0')) <= 9)
            {
                v = v * 10 + d;
                p++;
            }
            if (*p != '.') goto bad;
            d = (uint)(p[1] - '0');
            if (d > 9) goto bad;
            if (*(uint*)(p + 2) != MS_SP_QUOTE) goto bad;
            v = v * 10 + d;
            p += 6;

            // user agent: next '"' must be the last byte of the line
            if (Vector256.IsHardwareAccelerated)
            {
                for (;;)
                {
                    Vector256<byte> x = Vector256.Load(p);
                    uint mm = (Vector256.Equals(x, q256) | Vector256.Equals(x, nl256)).ExtractMostSignificantBits();
                    if (mm != 0)
                    {
                        p += BitOperations.TrailingZeroCount(mm);
                        break;
                    }
                    p += 32;
                }
            }
            else
            {
                for (;;)
                {
                    Vector128<byte> x = Vector128.Load(p);
                    uint mm = (Vector128.Equals(x, q128) | Vector128.Equals(x, nl128)).ExtractMostSignificantBits();
                    if (mm != 0)
                    {
                        p += BitOperations.TrailingZeroCount(mm);
                        break;
                    }
                    p += 16;
                }
            }
            if (*(ushort*)p != QUOTE_NL) goto bad;
            p += 2;

            // well-formed: record
            st[d0]++;
            int len = (int)(t - scratch);
            *(ulong*)t = 0;
            ulong* w = (ulong*)scratch;
            int nw = (len + 7) >> 3;
            ulong hsh = (ulong)len;
            for (int i = 0; i < nw; i++)
                hsh = (BitOperations.RotateLeft(hsh, 5) ^ w[i]) * 0x9E3779B97F4A7C15UL;

            int idx = (int)(hsh >> shift);
            Tmpl tm;
            for (;;)
            {
                ref Slot s = ref slots[idx];
                tm = s.T;
                if (tm == null)
                {
                    tm = Insert(hsh, len);
                    slots = Program.slots;
                    shift = slotShift;
                    mask = slots.Length - 1;
                    break;
                }
                if (s.Hash == hsh && tm.Len == len)
                {
                    ulong[] kw = tm.Words;
                    int i = 0;
                    while (i < kw.Length && kw[i] == w[i]) i++;
                    if (i == kw.Length) break;
                }
                idx = (idx + 1) & mask;
            }

            int cnt = tm.Count;
            long[] vals = tm.Vals;
            if (cnt == vals.Length) vals = Grow(tm);
            vals[cnt] = v;
            tm.Count = cnt + 1;
            continue;

        bad:
            nMal++;
            p += new ReadOnlySpan<byte>(p, (int)(end - p)).IndexOf((byte)'\n') + 1;
        }

        lines += nLines;
        malformed += nMal;
    }
}
