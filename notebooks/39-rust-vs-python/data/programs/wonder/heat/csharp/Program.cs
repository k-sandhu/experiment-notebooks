using System;
using System.IO;

class Program
{
    static void Main(string[] args)
    {
        byte[] buf = File.ReadAllBytes(args[0]);
        int n = buf.Length, p = 0;
        int[] hdr = new int[3];
        for (int k = 0; k < 3; k++)
        {
            while (p < n && (buf[p] < (byte)'0' || buf[p] > (byte)'9')) p++;
            int v = 0;
            while (p < n && buf[p] >= (byte)'0' && buf[p] <= (byte)'9') { v = v * 10 + (buf[p] - (byte)'0'); p++; }
            hdr[k] = v;
        }
        int H = hdr[0], W = hdr[1], S = hdr[2];
        while (p < n && buf[p] != (byte)'\n') p++;
        if (p < n) p++;
        int N = H * W;
        int[] cur = new int[N], nxt = new int[N];
        byte[] kind = new byte[N];
        for (int r = 0; r < H; r++)
        {
            while (p < n && (buf[p] == (byte)'\r' || buf[p] == (byte)'\n')) p++;
            for (int c = 0; c < W; c++)
            {
                byte ch = p < n ? buf[p++] : (byte)'.';
                int i = r * W + c;
                if (ch == (byte)'#') kind[i] = 0;
                else if (ch == (byte)'.') kind[i] = 1;
                else { kind[i] = 2; int v = 1000 * (ch - (byte)'0'); cur[i] = v; nxt[i] = v; }
            }
        }
        buf = null;
        int[] openIdx = new int[N]; int nOpen = 0;
        int[] runStart = new int[N]; int[] runLen = new int[N]; int nRuns = 0;
        int[] eIdx = new int[N]; int[] eU = new int[N]; int[] eD = new int[N]; int[] eL = new int[N]; int[] eR = new int[N]; int nEdge = 0;
        for (int r = 0; r < H; r++)
        {
            int c = 0;
            while (c < W)
            {
                int i = r * W + c;
                if (kind[i] != 1) { c++; continue; }
                bool fast = r > 0 && r + 1 < H && c > 0 && c + 1 < W
                    && kind[i - W] != 0 && kind[i + W] != 0 && kind[i - 1] != 0 && kind[i + 1] != 0;
                if (fast)
                {
                    int start = i, len = 0;
                    while (c < W)
                    {
                        int j = r * W + c;
                        if (kind[j] != 1) break;
                        if (!(r > 0 && r + 1 < H && c > 0 && c + 1 < W && kind[j - W] != 0 && kind[j + W] != 0 && kind[j - 1] != 0 && kind[j + 1] != 0)) break;
                        openIdx[nOpen++] = j; len++; c++;
                    }
                    runStart[nRuns] = start; runLen[nRuns] = len; nRuns++;
                }
                else
                {
                    openIdx[nOpen++] = i;
                    eIdx[nEdge] = i;
                    eU[nEdge] = (r > 0 && kind[i - W] != 0) ? i - W : i;
                    eD[nEdge] = (r + 1 < H && kind[i + W] != 0) ? i + W : i;
                    eL[nEdge] = (c > 0 && kind[i - 1] != 0) ? i - 1 : i;
                    eR[nEdge] = (c + 1 < W && kind[i + 1] != 0) ? i + 1 : i;
                    nEdge++; c++;
                }
            }
        }
        kind = null;
        unsafe
        {
            fixed (int* curBase = cur)
            fixed (int* nxtBase = nxt)
            {
                int* cp = curBase, np = nxtBase;
                for (int step = 0; step < S; step++)
                {
                    for (int ri = 0; ri < nRuns; ri++)
                    {
                        int start = runStart[ri], len = runLen[ri];
                        int* cptr = cp + start;
                        int* nptr = np + start;
                        for (int k = 0; k < len; k++)
                        {
                            int old = cptr[k];
                            nptr[k] = ((old << 2) + cptr[k - W] + cptr[k + W] + cptr[k - 1] + cptr[k + 1]) >> 3;
                        }
                    }
                    for (int k = 0; k < nEdge; k++)
                    {
                        int i = eIdx[k];
                        int old = cp[i];
                        np[i] = ((old << 2) + cp[eU[k]] + cp[eD[k]] + cp[eL[k]] + cp[eR[k]]) >> 3;
                    }
                    int* t = cp; cp = np; np = t;
                }
                // cp points into either cur or nxt; compute offset base for final read
                // Instead of tracking buffer, note parity: after S swaps, current is cp.
                // Copy pointer base identity by checking address.
                long sum = 0, checksum = 0;
                int best = -1, bestIdx = nOpen > 0 ? openIdx[0] : 0;
                for (int k = 0; k < nOpen; k++)
                {
                    int i = openIdx[k], v = cp[i];
                    sum += v; checksum += (long)v * (long)(i + 1);
                    if (v > best) { best = v; bestIdx = i; }
                }
                int br = W != 0 ? bestIdx / W : 0, bc = W != 0 ? bestIdx % W : 0;
                Console.Out.Write("sum " + sum + "\nmax " + best + " " + br + " " + bc + "\nchecksum " + checksum + "\n");
            }
        }
    }
}
