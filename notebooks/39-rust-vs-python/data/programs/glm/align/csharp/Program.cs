using System;
using System.IO;

internal static class Program
{
    private static byte[] d;
    private static int pos;
    private static int end;
    private static int tokStart;
    private static int tokLen;

    private static void SkipWs()
    {
        while (pos < end)
        {
            int c = d[pos];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') pos++;
            else break;
        }
    }

    private static long NextInt()
    {
        SkipWs();
        bool neg = false;
        if (pos < end && (d[pos] == '-' || d[pos] == '+'))
        {
            neg = d[pos] == '-';
            pos++;
        }
        long v = 0;
        while (pos < end)
        {
            int c = d[pos];
            if (c >= '0' && c <= '9')
            {
                v = v * 10 + (c - '0');
                pos++;
            }
            else break;
        }
        return neg ? -v : v;
    }

    private static void NextToken()
    {
        SkipWs();
        tokStart = pos;
        while (pos < end)
        {
            int c = d[pos];
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') break;
            pos++;
        }
        tokLen = pos - tokStart;
    }

    private static int[] rowBuf = new int[64];
    private static int[] tIdxBuf = new int[64];
    private static int[] insTBuf = new int[64];

    private static unsafe long Solve(int sStart, int sLen, int tStart, int tLen,
                              int[] idx, int[] ins, int[] del, int[] sub)
    {
        int n = sLen, m = tLen;
        int[] row = rowBuf;
        if (row.Length < m + 1)
        {
            row = new int[Math.Max(m + 1, row.Length * 2)];
            rowBuf = row;
        }
        int[] tIdx = tIdxBuf, insT = insTBuf;
        if (tIdx.Length < m)
        {
            int cap = Math.Max(m, tIdx.Length * 2);
            tIdx = new int[cap];
            tIdxBuf = tIdx;
            insT = new int[cap];
            insTBuf = insT;
        }
        for (int j = 0; j < m; j++)
        {
            int c = idx[d[tStart + j]];
            tIdx[j] = c;
            insT[j] = ins[c];
        }

        long cost;
        fixed (int* rp = row, tp = tIdx, ip = insT, sp = sub)
        {
            int* r = rp;
            int* ti = tp;
            int* it = ip;
            r[0] = 0;
            for (int j = 0; j < m; j++) r[j + 1] = r[j] + it[j];

            for (int i = 0; i < n; i++)
            {
                int si = idx[d[sStart + i]];
                int dl = del[si];
                int* subr = sp + (si << 5);
                int diag = r[0];
                r[0] = diag + dl;
                for (int j = 0; j < m; j++)
                {
                    int up = r[j + 1];
                    int v = up + dl;
                    int x = r[j] + it[j];
                    if (x < v) v = x;
                    x = diag + subr[ti[j]];
                    if (x < v) v = x;
                    r[j + 1] = v;
                    diag = up;
                }
            }
            cost = r[m];
        }
        return cost;
    }

    private static byte[] outBuf = new byte[1 << 16];
    private static int outLen;
    private static readonly byte[] scratch = new byte[20];

    private static void AppendInt(long v)
    {
        if (outLen + 24 > outBuf.Length)
        {
            var nb = new byte[outBuf.Length * 2];
            Buffer.BlockCopy(outBuf, 0, nb, 0, outLen);
            outBuf = nb;
        }
        if (v == 0)
        {
            outBuf[outLen++] = (byte)'0';
            return;
        }
        int k = 20;
        while (v > 0)
        {
            scratch[--k] = (byte)('0' + v % 10);
            v /= 10;
        }
        int cnt = 20 - k;
        Buffer.BlockCopy(scratch, k, outBuf, outLen, cnt);
        outLen += cnt;
    }

    private static int Main(string[] args)
    {
        d = File.ReadAllBytes(args[0]);
        end = d.Length;
        pos = 0;

        NextToken();
        int A = tokLen;
        var idx = new int[256];
        Array.Fill(idx, -1);
        for (int i = 0; i < A; i++) idx[d[tokStart + i]] = i;

        var ins = new int[A];
        var del = new int[A];
        var sub = new int[A << 5]; // stride 32 rows
        for (int i = 0; i < A; i++) ins[i] = (int)NextInt();
        for (int i = 0; i < A; i++) del[i] = (int)NextInt();
        for (int i = 0; i < A; i++)
            for (int j = 0; j < A; j++) sub[(i << 5) + j] = (int)NextInt();

        int P = (int)NextInt();

        outLen = 0;
        long total = 0;
        for (int q = 0; q < P; q++)
        {
            NextToken();
            int sStart = tokStart, n = tokLen;
            NextToken();
            int tStart = tokStart, m = tokLen;
            long cost = Solve(sStart, n, tStart, m, idx, ins, del, sub);
            total += cost;
            AppendInt(cost);
            outBuf[outLen++] = (byte)'\n';
        }
        if (outLen + 32 > outBuf.Length)
        {
            var nb = new byte[outBuf.Length * 2];
            Buffer.BlockCopy(outBuf, 0, nb, 0, outLen);
            outBuf = nb;
        }
        outBuf[outLen++] = (byte)'t';
        outBuf[outLen++] = (byte)'o';
        outBuf[outLen++] = (byte)'t';
        outBuf[outLen++] = (byte)'a';
        outBuf[outLen++] = (byte)'l';
        outBuf[outLen++] = (byte)' ';
        AppendInt(total);
        outBuf[outLen++] = (byte)'\n';

        using Stream stdout = Console.OpenStandardOutput();
        stdout.Write(outBuf, 0, outLen);
        stdout.Flush();
        return 0;
    }
}
