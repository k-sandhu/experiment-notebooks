using System.Text;

static class Program
{
    static byte[] b;
    static int p;

    static void SkipWs()
    {
        while (p < b.Length && b[p] <= ' ') p++;
    }

    static int NextInt()
    {
        SkipWs();
        int v = 0;
        while (p < b.Length && b[p] >= '0' && b[p] <= '9') v = v * 10 + (b[p++] - '0');
        return v;
    }

    static void Main(string[] args)
    {
        b = File.ReadAllBytes(args[0]);
        SkipWs();
        var code = new int[256];
        int A = 0;
        while (p < b.Length && b[p] > ' ') code[b[p++]] = A++;
        var ins = new int[A];
        var del = new int[A];
        var sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = NextInt();
        for (int i = 0; i < A; i++) del[i] = NextInt();
        for (int i = 0; i < A * A; i++) sub[i] = NextInt();
        int P = NextInt();

        var prev = new int[16];
        var cur = new int[16];
        var tc = new int[16];
        var insT = new int[16];
        var sb = new StringBuilder();
        long total = 0;
        for (int q = 0; q < P; q++)
        {
            SkipWs();
            int s = p;
            while (p < b.Length && b[p] > ' ') p++;
            int n = p - s;
            SkipWs();
            int t = p;
            while (p < b.Length && b[p] > ' ') p++;
            int m = p - t;
            if (tc.Length < m + 1)
            {
                prev = new int[m + 1];
                cur = new int[m + 1];
                tc = new int[m + 1];
                insT = new int[m + 1];
            }
            for (int j = 1; j <= m; j++)
            {
                int c = code[b[t + j - 1]];
                tc[j] = c;
                insT[j] = ins[c];
            }
            int[] pv = prev, cu = cur;
            pv[0] = 0;
            for (int j = 1; j <= m; j++) pv[j] = pv[j - 1] + insT[j];
            for (int i = 1; i <= n; i++)
            {
                int a = code[b[s + i - 1]];
                int d = del[a];
                var sr = new ReadOnlySpan<int>(sub, a * A, A);
                int left = pv[0] + d;
                cu[0] = left;
                for (int j = 1; j <= m; j++)
                {
                    int v = Math.Min(pv[j] + d, pv[j - 1] + sr[tc[j]]);
                    left = Math.Min(v, left + insT[j]);
                    cu[j] = left;
                }
                var tmp = pv; pv = cu; cu = tmp;
            }
            long r = pv[m];
            total += r;
            sb.Append(r).Append('\n');
        }
        sb.Append("total ").Append(total).Append('\n');
        var o = Console.OpenStandardOutput();
        var bytes = Encoding.ASCII.GetBytes(sb.ToString());
        o.Write(bytes, 0, bytes.Length);
        o.Flush();
    }
}
