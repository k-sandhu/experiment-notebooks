using System.Numerics;
using System.Runtime.CompilerServices;

public static unsafe class Program
{
    public static void Main(string[] args)
    {
        string[] lines = File.ReadAllLines(args[0]);
        string[] hdr = lines[0].Split(' ', StringSplitOptions.RemoveEmptyEntries);
        int H = int.Parse(hdr[0]), W = int.Parse(hdr[1]), S = int.Parse(hdr[2]);
        int P = W + 2;
        int size = (H + 2) * P;
        int[] A = GC.AllocateArray<int>(size, true);
        int[] B = GC.AllocateArray<int>(size, true);
        int[] C = GC.AllocateArray<int>(size, true);
        int[] M = GC.AllocateArray<int>(size, true);
        // 0 wall, 1 open, 2 source
        byte[] kind = new byte[size];
        for (int r = 0; r < H; r++)
        {
            string line = lines[1 + r];
            for (int c = 0; c < W; c++)
            {
                char ch = line[c];
                int idx = (r + 1) * P + c + 1;
                if (ch == '.') kind[idx] = 1;
                else if (ch >= '1' && ch <= '9')
                {
                    kind[idx] = 2;
                    A[idx] = 1000 * (ch - '0');
                    B[idx] = A[idx];
                }
            }
        }
        for (int r = 0; r < H; r++)
        {
            for (int c = 0; c < W; c++)
            {
                int idx = (r + 1) * P + c + 1;
                if (kind[idx] == 1)
                {
                    int cnt = 4;
                    if (kind[idx - P] == 0) cnt++;
                    if (kind[idx + P] == 0) cnt++;
                    if (kind[idx - 1] == 0) cnt++;
                    if (kind[idx + 1] == 0) cnt++;
                    C[idx] = cnt;
                    M[idx] = -1;
                }
            }
        }

        int start = P + 1;
        int end = (H + 1) * P - 1;
        int VL = Vector<int>.Count;

        fixed (int* pa = A, pb = B, pc = C, pm = M)
        {
            int* cur = pa;
            int* nxt = pb;
            for (int s = 0; s < S; s++)
            {
                int i = start;
                for (; i + VL <= end; i += VL)
                {
                    Vector<int> old = Vector.Load(cur + i);
                    Vector<int> sum = Vector.Load(cur + i - P) + Vector.Load(cur + i + P)
                                    + Vector.Load(cur + i - 1) + Vector.Load(cur + i + 1)
                                    + Vector.Load(pc + i) * old;
                    Vector<int> res = Vector.ShiftRightArithmetic(sum, 3);
                    Vector<int> mask = Vector.Load(pm + i);
                    Vector.Store(Vector.ConditionalSelect(mask, res, old), nxt + i);
                }
                for (; i < end; i++)
                {
                    int old = cur[i];
                    if (pm[i] != 0)
                        nxt[i] = (pc[i] * old + cur[i - P] + cur[i + P] + cur[i - 1] + cur[i + 1]) >> 3;
                    else
                        nxt[i] = old;
                }
                int* t = cur; cur = nxt; nxt = t;
            }

            long total = 0, checksum = 0;
            int best = -1, br = 0, bc = 0;
            for (int r = 0; r < H; r++)
            {
                for (int c = 0; c < W; c++)
                {
                    int idx = (r + 1) * P + c + 1;
                    if (kind[idx] == 1)
                    {
                        int v = cur[idx];
                        total += v;
                        checksum += (long)v * ((long)r * W + c + 1);
                        if (v > best) { best = v; br = r; bc = c; }
                    }
                }
            }
            Console.Out.Write("sum " + total + "\nmax " + best + " " + br + " " + bc + "\nchecksum " + checksum + "\n");
        }
    }
}
