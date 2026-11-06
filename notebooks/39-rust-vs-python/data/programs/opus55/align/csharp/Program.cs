// Weighted edit distance for many pairs.
//
// With Q[j] = sum of column (insert) costs of C[1..j], the kernels store E[i][j] = D[i][j] - Q[j]:
//   E[i][j] = min(E[i-1][j] + rc, E[i-1][j-1] + adj[j], E[i][j-1]),  adj[j] = M[r][C_j] - cc[C_j]
// The horizontal term becomes a plain running minimum, so the vertical part vectorizes
// (SSE4.1 path: vertical step in SIMD + in-register prefix minimum carried across blocks).
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

static unsafe class Program
{
    static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int p = 0, len = data.Length;

        Span<sbyte> idx = stackalloc sbyte[256];
        idx.Fill(-1);
        int A = 0;
        while (p < len && data[p] >= 'A' && data[p] <= 'Z') idx[data[p++]] = (sbyte)A++;

        long ReadInt()
        {
            while (p < len && (data[p] < '0' || data[p] > '9')) p++;
            long v = 0;
            while (p < len && data[p] >= '0' && data[p] <= '9') v = v * 10 + (data[p++] - '0');
            return v;
        }

        int[] insC = new int[26], delC = new int[26];
        int[] subM = new int[26 * 26], subT = new int[26 * 26];
        for (int i = 0; i < A; i++) insC[i] = (int)ReadInt();
        for (int i = 0; i < A; i++) delC[i] = (int)ReadInt();
        for (int i = 0; i < A; i++)
            for (int j = 0; j < A; j++)
            {
                int v = (int)ReadInt();
                subM[i * 26 + j] = v;
                subT[j * 26 + i] = v;
            }
        int P = (int)ReadInt();

        byte[] sBuf = new byte[16], tBuf = new byte[16];
        int[] adjStore = new int[16], rowA = new int[16], rowB = new int[16];
        int[] adjOff = new int[26];
        var sb = new System.Text.StringBuilder(P * 12 + 32);
        long total = 0;

        int ReadWord(ref byte[] w, ReadOnlySpan<sbyte> map)
        {
            while (p < len && (data[p] < 'A' || data[p] > 'Z')) p++;
            int q = p;
            while (p < len && data[p] >= 'A' && data[p] <= 'Z') p++;
            int n = p - q;
            if (w.Length < n) w = new byte[Math.Max(n, w.Length * 2)];
            for (int k = 0; k < n; k++) w[k] = (byte)map[data[q + k]];
            return n;
        }

        Span<bool> used = stackalloc bool[26];
        for (int k = 0; k < P; k++)
        {
            int ns = ReadWord(ref sBuf, idx);
            int nt = ReadWord(ref tBuf, idx);

            // Put the longer string on the inner (column) axis: transposing swaps insert/delete
            // and transposes the substitution table, leaving D[n][m] unchanged.
            byte[] R, C;
            int n, m;
            int[] rc, cc, M;
            if (ns <= nt) { R = sBuf; n = ns; C = tBuf; m = nt; rc = delC; cc = insC; M = subM; }
            else { R = tBuf; n = nt; C = sBuf; m = ns; rc = insC; cc = delC; M = subT; }

            used.Clear();
            int nUsed = 0;
            for (int i = 0; i < n; i++) if (!used[R[i]]) { used[R[i]] = true; nUsed++; }
            long Q = 0;
            for (int j = 0; j < m; j++) Q += cc[C[j]];

            int stride = ((m + 1) + 8) & ~3;
            if (adjStore.Length < stride * nUsed) adjStore = new int[Math.Max(stride * nUsed, adjStore.Length * 2)];
            int slot = 0;
            for (int a = 0; a < A; a++)
            {
                if (!used[a]) continue;
                int off = stride * slot++;
                adjOff[a] = off;
                BuildAdj(adjStore.AsSpan(off, stride), M.AsSpan(a * 26, 26), cc, C.AsSpan(0, m));
            }

            long cost;
            if ((long)(n + m + 4) * 1000 < (1L << 30))
            {
                if (rowA.Length < stride) { rowA = new int[stride]; rowB = new int[stride]; }
                int e;
                fixed (byte* pR = R)
                fixed (int* pRc = rc, pAdj = adjStore, pA = rowA, pB = rowB, pOff = adjOff)
                {
                    e = Sse41.IsSupported
                        ? DpSse(pR, n, m, pRc, pAdj, pOff, pA, pB)
                        : DpScalar(pR, n, m, pRc, pAdj, pOff, pA);
                }
                cost = e + Q;
            }
            else
            {
                cost = Dp64(R, n, m, rc, adjStore, adjOff) + Q;
            }
            total += cost;
            sb.Append(cost).Append('\n');
        }
        sb.Append("total ").Append(total).Append('\n');

