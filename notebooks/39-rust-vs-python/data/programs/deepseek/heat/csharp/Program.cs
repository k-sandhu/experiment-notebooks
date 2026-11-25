using System;
using System.IO;
using System.Text;

class Program
{
    static unsafe int Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        int pos = 0, len = buf.Length;

        int ReadInt()
        {
            while (pos < len && buf[pos] <= (byte)' ') pos++;
            int x = 0;
            while (pos < len && buf[pos] >= (byte)'0' && buf[pos] <= (byte)'9')
                x = x * 10 + (buf[pos++] - '0');
            return x;
        }

        int H = ReadInt();
        int W = ReadInt();
        int S = ReadInt();
        while (pos < len && buf[pos] != (byte)'\n') pos++;
        if (pos < len) pos++;

        int W2 = W + 2;
        int N = (H + 2) * W2;
        int[] cur = new int[N];
        int[] nxt = new int[N];
        byte[] kind = new byte[N]; // 0 wall, 1 open, 2 source
        int[] open = new int[H * W];
        int nOpen = 0;

        fixed (byte* bp = buf)
        {
            for (int r = 0; r < H; r++)
            {
                int rowStart = pos;
                int baseIdx = (r + 1) * W2 + 1;
                for (int c = 0; c < W; c++)
                {
                    byte ch = bp[rowStart + c];
                    int idx = baseIdx + c;
                    if (ch == (byte)'.')
                    {
                        kind[idx] = 1;
                        open[nOpen++] = idx;
                    }
                    else if (ch >= (byte)'1' && ch <= (byte)'9')
                    {
                        kind[idx] = 2;
                        int v = (ch - '0') * 1000;
                        cur[idx] = v;
                        nxt[idx] = v;
                    }
                }
                pos += W;
                while (pos < len && bp[pos] != (byte)'\n') pos++;
                if (pos < len) pos++;
            }
        }

        byte[] coef = new byte[nOpen];
        for (int j = 0; j < nOpen; j++)
        {
            int i = open[j];
            int a = kind[i - W2] != 0 ? 1 : 0;
            int b = kind[i + W2] != 0 ? 1 : 0;
            int l = kind[i - 1] != 0 ? 1 : 0;
            int rr = kind[i + 1] != 0 ? 1 : 0;
            coef[j] = (byte)(4 + (1 - a) + (1 - b) + (1 - l) + (1 - rr));
        }

        int[] cArr = cur, nArr = nxt;
        fixed (int* o = open)
        fixed (byte* cf = coef)
        {
            for (int s = 0; s < S; s++)
            {
                fixed (int* c = cArr)
                fixed (int* n = nArr)
                {
                    for (int j = 0; j < nOpen; j++)
                    {
                        int i = o[j];
                        n[i] = (cf[j] * c[i]
                              + c[i - W2] + c[i + W2] + c[i - 1] + c[i + 1]) >> 3;
                    }
                }
                int[] tmp = cArr; cArr = nArr; nArr = tmp;
            }
        }

        long sum = 0, chk = 0;
        int maxv = -1, bestR = 0, bestC = 0;
        for (int j = 0; j < nOpen; j++)
        {
            int i = open[j];
            int v = cArr[i];
            int r = i / W2 - 1;
            int col = i % W2 - 1;
            sum += v;
            chk += (long)v * ((long)r * W + col + 1);
            if (v > maxv) { maxv = v; bestR = r; bestC = col; }
        }

        var sb = new StringBuilder(80);
        sb.Append("sum ").Append(sum).Append('\n');
        sb.Append("max ").Append(maxv).Append(' ').Append(bestR).Append(' ').Append(bestC).Append('\n');
        sb.Append("checksum ").Append(chk).Append('\n');
        Console.Out.Write(sb.ToString());
        return 0;
    }
}
