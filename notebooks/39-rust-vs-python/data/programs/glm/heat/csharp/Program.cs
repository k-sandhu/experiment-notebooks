using System;
using System.Text;

internal static class Program
{
    private static void Main(string[] args)
    {
        byte[] buf = System.IO.File.ReadAllBytes(args[0]);
        int rd = buf.Length;
        int p = 0;

        int H = ParseInt(buf, ref p);
        int W = ParseInt(buf, ref p);
        int S = ParseInt(buf, ref p);

        int n = H * W;
        int[] cur = new int[n];
        int[] nxt = new int[n];
        bool[] wall = new bool[n];
        int[] openList = new int[n];
        int m = 0;

        while (p < rd && buf[p] != (byte)'\n') p++;
        if (p < rd) p++;

        for (int r = 0; r < H; r++)
        {
            for (int c = 0; c < W; c++)
            {
                char ch = (char)buf[p++];
                int i = r * W + c;
                if (ch == '#') wall[i] = true;
                else if (ch >= '1' && ch <= '9') cur[i] = 1000 * (ch - '0');
                else openList[m++] = i;
            }
            while (p < rd && buf[p] != (byte)'\n') p++;
            if (p < rd) p++;
        }

        int[] iup = new int[n];
        int[] idown = new int[n];
        int[] ileft = new int[n];
        int[] iright = new int[n];
        Array.Copy(cur, nxt, n);  // sources keep their fixed value in the swap buffer

        for (int k = 0; k < m; k++)
        {
            int i = openList[k];
            int r = i / W, c = i % W;
            iup[i] = r > 0 && !wall[i - W] ? i - W : i;
            idown[i] = r + 1 < H && !wall[i + W] ? i + W : i;
            ileft[i] = c > 0 && !wall[i - 1] ? i - 1 : i;
            iright[i] = c + 1 < W && !wall[i + 1] ? i + 1 : i;
        }

        for (int s = 0; s < S; s++)
        {
            for (int k = 0; k < m; k++)
            {
                int i = openList[k];
                int v = cur[i];
                nxt[i] = (4 * v + cur[iup[i]] + cur[idown[i]] + cur[ileft[i]] + cur[iright[i]]) >> 3;
            }
            (cur, nxt) = (nxt, cur);
        }

        long sum = 0, chk = 0;
        int mx = -1, mi = 0;
        for (int k = 0; k < m; k++)
        {
            int i = openList[k];
            int v = cur[i];
            sum += v;
            chk += (long)v * (i + 1);
            if (v > mx) { mx = v; mi = i; }
        }

        var sb = new StringBuilder(64);
        sb.Append("sum ").Append(sum).Append('\n')
          .Append("max ").Append(mx).Append(' ').Append(mi / W).Append(' ').Append(mi % W).Append('\n')
          .Append("checksum ").Append(chk).Append('\n');
        using var stdout = Console.OpenStandardOutput();
        stdout.Write(Encoding.ASCII.GetBytes(sb.ToString()));
    }

    private static int ParseInt(byte[] b, ref int p)
    {
        while (b[p] < '0' || b[p] > '9') p++;
        int v = 0;
        while (b[p] >= '0' && b[p] <= '9') { v = v * 10 + (b[p] - '0'); p++; }
        return v;
    }
}
