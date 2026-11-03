using System.Threading;

static class Prog
{
    static readonly int[] DX = { 1, -1, 0, 0 };
    static readonly int[] DY = { 0, 0, 1, -1 };

    static void Walk(ulong seed, int j, long L, int B, long[] res)
    {
        ulong state = seed + (ulong)j;
        int x = 0, y = 0;
        long bumps = 0, returns = 0;
        uint span = 2u * (uint)B;
        int[] dx = DX, dy = DY;
        for (long i = 0; i < L; i++)
        {
            state += 0x9E3779B97F4A7C15UL;
            ulong z = state;
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
            int d = (int)(z >> 62);
            int nx = x + dx[d], ny = y + dy[d];
            if ((uint)(nx + B) > span || (uint)(ny + B) > span)
            {
                bumps++;
            }
            else
            {
                x = nx; y = ny;
                if ((x | y) == 0) returns++;
            }
        }
        res[j * 4] = (long)x * x + (long)y * y;
        res[j * 4 + 1] = bumps;
        res[j * 4 + 2] = returns;
        res[j * 4 + 3] = Math.Abs(x) + Math.Abs(y);
    }

    static void Main(string[] args)
    {
        var p = File.ReadAllText(args[0]).Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        int J = int.Parse(p[0]);
        long L = long.Parse(p[1]);
        int B = int.Parse(p[2]);
        ulong seed = ulong.Parse(p[3]);
        int W = Math.Min(Math.Max(1, int.Parse(args[1])), J);
        long[] res = new long[J * 4];
        var th = new Thread[W];
        for (int w = 0; w < W; w++)
        {
            int ww = w;
            th[w] = new Thread(() => { for (int j = ww; j < J; j += W) Walk(seed, j, L, B, res); });
            th[w].Start();
        }
        foreach (var t in th) t.Join();
        long spread = 0, bumps = 0, returns = 0, bestD = -1;
        int bestJ = 0;
        for (int j = 0; j < J; j++)
        {
            spread += res[j * 4]; bumps += res[j * 4 + 1]; returns += res[j * 4 + 2];
            if (res[j * 4 + 3] > bestD) { bestD = res[j * 4 + 3]; bestJ = j; }
        }
        Console.Out.Write($"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {bestJ} {bestD}\n");
    }
}
