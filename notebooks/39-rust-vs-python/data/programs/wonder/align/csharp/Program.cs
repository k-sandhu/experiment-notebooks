using System;
using System.IO;
using System.Text;

unsafe class Program
{
    static byte[] d;
    static int pos, N;

    static void SkipWs()
    {
        while (pos < N)
        {
            byte c = d[pos];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') pos++;
            else break;
        }
    }

    static int ParseInt()
    {
        SkipWs();
        int v = 0;
        while (pos < N && d[pos] >= '0' && d[pos] <= '9') v = v * 10 + (d[pos++] - '0');
        return v;
    }

    static void Main(string[] args)
    {
        d = File.ReadAllBytes(args[0]);
        N = d.Length;
        pos = 0;

        int[] charIdx = new int[256];
        for (int i = 0; i < 256; i++) charIdx[i] = -1;
        int A = 0;
        while (pos < N && d[pos] != '\n')
        {
            int c = d[pos++];
            if (c >= 'A' && c <= 'Z') charIdx[c] = A++;
        }
        if (pos < N) pos++;

        int[] ins = new int[A], del = new int[A], sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = ParseInt();
        for (int i = 0; i < A; i++) del[i] = ParseInt();
        for (int i = 0; i < A * A; i++) sub[i] = ParseInt();
        int P = ParseInt();

        byte[][] strs = new byte[2 * P][];
        int maxLen = 0;
        for (int k = 0; k < 2 * P; k++)
        {
            SkipWs();
            int start = pos;
            while (pos < N)
            {
                byte c = d[pos];
                if (c == ' ' || c == '\n' || c == '\r' || c == '\t') break;
                pos++;
            }
            int len = pos - start;
            byte[] s = new byte[len];
            for (int i = 0; i < len; i++) s[i] = (byte)charIdx[d[start + i]];
            if (len > maxLen) maxLen = len;
            strs[k] = s;
        }

        int[] prev = new int[maxLen + 1], cur = new int[maxLen + 1], insT = new int[maxLen];
        var sb = new StringBuilder(P * 12);
        long total = 0;

        fixed (int* insP = ins)
        fixed (int* delP = del)
        fixed (int* subP = sub)
        fixed (int* insTP = insT)
        {
            for (int p = 0; p < P; p++)
            {
                byte[] s = strs[2 * p], t = strs[2 * p + 1];
                int n = s.Length, m = t.Length;
                fixed (byte* sP = s)
                fixed (byte* tP = t)
                fixed (int* prev0 = prev)
                fixed (int* cur0 = cur)
                {
                    int* prevP = prev0, curP = cur0;
                    for (int j = 0; j < m; j++) insTP[j] = insP[tP[j]];
                    prevP[0] = 0;
                    for (int j = 0; j < m; j++) prevP[j + 1] = prevP[j] + insTP[j];
                    for (int i = 0; i < n; i++)
                    {
                        int si = sP[i];
                        int dcost = delP[si];
                        int* subRow = subP + si * A;
                        int diag = prevP[0];
                        int left = diag + dcost;
                        curP[0] = left;
                        for (int j = 0; j < m; j++)
                        {
                            int up = prevP[j + 1];
                            int a = up + dcost;
                            int b = left + insTP[j];
                            int c = diag + subRow[tP[j]];
                            int v = a < b ? a : b;
                            if (c < v) v = c;
                            diag = up;
                            left = v;
                            curP[j + 1] = v;
                        }
                        int* tmp = prevP; prevP = curP; curP = tmp;
                    }
                    int ans;
                    // prevP points into prev or cur array depending on swaps
                    ans = prevP[m];
                    total += ans;
                    sb.Append(ans).Append('\n');
                    // swap back the managed array refs if needed: prevP alias tracking
                    // To keep next iteration consistent, copy pointer choice into arrays:
                    // Determine which buffer holds answer row and ensure 'prev' array holds it
                    // Simplest: if prevP != prev0, copy not needed since we re-pin each pair and
                    // reset prevP=prev0 above; but row data lives in whichever buffer prevP points.
                    // We already read ans, next pair reinitializes row 0 fully, so fine.
                }
            }
        }
        sb.Append("total ").Append(total).Append('\n');
        using (var stdout = Console.OpenStandardOutput())
        {
            byte[] bytes = Encoding.ASCII.GetBytes(sb.ToString());
            stdout.Write(bytes, 0, bytes.Length);
        }
    }
}
