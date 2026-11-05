using System.Numerics;

// Heat on a grid (see SPEC.md).
//
// The grid is stored padded with a one-cell border of zeros, row stride W + 2, so every
// neighbour lookup is a plain offset. Walls and border cells always hold 0, so a wall
// neighbour contributes 0 and the "use own old value" rule becomes (8 - valid) * old.
// Vector<int> processes Vector<int>.Count cells per iteration (8 with AVX2).
static class Program
{
    // One simulation step over the flat index range [begin, end).
    // mask is -1 for open cells and 0 otherwise; fixedV holds the constant value of sources.
    static void Step(int[] cur, int[] nxt, int[] mult, int[] mask, int[] fixedV, int begin, int end, int stride)
    {
        int width = Vector<int>.Count;
        int i = begin;
        for (; i + width <= end; i += width)
        {
            Vector<int> sum = new Vector<int>(mult, i) * new Vector<int>(cur, i)
                + new Vector<int>(cur, i - 1) + new Vector<int>(cur, i + 1)
                + new Vector<int>(cur, i - stride) + new Vector<int>(cur, i + stride);
            Vector<int> res = (Vector.ShiftRightArithmetic(sum, 3) & new Vector<int>(mask, i))
                | new Vector<int>(fixedV, i);
            res.CopyTo(nxt, i);
        }
        for (; i < end; i++)
        {
            int sum = mult[i] * cur[i] + cur[i - 1] + cur[i + 1] + cur[i - stride] + cur[i + stride];
            nxt[i] = ((sum >> 3) & mask[i]) | fixedV[i];
        }
    }

    static bool IsCell(byte ch)
    {
        return ch == '.' || ch == '#' || (ch >= '1' && ch <= '9');
    }

    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT_PATH");
            return 2;
        }
        byte[] buf = File.ReadAllBytes(args[0]);
        int p = 0;

        long ReadInt()
        {
            while (p < buf.Length && (buf[p] < '0' || buf[p] > '9')) p++;
            long v = 0;
            while (p < buf.Length && buf[p] >= '0' && buf[p] <= '9') v = v * 10 + (buf[p++] - '0');
            return v;
        }

        int H = (int)ReadInt();
        int W = (int)ReadInt();
        long S = ReadInt();

        int P = W + 2;
        int N = (H + 2) * P;
        byte[] kind = new byte[N];  // 0 = wall or border, 1 = open, 2 = source
        int[] mult = new int[N];
        int[] mask = new int[N];
        int[] fixedV = new int[N];

        for (int r = 1; r <= H; r++)
        {
            for (int c = 1; c <= W; c++)
            {
                while (p < buf.Length && !IsCell(buf[p])) p++;
                if (p >= buf.Length) break;
                byte ch = buf[p++];
                int i = r * P + c;
                if (ch == '.')
                {
                    kind[i] = 1;
                }
                else if (ch != '#')
                {
                    kind[i] = 2;
                    fixedV[i] = 1000 * (ch - '0');
                }
            }
        }

        for (int r = 1; r <= H; r++)
        {
            for (int c = 1; c <= W; c++)
            {
                int i = r * P + c;
                if (kind[i] == 1)
                {
                    int valid = (kind[i - 1] != 0 ? 1 : 0) + (kind[i + 1] != 0 ? 1 : 0)
                        + (kind[i - P] != 0 ? 1 : 0) + (kind[i + P] != 0 ? 1 : 0);
                    mult[i] = 8 - valid;
                    mask[i] = -1;
                }
            }
        }

        int[] cur = (int[])fixedV.Clone();  // sources start at their fixed value
        int[] nxt = (int[])fixedV.Clone();
        int rowsBegin = P;
        int rowsEnd = (H + 1) * P;
        for (long s = 0; s < S; s++)
        {
            Step(cur, nxt, mult, mask, fixedV, rowsBegin, rowsEnd, P);
            (cur, nxt) = (nxt, cur);
        }

        long total = 0, checksum = 0;
        long bestV = -1;
        int bestR = -1, bestC = -1;
        for (int r = 0; r < H; r++)
        {
            for (int c = 0; c < W; c++)
            {
                int i = (r + 1) * P + c + 1;
                if (kind[i] != 1) continue;
                long v = cur[i];
                total += v;
                if (v > bestV)
                {
                    bestV = v;
                    bestR = r;
                    bestC = c;
                }
                checksum += v * ((long)r * W + c + 1);
            }
        }

        // Write "\n" explicitly; Console.WriteLine would emit "\r\n" on Windows.
        Console.Out.Write($"sum {total}\nmax {bestV} {bestR} {bestC}\nchecksum {checksum}\n");
        Console.Out.Flush();
        return 0;
    }
}
