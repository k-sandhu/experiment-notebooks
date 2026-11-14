using System;
using System.IO;
using System.Runtime.Intrinsics;

static unsafe class Program
{
    static int ReadInt(byte[] d, ref int p)
    {
        while (p < d.Length && (d[p] < (byte)'0' || d[p] > (byte)'9')) p++;
        int v = 0;
        while (p < d.Length && d[p] >= (byte)'0' && d[p] <= (byte)'9')
        {
            v = v * 10 + (d[p] - '0');
            p++;
        }
        return v;
    }

    static void Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int pos = 0;
        int H = ReadInt(data, ref pos);
        int W = ReadInt(data, ref pos);
        int S = ReadInt(data, ref pos);

        // Padded layout: one blank row above/below and one blank column left/right.
        int P = W + 2;
        int total = (H + 2) * P;

        // ty: 0 = wall/outside, 1 = open, 2 = source
        byte[] ty = new byte[total];
        int[] A = new int[total];

        for (int r = 0; r < H; r++)
        {
            while (pos < data.Length && data[pos] <= 32) pos++;
            int rowBase = (r + 1) * P + 1;
            for (int c = 0; c < W; c++)
            {
                byte ch = pos < data.Length ? data[pos] : (byte)'#';
                pos++;
                int idx = rowBase + c;
                if (ch == '.')
                {
                    ty[idx] = 1;
                }
                else if (ch >= '1' && ch <= '9')
                {
                    ty[idx] = 2;
                    A[idx] = 1000 * (ch - '0');
                }
                // '#' (or anything else): wall, stays 0
            }
        }

        // For an open cell: new = ((4 + b) * old + sum of open/source neighbours) / 8,
        // where b = number of wall/outside neighbours. Walls store 0, so they add nothing.
        int[] K = new int[total];
        int[] M = new int[total];
        for (int r = 1; r <= H; r++)
        {
            int rowBase = r * P;
            for (int c = 1; c <= W; c++)
            {
                int idx = rowBase + c;
                if (ty[idx] == 1)
                {
                    int b = (ty[idx - 1] == 0 ? 1 : 0) + (ty[idx + 1] == 0 ? 1 : 0)
                          + (ty[idx - P] == 0 ? 1 : 0) + (ty[idx + P] == 0 ? 1 : 0);
                    K[idx] = 4 + b;
                    M[idx] = -1;
                }
            }
        }

        int[] B = (int[])A.Clone();

        long T = 0;
        long Ksum = 0;
        int best = -1, bR = 0, bC = 0;

        fixed (int* pA = A, pB = B, pK = K, pM = M)
        {
            int* cur = pA;
            int* nxt = pB;
            int end = total - P;

            for (int s = 0; s < S; s++)
            {
                int i = P;
                int vEnd = end - 8; // vector loop while i + 8 <= end
                for (; i <= vEnd; i += 8)
                {
                    Vector256<int> cv = Vector256.Load(cur + i);
                    Vector256<int> sum = Vector256.Load(cur + i - 1)
                                       + Vector256.Load(cur + i + 1)
                                       + Vector256.Load(cur + i - P)
                                       + Vector256.Load(cur + i + P);
                    Vector256<int> kv = Vector256.Load(pK + i);
                    Vector256<int> v = Vector256.ShiftRightLogical(sum + kv * cv, 3);
                    Vector256<int> mv = Vector256.Load(pM + i);
                    Vector256.ConditionalSelect(mv, v, cv).Store(nxt + i);
                }
                for (; i < end; i++)
                {
                    int cvs = cur[i];
                    int sm = cur[i - 1] + cur[i + 1] + cur[i - P] + cur[i + P];
                    nxt[i] = pM[i] != 0 ? (sm + pK[i] * cvs) >> 3 : cvs;
                }
                (cur, nxt) = (nxt, cur);
            }

            for (int r = 0; r < H; r++)
            {
                int rowBase = (r + 1) * P + 1;
                for (int c = 0; c < W; c++)
                {
                    int idx = rowBase + c;
                    if (pM[idx] != 0)
                    {
                        int v = cur[idx];
                        T += v;
                        if (v > best)
                        {
                            best = v;
                            bR = r;
                            bC = c;
                        }
                        Ksum += (long)v * ((long)r * W + c + 1);
                    }
                }
            }
        }

        Console.Out.Write($"sum {T}\nmax {best} {bR} {bC}\nchecksum {Ksum}\n");
    }
}
