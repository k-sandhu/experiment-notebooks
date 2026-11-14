using System.Text;

internal static class Program
{
    private static ReadOnlySpan<byte> Stamp => "0000-00-00T00:00:00.000Z "u8;
    private static readonly bool[] PathChars = MakePathChars();
    private static bool Digit(byte c) => (uint)(c - '0') <= 9;
    private static bool[] MakePathChars()
    {
        var result = new bool[256];
        for (int c = 0; c < 256; c++)
            result[c] = Digit((byte)c) || c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z' || c is '_' or '/' or '-';
        return result;
    }

    private readonly struct PathKey : IEquatable<PathKey>
    {
        public readonly byte[] Bytes;
        public readonly int Length;
        private readonly int hash;
        public PathKey(byte[] bytes, int length, int hash) { Bytes = bytes; Length = length; this.hash = hash; }
        public override int GetHashCode() => hash;
        public bool Equals(PathKey other) => hash == other.hash &&
            Bytes.AsSpan(0, Length).SequenceEqual(other.Bytes.AsSpan(0, other.Length));
        public override bool Equals(object other) => other is PathKey k && Equals(k);
    }
    private sealed class Group
    {
        public readonly byte[] Key;
        public long[] Values;
        public int Size;
        public List<string> Large;
        public long Count => (long)Size + (Large?.Count ?? 0);
        public Group(byte[] key) { Key = key; }
        public void Add(long value)
        {
            if (Values == null) Values = new long[4];
            else if (Size == Values.Length) Array.Resize(ref Values, Size * 2);
            Values[Size++] = value;
        }
    }
    private sealed class Scanner
    {
        private readonly Dictionary<PathKey, Group> groups = new();
        private byte[] key = new byte[256];
        private readonly long[] statuses = new long[10];
        private long lines, malformed;

        private bool Parse(ReadOnlySpan<byte> b)
        {
            int end = b.Length;
            if (end < 50) return false;
            var stamp = Stamp;
            for (int j = 0; j < stamp.Length; j++)
                if (stamp[j] == '0' ? !Digit(b[j]) : b[j] != stamp[j]) return false;
            int i = 25, start = i;
            while (i < end && b[i] >= 'a' && b[i] <= 'z') i++;
            if (i == start || i == end || b[i++] != '-') return false;
            start = i;
            while (i < end && Digit(b[i])) i++;
            if (i == start || i == end || b[i++] != ' ') return false;
            start = i;
            while (i < end && b[i] != ' ') i++;
            var method = b.Slice(start, i-start);
            if (i == end || !(method.SequenceEqual("GET"u8) || method.SequenceEqual("POST"u8) ||
                method.SequenceEqual("PUT"u8) || method.SequenceEqual("DELETE"u8) || method.SequenceEqual("PATCH"u8))) return false;
            i++;
            if (i == end || b[i] != '/') return false;
            int pathStart = i;
            while (i < end && PathChars[b[i]]) i++;
            int pathEnd = i;
            if (i < end && b[i] == '?') while (i < end && b[i] != ' ') i++;
            if (i == end || b[i++] != ' ') return false;
            if (end - i < 4 || !Digit(b[i]) || !Digit(b[i+1]) || !Digit(b[i+2]) || b[i+3] != ' ') return false;
            int status = b[i] - '0';
            i += 4;
            start = i;
            while (i < end && Digit(b[i])) i++;
            if (i == start || end - i < 2 || b[i] != 'B' || b[i+1] != ' ') return false;
            i += 2;
            start = i;
            while (i < end && b[i] == '0') i++;
            int significant = i;
            while (i < end && Digit(b[i])) i++;
            int decimalAt = i;
            if (i == start || end - i < 7 || b[i] != '.' || !Digit(b[i+1]) || b[i+2] != 'm' ||
                b[i+3] != 's' || b[i+4] != ' ' || b[i+5] != '"' || b[end-1] != '"' ||
                b.Slice(i+6, end-i-7).IndexOf((byte)'"') >= 0) return false;

            int needed = (pathEnd-pathStart) * 3;
            if (key.Length < needed) key = new byte[Math.Max(needed, key.Length * 2)];
            int p = pathStart, used = 0;
            while (p < pathEnd)
            {
                key[used++] = (byte)'/';
                start = ++p;
                bool numeric = true;
                while (p < pathEnd && b[p] != '/') { numeric &= Digit(b[p]); p++; }
                if (p != start && numeric)
                {
                    key[used++] = (byte)'{'; key[used++] = (byte)'i'; key[used++] = (byte)'d'; key[used++] = (byte)'}';
                }
                else { b.Slice(start, p-start).CopyTo(key.AsSpan(used)); used += p-start; }
            }
            int hash = 0;
            for (int j = 0; j < used; j++) hash = unchecked(hash * 31 + key[j]);
            if (!groups.TryGetValue(new PathKey(key, used, hash), out Group g))
            {
                byte[] stored = key.AsSpan(0, used).ToArray();
                g = new Group(stored);
                groups.Add(new PathKey(stored, used, hash), g);
            }
            if (decimalAt-significant <= 14)
            {
                long value = 0;
                for (int j = significant; j < decimalAt; j++) value = value * 10 + b[j] - '0';
                g.Add(value * 10 + b[decimalAt+1] - '0');
            }
            else
            {
                g.Large ??= new List<string>();
                g.Large.Add(Encoding.ASCII.GetString(b.Slice(significant, decimalAt-significant)) + (char)b[decimalAt+1]);
            }
            statuses[status]++;
            return true;
        }

