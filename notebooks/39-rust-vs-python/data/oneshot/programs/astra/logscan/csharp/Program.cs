using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;

internal static class Program
{
    private static void Main(string[] args)
    {
        var scanner = new Scanner();
        long lines = 0;
        long malformed = 0;

        using (var file = new FileStream(
            args[0], FileMode.Open, FileAccess.Read, FileShare.Read,
            1, FileOptions.SequentialScan))
        {
            byte[] buffer = new byte[1 << 20];
            int retained = 0;

            while (true)
            {
                if (retained == buffer.Length)
                    Array.Resize(ref buffer, checked(buffer.Length * 2));

                int read = file.Read(buffer, retained, buffer.Length - retained);
                if (read == 0)
                    break;

                int end = retained + read;
                int start = 0;

                while (start < end)
                {
                    int length = buffer.AsSpan(start, end - start).IndexOf((byte)'\n');
                    if (length < 0)
                        break;

                    lines++;
                    if (!scanner.ProcessLine(buffer.AsSpan(start, length)))
                        malformed++;

                    start += length + 1;
                }

                retained = end - start;
                if (retained != 0)
                    Buffer.BlockCopy(buffer, start, buffer, 0, retained);
            }
        }

        var output = new StringBuilder();
        output.Append("lines ").Append(lines).Append('\n');
        output.Append("malformed ").Append(malformed).Append('\n');

        for (int i = 0; i < scanner.Status.Length; i++)
        {
            if (scanner.Status[i] != 0)
            {
                output.Append("status ").Append(i).Append("xx ")
                    .Append(scanner.Status[i]).Append('\n');
            }
        }

        foreach (Entry entry in scanner.GetTopEntries())
            AppendEntry(output, entry);

        Console.Out.Write(output.ToString());
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool IsDigit(byte value) => (uint)(value - '0') <= 9;

    private sealed class Entry
    {
        internal readonly byte[] Key;
        internal readonly uint Hash;
        internal Entry Next;

        internal ulong First;
        internal ulong[] Values;
        internal int SmallCount;
        internal List<BigInteger> Large;

        internal long Count => (long)SmallCount + (Large?.Count ?? 0);

        internal Entry(byte[] key, uint hash, Entry next)
        {
            Key = key;
            Hash = hash;
            Next = next;
        }

        internal void Add(ulong value)
        {
            int count = SmallCount;

            if (count == 0)
            {
                First = value;
            }
            else
            {
                if (Values == null)
                {
                    Values = new ulong[4];
                    Values[0] = First;
                }
                else if (count == Values.Length)
                {
                    Array.Resize(ref Values, checked(Values.Length * 2));
                }

                Values[count] = value;
            }

            SmallCount = count + 1;
        }

        internal void Add(BigInteger value)
        {
            (Large ??= new List<BigInteger>()).Add(value);
        }
    }

    private sealed class Scanner
    {
        internal readonly long[] Status = new long[10];

        private static readonly bool[] PathCharacters = CreatePathCharacters();
        private Entry[] buckets = new Entry[1024];
        private byte[] keyBuffer = new byte[256];
        private int entryCount;

        private static bool[] CreatePathCharacters()
        {
            var result = new bool[256];

            for (int c = 'a'; c <= 'z'; c++) result[c] = true;
            for (int c = 'A'; c <= 'Z'; c++) result[c] = true;
            for (int c = '0'; c <= '9'; c++) result[c] = true;

            result['/'] = true;
            result['_'] = true;
            result['-'] = true;
            return result;
        }

        internal bool ProcessLine(ReadOnlySpan<byte> line)
        {
            int n = line.Length;
            if (n < 50)
                return false;

            if (line[4] != '-' || line[7] != '-' || line[10] != 'T' ||
                line[13] != ':' || line[16] != ':' || line[19] != '.' ||
                line[23] != 'Z' || line[24] != ' ')
                return false;

            if (!IsDigit(line[0]) || !IsDigit(line[1]) ||
                !IsDigit(line[2]) || !IsDigit(line[3]) ||
                !IsDigit(line[5]) || !IsDigit(line[6]) ||
                !IsDigit(line[8]) || !IsDigit(line[9]) ||
                !IsDigit(line[11]) || !IsDigit(line[12]) ||
                !IsDigit(line[14]) || !IsDigit(line[15]) ||
                !IsDigit(line[17]) || !IsDigit(line[18]) ||
                !IsDigit(line[20]) || !IsDigit(line[21]) ||
                !IsDigit(line[22]))
                return false;

            int i = 25;
            int start = i;

            while (i < n && (uint)(line[i] - 'a') <= 25)
                i++;

            if (i == start || i >= n || line[i] != '-')
                return false;

            start = ++i;
            while (i < n && IsDigit(line[i]))
                i++;

            if (i == start || i >= n || line[i] != ' ')
                return false;

            i++;
            ReadOnlySpan<byte> method = line.Slice(i);

            if (method.StartsWith("GET "u8))
                i += 4;
            else if (method.StartsWith("POST "u8))
                i += 5;
            else if (method.StartsWith("PUT "u8))
                i += 4;
            else if (method.StartsWith("DELETE "u8))
                i += 7;
            else if (method.StartsWith("PATCH "u8))
                i += 6;
            else
                return false;

            if (i >= n || line[i] != '/')
                return false;

            int pathStart = i++;
            while (i < n && PathCharacters[line[i]])
                i++;

            int pathLength = i - pathStart;

            if (i < n && line[i] == '?')
            {
                int queryLength = line.Slice(i + 1).IndexOf((byte)' ');
                if (queryLength < 0)
                    return false;
                i += queryLength + 1;
            }

            if (i >= n || line[i] != ' ')
                return false;

            i++;
            if (n - i < 4 ||
                !IsDigit(line[i]) || !IsDigit(line[i + 1]) ||
                !IsDigit(line[i + 2]) || line[i + 3] != ' ')
                return false;

            int status = line[i] - '0';
            i += 4;

            start = i;
            while (i < n && IsDigit(line[i]))
                i++;

            if (i == start || n - i < 2 ||
                line[i] != 'B' || line[i + 1] != ' ')
                return false;

            i += 2;
            int latencyStart = i;

            while (i < n && IsDigit(line[i]))
                i++;

            int latencyDigits = i - latencyStart;

            if (latencyDigits == 0 || n - i < 7 ||
                line[i] != '.' || !IsDigit(line[i + 1]) ||
                line[i + 2] != 'm' || line[i + 3] != 's' ||
                line[i + 4] != ' ' || line[i + 5] != '"' ||
                line[n - 1] != '"')
                return false;

            if (line.Slice(i + 6, n - i - 7).IndexOf((byte)'"') >= 0)
                return false;

            uint fraction = (uint)(line[i + 1] - '0');
            ReadOnlySpan<byte> whole = line.Slice(latencyStart, latencyDigits);
            Entry entry = GetEntry(line.Slice(pathStart, pathLength));

            if (TrySmallLatency(whole, fraction, out ulong latency))
            {
                entry.Add(latency);
            }
            else
            {
                BigInteger large = BigInteger.Parse(
                    Encoding.ASCII.GetString(whole),
                    NumberStyles.None,
                    CultureInfo.InvariantCulture);

                entry.Add(large * 10 + fraction);
            }

            Status[status]++;
            return true;
        }

        private static bool TrySmallLatency(
            ReadOnlySpan<byte> whole, uint fraction, out ulong value)
        {
            value = 0;

            if (whole.Length <= 18)
            {
                foreach (byte b in whole)
                    value = value * 10 + (uint)(b - '0');

                value = value * 10 + fraction;
                return true;
            }

            const ulong limit = ulong.MaxValue / 10;
            const uint remainder = (uint)(ulong.MaxValue % 10);

            foreach (byte b in whole)
            {
                uint digit = (uint)(b - '0');

                if (value > limit || (value == limit && digit > remainder))
                    return false;

                value = value * 10 + digit;
            }

            if (value > limit || (value == limit && fraction > remainder))
                return false;

            value = value * 10 + fraction;
            return true;
        }

        private void EnsureKeyCapacity(int required)
        {
            if (required <= keyBuffer.Length)
                return;

            int capacity = (int)Math.Min(
                int.MaxValue, Math.Max((long)required, (long)keyBuffer.Length * 2));

            Array.Resize(ref keyBuffer, capacity);
        }

        private Entry GetEntry(ReadOnlySpan<byte> path)
        {
            int written = 0;
            int i = 0;

            while (i < path.Length)
            {
                if (path[i] == '/')
                {
                    EnsureKeyCapacity(written + 1);
                    keyBuffer[written++] = (byte)'/';
                    i++;
                    continue;
                }

                int start = i;
                bool numeric = true;

                do
                {
                    if (!IsDigit(path[i]))
                        numeric = false;
                    i++;
                }
                while (i < path.Length && path[i] != '/');

                int length = numeric ? 4 : i - start;
                EnsureKeyCapacity(checked(written + length));

                if (numeric)
                {
                    keyBuffer[written] = (byte)'{';
                    keyBuffer[written + 1] = (byte)'i';
                    keyBuffer[written + 2] = (byte)'d';
                    keyBuffer[written + 3] = (byte)'}';
                }
                else
                {
                    path.Slice(start, length).CopyTo(keyBuffer.AsSpan(written));
                }

                written += length;
            }

            ReadOnlySpan<byte> key = keyBuffer.AsSpan(0, written);
            uint hash = 2166136261;

            foreach (byte b in key)
                hash = unchecked((hash ^ b) * 16777619);

            int bucket = (int)(hash & (uint)(buckets.Length - 1));

            for (Entry entry = buckets[bucket]; entry != null; entry = entry.Next)
            {
                if (entry.Hash == hash && key.SequenceEqual(entry.Key))
                    return entry;
            }

            var added = new Entry(key.ToArray(), hash, buckets[bucket]);
            buckets[bucket] = added;
            entryCount++;

            if (entryCount > buckets.Length - buckets.Length / 4)
                Grow();

            return added;
        }

        private void Grow()
        {
            var expanded = new Entry[checked(buckets.Length * 2)];
            uint mask = (uint)(expanded.Length - 1);

            foreach (Entry head in buckets)
            {
                Entry entry = head;

                while (entry != null)
                {
                    Entry next = entry.Next;
                    int index = (int)(entry.Hash & mask);
                    entry.Next = expanded[index];
                    expanded[index] = entry;
                    entry = next;
                }
            }

            buckets = expanded;
        }

        private static int Compare(Entry a, Entry b)
        {
            int countComparison = b.Count.CompareTo(a.Count);
            return countComparison != 0
                ? countComparison
                : a.Key.AsSpan().SequenceCompareTo(b.Key);
        }

        internal Entry[] GetTopEntries()
        {
            var top = new Entry[10];
            int count = 0;

            foreach (Entry head in buckets)
            {
                for (Entry entry = head; entry != null; entry = entry.Next)
                {
                    if (count == 10 && Compare(entry, top[9]) >= 0)
                        continue;

                    int position = 0;
                    while (position < count && Compare(top[position], entry) <= 0)
                        position++;

                    if (count < 10)
                        count++;

                    for (int j = count - 1; j > position; j--)
                        top[j] = top[j - 1];

                    top[position] = entry;
                }
            }

            if (count != top.Length)
                Array.Resize(ref top, count);

            return top;
        }
    }

    private static ulong Select(Span<ulong> values, int rank)
    {
        int left = 0;
        int right = values.Length - 1;
        int budget = 2 * BitOperations.Log2((uint)values.Length) + 3;

        while (right - left > 24)
        {
            if (budget-- == 0)
            {
                values.Slice(left, right - left + 1).Sort();
                return values[rank];
            }

            int middle = left + ((right - left) >> 1);
            ulong a = values[left];
            ulong b = values[middle];
            ulong c = values[right];

            ulong pivot = a < b
                ? (b < c ? b : (a < c ? c : a))
                : (a < c ? a : (b < c ? c : b));

            int i = left;
            int j = right;

            while (i <= j)
            {
                while (values[i] < pivot) i++;
                while (values[j] > pivot) j--;

                if (i <= j)
                {
                    ulong temporary = values[i];
                    values[i] = values[j];
                    values[j] = temporary;
                    i++;
                    j--;
                }
            }

            if (rank <= j)
                right = j;
            else if (rank >= i)
                left = i;
            else
                return values[rank];
        }

        values.Slice(left, right - left + 1).Sort();
        return values[rank];
    }

    private static void AppendEntry(StringBuilder output, Entry entry)
    {
        long count = entry.Count;
        long rank50 = (count - 1) / 2;
        long rank95 = count - count / 20 - 1;

        Span<ulong> small = entry.SmallCount == 0
            ? Span<ulong>.Empty
            : entry.SmallCount == 1
                ? MemoryMarshal.CreateSpan(ref entry.First, 1)
                : entry.Values.AsSpan(0, entry.SmallCount);

        if (entry.Large != null)
            entry.Large.Sort();

        BigInteger p50;
        BigInteger p95;
        BigInteger maximum;

        if (rank50 < small.Length)
            p50 = Select(small, (int)rank50);
        else
            p50 = entry.Large[(int)(rank50 - small.Length)];

        if (rank95 < small.Length)
        {
            if (rank95 == rank50)
            {
                p95 = p50;
            }
            else
            {
                int start = (int)rank50 + 1;
                p95 = Select(small.Slice(start), (int)(rank95 - start));
            }
        }
        else
        {
            p95 = entry.Large[(int)(rank95 - small.Length)];
        }

        if (entry.Large != null)
        {
            maximum = entry.Large[entry.Large.Count - 1];
        }
        else
        {
            ulong largest = small[(int)rank95];
            for (int i = (int)rank95 + 1; i < small.Length; i++)
            {
                if (small[i] > largest)
                    largest = small[i];
            }

            maximum = largest;
        }

        output.Append("path ").Append(Encoding.ASCII.GetString(entry.Key))
            .Append(' ').Append(count).Append(' ');

        AppendLatency(output, p50);
        output.Append(' ');
        AppendLatency(output, p95);
        output.Append(' ');
        AppendLatency(output, maximum);
        output.Append('\n');
    }

    private static void AppendLatency(StringBuilder output, BigInteger tenths)
    {
        BigInteger whole = BigInteger.DivRem(tenths, 10, out BigInteger fraction);
        output.Append(whole.ToString(CultureInfo.InvariantCulture))
            .Append('.').Append((int)fraction);
    }
}
