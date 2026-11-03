using System.Numerics;
using System.Runtime.InteropServices;

static class Program
{
    static int ReadInt(byte[] buf, ref int p)
    {
        while (p < buf.Length && (buf[p] < '0' || buf[p] > '9')) p++;
        int v = 0;
        while (p < buf.Length && buf[p] >= '0' && buf[p] <= '9') v = v * 10 + (buf[p++] - '0');
        return v;
    }

    static void Step(int[] a, int[] b, int[] c, int[] m, int lo, int hi, int w2)
    {
        int i = lo;
        int vc = Vector<int>.Count;
        ref int ra = ref MemoryMarshal.GetArrayDataReference(a);
        ref int rb = ref MemoryMarshal.GetArrayDataReference(b);
        ref int rc = ref MemoryMarshal.GetArrayDataReference(c);
        ref int rm = ref MemoryMarshal.GetArrayDataReference(m);
        for (; i + vc <= hi; i += vc)
        {
            var cur = Vector.LoadUnsafe(ref ra, (nuint)i);
            var l = Vector.LoadUnsafe(ref ra, (nuint)(i - 1));
            var r = Vector.LoadUnsafe(ref ra, (nuint)(i + 1));
            var u = Vector.LoadUnsafe(ref ra, (nuint)(i - w2));
            var d = Vector.LoadUnsafe(ref ra, (nuint)(i + w2));
            var cc = Vector.LoadUnsafe(ref rc, (nuint)i);
            var mm = Vector.LoadUnsafe(ref rm, (nuint)i);
            var res = Vector.ShiftRightArithmetic(cc * cur + ((l + r + u + d) & mm), 3);
            res.StoreUnsafe(ref rb, (nuint)i);
        }
        for (; i < hi; i++)
            b[i] = (c[i] * a[i] + ((a[i - 1] + a[i + 1] + a[i - w2] + a[i + w2]) & m[i])) >> 3;
    }

    static void Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        int p = 0;
        int H = ReadInt(buf, ref p), W = ReadInt(buf, ref p), S = ReadInt(buf, ref p);
        int w2 = W + 2, h2 = H + 2, n = w2 * h2;
        int[] a = new int[n], b = new int[n], c = new int[n], m = new int[n];
        bool[] open = new bool[n];
        int[] wall = new int[n];
        Array.Fill(c, 8);
        Array.Fill(wall, 1);
        for (int r = 0; r < H; r++)
        {
            while (p < buf.Length && buf[p] != '.' && buf[p] != '#' && (buf[p] < '1' || buf[p] > '9')) p++;
            for (int col = 0; col < W; col++)
            {
                byte ch = buf[p++];
                int idx = (r + 1) * w2 + col + 1;
                if (ch == '.') { open[idx] = true; wall[idx] = 0; m[idx] = -1; }
                else if (ch != '#') { a[idx] = 1000 * (ch - '0'); wall[idx] = 0; }
            }
        }
        for (int r = 1; r <= H; r++)
            for (int col = 1; col <= W; col++)
            {
                int idx = r * w2 + col;
                if (!open[idx]) continue;
                c[idx] = 4 + wall[idx - 1] + wall[idx + 1] + wall[idx - w2] + wall[idx + w2];
            }
        Array.Copy(a, b, n);
        int lo = w2 + 1, hi = (H + 1) * w2 - 1;
        for (int s = 0; s < S; s++)
        {
            Step(a, b, c, m, lo, hi, w2);
            (a, b) = (b, a);
        }
        long sum = 0, best = -1, br = 0, bc = 0, chk = 0;
        for (int r = 0; r < H; r++)
            for (int col = 0; col < W; col++)
            {
                int idx = (r + 1) * w2 + col + 1;
                if (!open[idx]) continue;
                long v = a[idx];
                sum += v;
                if (v > best) { best = v; br = r; bc = col; }
                chk += v * ((long)r * W + col + 1);
            }
        Console.Out.Write($"sum {sum}\nmax {best} {br} {bc}\nchecksum {chk}\n");
    }
}