        string s = sb.ToString();
        byte[] outBytes = new byte[s.Length];
        for (int i = 0; i < s.Length; i++) outBytes[i] = (byte)s[i];
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(outBytes, 0, outBytes.Length);
        return 0;
    }

    static void BuildAdj(Span<int> r, ReadOnlySpan<int> Ma, int[] cc, ReadOnlySpan<byte> C)
    {
        r.Clear();
        for (int j = 0; j < C.Length; j++)
        {
            int c = C[j];
            r[j + 1] = Ma[c] - cc[c];
        }
    }

    // Two row buffers; vector blocks cover j = 1..mv (m rounded up to 4), reading prev[j-1..j+3].
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static int DpSse(byte* R, int n, int m, int* rc, int* adjBase, int* adjOff, int* prev, int* cur)
    {
        int mv = (m + 3) & ~3;
        for (int j = 0; j <= mv; j++) prev[j] = 0;
        Vector128<int> INF = Vector128.Create(0x3fffffff);
        for (int i = 0; i < n; i++)
        {
            int a = R[i];
            int d = rc[a];
            int* adj = adjBase + adjOff[a];
            Vector128<int> dv = Vector128.Create(d);
            int c0 = prev[0] + d;
            cur[0] = c0;
            Vector128<int> carry = Vector128.Create(c0);
            for (int j = 1; j <= mv; j += 4)
            {
                Vector128<int> up = Sse2.LoadVector128(prev + j);
                Vector128<int> dg = Sse2.LoadVector128(prev + j - 1);
                Vector128<int> ad = Sse2.LoadVector128(adj + j);
                Vector128<int> x = Sse41.Min(Sse2.Add(up, dv), Sse2.Add(dg, ad));
                // in-register prefix min, shifting in +INF
                x = Sse41.Min(x, Ssse3.AlignRight(x.AsByte(), INF.AsByte(), 12).AsInt32());
                x = Sse41.Min(x, Ssse3.AlignRight(x.AsByte(), INF.AsByte(), 8).AsInt32());
                x = Sse41.Min(x, carry);
                Sse2.Store(cur + j, x);
                carry = Sse2.Shuffle(x, 0xFF);
            }
            int* t = prev; prev = cur; cur = t;
        }
        return prev[m];
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    static int DpScalar(byte* R, int n, int m, int* rc, int* adjBase, int* adjOff, int* row)
    {
        for (int j = 0; j <= m; j++) row[j] = 0;
        for (int i = 0; i < n; i++)
        {
            int a = R[i];
            int d = rc[a];
            int* adj = adjBase + adjOff[a];
            int diag = row[0];
            int left = diag + d;
            row[0] = left;
            for (int j = 1; j <= m; j++)
            {
                int up = row[j];
                int v = Math.Min(Math.Min(up + d, diag + adj[j]), left);
                row[j] = v;
                left = v;
                diag = up;
            }
        }
        return row[m];
    }

    // int64 fallback for extremely long strings, where values could exceed int32.
    static long Dp64(byte[] R, int n, int m, int[] rc, int[] adjStore, int[] adjOff)
    {
        long[] row = new long[m + 1];
        for (int i = 0; i < n; i++)
        {
            int a = R[i];
            long d = rc[a];
            int off = adjOff[a];
            long diag = row[0];
            long left = diag + d;
            row[0] = left;
            for (int j = 1; j <= m; j++)
            {
                long up = row[j];
                long v = Math.Min(Math.Min(up + d, diag + adjStore[off + j]), left);
                row[j] = v;
                left = v;
                diag = up;
            }
        }
        return row[m];
    }
}
