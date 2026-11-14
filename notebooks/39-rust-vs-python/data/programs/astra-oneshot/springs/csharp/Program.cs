using System;
using System.Globalization;
using System.IO;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

internal static class Program
{
    private static readonly CultureInfo Culture = CultureInfo.InvariantCulture;

    private sealed class Parser
    {
        private readonly string text;
        private int position;

        public Parser(string path)
        {
            text = File.ReadAllText(path);
        }

        private ReadOnlySpan<char> Next()
        {
            while (position < text.Length && text[position] <= ' ')
                position++;

            int start = position;
            while (position < text.Length && text[position] > ' ')
                position++;

            return text.AsSpan(start, position - start);
        }

        public int Integer() =>
            int.Parse(Next(), NumberStyles.Integer, Culture);

        public double Number() =>
            double.Parse(Next(), NumberStyles.Float, Culture);
    }

    public static void Main(string[] args)
    {
        var input = new Parser(args[0]);
        int n = input.Integer();
        int steps = input.Integer();
        double dt = input.Number();
        double circumference = input.Number();

        var x = new double[n];
        var v = new double[n];
        var m = new double[n];
        var k = new double[n];
        var r = new double[n];
        var c = new double[n];

        for (int i = 0; i < n; i++)
        {
            x[i] = input.Number();
            v[i] = input.Number();
            m[i] = input.Number();
            k[i] = input.Number();
            r[i] = input.Number();
            c[i] = input.Number();
        }

        Simulate(n, steps, dt, circumference, x, v, m, k, r, c);

        double kinetic = 0.0;
        double potential = 0.0;
        double position = 0.0;
        double maximumSpeed = Math.Abs(v[0]);
        int fastest = 0;

        for (int i = 0; i < n; i++)
        {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
            position += x[i];

            double stretch = i < n - 1
                ? (x[i + 1] - x[i]) - r[i]
                : ((x[0] + circumference) - x[i]) - r[i];

            potential += ((0.5 * k[i]) * stretch) * stretch;

            double speed = Math.Abs(v[i]);
            if (speed > maximumSpeed)
            {
                maximumSpeed = speed;
                fastest = i;
            }
        }

        Console.WriteLine("kinetic " + kinetic.ToString("E16", Culture));
        Console.WriteLine("potential " + potential.ToString("E16", Culture));
        Console.WriteLine("position " + position.ToString("E16", Culture));
        Console.WriteLine("fastest " + fastest.ToString(Culture));
    }

    private static unsafe void Simulate(
        int n, int steps, double dt, double circumference,
        double[] x, double[] v, double[] m,
        double[] k, double[] r, double[] c)
    {
        // force[i + 1] is spring i's force; force[0] duplicates the last.
        var force = new double[n + 1];

        fixed (double* px = x, pv = v, pm = m,
                       pk = k, pr = r, pc = c, pf = force)
        {
            Vector256<double> timeStep = Vector256.Create(dt);
            int last = n - 1;

            for (int step = 0; step < steps; step++)
            {
                int i = 0;

                if (Avx.IsSupported)
                {
                    for (; i <= n - 5; i += 4)
                    {
                        var stretch = Avx.Subtract(
                            Avx.Subtract(
                                Avx.LoadVector256(px + i + 1),
                                Avx.LoadVector256(px + i)),
                            Avx.LoadVector256(pr + i));

                        Avx.Store(pf + i + 1,
                            Avx.Multiply(
                                Avx.LoadVector256(pk + i), stretch));
                    }
                }

                for (; i < last; i++)
                    pf[i + 1] = pk[i] * ((px[i + 1] - px[i]) - pr[i]);

                pf[n] = pk[last] *
                    (((px[0] + circumference) - px[last]) - pr[last]);
                pf[0] = pf[n];

                i = 0;

                if (Avx.IsSupported)
                {
                    for (; i <= n - 4; i += 4)
                    {
                        var velocity = Avx.LoadVector256(pv + i);

                        var netForce = Avx.Subtract(
                            Avx.Subtract(
                                Avx.LoadVector256(pf + i + 1),
                                Avx.LoadVector256(pf + i)),
                            Avx.Multiply(
                                Avx.LoadVector256(pc + i), velocity));

                        var acceleration = Avx.Divide(
                            netForce, Avx.LoadVector256(pm + i));

                        velocity = Avx.Add(
                            velocity, Avx.Multiply(timeStep, acceleration));

                        var position = Avx.Add(
                            Avx.LoadVector256(px + i),
                            Avx.Multiply(timeStep, velocity));

                        Avx.Store(pv + i, velocity);
                        Avx.Store(px + i, position);
                    }
                }

                for (; i < n; i++)
                {
                    double netForce = (pf[i + 1] - pf[i]) - (pc[i] * pv[i]);
                    double velocity = pv[i] + dt * (netForce / pm[i]);
                    pv[i] = velocity;
                    px[i] = px[i] + dt * velocity;
                }
            }
        }
    }
}
