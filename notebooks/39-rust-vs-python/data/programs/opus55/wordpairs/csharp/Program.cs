// Word pairs: count adjacent word pairs within sentences, report the top 20.
//
// 1. Scan the input once. Words are found 8 bytes at a time (SWAR) and interned
//    to dense ids by an open-addressing table whose slots hold the first 8 bytes
//    of the word. The scan records the id sequence, with a flag on each word that
//    starts a sentence, and counts pairs per first word.
// 2. Counting-sort the pairs by first word (second words only).
// 3. For each first word, count its second words in a dense counter array that
//    stays in cache, and keep the 20 best pairs. Ties are broken by each word's
//    lexicographic rank, so the selection compares integers only.
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;

unsafe static class Program
{
    const ulong Ones = 0x0101010101010101UL;
    const ulong High = 0x8080808080808080UL;
    const ulong Fold = 0x2020202020202020UL;
    const uint Start = 0x80000000u; // flag: word starts a sentence

    struct Slot
    {
        public ulong Prefix; // first 8 lower-case bytes, zero padded
        public uint Hash;
        public uint Id; // 0 = empty
    }

    struct Top
    {
        public uint Cnt, R1, R2, A, B;
    }

    static Slot[] slots;
    static int bits;
    static uint mask;
    static uint[] wOff = new uint[1 << 16];
    static uint[] wLen = new uint[1 << 16];
    static uint nextId = 1;

    // High bit set in each byte of v (bytes < 0x80) that is an ASCII letter.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static ulong LetterMask(ulong v)
    {
        ulong x = v | Fold;
        ulong geA = x + 0x1FUL * Ones; // >= 0x80 iff x >= 'a'
        ulong gtZ = x + 0x05UL * Ones; // >= 0x80 iff x > 'z'
        return geA & ~gtZ & High;
    }

    // Mask covering the low n bytes.
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static ulong LowBytes(int n) => n >= 8 ? ulong.MaxValue : (1UL << (8 * n)) - 1;

    static void Resize(int b)
    {
        Slot[] old = slots;
        slots = new Slot[1 << b];
        bits = b;
        mask = (1u << b) - 1;
        if (old == null) return;
        foreach (Slot s in old)
        {
            if (s.Id == 0) continue;
            uint i = s.Hash >> (32 - b);
            while (slots[i].Id != 0) i = (i + 1) & mask;
            slots[i] = s;
        }
    }

    // Bytes 8..n of a (lower case) and b (any case) are equal, ignoring case.
    static bool TailEq(byte* a, byte* b, int n)
    {
        for (int j = 8; j < n; j += 8)
        {
            ulong m = LowBytes(n - j);
            if (((Unsafe.ReadUnaligned<ulong>(a + j) ^ (Unsafe.ReadUnaligned<ulong>(b + j) | Fold)) & m) != 0) return false;
        }
        return true;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static uint Intern(byte* buf, int start, int n, ulong prefix, uint h)
    {
        Slot[] sl = slots;
        uint i = h >> (32 - bits);
        for (;;)
        {
            ref Slot s = ref sl[i];
            if (s.Id == 0) break;
            if (s.Hash == h && s.Prefix == prefix &&
                (n < 8 || (wLen[s.Id] == (uint)n && TailEq(buf + wOff[s.Id], buf + start, n))))
                return s.Id;
            i = (i + 1) & mask;
        }
        return Add(buf, start, n, prefix, h, i);
    }

    static uint Add(byte* buf, int start, int n, ulong prefix, uint h, uint i)
    {
        uint id = nextId++;
        for (int j = 0; j < n; j++) buf[start + j] |= 0x20; // lower-case the stored copy
        if (id == wOff.Length)
        {
            Array.Resize(ref wOff, wOff.Length * 2);
            Array.Resize(ref wLen, wLen.Length * 2);
        }
        wOff[id] = (uint)start;
        wLen[id] = (uint)n;
        slots[i] = new Slot { Prefix = prefix, Hash = h, Id = id };
        if ((ulong)id * 2 > (ulong)slots.Length) Resize(bits + 1);
        return id;
    }

    // True if x ranks before y in the output order.
    static bool Better(in Top x, in Top y)
    {
        if (x.Cnt != y.Cnt) return x.Cnt > y.Cnt;
        if (x.R1 != y.R1) return x.R1 < y.R1;
        return x.R2 < y.R2;
    }

    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT");
            return 1;
        }
        byte[] data;
        int n;
        using (var fs = new FileStream(args[0], FileMode.Open, FileAccess.Read, FileShare.Read, 1, FileOptions.None))
        {
            long len = fs.Length;
            data = GC.AllocateUninitializedArray<byte>((int)len + 16, pinned: true);
            n = 0;
            while (n < len)
            {
                int r = fs.Read(data, n, (int)len - n);
                if (r <= 0) break;
                n += r;
            }
        }
        new Span<byte>(data, n, 16).Clear(); // zero padding: non-letters, safe 8-byte loads

        Resize(16);
        uint[] seq = GC.AllocateUninitializedArray<uint>(n / 2 + 2); // at most one word per two bytes, plus one
        int nseq = 0;
        uint[] deg = new uint[1 << 16]; // pairs per first word
        long totalPairs = 0;
        uint prev = 0; // previous word id in the current sentence, 0 = none

