using System;
using System.Globalization;
using System.IO;
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

internal static class Program
{
    private sealed class InputReader
    {
        private readonly string text;
        private int position;

        public InputReader(string path)
        {
            text = File.ReadAllText(path);
        }

        public int ReadInt()
        {
            while (position < text.Length && text[position] <= ' ')
                position++;

            int value = 0;
            while (position < text.Length)
            {
                int digit = text[position] - '0';
                if ((uint)digit > 9)
                    break;
                value = value * 10 + digit;
                position++;
            }
            return value;
        }

        public double ReadDouble()
        {
            while (position < text.Length && text[position] <= ' ')
                position++;

            int start = position;
            while (position < text.Length && text[position] > ' ')
                position++;

            return double.Parse(
                text.AsSpan(start, position - start),
                NumberStyles.Float,
                CultureInfo.InvariantCulture);
        }
    }

    public static void Main(string[] args)
    {
        var input = new InputReader(args[0]);

        int n = input.ReadInt();
        int steps = input.ReadInt();
        double dt = input.ReadDouble();
        double circumference = input.ReadDouble();

        var x = new double[n];
        var v = new double[n];
        var m = new double[n];
        var k = new double[n];
        var r = new double[n];
        var c = new double[n];
        var forces = new double[n + 1];

        for (int i = 0; i < n; i++)
        {
            x[i] = input.ReadDouble();
            v[i] = input.ReadDouble();
            m[i] = input.ReadDouble();
            k[i] = input.ReadDouble();
            r[i] = input.ReadDouble();
            c[i] = input.ReadDouble();
        }

        Simulate(n, steps, dt, circumference, x, v, m, k, r, c, forces);

        double kinetic = 0.0;
        double potential = 0.0;
        double position = 0.0;
        int fastest = 0;
        double maximumSpeed = Math.Abs(v[0]);

        for (int i = 0; i < n; i++)
        {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
            position += x[i];

            double speed = Math.Abs(v[i]);
            if (speed > maximumSpeed)
            {
                maximumSpeed = speed;
                fastest = i;
            }

            double stretch = i + 1 < n
                ? (x[i + 1] - x[i]) - r[i]
                : ((x[0] + circumference) - x[i]) - r[i];

            potential += ((0.5 * k[i]) * stretch) * stretch;
        }

        Console.Write(FormattableString.Invariant(
            $"kinetic {kinetic:e16}\npotential {potential:e16}\nposition {position:e16}\nfastest {fastest}\n"));
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static unsafe void Simulate(
        int n, int steps, double dt, double circumference,
        double[] x, double[] v, double[] m,
        double[] k, double[] r, double[] c, double[] forces)
    {
        fixed (double* px = x, pv = v, pm = m,
                       pk = k, pr = r, pc = c, pf = forces)
        {
            int last = n - 1;

            if (Avx.IsSupported)
            {
                Vector256<double> timeStep = Vector256.Create(dt);
                int springVectorEnd = last & ~3;
                int massVectorEnd = n & ~3;

                for (int step = 0; step < steps; step++)
                {
                    int i = 0;

                    for (; i < springVectorEnd; i += 4)
                    {
                        Vector256<double> stretch = Avx.Subtract(
                            Avx.Subtract(
                                Avx.LoadVector256(px + i + 1),
                                Avx.LoadVector256(px + i)),
                            Avx.LoadVector256(pr + i));

                        Avx.Store(pf + i + 1,
                            Avx.Multiply(Avx.LoadVector256(pk + i), stretch));
                    }

                    for (; i < last; i++)
                        pf[i + 1] = pk[i] * ((px[i + 1] - px[i]) - pr[i]);

                    pf[n] = pk[last] *
                        (((px[0] + circumference) - px[last]) - pr[last]);
                    pf[0] = pf[n];

                    i = 0;
                    for (; i < massVectorEnd; i += 4)
                    {
                        Vector256<double> velocity = Avx.LoadVector256(pv + i);
                        Vector256<double> force = Avx.Subtract(
                            Avx.Subtract(
                                Avx.LoadVector256(pf + i + 1),
                                Avx.LoadVector256(pf + i)),
                            Avx.Multiply(Avx.LoadVector256(pc + i), velocity));

                        Vector256<double> newVelocity = Avx.Add(
                            velocity,
                            Avx.Multiply(
                                timeStep,
                                Avx.Divide(force, Avx.LoadVector256(pm + i))));

                        Vector256<double> newPosition = Avx.Add(
                            Avx.LoadVector256(px + i),
                            Avx.Multiply(timeStep, newVelocity));

                        Avx.Store(pv + i, newVelocity);
                        Avx.Store(px + i, newPosition);
                    }

                    for (; i < n; i++)
                    {
                        double force = (pf[i + 1] - pf[i]) - (pc[i] * pv[i]);
                        double velocity = pv[i] + dt * (force / pm[i]);
                        pv[i] = velocity;
                        px[i] = px[i] + dt * velocity;
                    }
                }
            }
            else
            {
                for (int step = 0; step < steps; step++)
                {
                    for (int i = 0; i < last; i++)
                        pf[i + 1] = pk[i] * ((px[i + 1] - px[i]) - pr[i]);

                    pf[n] = pk[last] *
                        (((px[0] + circumference) - px[last]) - pr[last]);
                    pf[0] = pf[n];

                    for (int i = 0; i < n; i++)
                    {
                        double force = (pf[i + 1] - pf[i]) - (pc[i] * pv[i]);
                        double velocity = pv[i] + dt * (force / pm[i]);
                        pv[i] = velocity;
                        px[i] = px[i] + dt * velocity;
                    }
                }
            }
        }
    }
}
