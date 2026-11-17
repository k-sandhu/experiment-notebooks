using System;
using System.IO;
using System.Text;

internal static class Program
{
    private static void Main(string[] args)
    {
        var reader = new InputReader(File.ReadAllBytes(args[0]));
        ReadOnlySpan<byte> alphabet = reader.NextToken();
        int a = alphabet.Length;

        int[] insertion = new int[26];
        int[] deletion = new int[26];
        int[] substitution = new int[26 * 26];

        for (int i = 0; i < a; i++)
            insertion[alphabet[i] - 'A'] = reader.NextInt();

        for (int i = 0; i < a; i++)
            deletion[alphabet[i] - 'A'] = reader.NextInt();

        for (int i = 0; i < a; i++)
        {
            int offset = (alphabet[i] - 'A') * 26;
            for (int j = 0; j < a; j++)
                substitution[offset + alphabet[j] - 'A'] = reader.NextInt();
        }

        int pairs = reader.NextInt();
        var output = new StringBuilder();
        long total = 0;

        int[] row32 = Array.Empty<int>();
        long[] row64 = Array.Empty<long>();
        int[] targetInsertion = Array.Empty<int>();

        for (int p = 0; p < pairs; p++)
        {
            ReadOnlySpan<byte> source = reader.NextToken();
            ReadOnlySpan<byte> target = reader.NextToken();

            long cost;
            if (source.SequenceEqual(target))
            {
                cost = 0;
            }
            else
            {
                int m = target.Length;
                if (targetInsertion.Length < m)
                    targetInsertion = new int[m];

                for (int j = 0; j < m; j++)
                    targetInsertion[j] = insertion[target[j] - 'A'];

                if (1000L * (source.Length + (long)m) <= int.MaxValue - 1000L)
                {
                    if (row32.Length < m + 1)
                        row32 = new int[m + 1];

                    cost = Distance32(source, target, targetInsertion,
                        deletion, substitution, row32);
                }
                else
                {
                    if (row64.Length < m + 1)
                        row64 = new long[m + 1];

                    cost = Distance64(source, target, targetInsertion,
                        deletion, substitution, row64);
                }
            }

            total += cost;
            output.Append(cost).Append('\n');
        }

        output.Append("total ").Append(total).Append('\n');
        Console.Write(output.ToString());
    }

    private static unsafe int Distance32(
        ReadOnlySpan<byte> source,
        ReadOnlySpan<byte> target,
        int[] targetInsertion,
        int[] deletion,
        int[] substitution,
        int[] row)
    {
        int n = source.Length;
        int m = target.Length;

        fixed (byte* ps = source, pt = target)
        fixed (int* pins = targetInsertion, pdel = deletion,
                    psub = substitution, dp = row)
        {
            dp[0] = 0;
            for (int j = 0; j < m; j++)
                dp[j + 1] = dp[j] + pins[j];

            for (int i = 0; i < n; i++)
            {
                int letter = ps[i] - 'A';
                int deleteCost = pdel[letter];
                int* substitutions = psub + letter * 26;

                int diagonal = dp[0];
                int left = diagonal + deleteCost;
                dp[0] = left;

                for (int j = 0; j < m; j++)
                {
                    int above = dp[j + 1];
                    int value = diagonal + substitutions[pt[j] - 'A'];
                    value = Math.Min(value, above + deleteCost);
                    left = Math.Min(value, left + pins[j]);
                    dp[j + 1] = left;
                    diagonal = above;
                }
            }

            return dp[m];
        }
    }

    private static unsafe long Distance64(
        ReadOnlySpan<byte> source,
        ReadOnlySpan<byte> target,
        int[] targetInsertion,
        int[] deletion,
        int[] substitution,
        long[] row)
    {
        int n = source.Length;
        int m = target.Length;

        fixed (byte* ps = source, pt = target)
        fixed (int* pins = targetInsertion, pdel = deletion, psub = substitution)
        fixed (long* dp = row)
        {
            dp[0] = 0;
            for (int j = 0; j < m; j++)
                dp[j + 1] = dp[j] + pins[j];

            for (int i = 0; i < n; i++)
            {
                int letter = ps[i] - 'A';
                int deleteCost = pdel[letter];
                int* substitutions = psub + letter * 26;

                long diagonal = dp[0];
                long left = diagonal + deleteCost;
                dp[0] = left;

                for (int j = 0; j < m; j++)
                {
                    long above = dp[j + 1];
                    long value = diagonal + substitutions[pt[j] - 'A'];
                    value = Math.Min(value, above + deleteCost);
                    left = Math.Min(value, left + pins[j]);
                    dp[j + 1] = left;
                    diagonal = above;
                }
            }

            return dp[m];
        }
    }

    private sealed class InputReader
    {
        private readonly byte[] data;
        private int position;

        public InputReader(byte[] data)
        {
            this.data = data;
        }

        public ReadOnlySpan<byte> NextToken()
        {
            while (position < data.Length && data[position] <= 32)
                position++;

            int start = position;
            while (position < data.Length && data[position] > 32)
                position++;

            return data.AsSpan(start, position - start);
        }

        public int NextInt()
        {
            while (position < data.Length && data[position] <= 32)
                position++;

            int value = 0;
            while (position < data.Length)
            {
                uint digit = (uint)(data[position] - '0');
                if (digit > 9)
                    break;

                value = value * 10 + (int)digit;
                position++;
            }

            return value;
        }
    }
}
