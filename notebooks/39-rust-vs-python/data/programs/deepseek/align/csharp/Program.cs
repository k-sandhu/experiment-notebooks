using System;
using System.IO;
using System.Text;

internal static class Program
{
    private static byte[] data = Array.Empty<byte>();
    private static int pos;
    private static int len;

    private static void SkipWs()
    {
        byte[] d = data;
        int p = pos, n = len;
        while (p < n && d[p] <= (byte)' ') ++p;
        pos = p;
    }

    private static int NextInt()
    {
        byte[] d = data;
        int p = pos, n = len;
        while (p < n && d[p] <= (byte)' ') ++p;
        int v = 0;
        while (p < n)
        {
            int c = d[p];
            if (c < '0' || c > '9') break;
            v = v * 10 + (c - '0');
            ++p;
        }
        pos = p;
        return v;
    }

    private static void Main(string[] args)
    {
        data = File.ReadAllBytes(args[0]);
        len = data.Length;
        pos = 0;

        SkipWs();
        int abStart = pos;
        while (pos < len && data[pos] > (byte)' ') ++pos;
        int A = pos - abStart;
        byte[] mp = new byte[256];
        for (int i = 0; i < A; ++i) mp[data[abStart + i]] = (byte)i;

        int[] ins = new int[A];
        int[] delc = new int[A];
        int[] sub = new int[A * A];
        for (int i = 0; i < A; ++i) ins[i] = NextInt();
        for (int i = 0; i < A; ++i) delc[i] = NextInt();
        for (int i = 0; i < A * A; ++i) sub[i] = NextInt();

        int P = NextInt();

        byte[] s = new byte[1024];
        byte[] t = new byte[1024];
        int[] tins = new int[1024];
        int[] row = new int[1024];

        var outSb = new StringBuilder(P * 8 + 16);
        long total = 0;

        for (int q = 0; q < P; ++q)
        {
            SkipWs();
            int sl = 0;
            while (pos < len && data[pos] > (byte)' ')
            {
                if (sl == s.Length) Array.Resize(ref s, s.Length * 2);
                s[sl++] = mp[data[pos]];
                ++pos;
            }
            SkipWs();
            int tl = 0;
            while (pos < len && data[pos] > (byte)' ')
            {
                if (tl == t.Length) Array.Resize(ref t, t.Length * 2);
                t[tl++] = mp[data[pos]];
                ++pos;
            }

            int n = sl;
            int M = tl;

            bool same = n == M;
            if (same)
            {
                for (int i = 0; i < n; ++i)
                {
                    if (s[i] != t[i]) { same = false; break; }
                }
            }
            if (same)
            {
                outSb.Append('0').Append('\n');
                continue;
            }

            if (tins.Length < M) tins = new int[Math.Max(M, tins.Length * 2)];
            for (int j = 0; j < M; ++j) tins[j] = ins[t[j]];
            if (row.Length < M + 1) row = new int[Math.Max(M + 1, row.Length * 2)];

            int[] r = row;
            r[0] = 0;
            for (int j = 1; j <= M; ++j) r[j] = r[j - 1] + tins[j - 1];

            unsafe
            {
                fixed (int* rp = r)
                fixed (int* tip = tins)
                fixed (byte* tp = t)
                fixed (byte* sp2 = s)
                fixed (int* subp = sub)
                {
                    for (int i = 0; i < n; ++i)
                    {
                        int si = sp2[i];
                        int dc = delc[si];
                        int* srow = subp + si * A;

                        int diag = rp[0];
                        int left = diag + dc;
                        rp[0] = left;

                        for (int j = 1; j <= M; ++j)
                        {
                            int up = rp[j];
                            int a = up + dc;
                            int b = diag + srow[tp[j - 1]];
                            int d = b - a;
                            int mn = a + (d & (d >> 31));
                            int x = left + tip[j - 1];
                            d = x - mn;
                            left = mn + (d & (d >> 31));
                            diag = up;
                            rp[j] = left;
                        }
                    }
                }
            }

            int cost = r[M];
            total += cost;
            outSb.Append(cost).Append('\n');
        }

        outSb.Append("total ").Append(total).Append('\n');
        using Stream stdout = Console.OpenStandardOutput();
        byte[] bytes = Encoding.UTF8.GetBytes(outSb.ToString());
        stdout.Write(bytes, 0, bytes.Length);
    }
}
