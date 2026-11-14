using System.Globalization;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

internal static class Program
{
    private const int BlockSize = 256;
    private ref struct Input
    {
        private ReadOnlySpan<char> text;
        public Input(string path) { text = File.ReadAllText(path); }
        public ReadOnlySpan<char> Token()
        {
            int start = 0;
            while (start < text.Length && text[start] <= ' ') ++start;
            int end = start;
            while (end < text.Length && text[end] > ' ') ++end;
            var token = text.Slice(start, end - start);
            text = text.Slice(end);
            return token;
        }
        public double Number() => double.Parse(Token(), NumberStyles.Float, CultureInfo.InvariantCulture);
    }

    // Compile the hot method directly at its optimized tier, including SIMD.
    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static void Simulate(int n, long steps, double dt, double p,
        double[] x, double[] v, double[] m, double[] k, double[] r, double[] c, double[] f)
    {
        int width = Vector<double>.Count;
        var time = new Vector<double>(dt);
        // The caller supplies n masses, an extra x entry, and one force block.
        // Loop limits establish bounds, avoiding checks on every vector access.
        ref double xp = ref MemoryMarshal.GetArrayDataReference(x);
        ref double vp = ref MemoryMarshal.GetArrayDataReference(v);
        ref double mp = ref MemoryMarshal.GetArrayDataReference(m);
        ref double kp = ref MemoryMarshal.GetArrayDataReference(k);
        ref double rp = ref MemoryMarshal.GetArrayDataReference(r);
        ref double cp = ref MemoryMarshal.GetArrayDataReference(c);
        ref double fp = ref MemoryMarshal.GetArrayDataReference(f);
        for (long step = 0; step < steps; ++step)
        {
            x[n] = x[0] + p;
            double previous = k[n - 1] * ((x[n] - x[n - 1]) - r[n - 1]);
            // Finish a cache-resident block before moving on. Only the old
            // force at its left edge must be carried over from the prior block.
            for (int start = 0; start < n; start += BlockSize)
            {
                int count = Math.Min(BlockSize, n - start);
                int vectorEnd = Vector.IsHardwareAccelerated ? count - count % width : 0;
                f[0] = previous;
                int j = 0;
                for (; j < vectorEnd; j += width)
                {
                    nuint offset = (nuint)(start + j);
                    var stretch = (Vector.LoadUnsafe(ref xp, offset + 1) - Vector.LoadUnsafe(ref xp, offset))
                        - Vector.LoadUnsafe(ref rp, offset);
                    (Vector.LoadUnsafe(ref kp, offset) * stretch).StoreUnsafe(ref fp, (nuint)j + 1);
                }
                for (; j < count; ++j)
                {
                    int i = start + j;
                    f[j + 1] = k[i] * ((x[i + 1] - x[i]) - r[i]);
                }
                previous = f[count];
                j = 0;
                for (; j < vectorEnd; j += width)
                {
                    nuint offset = (nuint)(start + j);
                    var velocity = Vector.LoadUnsafe(ref vp, offset);
                    var force = (Vector.LoadUnsafe(ref fp, (nuint)j + 1) - Vector.LoadUnsafe(ref fp, (nuint)j))
                        - Vector.LoadUnsafe(ref cp, offset) * velocity;
                    velocity = velocity + time * (force / Vector.LoadUnsafe(ref mp, offset));
                    velocity.StoreUnsafe(ref vp, offset);
                    (Vector.LoadUnsafe(ref xp, offset) + time * velocity).StoreUnsafe(ref xp, offset);
                }
                for (; j < count; ++j)
                {
                    int i = start + j;
                    double force = (f[j + 1] - f[j]) - c[i] * v[i];
                    double velocity = v[i] + dt * (force / m[i]);
                    v[i] = velocity;
                    x[i] = x[i] + dt * velocity;
                }
            }
        }
    }

    public static void Main(string[] args)
    {
        var input = new Input(args[0]);
        int n = int.Parse(input.Token(), CultureInfo.InvariantCulture);
        long steps = long.Parse(input.Token(), CultureInfo.InvariantCulture);
        double dt = input.Number(), p = input.Number();
        var x = new double[n + 1]; var v = new double[n]; var m = new double[n];
        var k = new double[n]; var r = new double[n]; var c = new double[n];
        var f = new double[Math.Min(BlockSize, n) + 1];
        for (int i = 0; i < n; ++i)
        {
            x[i] = input.Number(); v[i] = input.Number(); m[i] = input.Number();
            k[i] = input.Number(); r[i] = input.Number(); c[i] = input.Number();
        }
        Simulate(n, steps, dt, p, x, v, m, k, r, c, f);
        x[n] = x[0] + p;
        double kinetic = 0, potential = 0, position = 0;
        int fastest = 0;
        double speed = Math.Abs(v[0]);
        for (int i = 0; i < n; ++i)
        {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
            double stretch = (x[i + 1] - x[i]) - r[i];
            potential += ((0.5 * k[i]) * stretch) * stretch;
            position += x[i];
            if (Math.Abs(v[i]) > speed) { speed = Math.Abs(v[i]); fastest = i; }
        }
        Console.WriteLine("kinetic " + kinetic.ToString("G17", CultureInfo.InvariantCulture));
        Console.WriteLine("potential " + potential.ToString("G17", CultureInfo.InvariantCulture));
        Console.WriteLine("position " + position.ToString("G17", CultureInfo.InvariantCulture));
        Console.WriteLine("fastest " + fastest.ToString(CultureInfo.InvariantCulture));
    }
}
