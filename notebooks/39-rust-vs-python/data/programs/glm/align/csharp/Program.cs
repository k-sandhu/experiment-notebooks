using System;
using System.IO;
using System.Text;

internal static class Program
{
    private static void Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        int pos = 0;
        int len = buf.Length;

        static bool IsWs(byte b) => b == (byte)' ' || b == (byte)'\n' || b == (byte)'\r' || b == (byte)'\t' || b == (byte)'\f' || b == 11;

        int ReadInt()
        {
            while (pos < len && IsWs(buf[pos])) pos++;
            int v = 0;
            while (pos < len && !IsWs(buf[pos]))
            {
                v = v * 10 + (buf[pos] - '0');
                pos++;
            }
            return v;
        }

        (int start, int end) Token()
        {
            while (pos < len && IsWs(buf[pos])) pos++;
            int start = pos;
            while (pos < len && !IsWs(buf[pos])) pos++;
            return (start, pos);
        }

        // Alphabet token
        var (ts, te) = Token();
        int a = te - ts;
        Span<int> charId = stackalloc int[128];
        charId.Fill(-1);
        for (int i = 0; i < a; i++) charId[buf[ts + i]] = i;

        int[] ins = new int[a];
        int[] del = new int[a];
        int[] sub = new int[a * a];
        for (int i = 0; i < a; i++) ins[i] = ReadInt();
        for (int i = 0; i < a; i++) del[i] = ReadInt();
        for (int i = 0; i < a * a; i++) sub[i] = ReadInt();
        int p = ReadInt();

        var outSb = new StringBuilder(p * 9 + 16);
        long total = 0;

        int[] sIds = new int[1100];
        int[] tIds = new int[1100];
        int[] rowA = new int[1101];
        int[] rowB = new int[1101];

        for (int q = 0; q < p; q++)
        {
            (ts, te) = Token();
            int n = te - ts;
            for (int i = 0; i < n; i++) sIds[i] = charId[buf[ts + i]];
            (ts, te) = Token();
            int m = te - ts;
            for (int j = 0; j < m; j++) tIds[j] = charId[buf[ts + j]];

            int[] prev = rowA;
            int[] cur = rowB;
            prev[0] = 0;
            for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + ins[tIds[j - 1]];
            for (int i = 0; i < n; i++)
            {
                int si = sIds[i];
                int dc = del[si];
                int subBase = si * a;
                int left = prev[0] + dc;
                cur[0] = left;
                int diag = prev[0];
                for (int j = 1; j <= m; j++)
                {
                    int tj = tIds[j - 1];
                    int best = prev[j] + dc;
                    int l = left + ins[tj];
                    int d = diag + sub[subBase + tj];
                    if (l < best) best = l;
                    if (d < best) best = d;
                    cur[j] = best;
                    left = best;
                    diag = prev[j];
                }
                (prev, cur) = (cur, prev);
            }
            long cost = prev[m];
            total += cost;
            outSb.Append(cost).Append('\n');
        }
        outSb.Append("total ").Append(total).Append('\n');
        Console.Out.Write(outSb.ToString());
    }
}
