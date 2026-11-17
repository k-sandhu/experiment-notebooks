using System;
using System.Globalization;
using System.IO;
using System.Text;

// Springs on a ring: explicit time stepping of N masses joined by N springs (see SPEC.md).
//
// Each step runs in two passes over pinned arrays, so the loops are plain pointer loops with
// no bounds checks. The arithmetic keeps the spec's operation order, so the results match the
// reference bit for bit, apart from summation order in the final sums.
internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: solution INPUT_PATH");
            return 1;
        }

        Ring ring = Ring.Read(args[0]);
        int n = ring.N;

        for (long s = 0; s < ring.Steps; s++)
        {
            ring.Step();
        }

        double p = ring.Circumference;
        double[] x = ring.X, v = ring.V, m = ring.M, k = ring.K, r = ring.R;

        double kinetic = 0.0;
        for (int i = 0; i < n; i++)
        {
            kinetic += ((0.5 * m[i]) * v[i]) * v[i];
        }

        double potential = 0.0;
        for (int i = 0; i + 1 < n; i++)
        {
            double s = (x[i + 1] - x[i]) - r[i];
            potential += ((0.5 * k[i]) * s) * s;
        }
        double sLast = ((x[0] + p) - x[n - 1]) - r[n - 1];
        potential += ((0.5 * k[n - 1]) * sLast) * sLast;

        double position = 0.0;
        for (int i = 0; i < n; i++)
        {
            position += x[i];
        }

        int fastest = 0;
        for (int i = 1; i < n; i++)
        {
            if (Math.Abs(v[i]) > Math.Abs(v[fastest]))
            {
                fastest = i;
            }
        }

        var output = new StringBuilder();
        output.Append("kinetic ").Append(kinetic.ToString("e16", CultureInfo.InvariantCulture)).Append('\n');
        output.Append("potential ").Append(potential.ToString("e16", CultureInfo.InvariantCulture)).Append('\n');
        output.Append("position ").Append(position.ToString("e16", CultureInfo.InvariantCulture)).Append('\n');
        output.Append("fastest ").Append(fastest.ToString(CultureInfo.InvariantCulture)).Append('\n');
        Console.Out.Write(output.ToString());
        return 0;
    }
}

internal sealed class Ring
{
    public readonly int N;
    public readonly long Steps;
    public readonly double Dt;
    public readonly double Circumference;
    public readonly double[] X, V, M, K, R, C;
    private readonly double[] F;  // spring forces for the current step

    private Ring(int n, long steps, double dt, double circumference)
    {
        N = n;
        Steps = steps;
        Dt = dt;
        Circumference = circumference;
        X = new double[n];
        V = new double[n];
        M = new double[n];
        K = new double[n];
        R = new double[n];
        C = new double[n];
        F = new double[n];
    }

    public static Ring Read(string path)
    {
        var tokens = new Tokens(File.ReadAllBytes(path));
        int n = int.Parse(tokens.Next(), CultureInfo.InvariantCulture);
        long steps = long.Parse(tokens.Next(), CultureInfo.InvariantCulture);
        double dt = Tokens.ParseDouble(tokens.Next());
        double circumference = Tokens.ParseDouble(tokens.Next());

        var ring = new Ring(n, steps, dt, circumference);
        for (int i = 0; i < n; i++)
        {
            ring.X[i] = Tokens.ParseDouble(tokens.Next());
            ring.V[i] = Tokens.ParseDouble(tokens.Next());
            ring.M[i] = Tokens.ParseDouble(tokens.Next());
            ring.K[i] = Tokens.ParseDouble(tokens.Next());
            ring.R[i] = Tokens.ParseDouble(tokens.Next());
            ring.C[i] = Tokens.ParseDouble(tokens.Next());
        }
        return ring;
    }

    // One time step (SPEC.md, "One time step").
    public unsafe void Step()
    {
        int n = N;
        double p = Circumference;
        double dt = Dt;
        fixed (double* x = X, v = V, m = M, k = K, r = R, c = C, f = F)
        {
            // Pass 1: spring forces from the old positions. Spring n-1 wraps around to mass 0.
            for (int i = 0; i + 1 < n; i++)
            {
                f[i] = k[i] * ((x[i + 1] - x[i]) - r[i]);
            }
            f[n - 1] = k[n - 1] * (((x[0] + p) - x[n - 1]) - r[n - 1]);

            // Pass 2: velocity from the forces (old velocity), then position from the new velocity.
            // Mass 0 uses the force of spring n-1 as its left neighbour.
            v[0] = v[0] + dt * (((f[0] - f[n - 1]) - (c[0] * v[0])) / m[0]);
            for (int i = 1; i < n; i++)
            {
                v[i] = v[i] + dt * (((f[i] - f[i - 1]) - (c[i] * v[i])) / m[i]);
            }
            for (int i = 0; i < n; i++)
            {
                x[i] = x[i] + dt * v[i];
            }
        }
    }
}

// Splits the file on whitespace and parses each token.
internal sealed class Tokens
{
    private readonly byte[] _text;
    private int _pos;

    public Tokens(byte[] text)
    {
        _text = text;
    }

    public string Next()
    {
        while (_pos < _text.Length && _text[_pos] <= ' ')
        {
            _pos++;
        }
        int start = _pos;
        while (_pos < _text.Length && _text[_pos] > ' ')
        {
            _pos++;
        }
        return Encoding.ASCII.GetString(_text, start, _pos - start);
    }

    // Correctly rounded decimal parse (.NET Core 3.0 and later).
    public static double ParseDouble(string token)
    {
        return double.Parse(token, NumberStyles.Float, CultureInfo.InvariantCulture);
    }
}
