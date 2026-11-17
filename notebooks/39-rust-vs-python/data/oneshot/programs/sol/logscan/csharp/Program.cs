using System;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;

static class Program
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static bool IsDigit(byte c) => (uint)(c - '0') <= 9;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static bool IsPathChar(byte c) =>
        (uint)(c - 'a') <= 25 ||
        (uint)(c - 'A') <= 25 ||
        (uint)(c - '0') <= 9 ||
        c == '/' || c == '_' || c == '-';

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    static void AppendDigit(ref ulong value, uint digit, ref bool large)
    {
        if (large)
            return;

        if (value > 1844674407370955161UL ||
            (value == 1844674407370955161UL && digit > 5))
        {
            large = true;
        }
        else
        {
            value = value * 10 + digit;
        }
    }

    static bool TryParse(
        ReadOnlySpan<byte> s,
        out int pathStart,
        out int pathLength,
        out int status,
        out ulong latency,
        out BigInteger bigLatency,
        out bool large)
    {
        pathStart = pathLength = status = 0;
        latency = 0;
        bigLatency = default;
        large = false;

        int n = s.Length;
        if (n < 50 || s[n - 1] != '"')
            return false;

        if (s[4] != '-' || s[7] != '-' || s[10] != 'T' ||
            s[13] != ':' || s[16] != ':' || s[19] != '.' ||
            s[23] != 'Z' || s[24] != ' ')
            return false;

        if (!IsDigit(s[0]) || !IsDigit(s[1]) ||
            !IsDigit(s[2]) || !IsDigit(s[3]) ||
            !IsDigit(s[5]) || !IsDigit(s[6]) ||
            !IsDigit(s[8]) || !IsDigit(s[9]) ||
            !IsDigit(s[11]) || !IsDigit(s[12]) ||
            !IsDigit(s[14]) || !IsDigit(s[15]) ||
            !IsDigit(s[17]) || !IsDigit(s[18]) ||
            !IsDigit(s[20]) || !IsDigit(s[21]) || !IsDigit(s[22]))
            return false;

        int i = 25;
        int start = i;
        while (i < n && (uint)(s[i] - 'a') <= 25)
            i++;

        if (i == start || i >= n || s[i] != '-')
            return false;

        start = ++i;
        while (i < n && IsDigit(s[i]))
            i++;

        if (i == start || i >= n || s[i] != ' ')
            return false;

        i++;
        if (i >= n)
            return false;

        ReadOnlySpan<byte> rest = s.Slice(i);
        switch (s[i])
        {
            case (byte)'G':
                if (!rest.StartsWith("GET "u8))
                    return false;
                i += 4;
                break;

            case (byte)'P':
                if (rest.StartsWith("POST "u8))
                    i += 5;
                else if (rest.StartsWith("PUT "u8))
                    i += 4;
                else if (rest.StartsWith("PATCH "u8))
                    i += 6;
                else
                    return false;
                break;

            case (byte)'D':
                if (!rest.StartsWith("DELETE "u8))
                    return false;
                i += 7;
                break;

            default:
                return false;
        }

        if (i >= n || s[i] != '/')
            return false;

        pathStart = i++;
        while (i < n && IsPathChar(s[i]))
            i++;
        pathLength = i - pathStart;

        if (i < n && s[i] == '?')
        {
            i++;
            while (i < n && s[i] != ' ')
                i++;
        }

        if (i >= n || s[i] != ' ')
            return false;
        i++;

        if (n - i < 4 ||
            !IsDigit(s[i]) || !IsDigit(s[i + 1]) ||
            !IsDigit(s[i + 2]) || s[i + 3] != ' ')
            return false;

        status = s[i] - '0';
        i += 4;

        start = i;
        while (i < n && IsDigit(s[i]))
            i++;

        if (i == start || n - i < 2 ||
            s[i] != 'B' || s[i + 1] != ' ')
            return false;
        i += 2;

        int latencyStart = i;
        while (i < n && IsDigit(s[i]))
        {
            AppendDigit(ref latency, (uint)(s[i] - '0'), ref large);
            i++;
        }

        if (i == latencyStart || n - i < 7 ||
            s[i] != '.' || !IsDigit(s[i + 1]) ||
            s[i + 2] != 'm' || s[i + 3] != 's' ||
            s[i + 4] != ' ' || s[i + 5] != '"')
            return false;

        if (s.Slice(i + 6, n - i - 7).IndexOf((byte)'"') >= 0)
            return false;

        uint fraction = (uint)(s[i + 1] - '0');
        AppendDigit(ref latency, fraction, ref large);

        if (large)
        {
            bigLatency = BigInteger.Parse(
                Encoding.ASCII.GetString(s.Slice(latencyStart, i - latencyStart)),
                NumberStyles.None,
                CultureInfo.InvariantCulture) * 10 + fraction;
        }

        return true;
    }

    static void EnsureCapacity(ref char[] buffer, int required)
    {
        if (required <= buffer.Length)
            return;

        int capacity = buffer.Length <= int.MaxValue / 2
            ? buffer.Length * 2
            : int.MaxValue;
        Array.Resize(ref buffer, Math.Max(required, capacity));
    }

    static int Normalize(ReadOnlySpan<byte> path, ref char[] buffer, out uint hash)
    {
        EnsureCapacity(ref buffer, path.Length);

        int written = 0;
        int start = 0;

        while (true)
        {
            int end = start;
            bool numeric = true;

            while (end < path.Length && path[end] != '/')
            {
                numeric &= IsDigit(path[end]);
                end++;
            }

            int length = end - start;
            numeric &= length != 0;

            int required = written + (numeric ? 4 : length);
            if (end < path.Length)
                required++;
            EnsureCapacity(ref buffer, required);

            if (numeric)
            {
                buffer[written++] = '{';
                buffer[written++] = 'i';
                buffer[written++] = 'd';
                buffer[written++] = '}';
            }
            else
            {
                for (int j = start; j < end; j++)
                    buffer[written++] = (char)path[j];
            }

            if (end == path.Length)
                break;

            buffer[written++] = '/';
            start = end + 1;
        }

        unchecked
        {
            uint h = 2166136261;
            for (int j = 0; j < written; j++)
                h = (h ^ buffer[j]) * 16777619;

            h ^= h >> 16;
            h *= 0x85ebca6b;
            h ^= h >> 13;
            h *= 0xc2b2ae35;
            h ^= h >> 16;
            hash = h;
        }

        return written;
    }

    sealed class PathStats
    {
        internal readonly string Name;
        internal readonly uint Hash;

        ulong first;
        ulong[] values;
        int smallCount;
        System.Collections.Generic.List<BigInteger> largeValues;

        internal long Count => (long)smallCount + (largeValues?.Count ?? 0);

        internal PathStats(ReadOnlySpan<char> name, uint hash)
        {
            Name = new string(name);
            Hash = hash;
        }

        internal void Add(ulong value, bool large, BigInteger bigValue)
        {
            if (large)
            {
                largeValues ??= new System.Collections.Generic.List<BigInteger>();
                largeValues.Add(bigValue);
                return;
            }

            if (smallCount == 0)
            {
                first = value;
            }
            else if (smallCount == 1)
            {
                values = new ulong[4];
                values[0] = first;
                values[1] = value;
            }
            else
            {
                if (smallCount == values.Length)
                    Array.Resize(ref values, checked(values.Length * 2));
                values[smallCount] = value;
            }

            smallCount++;
        }

        internal void Quantiles(
            out BigInteger p50, out BigInteger p95, out BigInteger maximum)
        {
            int largeCount = largeValues?.Count ?? 0;
            if (largeCount > 0)
                largeValues.Sort();

            long count = Count;
            long k50 = (count - 1) / 2;
            long k95 = count - count / 20 - 1;

            if (k50 < smallCount)
            {
                p50 = smallCount == 1
                    ? first
                    : Select(values, 0, smallCount - 1, (int)k50);
            }
            else
            {
                p50 = largeValues[(int)(k50 - smallCount)];
            }

            if (k95 == k50)
            {
                p95 = p50;
            }
            else if (k95 < smallCount)
            {
                p95 = Select(values, (int)k50 + 1, smallCount - 1, (int)k95);
            }
            else
            {
                p95 = largeValues[(int)(k95 - smallCount)];
            }

            if (largeCount > 0)
            {
                maximum = largeValues[largeCount - 1];
            }
            else if (smallCount == 1)
            {
                maximum = first;
            }
            else
            {
                ulong max = values[0];
                for (int i = 1; i < smallCount; i++)
                    if (values[i] > max)
                        max = values[i];
                maximum = max;
            }
        }
    }

    static ulong Select(ulong[] values, int left, int right, int k)
    {
        int budget = 2 * (BitOperations.Log2((uint)(right - left + 1)) + 1);

        while (right - left > 24)
        {
            if (budget-- == 0)
            {
                Array.Sort(values, left, right - left + 1);
                return values[k];
            }

            ulong a = values[left];
            ulong b = values[left + ((right - left) >> 1)];
            ulong c = values[right];
            ulong pivot = a < b
                ? (b < c ? b : (a < c ? c : a))
                : (a < c ? a : (b < c ? c : b));

            int i = left;
            int j = right;

            while (i <= j)
            {
                while (values[i] < pivot)
                    i++;
                while (values[j] > pivot)
                    j--;

                if (i <= j)
                {
                    ulong temp = values[i];
                    values[i] = values[j];
                    values[j] = temp;
                    i++;
                    j--;
                }
            }

            if (k <= j)
                right = j;
            else if (k >= i)
                left = i;
            else
                return values[k];
        }

        Array.Sort(values, left, right - left + 1);
        return values[k];
    }

    sealed class PathTable
    {
        internal PathStats[] Entries = new PathStats[1024];
        int count;
        int limit = 716;

        internal PathStats GetOrAdd(ReadOnlySpan<char> name, uint hash)
        {
            int mask = Entries.Length - 1;
            int index = (int)(hash & (uint)mask);

            while (Entries[index] != null)
            {
                PathStats entry = Entries[index];
                if (entry.Hash == hash && entry.Name.AsSpan().SequenceEqual(name))
                    return entry;
                index = (index + 1) & mask;
            }

            if (count >= limit)
            {
                Grow();
                mask = Entries.Length - 1;
                index = (int)(hash & (uint)mask);
                while (Entries[index] != null)
                    index = (index + 1) & mask;
            }

            PathStats result = new PathStats(name, hash);
            Entries[index] = result;
            count++;
            return result;
        }

        void Grow()
        {
            PathStats[] old = Entries;
            Entries = new PathStats[checked(old.Length * 2)];
            int mask = Entries.Length - 1;
            limit = (int)((long)Entries.Length * 7 / 10);

            foreach (PathStats entry in old)
            {
                if (entry == null)
                    continue;

                int index = (int)(entry.Hash & (uint)mask);
                while (Entries[index] != null)
                    index = (index + 1) & mask;
                Entries[index] = entry;
            }
        }
    }

    static int Compare(PathStats a, PathStats b)
    {
        int countComparison = b.Count.CompareTo(a.Count);
        return countComparison != 0
            ? countComparison
            : string.CompareOrdinal(a.Name, b.Name);
    }

    static void AppendLatency(StringBuilder output, BigInteger value)
    {
        BigInteger whole = BigInteger.DivRem(value, 10, out BigInteger fraction);
        output.Append(whole.ToString(CultureInfo.InvariantCulture));
        output.Append('.');
        output.Append((char)('0' + (int)fraction));
    }

    static void Main(string[] args)
    {
        long lines = 0;
        long malformed = 0;
        long[] statuses = new long[10];
        var paths = new PathTable();
        char[] templateBuffer = new char[256];
        byte[] inputBuffer = new byte[1 << 20];

        using (var input = new FileStream(
            args[0], FileMode.Open, FileAccess.Read, FileShare.Read,
            1, FileOptions.SequentialScan))
        {
            int pending = 0;

            while (true)
            {
                if (pending == inputBuffer.Length)
                    Array.Resize(ref inputBuffer, checked(inputBuffer.Length * 2));

                int read = input.Read(
                    inputBuffer, pending, inputBuffer.Length - pending);
                if (read == 0)
                    break;

                int end = pending + read;
                int start = 0;

                while (start < end)
                {
                    int length = inputBuffer.AsSpan(start, end - start)
                        .IndexOf((byte)'\n');
                    if (length < 0)
                        break;

                    ReadOnlySpan<byte> line = inputBuffer.AsSpan(start, length);
                    lines++;

                    if (!TryParse(
                        line, out int pathStart, out int pathLength,
                        out int status, out ulong latency,
                        out BigInteger bigLatency, out bool large))
                    {
                        malformed++;
                    }
                    else
                    {
                        statuses[status]++;
                        int templateLength = Normalize(
                            line.Slice(pathStart, pathLength),
                            ref templateBuffer, out uint hash);

                        PathStats stats = paths.GetOrAdd(
                            templateBuffer.AsSpan(0, templateLength), hash);
                        stats.Add(latency, large, bigLatency);
                    }

                    start += length + 1;
                }

                pending = end - start;
                if (pending != 0 && start != 0)
                    Buffer.BlockCopy(inputBuffer, start, inputBuffer, 0, pending);
            }
        }

        PathStats[] best = new PathStats[10];
        int bestCount = 0;

        foreach (PathStats entry in paths.Entries)
        {
            if (entry == null)
                continue;

            int position = bestCount;
            if (position == 10)
            {
                if (Compare(entry, best[9]) >= 0)
                    continue;
                position = 9;
            }

            while (position > 0 && Compare(entry, best[position - 1]) < 0)
            {
                best[position] = best[position - 1];
                position--;
            }

            best[position] = entry;
            if (bestCount < 10)
                bestCount++;
        }

        var output = new StringBuilder();
        output.Append("lines ").Append(lines).Append('\n');
        output.Append("malformed ").Append(malformed).Append('\n');

        for (int i = 0; i < statuses.Length; i++)
        {
            if (statuses[i] != 0)
            {
                output.Append("status ").Append(i).Append("xx ")
                    .Append(statuses[i]).Append('\n');
            }
        }

        for (int i = 0; i < bestCount; i++)
        {
            PathStats stats = best[i];
            stats.Quantiles(
                out BigInteger p50, out BigInteger p95, out BigInteger maximum);

            output.Append("path ").Append(stats.Name).Append(' ')
                .Append(stats.Count).Append(' ');
            AppendLatency(output, p50);
            output.Append(' ');
            AppendLatency(output, p95);
            output.Append(' ');
            AppendLatency(output, maximum);
            output.Append('\n');
        }

        Console.Write(output.ToString());
    }
}
