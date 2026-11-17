using System.Numerics;

internal static class Program
{
    private static byte[] input;
    private static int pos;

    private static long Number()
    {
        while (input[pos] <= 32) ++pos;
        long value = 0;
        while (pos < input.Length && input[pos] >= '0' && input[pos] <= '9')
        {
            int digit = input[pos++] - '0';
            value = value > (long.MaxValue - digit) / 10
                  ? long.MaxValue : value * 10 + digit;
        }
        return value;
    }

    private static void Main(string[] args)
    {
        input = File.ReadAllBytes(args[0]);
        int h = (int)Number(), w = (int)Number();
        long steps = Number();
        int stride = w + 2, size = (h + 2) * stride;
        int begin = stride, end = (h + 1) * stride;
        byte[] grid = new byte[size];
        Array.Fill(grid, (byte)'#');
        int[] a = new int[size], b = new int[size], weight = new int[size];
        int openCount = 0;
        bool hasSource = false;
        for (int r = 1; r <= h; ++r)
        {
            while (pos < input.Length && input[pos] <= 32) ++pos;
            for (int c = 1; c <= w; ++c)
            {
                int i = r * stride + c;
                byte ch = input[pos++];
                grid[i] = ch;
                if (ch == '.') ++openCount;
                if (ch >= '1' && ch <= '9')
                {
                    a[i] = b[i] = (ch - '0') * 1000;
                    hasSource = true;
                }
            }
        }
        bool sparse = openCount < (end - begin) / 4;
        int[] indices = new int[sparse ? openCount : end - begin - openCount];
        int count = 0;
        for (int i = begin; i < end; ++i)
        {
            if (grid[i] == '.')
            {
                weight[i] = 4 + (grid[i - stride] == '#' ? 1 : 0)
                              + (grid[i + stride] == '#' ? 1 : 0)
                              + (grid[i - 1] == '#' ? 1 : 0)
                              + (grid[i + 1] == '#' ? 1 : 0);
                if (sparse) indices[count++] = i;
            }
            else if (!sparse) indices[count++] = i;
        }
        input = null;
        if (hasSource)
            a = Simulate(a, b, weight, indices, sparse, stride, begin, end, steps);
        long total = 0, checksum = 0;
        int best = -1, bestR = 0, bestC = 0;
        for (int r = 0; r < h; ++r)
        {
            for (int c = 0; c < w; ++c)
            {
                int i = (r + 1) * stride + c + 1;
                if (grid[i] != '.') continue;
                int value = a[i];
                total += value;
                checksum += (long)value * ((long)r * w + c + 1);
                if (value > best) { best = value; bestR = r; bestC = c; }
            }
        }
        Console.Write($"sum {total}\nmax {best} {bestR} {bestC}\nchecksum {checksum}\n");
    }

    private static unsafe int[] Simulate(int[] a, int[] b, int[] weight, int[] indices,
                                         bool sparse, int stride, int begin, int end, long steps)
    {
        fixed (int* a0 = a, b0 = b, weights = weight, cells = indices)
        {
            int* old = a0;
            int* next = b0;
            int lanes = Vector<int>.Count;
            int vectorEnd = end - lanes + 1;
            for (long step = 0; step < steps; ++step)
            {
                if (sparse)
                {
                    for (int k = 0; k < indices.Length; ++k)
                    {
                        int i = cells[k];
                        next[i] = (weights[i] * old[i] + old[i - stride] + old[i + stride]
                                   + old[i - 1] + old[i + 1]) >> 3;
                    }
                }
                else
                {
                    int i = begin;
                    if (Vector.IsHardwareAccelerated)
                    {
                        for (; i < vectorEnd; i += lanes)
                        {
                            var values = Vector.Load(old + i) * Vector.Load(weights + i)
                                       + Vector.Load(old + i - stride) + Vector.Load(old + i + stride)
                                       + Vector.Load(old + i - 1) + Vector.Load(old + i + 1);
                            Vector.Store(values >> 3, next + i);
                        }
                    }
                    for (; i < end; ++i)
                        next[i] = (weights[i] * old[i] + old[i - stride] + old[i + stride]
                                   + old[i - 1] + old[i + 1]) >> 3;
                    for (int k = 0; k < indices.Length; ++k)
                    {
                        int index = cells[k];
                        next[index] = old[index];
                    }
                }
                bool stable = (step & 63) == 63 &&
                    new ReadOnlySpan<int>(old + begin, end - begin)
                        .SequenceEqual(new ReadOnlySpan<int>(next + begin, end - begin));
                int* temp = old; old = next; next = temp;
                if (stable) break;
            }
            return old == a0 ? a : b;
        }
    }
}
