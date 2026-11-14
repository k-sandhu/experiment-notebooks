using System;
using System.IO;
using System.Text;

internal static class Program
{
    private static readonly int[] Map = new int[256];
    private static int[] Insert;
    private static int[] Delete;
    private static int[] Substitute;
    private static int[] Transposed;
    private static int AlphabetSize;

    private static void Main(string[] args)
    {
        var reader = new InputReader(File.ReadAllBytes(args[0]));
        ReadOnlySpan<byte> alphabet = reader.NextToken();
        AlphabetSize = alphabet.Length;

        for (int i = 0; i < AlphabetSize; i++)
            Map[alphabet[i]] = i;

        Insert = new int[AlphabetSize];
        Delete = new int[AlphabetSize];
        Substitute = new int[AlphabetSize * AlphabetSize];
        Transposed = new int[Substitute.Length];

        for (int i = 0; i < AlphabetSize; i++)
            Insert[i] = reader.ReadInt();

        for (int i = 0; i < AlphabetSize; i++)
            Delete[i] = reader.ReadInt();

        for (int i = 0; i < AlphabetSize; i++)
        {
            for (int j = 0; j < AlphabetSize; j++)
            {
                int value = reader.ReadInt();
                Substitute[i * AlphabetSize + j] = value;
                Transposed[j * AlphabetSize + i] = value;
            }
        }

        int pairs = reader.ReadInt();
        var output = new StringBuilder();
        long total = 0;

        for (int p = 0; p < pairs; p++)
        {
            ReadOnlySpan<byte> s = reader.NextToken();
            ReadOnlySpan<byte> t = reader.NextToken();
            long cost = Calculate(s, t);
            total += cost;
            output.Append(cost).Append('\n');
        }

        output.Append("total ").Append(total).Append('\n');
        Console.Out.Write(output.ToString());
    }

    private static unsafe long Calculate(ReadOnlySpan<byte> s, ReadOnlySpan<byte> t)
    {
        if (s.SequenceEqual(t))
            return 0;

        int[] insertion = Insert;
        int[] deletion = Delete;
        int[] substitution = Substitute;

        if (t.Length > s.Length)
        {
            ReadOnlySpan<byte> temporary = s;
            s = t;
            t = temporary;

            insertion = Delete;
            deletion = Insert;
            substitution = Transposed;
        }

        int n = s.Length;
        int m = t.Length;
        int[] target = new int[m];
        int[] targetInsertion = new int[m];

        long bound = 0;
        for (int j = 0; j < m; j++)
        {
            int letter = Map[t[j]];
            target[j] = letter;
            int cost = insertion[letter];
            targetInsertion[j] = cost;
            bound += cost;
        }

        for (int i = 0; i < n; i++)
            bound += deletion[Map[s[i]]];

        if (bound == 0)
            return 0;

        fixed (int* targetPointer = target)
        fixed (int* insertionPointer = targetInsertion)
        fixed (int* substitutionPointer = substitution)
        {
            // Every DP entry is bounded by deleting and inserting its prefixes.
            // Reserve 1000 for the candidate addition before taking the minimum.
            if (bound <= int.MaxValue - 1000L)
            {
                int[] row = new int[m + 1];
                fixed (int* dp = row)
                {
                    for (int j = 0; j < m; j++)
                        dp[j + 1] = dp[j] + insertionPointer[j];

                    for (int i = 0; i < n; i++)
                    {
                        int letter = Map[s[i]];
                        int deleteCost = deletion[letter];
                        int* sub = substitutionPointer + letter * AlphabetSize;

                        int diagonal = dp[0];
                        int left = diagonal + deleteCost;
                        dp[0] = left;

                        for (int j = 0; j < m; j++)
                        {
                            int above = dp[j + 1];
                            int best = Math.Min(
                                above + deleteCost,
                                left + insertionPointer[j]);
                            best = Math.Min(best, diagonal + sub[targetPointer[j]]);
                            dp[j + 1] = best;
                            diagonal = above;
                            left = best;
                        }
                    }

                    return dp[m];
                }
            }
            else
            {
                long[] row = new long[m + 1];
                fixed (long* dp = row)
                {
                    for (int j = 0; j < m; j++)
                        dp[j + 1] = dp[j] + insertionPointer[j];

                    for (int i = 0; i < n; i++)
                    {
                        int letter = Map[s[i]];
                        int deleteCost = deletion[letter];
                        int* sub = substitutionPointer + letter * AlphabetSize;

                        long diagonal = dp[0];
                        long left = diagonal + deleteCost;
                        dp[0] = left;

                        for (int j = 0; j < m; j++)
                        {
                            long above = dp[j + 1];
                            long best = Math.Min(
                                above + deleteCost,
                                left + insertionPointer[j]);
                            best = Math.Min(best, diagonal + sub[targetPointer[j]]);
                            dp[j + 1] = best;
                            diagonal = above;
                            left = best;
                        }
                    }

                    return dp[m];
                }
            }
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
            int p = position;
            while (p < data.Length && data[p] <= 32)
                p++;

            int start = p;
            while (p < data.Length && data[p] > 32)
                p++;

            position = p;
            return data.AsSpan(start, p - start);
        }

        public int ReadInt()
        {
            int p = position;
            while (p < data.Length && data[p] <= 32)
                p++;

            int value = 0;
            while (p < data.Length && data[p] >= (byte)'0' && data[p] <= (byte)'9')
            {
                value = value * 10 + data[p] - (byte)'0';
                p++;
            }

            position = p;
            return value;
        }
    }
}
