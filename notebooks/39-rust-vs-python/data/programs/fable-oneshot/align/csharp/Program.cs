using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;
using System.Text;

internal static unsafe class Program
{
    static int ReadInt(byte[] d, ref int pos)
    {
        int p = pos, len = d.Length;
        while (p < len && d[p] <= 32) p++;
        bool neg = false;
        if (p < len && d[p] == (byte)'-') { neg = true; p++; }
        int v = 0;
        while (p < len)
        {
            uint c = (uint)(d[p] - '0');
            if (c > 9) break;
            v = v * 10 + (int)c;
            p++;
        }
        pos = p;
        return neg ? -v : v;
    }

    // Anti-diagonal DP. Buffers are indexed by i (position in s).
    // delS[i] = del[s_i] (i = 1..n), sIdx[i] = letter(s_i) * 32,
    // tR[x] = letter(t_{m-x}), insR[x] = ins[t_{m-x}] (x = 0..m-1).
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static int Solve(int n, int m, int* bufA, int* bufB, int* bufC,
                     int* delS, int* sIdx, int* tR, int* insR, int* sub)
    {
        int* d2 = bufA, d1 = bufB, cur = bufC;

        d2[0] = 0;
        int insAcc = insR[m - 1];
        int delAcc = delS[1];
        d1[0] = insAcc;
        d1[1] = delAcc;

        int last = n + m;
        for (int k = 2; k <= last; k++)
        {
            int lo = k - m; if (lo < 1) lo = 1;
            int hi = k - 1; if (hi > n) hi = n;
            long off = (long)m - k;
            int* tRk = tR + off;
            int* insk = insR + off;
            long i = lo;
            long hiL = hi;

            if (Avx2.IsSupported)
            {
                for (; i <= hiL; i += 8)
                {
                    Vector256<int> a = Avx2.Add(Avx.LoadVector256(d1 + i - 1), Avx.LoadVector256(delS + i));
                    Vector256<int> b = Avx2.Add(Avx.LoadVector256(d1 + i), Avx.LoadVector256(insk + i));
                    Vector256<int> idx = Avx2.Add(Avx.LoadVector256(sIdx + i), Avx.LoadVector256(tRk + i));
                    Vector256<int> g = Avx2.GatherVector256(sub, idx, 4);
                    Vector256<int> c = Avx2.Add(Avx.LoadVector256(d2 + i - 1), g);
                    Avx.Store(cur + i, Avx2.Min(Avx2.Min(a, b), c));
                }
            }
            else
            {
                for (; i <= hiL; i++)
                {
                    int a = d1[i - 1] + delS[i];
                    int b = d1[i] + insk[i];
                    int c = d2[i - 1] + sub[sIdx[i] + tRk[i]];
                    if (b < a) a = b;
                    if (c < a) a = c;
                    cur[i] = a;
                }
            }

            if (k <= m) { insAcc += insR[m - k]; cur[0] = insAcc; }
            if (k <= n) { delAcc += delS[k]; cur[k] = delAcc; }

            int* tmp = d2; d2 = d1; d1 = cur; cur = tmp;
        }
        return d1[n];
    }

    static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int len = data.Length;
        int pos = 0;
        if (len >= 3 && data[0] == 0xEF && data[1] == 0xBB && data[2] == 0xBF) pos = 3;

        int[] map = new int[256];
        while (pos < len && data[pos] <= 32) pos++;
        int A = 0;
        while (pos < len && data[pos] > 32)
        {
            if (A < 32) map[data[pos]] = A;
            A++;
            pos++;
        }
        if (A > 32) A = 32;

        int[] ins = new int[32];
        int[] del = new int[32];
        for (int i = 0; i < A; i++) ins[i] = ReadInt(data, ref pos);
        for (int i = 0; i < A; i++) del[i] = ReadInt(data, ref pos);

        int* sub = (int*)NativeMemory.AlignedAlloc(4096, 64);
        NativeMemory.Clear(sub, 4096);
        for (int i = 0; i < A; i++)
            for (int j = 0; j < A; j++)
                sub[i * 32 + j] = ReadInt(data, ref pos);

        int P = ReadInt(data, ref pos);

        var sb = new StringBuilder(4096);
        long total = 0;

        byte* block = null;
        int cap = 0;
        int* bufA = null, bufB = null, bufC = null, delS = null, sIdx = null, tR = null, insR = null;

        fixed (byte* dp = data)
        {
            for (int q = 0; q < P; q++)
            {
                while (pos < len && data[pos] <= 32) pos++;
                int sStart = pos;
                while (pos < len && data[pos] > 32) pos++;
                int n = pos - sStart;
                while (pos < len && data[pos] <= 32) pos++;
                int tStart = pos;
                while (pos < len && data[pos] > 32) pos++;
                int m = pos - tStart;
                if (n == 0 || m == 0) break;

                int need = (n > m ? n : m) + 64;
                if (need > cap)
                {
                    if (block != null) NativeMemory.AlignedFree(block);
                    cap = Math.Max(need + need / 2, 1280);
                    nuint slot = (((nuint)cap * 4 + 4095) & ~(nuint)4095) + 4096;
                    nuint bytes = slot * 7;
                    block = (byte*)NativeMemory.AlignedAlloc(bytes, 4096);
                    NativeMemory.Clear(block, bytes);
                    bufA = (int*)(block);
                    bufB = (int*)(block + slot + 1344);
                    bufC = (int*)(block + slot * 2 + 2688);
                    delS = (int*)(block + slot * 3 + 128);
                    sIdx = (int*)(block + slot * 4 + 256);
                    tR = (int*)(block + slot * 5 + 2048);
                    insR = (int*)(block + slot * 6 + 3072);
                }

                byte* sp = dp + sStart;
                for (int i = 0; i < n; i++)
                {
                    int c = map[sp[i]];
                    delS[i + 1] = del[c];
                    sIdx[i + 1] = c << 5;
                }
                byte* tp = dp + tStart + m - 1;
                for (int x = 0; x < m; x++)
                {
                    int c = map[tp[-x]];
                    tR[x] = c;
                    insR[x] = ins[c];
                }

                int cost = Solve(n, m, bufA, bufB, bufC, delS, sIdx, tR, insR, sub);
                total += cost;
                sb.Append(cost).Append('\n');
            }
        }

        sb.Append("total ").Append(total).Append('\n');

        byte[] ob = Encoding.ASCII.GetBytes(sb.ToString());
        using (Stream o = Console.OpenStandardOutput())
        {
            o.Write(ob, 0, ob.Length);
            o.Flush();
        }
        return 0;
    }
}