        public void Read(string path)
        {
            using var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1);
            byte[] buffer = new byte[1 << 20];
            int used = 0;
            while (true)
            {
                int got = input.Read(buffer.AsSpan(used));
                if (got == 0) break;
                int end = used + got, begin = 0;
                while (begin < end)
                {
                    int length = buffer.AsSpan(begin, end-begin).IndexOf((byte)'\n');
                    if (length < 0) break;
                    lines++;
                    if (!Parse(buffer.AsSpan(begin, length))) malformed++;
                    begin += length+1;
                }
                used = end-begin;
                buffer.AsSpan(begin, used).CopyTo(buffer);
                if (used == buffer.Length) Array.Resize(ref buffer, buffer.Length * 2);
            }
        }

        private static int Compare(Group a, Group b)
        {
            int c = b.Count.CompareTo(a.Count);
            return c != 0 ? c : a.Key.AsSpan().SequenceCompareTo(b.Key);
        }
        private static string At(Group g, int rank)
        {
            if (rank < g.Size) return $"{g.Values[rank] / 10}.{g.Values[rank] % 10}";
            string s = g.Large[rank-g.Size];
            return s.Insert(s.Length-1, ".");
        }
        public void Output()
        {
            var output = new StringBuilder();
            output.Append("lines ").Append(lines).Append("\nmalformed ").Append(malformed).Append('\n');
            for (int c = 0; c < 10; c++)
                if (statuses[c] != 0) output.Append("status ").Append(c).Append("xx ").Append(statuses[c]).Append('\n');
            Group[] top = new Group[10];
            int size = 0;
            foreach (Group g in groups.Values)
            {
                int pos = size;
                while (pos > 0 && Compare(g, top[pos-1]) < 0) pos--;
                if (pos >= 10) continue;
                for (int j = Math.Min(size, 9); j > pos; j--) top[j] = top[j-1];
                top[pos] = g;
                if (size < 10) size++;
            }
            for (int j = 0; j < size; j++)
            {
                Group g = top[j];
                if (g.Size > 1) Array.Sort(g.Values, 0, g.Size);
                g.Large?.Sort((a,b) => a.Length != b.Length ? a.Length.CompareTo(b.Length) : string.CompareOrdinal(a,b));
                int count = (int)g.Count;
                output.Append("path ").Append(Encoding.ASCII.GetString(g.Key)).Append(' ').Append(count).Append(' ')
                    .Append(At(g, (count-1)/2)).Append(' ').Append(At(g, count-1-count/20)).Append(' ')
                    .Append(At(g, count-1)).Append('\n');
            }
            Console.Write(output);
        }
    }
    private static void Main(string[] args)
    {
        if (args.Length == 0) Environment.Exit(1);
        var scanner = new Scanner();
        scanner.Read(args[0]);
        scanner.Output();
    }
}
