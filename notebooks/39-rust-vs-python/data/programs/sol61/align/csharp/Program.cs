using System.Text;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

sealed class Input
{
    public readonly byte[] Data;
    public int Start, Length;
    private int position;
    public Input(string path) => Data = File.ReadAllBytes(path);
    public void Token()
    {
        while (position < Data.Length && Data[position] <= 32) ++position;
        Start = position;
        while (position < Data.Length && Data[position] > 32) ++position;
        Length = position - Start;
    }
    public int Number()
    {
        Token();
        int value = 0;
        for (int i = Start; i < position; ++i) value = value * 10 + Data[i] - 48;
        return value;
    }
}

sealed class Alignment
{
    public readonly int[][] Ins = { new int[26], new int[26] };
    public readonly int[][] Del = { new int[26], new int[26] };
    public readonly int[][] Sub = { new int[26 * 26], new int[26 * 26] };
    private int[] insertion = Array.Empty<int>(), profile = Array.Empty<int>(), row32 = Array.Empty<int>();
    private long[] row64 = Array.Empty<long>();
    private int capacity;

    public long Cost(byte[] data, int s, int n, int t, int m)
    {
        if (n == m && data.AsSpan(s, n).SequenceEqual(data.AsSpan(t, m))) return 0;
        int direction = 0;
        if (n < m)
        {
            (s, t) = (t, s);
            (n, m) = (m, n);
            direction = 1;
        }
        if (capacity < m)
        {
            capacity = m;
            insertion = new int[m];
            profile = new int[26 * m];
        }
        int[] deletion = Del[direction], insert = Ins[direction], table = Sub[direction];
        long bound = 0;
        uint used = 0;
        for (int i = 0; i < n; ++i)
        {
            int c = data[s + i] - 65;
            bound += deletion[c];
            used |= 1u << c;
        }
        for (int j = 0; j < m; ++j)
        {
            int value = insert[data[t + j] - 65];
            insertion[j] = value;
            bound += value;
        }
        if (bound == 0) return 0;
        for (int c = 0; c < 26; ++c)
        {
            if ((used & (1u << c)) == 0) continue;
            int offset = c * capacity, tableOffset = c * 26;
            for (int j = 0; j < m; ++j) profile[offset + j] = table[tableOffset + data[t + j] - 65];
        }
        // Keep a full cost of headroom for candidate additions.
        return bound <= int.MaxValue - 1000
            ? Evaluate32(data, s, n, m, deletion)
            : Evaluate64(data, s, n, m, deletion);
    }

    private unsafe int Evaluate32(byte[] data, int s, int n, int m, int[] deletion)
    {
        if (row32.Length < m) row32 = new int[m];
        fixed (int* row = row32, insert = insertion, profiles = profile, del = deletion)
        fixed (byte* source = data)
        {
            int prefix = 0;
            for (int j = 0; j < m; ++j) row[j] = prefix += insert[j];
            int boundary = 0;
            for (int i = 0; i < n; ++i)
            {
                int c = source[s + i] - 65, d = del[c];
                int* costs = profiles + c * capacity;
                int diagonal = boundary, left = boundary += d;
                if (Sse41.IsSupported)
                {
                    // .NET 8 lowers scalar integer Math.Min to branches.
                    // Keep the recurrence in the low SIMD lane for hardware min.
                    var diagonalVector = Vector128.CreateScalarUnsafe(diagonal);
                    var leftVector = Vector128.CreateScalarUnsafe(left);
                    var deletionVector = Vector128.CreateScalarUnsafe(d);
                    for (int j = 0; j < m; ++j)
                    {
                        var above = Vector128.CreateScalarUnsafe(row[j]);
                        var down = Sse2.Add(above, deletionVector);
                        var across = Sse2.Add(leftVector, Vector128.CreateScalarUnsafe(insert[j]));
                        var replace = Sse2.Add(diagonalVector, Vector128.CreateScalarUnsafe(costs[j]));
                        leftVector = Sse41.Min(Sse41.Min(down, across), replace);
                        row[j] = leftVector.ToScalar();
                        diagonalVector = above;
                    }
                }
                else
                {
                    for (int j = 0; j < m; ++j)
                    {
                        int above = row[j];
                        // All candidates are nonnegative and bounded, so
                        // their differences fit in a signed integer.
                        int across = left + insert[j];
                        int difference = above + d - across;
                        int best = across + (difference & (difference >> 31));
                        int replace = diagonal + costs[j];
                        difference = best - replace;
                        left = replace + (difference & (difference >> 31));
                        row[j] = left;
                        diagonal = above;
                    }
                }
            }
            return row[m - 1];
        }
    }

    private unsafe long Evaluate64(byte[] data, int s, int n, int m, int[] deletion)
    {
        if (row64.Length < m) row64 = new long[m];
        fixed (long* row = row64)
        fixed (int* insert = insertion, profiles = profile, del = deletion)
        fixed (byte* source = data)
        {
            long prefix = 0;
            for (int j = 0; j < m; ++j) row[j] = prefix += insert[j];
            long boundary = 0;
            for (int i = 0; i < n; ++i)
            {
                int c = source[s + i] - 65, d = del[c];
                int* costs = profiles + c * capacity;
                long diagonal = boundary, left = boundary += d;
                for (int j = 0; j < m; ++j)
                {
                    long above = row[j];
                    left = Math.Min(Math.Min(above + d, left + insert[j]), diagonal + costs[j]);
                    row[j] = left;
                    diagonal = above;
                }
            }
            return row[m - 1];
        }
    }
}

static class Program
{
    static void Main(string[] args)
    {
        var input = new Input(args[0]);
        input.Token();
        int alphabet = input.Start, size = input.Length;
        var solver = new Alignment();
        for (int i = 0; i < size; ++i) solver.Ins[0][input.Data[alphabet + i] - 65] = input.Number();
        for (int i = 0; i < size; ++i) solver.Del[0][input.Data[alphabet + i] - 65] = input.Number();
        for (int i = 0; i < size; ++i)
            for (int j = 0; j < size; ++j)
                solver.Sub[0][(input.Data[alphabet + i] - 65) * 26 + input.Data[alphabet + j] - 65] = input.Number();
        for (int i = 0; i < 26; ++i)
        {
            solver.Ins[1][i] = solver.Del[0][i];
            solver.Del[1][i] = solver.Ins[0][i];
            for (int j = 0; j < 26; ++j) solver.Sub[1][i * 26 + j] = solver.Sub[0][j * 26 + i];
        }
        int pairs = input.Number();
        long total = 0;
        var output = new StringBuilder();
        for (int p = 0; p < pairs; ++p)
        {
            input.Token();
            int s = input.Start, n = input.Length;
            input.Token();
            long result = solver.Cost(input.Data, s, n, input.Start, input.Length);
            total += result;
            output.Append(result).Append('\n');
        }
        output.Append("total ").Append(total).Append('\n');
        Console.Write(output);
    }
}
