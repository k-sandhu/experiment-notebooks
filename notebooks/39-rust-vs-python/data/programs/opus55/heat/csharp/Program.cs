// Heat on a grid: exact integer diffusion with walls and fixed sources.
//
// Values never exceed 9000 (each new value is a floor-average of values <= the largest source), so
// cells are ushort in a zero-padded grid. With S = sum of the four neighbour terms (wall or outside
// neighbours replaced by the cell's own value), floor((4*o + S) / 8) == (o + (S >> 2)) >> 1 and
// S <= 36000, so every intermediate fits in 16 bits and a 256-bit vector updates 16 cells at once.
// Walls hold 0, so S = up+down+left+right + w*o with w the number of wall/outside neighbours.
// A per-cell meta word holds w (0..4) for open cells, the value for sources, and 0x8000 for walls.
//
// The iteration is monotone non-decreasing, so a row whose neighbourhood of rows did not change in the
// previous step cannot change; such rows are skipped, and a step with no change ends the run.

using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;

internal static unsafe class Program
{
    private const ushort Wall = 0x8000;

    private static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int pos = 0;
        long ReadInt()
        {
            while (pos < data.Length && (uint)(data[pos] - '0') > 9) pos++;
            long v = 0;
            while (pos < data.Length && (uint)(data[pos] - '0') <= 9) v = v * 10 + (data[pos++] - '0');
            return v;
        }
        int h = (int)ReadInt();
        int w = (int)ReadInt();
        long steps = ReadInt();

        int n = (w + 15) / 16 * 16;  // columns processed per row (1..n)
        int stride = n + 2;          // padded row length
        int total = (h + 2) * stride + 16;
        ushort[] a = new ushort[total];
        ushort[] meta = new ushort[total];
        Array.Fill(meta, Wall);
        for (int r = 0; r < h; r++)
        {
            while (data[pos] == '\r' || data[pos] == '\n' || data[pos] == ' ' || data[pos] == '\t') pos++;
            int baseIdx = (r + 1) * stride + 1;
            for (int c = 0; c < w; c++)
            {
                byte ch = data[pos + c];
                if (ch == '#') continue;
                int i = baseIdx + c;
                if (ch >= '1' && ch <= '9')
                {
                    meta[i] = (ushort)(1000 * (ch - '0'));
                    a[i] = meta[i];
                }
                else
                {
                    meta[i] = 0;
                }
            }
            pos += w;
        }
        for (int r = 1; r <= h; r++)
        {
            for (int c = 1; c <= w; c++)
            {
                int i = r * stride + c;
                if (meta[i] == 0)
                {
                    meta[i] = (ushort)((meta[i - 1] == Wall ? 1 : 0) + (meta[i + 1] == Wall ? 1 : 0) +
                                       (meta[i - stride] == Wall ? 1 : 0) + (meta[i + stride] == Wall ? 1 : 0));
                }
            }
        }
        ushort[] b = (ushort[])a.Clone();

        ushort[] result = Simulate(a, b, meta, h, n, stride, steps);