        ReadOnlySpan<byte> cls = Classes;
        fixed (byte* buf = data)
        fixed (uint* sq = seq)
        {
            int i = 0;
            while (i < n)
            {
                byte c = buf[i];
                byte k = cls[c];
                if (k != 1)
                {
                    if (k == 2) prev = 0;
                    i++;
                    continue;
                }
                // Word starting at i: fold case and hash it 8 bytes at a time.
                int start = i;
                ulong v = Unsafe.ReadUnaligned<ulong>(buf + i);
                ulong nl = ~LetterMask(v) & High;
                ulong prefix, h;
                if (nl != 0)
                {
                    int w = BitOperations.TrailingZeroCount(nl) >> 3;
                    prefix = (v | Fold) & LowBytes(w);
                    h = prefix * 0x9E3779B97F4A7C15UL;
                    i += w;
                }
                else
                {
                    prefix = v | Fold;
                    h = prefix * 0x9E3779B97F4A7C15UL;
                    i += 8;
                    for (;;)
                    {
                        v = Unsafe.ReadUnaligned<ulong>(buf + i);
                        nl = ~LetterMask(v) & High;
                        if (nl != 0)
                        {
                            int w = BitOperations.TrailingZeroCount(nl) >> 3;
                            if (w != 0)
                            {
                                h = (h ^ ((v | Fold) & LowBytes(w))) * 0xC2B2AE3D27D4EB4FUL;
                                i += w;
                            }
                            break;
                        }
                        h = (h ^ (v | Fold)) * 0xC2B2AE3D27D4EB4FUL;
                        i += 8;
                    }
                }
                int wl = i - start;
                h ^= h >> 31;
                h += (ulong)wl;
                h *= 0xBF58476D1CE4E5B9UL;
                uint id = Intern(buf, start, wl, prefix, (uint)(h >> 32));
                if (id == deg.Length) Array.Resize(ref deg, deg.Length * 2);
                if (prev != 0)
                {
                    deg[prev]++;
                    totalPairs++;
                    sq[nseq++] = id;
                }
                else
                {
                    sq[nseq++] = id | Start;
                }
                prev = id;
            }
        }
        long totalWords = nseq;
        int nw = (int)nextId - 1;

        // Bucket the second word of every pair by its first word.
        int[] pos = new int[nw + 2];
        for (int id = 1; id <= nw; id++) pos[id + 1] = pos[id] + (int)deg[id];
        int[] fill = (int[])pos.Clone();
        uint[] second = GC.AllocateUninitializedArray<uint>((int)totalPairs + 1);
        for (int j = 1; j < nseq; j++)
        {
            uint x = seq[j];
            if ((x & Start) == 0) second[fill[seq[j - 1] & ~Start]++] = x;
        }
        seq = null;

        // Lexicographic rank of each word id.
        uint[] off = wOff, wlen = wLen;
        int[] order = new int[nw];
        for (int id = 0; id < nw; id++) order[id] = id + 1;
        Array.Sort(order, (a, b) =>
            new ReadOnlySpan<byte>(data, (int)off[a], (int)wlen[a]).SequenceCompareTo(
                new ReadOnlySpan<byte>(data, (int)off[b], (int)wlen[b])));
        uint[] rank = new uint[nw + 1];
        for (int r = 0; r < nw; r++) rank[order[r]] = (uint)r;

        // Count second words per first word; keep the 20 best pairs.
        const int K = 20;
        Top[] top = new Top[K];
        int nt = 0;
        long distinct = 0;
        uint[] cnt = new uint[nw + 1];
        for (int a = 1; a <= nw; a++)
        {
            int lo = pos[a], hi = pos[a + 1];
            if (lo == hi) continue;
            for (int j = lo; j < hi; j++) cnt[second[j]]++;
            for (int j = lo; j < hi; j++)
            {
                uint b = second[j];
                uint c = cnt[b];
                if (c == 0) continue;
                cnt[b] = 0;
                distinct++;
                if (nt == K && c < top[K - 1].Cnt) continue;
                var t = new Top { Cnt = c, R1 = rank[a], R2 = rank[b], A = (uint)a, B = b };
                if (nt == K && !Better(t, top[K - 1])) continue;
                int p = nt < K ? nt++ : K - 1;
                while (p > 0 && Better(t, top[p - 1]))
                {
                    top[p] = top[p - 1];
                    p--;
                }
                top[p] = t;
            }
        }

        var sb = new StringBuilder(4096);
        sb.Append("words ").Append(totalWords).Append('\n');
        sb.Append("pairs ").Append(totalPairs).Append('\n');
        sb.Append("distinct ").Append(distinct).Append('\n');
        for (int t = 0; t < nt; t++)
        {
            sb.Append(top[t].Cnt).Append(' ');
            sb.Append(Encoding.ASCII.GetString(data, (int)off[top[t].A], (int)wlen[top[t].A])).Append(' ');
            sb.Append(Encoding.ASCII.GetString(data, (int)off[top[t].B], (int)wlen[top[t].B])).Append('\n');
        }
        byte[] outBytes = Encoding.ASCII.GetBytes(sb.ToString());
        using (Stream stdout = Console.OpenStandardOutput()) stdout.Write(outBytes, 0, outBytes.Length);
        return 0;
    }

    // 1 = letter, 2 = sentence end, 0 = other.
    static ReadOnlySpan<byte> Classes => new byte[256]
    {
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,2,0,0,0,0,0,0,0,0,0,0,0,0,2,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,
        0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,
        0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    };
}
