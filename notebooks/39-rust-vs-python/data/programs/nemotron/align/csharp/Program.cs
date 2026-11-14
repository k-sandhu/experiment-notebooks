using System;
using System.IO;
using System.Text;

// Weighted edit distance for many string pairs (exact DP recurrence from SPEC.md).
// Two rolling rows; cells fit in int, the grand total in long.
// The hot loop runs over pinned arrays with unsafe pointers to drop bounds checks.

class Program {
    static byte[] b;
    static int pos;
    static int len;

    static void SkipWs() {
        while (pos < len && b[pos] <= 32) pos++;
    }

    static int NextInt() {
        SkipWs();
        int x = 0;
        while (pos < len && b[pos] > 32) {
            x = x * 10 + (b[pos] - '0');
            pos++;
        }
        return x;
    }

    static int[] ReadTokenIdx(int[] idx) {
        SkipWs();
        int start = pos;
        while (pos < len && b[pos] > 32) pos++;
        int n = pos - start;
        int[] a = new int[n];
        for (int i = 0; i < n; i++) a[i] = idx[b[start + i]];
        return a;
    }

    static int EditDistance(int[] s, int[] t, int[] ins, int[] del, int[] sub, int A,
                            int[] prev, int[] cur) {
        int n = s.Length;
        int m = t.Length;
        int result = 0;

        prev[0] = 0;
        for (int j = 1; j <= m; j++) prev[j] = prev[j - 1] + ins[t[j - 1]];

        unsafe {
            fixed (int* sp = s, tp = t, pp = prev, cp = cur, subp = sub) {
                int* pv = pp;
                int* cv = cp;
                for (int i = 0; i < n; i++) {
                    int d = del[sp[i]];
                    int* subrow = subp + sp[i] * A;
                    cv[0] = pv[0] + d;
                    int diag = pv[0];
                    for (int j = 1; j <= m; j++) {
                        int tj = tp[j - 1];
                        int best = pv[j] + d;
                        int v = cv[j - 1] + ins[tj];
                        if (v < best) best = v;
                        v = diag + subrow[tj];
                        if (v < best) best = v;
                        cv[j] = best;
                        diag = pv[j];
                    }
                    int* tmp = pv; pv = cv; cv = tmp;
                }
                result = pv[m]; // cell values fit in int; pv points at the last row
            }
        }
        return result;
    }

    static int[] Ensure(ref int[] arr, int minLen) {
        if (arr == null || arr.Length < minLen) arr = new int[minLen];
        return arr;
    }

    static void Main(string[] args) {
        b = File.ReadAllBytes(args[0]);
        len = b.Length;

        SkipWs();
        int alphaStart = pos;
        while (pos < len && b[pos] > 32) pos++;
        int A = pos - alphaStart;

        int[] idx = new int[256];
        for (int i = 0; i < 256; i++) idx[i] = -1;
        for (int i = 0; i < A; i++) idx[b[alphaStart + i]] = i;

        int[] ins = new int[A];
        int[] del = new int[A];
        int[] sub = new int[A * A];
        for (int i = 0; i < A; i++) ins[i] = NextInt();
        for (int i = 0; i < A; i++) del[i] = NextInt();
        for (int i = 0; i < A * A; i++) sub[i] = NextInt();

        int P = NextInt();

        int[] prev = null;
        int[] cur = null;
        long total = 0;
        var sb = new StringBuilder();

        for (int pair = 0; pair < P; pair++) {
            int[] s = ReadTokenIdx(idx);
            int[] t = ReadTokenIdx(idx);
            int m = t.Length;
            Ensure(ref prev, m + 1);
            Ensure(ref cur, m + 1);

            long cost = EditDistance(s, t, ins, del, sub, A, prev, cur);
            total += cost;
            sb.Append(cost);
            sb.Append('\n');
        }

        sb.Append("total ");
        sb.Append(total);
        sb.Append('\n');
        Console.Write(sb.ToString());
    }
}