        long sum = 0, checksum = 0;
        int best = -1, bestR = 0, bestC = 0;
        for (int r = 0; r < h; r++)
        {
            int baseIdx = (r + 1) * stride + 1;
            long idx0 = (long)r * w + 1;
            for (int c = 0; c < w; c++)
            {
                if (meta[baseIdx + c] > 4) continue;
                int v = result[baseIdx + c];
                sum += v;
                checksum += v * (idx0 + c);
                if (v > best) { best = v; bestR = r; bestC = c; }
            }
        }
        byte[] outBytes = System.Text.Encoding.ASCII.GetBytes(
            $"sum {sum}\nmax {best} {bestR} {bestC}\nchecksum {checksum}\n");
        using (Stream stdout = Console.OpenStandardOutput()) stdout.Write(outBytes, 0, outBytes.Length);
        return 0;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static ushort[] Simulate(ushort[] a, ushort[] b, ushort[] meta, int h, int n, int stride, long steps)
    {
        bool[] changed = new bool[h + 2];
        bool[] nextChanged = new bool[h + 2];
        for (int r = 1; r <= h; r++) changed[r] = true;
        bool wide = Vector256.IsHardwareAccelerated;
        fixed (ushort* pa = a, pb = b, pm = meta)
        {
            ushort* cur = pa, nxt = pb;
            for (long step = 0; step < steps; step++)
            {
                bool any = false;
                for (int r = 1; r <= h; r++)
                {
                    if (!(changed[r - 1] | changed[r] | changed[r + 1]))
                    {
                        nextChanged[r] = false;
                        continue;
                    }
                    int off = r * stride;
                    bool ch = wide ? Row256(cur + off, nxt + off, pm + off, n, stride)
                                   : Row128(cur + off, nxt + off, pm + off, n, stride);
                    nextChanged[r] = ch;
                    any |= ch;
                }
                // Skipped rows hold equal values in both buffers, so swapping is safe.
                ushort* t = cur; cur = nxt; nxt = t;
                (changed, nextChanged) = (nextChanged, changed);
                if (!any) break;
            }
            return cur == pa ? a : b;
        }
    }

    // Computes one row (cols 1..n) from src into dst; returns true if any value changed.
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static bool Row256(ushort* src, ushort* dst, ushort* meta, int n, int stride)
    {
        Vector256<ushort> four = Vector256.Create((ushort)4);
        Vector256<ushort> low15 = Vector256.Create((ushort)0x7FFF);
        Vector256<ushort> diff = Vector256<ushort>.Zero;
        for (int i = 1; i <= n; i += 16)
        {
            Vector256<ushort> o = Vector256.Load(src + i);
            Vector256<ushort> up = Vector256.Load(src + i - stride);
            Vector256<ushort> dn = Vector256.Load(src + i + stride);
            Vector256<ushort> l = Vector256.Load(src + i - 1);
            Vector256<ushort> r = Vector256.Load(src + i + 1);
            Vector256<ushort> m = Vector256.Load(meta + i);
            Vector256<ushort> open = Vector256.Equals(Vector256.Min(m, four), m);
            Vector256<ushort> s = (up + dn) + (l + r) + m * o;
            Vector256<ushort> v = Vector256.ShiftRightLogical(o + Vector256.ShiftRightLogical(s, 2), 1);
            v = Vector256.ConditionalSelect(open, v, m & low15);
            v.Store(dst + i);
            diff |= v ^ o;
        }
        return diff != Vector256<ushort>.Zero;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static bool Row128(ushort* src, ushort* dst, ushort* meta, int n, int stride)
    {
        Vector128<ushort> four = Vector128.Create((ushort)4);
        Vector128<ushort> low15 = Vector128.Create((ushort)0x7FFF);
        Vector128<ushort> diff = Vector128<ushort>.Zero;
        for (int i = 1; i <= n; i += 8)
        {
            Vector128<ushort> o = Vector128.Load(src + i);
            Vector128<ushort> up = Vector128.Load(src + i - stride);
            Vector128<ushort> dn = Vector128.Load(src + i + stride);
            Vector128<ushort> l = Vector128.Load(src + i - 1);
            Vector128<ushort> r = Vector128.Load(src + i + 1);
            Vector128<ushort> m = Vector128.Load(meta + i);
            Vector128<ushort> open = Vector128.Equals(Vector128.Min(m, four), m);
            Vector128<ushort> s = (up + dn) + (l + r) + m * o;
            Vector128<ushort> v = Vector128.ShiftRightLogical(o + Vector128.ShiftRightLogical(s, 2), 1);
            v = Vector128.ConditionalSelect(open, v, m & low15);
            v.Store(dst + i);
            diff |= v ^ o;
        }
        return diff != Vector128<ushort>.Zero;
    }
}
