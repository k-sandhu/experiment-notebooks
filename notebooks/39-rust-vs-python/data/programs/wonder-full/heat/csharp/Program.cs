using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

internal static class Program
{
    private static unsafe void Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int pos = 0;
        int ParseInt()
        {
            while (pos < data.Length && (data[pos] < (byte)'0' || data[pos] > (byte)'9')) pos++;
            int v = 0;
            while (pos < data.Length && data[pos] >= (byte)'0' && data[pos] <= (byte)'9')
                v = v * 10 + (data[pos++] - (byte)'0');
            return v;
        }
        int H = ParseInt(), W = ParseInt(), S = ParseInt();
        while (pos < data.Length && data[pos] != (byte)'\n') pos++;
        if (pos < data.Length) pos++;
        int N = H * W;
        byte[] grid = new byte[N];
        int gi = 0;
        for (int q = pos; q < data.Length && gi < N; q++)
        {
            byte c = data[q];
            if (c == (byte)'.' || c == (byte)'#' || (c >= (byte)'1' && c <= (byte)'9')) grid[gi++] = c;
        }

        int[] bufA = new int[N], bufB = new int[N];
        for (int i = 0; i < N; i++)
        {
            byte c = grid[i];
            if (c >= (byte)'1' && c <= (byte)'9') { int v = 1000 * (c - (byte)'0'); bufA[i] = v; bufB[i] = v; }
        }

        var runsL = new List<int>();
        var specL = new List<int>();
        var openL = new List<int>();
        for (int r = 0; r < H; r++)
        {
            int runStart = -1;
            for (int c = 0; c < W; c++)
            {
                int i = r * W + c;
                if (grid[i] != (byte)'.')
                {
                    if (runStart >= 0) { runsL.Add(runStart); runsL.Add(i - runStart); runStart = -1; }
                    continue;
                }
                openL.Add(i);
                bool interior = r > 0 && r < H - 1 && c > 0 && c < W - 1
                    && grid[i - W] != (byte)'#' && grid[i + W] != (byte)'#' && grid[i - 1] != (byte)'#' && grid[i + 1] != (byte)'#';
                if (interior)
                {
                    if (runStart < 0) runStart = i;
                }
                else
                {
                    if (runStart >= 0) { runsL.Add(runStart); runsL.Add(i - runStart); runStart = -1; }
                    int up = (r > 0     && grid[i - W] != (byte)'#') ? i - W : i;
                    int dn = (r < H - 1 && grid[i + W] != (byte)'#') ? i + W : i;
                    int lf = (c > 0     && grid[i - 1] != (byte)'#') ? i - 1 : i;
                    int rt = (c < W - 1 && grid[i + 1] != (byte)'#') ? i + 1 : i;
                    specL.Add(i); specL.Add(up); specL.Add(dn); specL.Add(lf); specL.Add(rt);
                }
            }
            if (runStart >= 0) { runsL.Add(runStart); runsL.Add(r * W + W - runStart); }
        }
        int[] runs = runsL.ToArray(), spec = specL.ToArray(), openIdx = openL.ToArray();

        int[] cur = bufA, nxt = bufB;
        bool avx2 = Avx2.IsSupported;
        for (int step = 0; step < S; step++)
        {
            fixed (int* cp = cur)
            fixed (int* np = nxt)
            {
                for (int ri = 0; ri < runs.Length; ri += 2)
                {
                    int start = runs[ri], len = runs[ri + 1];
                    int* outp = np + start;
                    int* mp = cp + start;
                    int* up = mp - W;
                    int* dn = mp + W;
                    int k = 0;
                    if (avx2)
                    {
                        int simdEnd = len & ~7;
                        for (; k < simdEnd; k += 8)
                        {
                            Vector256<int> m = Avx.LoadVector256(mp + k);
                            Vector256<int> s = Avx2.Add(Avx2.ShiftLeftLogical(m, 2),
                                Avx2.Add(Avx.LoadVector256(up + k),
                                    Avx2.Add(Avx.LoadVector256(dn + k),
                                        Avx2.Add(Avx.LoadVector256(mp + k - 1), Avx.LoadVector256(mp + k + 1)))));
                            Avx.Store(outp + k, Avx2.ShiftRightArithmetic(s, 3));
                        }
                    }
                    for (; k < len; k++)
                        outp[k] = (4 * mp[k] + up[k] + dn[k] + mp[k - 1] + mp[k + 1]) >> 3;
                }
                for (int si = 0; si < spec.Length; si += 5)
                {
                    int i = spec[si];
                    np[i] = (4 * cp[i] + cp[spec[si + 1]] + cp[spec[si + 2]] + cp[spec[si + 3]] + cp[spec[si + 4]]) >> 3;
                }
            }
            (cur, nxt) = (nxt, cur);
        }

        long sum = 0, checksum = 0;
        int best = -1, bestIdx = openIdx.Length > 0 ? openIdx[0] : 0;
        foreach (int i in openIdx)
        {
            int v = cur[i];
            sum += v;
            checksum += (long)v * (i + 1L);
            if (v > best) { best = v; bestIdx = i; }
        }
        if (best < 0) best = 0;
        int br = W > 0 ? bestIdx / W : 0, bc = W > 0 ? bestIdx % W : 0;
        Console.Out.Write($"sum {sum}\nmax {best} {br} {bc}\nchecksum {checksum}\n");
    }
}
