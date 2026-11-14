using System.Runtime.CompilerServices;
using System.Text;

sealed class PairList
{
    uint[] narrow;
    ulong[] wide;
    public int Size;
    public PairList(int estimate) { narrow = new uint[Math.Max(16, estimate)]; }
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public void Add(uint a, uint b)
    {
        if (wide == null && (a > 65535 || b > 65535))
        {
            wide = new ulong[narrow.Length];
            for (int i = 0; i < Size; ++i) wide[i] = ((ulong)(narrow[i] >> 16) << 32) | (narrow[i] & 65535);
            narrow = null;
        }
        if (wide == null)
        {
            if (Size == narrow.Length) Array.Resize(ref narrow, narrow.Length * 2);
            narrow[Size++] = (a << 16) | b;
        }
        else
        {
            if (Size == wide.Length) Array.Resize(ref wide, wide.Length * 2);
            wide[Size++] = ((ulong)a << 32) | b;
        }
    }
    public void Sort()
    {
        if (Size < 2048)
        {
            if (wide == null) Array.Sort(narrow, 0, Size); else Array.Sort(wide, 0, Size);
            return;
        }
        var offsets = new int[2048];
        if (wide == null)
        {
            uint variation = 0, first = narrow[0];
            for (int i = 0; i < Size; ++i) variation |= narrow[i] ^ first;
            if (variation == 0) return;
            var scratch = new uint[Size];
            for (int shift = 0; shift < 32; shift += 11)
            {
                if (((variation >> shift) & 2047) == 0) continue;
                Array.Clear(offsets);
                for (int i = 0; i < Size; ++i) ++offsets[(narrow[i] >> shift) & 2047];
                int total = 0;
                for (int j = 0; j < offsets.Length; ++j) { int count = offsets[j]; offsets[j] = total; total += count; }
                for (int i = 0; i < Size; ++i) scratch[offsets[(narrow[i] >> shift) & 2047]++] = narrow[i];
                (narrow, scratch) = (scratch, narrow);
            }
        }
        else
        {
            ulong variation = 0, first = wide[0];
            for (int i = 0; i < Size; ++i) variation |= wide[i] ^ first;
            if (variation == 0) return;
            var scratch = new ulong[Size];
            for (int shift = 0; shift < 64; shift += 11)
            {
                if (((variation >> shift) & 2047) == 0) continue;
                Array.Clear(offsets);
                for (int i = 0; i < Size; ++i) ++offsets[(wide[i] >> shift) & 2047];
                int total = 0;
                for (int j = 0; j < offsets.Length; ++j) { int count = offsets[j]; offsets[j] = total; total += count; }
                for (int i = 0; i < Size; ++i) scratch[offsets[(wide[i] >> shift) & 2047]++] = wide[i];
                (wide, scratch) = (scratch, wide);
            }
        }
    }
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public ulong Key(int i) => wide != null ? wide[i] : ((ulong)(narrow[i] >> 16) << 32) | (narrow[i] & 65535);
}

sealed class Vocabulary
{
    readonly byte[] data;
    int[] slots = new int[1024], starts = new int[1024], lengths = new int[1024];
    uint[] hashes = new uint[1024];
    public int Size = 1;
    public Vocabulary(byte[] input) { data = input; }
    public int Intern(int start, int length, uint hash)
    {
        int mask = slots.Length - 1, p = (int)hash & mask;
        while (slots[p] != 0)
        {
            int id = slots[p];
            if (hashes[id] == hash && lengths[id] == length &&
                data.AsSpan(start, length).SequenceEqual(data.AsSpan(starts[id], length))) return id;
            p = (p + 1) & mask;
        }
        if (Size >= slots.Length - slots.Length / 4)
        {
            slots = new int[slots.Length * 2]; mask = slots.Length - 1;
            for (int id = 1; id < Size; ++id)
            {
                int q = (int)hashes[id] & mask;
                while (slots[q] != 0) q = (q + 1) & mask;
                slots[q] = id;
            }
            p = (int)hash & mask; while (slots[p] != 0) p = (p + 1) & mask;
        }
        if (Size == starts.Length)
        {
            Array.Resize(ref starts, Size * 2); Array.Resize(ref lengths, Size * 2);
            Array.Resize(ref hashes, Size * 2);
        }
        int result = Size++;
        starts[result] = start; lengths[result] = length; hashes[result] = hash; slots[p] = result;
        return result;
    }
    public string Word(int id) => Encoding.ASCII.GetString(data, starts[id], lengths[id]);
}

static class Program
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static bool Better(ulong ak, long ac, ulong bk, long bc, int[] rank)
    {
        if (ac != bc) return ac > bc;
        int a = rank[(int)(ak >> 32)], b = rank[(int)(bk >> 32)];
        return a != b ? a < b : rank[(int)(uint)ak] < rank[(int)(uint)bk];
    }
    static void Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        var vocabulary = new Vocabulary(data);
        var pairs = new PairList(data.Length / 6);
        long wordCount = 0, pairCount = 0;
        int previous = 0, i = 0;
        while (i < data.Length)
        {
            int c = data[i] | 32;
            if ((uint)(c - 'a') <= 25)
            {
                int start = i;
                uint hash = 2166136261;
                do
                {
                    data[i++] = (byte)c; hash = (hash ^ (uint)c) * 16777619;
                    if (i == data.Length) break;
                    c = data[i] | 32;
                } while ((uint)(c - 'a') <= 25);
                int id = vocabulary.Intern(start, i - start, hash);
                ++wordCount;
                if (previous != 0) { pairs.Add((uint)previous, (uint)id); ++pairCount; }
                previous = id;
            }
            else
            {
                int raw = data[i++];
                if (raw == '.' || raw == '!' || raw == '?') previous = 0;
            }
        }
        var order = new int[vocabulary.Size - 1];
        var words = new string[vocabulary.Size];
        for (i = 1; i < vocabulary.Size; ++i) { order[i - 1] = i; words[i] = vocabulary.Word(i); }
        Array.Sort(order, (a, b) => string.CompareOrdinal(words[a], words[b]));
        var rank = new int[vocabulary.Size];
        for (i = 0; i < order.Length; ++i) rank[order[i]] = i;
        var topKeys = new ulong[20]; var topCounts = new long[20];
        int used = 0, distinct = 0;
        pairs.Sort();
        for (i = 0; i < pairs.Size;)
        {
            int start = i;
            ulong key = pairs.Key(i++);
            while (i < pairs.Size && pairs.Key(i) == key) ++i;
            long count = i - start;
            ++distinct;
            if (used == 20 && !Better(key, count, topKeys[19], topCounts[19], rank)) continue;
            int p = Math.Min(used, 19);
            while (p > 0 && Better(key, count, topKeys[p - 1], topCounts[p - 1], rank))
            {
                topKeys[p] = topKeys[p - 1]; topCounts[p] = topCounts[p - 1]; --p;
            }
            topKeys[p] = key; topCounts[p] = count;
            if (used < 20) ++used;
        }
        var output = new StringBuilder();
        output.Append("words ").Append(wordCount).Append("\npairs ").Append(pairCount)
              .Append("\ndistinct ").Append(distinct).Append('\n');
        for (i = 0; i < used; ++i) output.Append(topCounts[i]).Append(' ')
            .Append(words[(int)(topKeys[i] >> 32)]).Append(' ').Append(words[(int)(uint)topKeys[i]]).Append('\n');
        Console.Write(output.ToString());
    }
}
