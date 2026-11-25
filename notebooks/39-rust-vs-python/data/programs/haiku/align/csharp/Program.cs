using System;
using System.IO;
using System.Text;

// Weighted alignment cost (see SPEC.md).
//
// The input file is read as one byte array and parsed in place. The DP keeps one row of longs,
// updated in place, with the diagonal and left values held in locals. The inner loop works
// through pinned pointers, so it has no bounds checks. Scratch arrays are reused across pairs
// and only grow.
internal static unsafe class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT_PATH");
            return 1;
        }

        byte[] data = File.ReadAllBytes(args[0]);
        int pos = 0;
        int tokenEnd = 0;

        // Skips whitespace and returns the start of the next token; tokenEnd is set to its end.
        int NextToken()
        {
            int p = pos;
            while (p < data.Length && data[p] <= (byte)' ') p++;
            int start = p;
            while (p < data.Length && data[p] > (byte)' ') p++;
            pos = p;
            tokenEnd = p;
            return start;
        }

        long NextNumber()
        {
            int start = NextToken();
            long v = 0;
            for (int k = start; k < tokenEnd; k++) v = v * 10 + (data[k] - '0');
            return v;
        }

        int aStart = NextToken();
        int a = tokenEnd - aStart;
        int[] code = new int[256];
        for (int i = 0; i < a; i++) code[data[aStart + i]] = i;

        long[] ins = new long[a];
        long[] del = new long[a];
        long[] sub = new long[a * a];
        for (int i = 0; i < a; i++) ins[i] = NextNumber();
        for (int i = 0; i < a; i++) del[i] = NextNumber();
        for (int i = 0; i < a * a; i++) sub[i] = NextNumber();

        int pairs = (int)NextNumber();

        int[] s = new int[1];
        int[] t = new int[1];
        long[] tIns = new long[1];
        long[] row = new long[1];
        var output = new StringBuilder();
        long total = 0;

        for (int p = 0; p < pairs; p++)
        {
            int sStart = NextToken();
            int n = tokenEnd - sStart;
            int tStart = NextToken();
            int m = tokenEnd - tStart;

            if (s.Length < n + 1) s = new int[n + 1];
            if (t.Length < m + 1)
            {
                t = new int[m + 1];
                tIns = new long[m + 1];
                row = new long[m + 1];
            }
            for (int i = 1; i <= n; i++) s[i] = code[data[sStart + i - 1]];
            for (int j = 1; j <= m; j++)
            {
                t[j] = code[data[tStart + j - 1]];
                tIns[j] = ins[t[j]];
            }

            long cost;
            fixed (int* sp = s, tp = t)
            fixed (long* tip = tIns, rp = row, dp = del, subp = sub)
            {
                cost = AlignCost(sp, n, tp, m, tip, dp, subp, a, rp);
            }

            total += cost;
            output.Append(cost).Append('\n');
        }

        output.Append("total ").Append(total).Append('\n');
        using (Stream stdout = Console.OpenStandardOutput())
        {
            byte[] bytes = Encoding.ASCII.GetBytes(output.ToString());
            stdout.Write(bytes, 0, bytes.Length);
        }
        return 0;
    }

    // Cost of the pair: s[1..n] are rows (deletions), t[1..m] are columns (insertions).
    // tIns[j] = ins[t[j]]. row must hold m + 1 values.
    private static long AlignCost(int* s, int n, int* t, int m, long* tIns,
                                  long* del, long* sub, int a, long* row)
    {
        row[0] = 0;
        for (int j = 1; j <= m; j++) row[j] = row[j - 1] + tIns[j];

        for (int i = 1; i <= n; i++)
        {
            int si = s[i];
            long d = del[si];
            long* subRow = sub + si * a;

            long diag = row[0];
            long left = row[0] += d;
            for (int j = 1; j <= m; j++)
            {
                long up = row[j];
                // left is the only term that depends on the previous cell, so it goes last.
                long v = Min(Min(up + d, diag + subRow[t[j]]), left + tIns[j]);
                row[j] = v;
                left = v;
                diag = up;
            }
        }
        return row[m];
    }

    // Branch-free minimum. Costs are small, so the subtraction cannot overflow. The JIT turns
    // Math.Min into a branch here, and its mispredictions dominate the loop.
    [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
    private static long Min(long a, long b)
    {
        long d = a - b;
        return b + (d & (d >> 63));
    }
}
