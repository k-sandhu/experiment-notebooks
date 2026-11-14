using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Text;

internal static unsafe class Program
{
    private static int ReadInt(byte[] d, ref int pos)
    {
        int n = d.Length;
        while (pos < n && (d[pos] < (byte)'0' || d[pos] > (byte)'9')) pos++;
        int v = 0;
        while (pos < n && d[pos] >= (byte)'0' && d[pos] <= (byte)'9')
        {
            v = v * 10 + (d[pos] - (byte)'0');
            pos++;
        }
        return v;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static ushort* Run512(ushort* src, ushort* dst, ushort* m, ushort* k, nint start, nint end, nint stride, int steps)
    {
        for (int s = 0; s < steps; s++)
        {
            for (nint i = start; i < end; i += 32)
            {
                ushort* p = src + i;
                Vector512<ushort> a = Vector512.Load(p);
                Vector512<ushort> n = (Vector512.Load(p - 1) + Vector512.Load(p + 1)) + (Vector512.Load(p - stride) + Vector512.Load(p + stride));
                n = (n & Vector512.Load(m + i)) + a * Vector512.Load(k + i);
                Vector512<ushort> res = Vector512.ShiftRightLogical(a + Vector512.ShiftRightLogical(n, 2), 1);
                res.Store(dst + i);
            }
            ushort* t = src; src = dst; dst = t;
        }
        return src;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static ushort* Run256(ushort* src, ushort* dst, ushort* m, ushort* k, nint start, nint end, nint stride, int steps)
    {
        for (int s = 0; s < steps; s++)
        {
            for (nint i = start; i < end; i += 16)
            {
                ushort* p = src + i;
                Vector256<ushort> a = Vector256.Load(p);
                Vector256<ushort> n = (Vector256.Load(p - 1) + Vector256.Load(p + 1)) + (Vector256.Load(p - stride) + Vector256.Load(p + stride));
                n = (n & Vector256.Load(m + i)) + a * Vector256.Load(k + i);
                Vector256<ushort> res = Vector256.ShiftRightLogical(a + Vector256.ShiftRightLogical(n, 2), 1);
                res.Store(dst + i);
            }
            ushort* t = src; src = dst; dst = t;
        }
        return src;
    }

    [MethodImpl(MethodImplOptions.AggressiveOptimization)]
    private static ushort* Run128(ushort* src, ushort* dst, ushort* m, ushort* k, nint start, nint end, nint stride, int steps)
    {
        for (int s = 0; s < steps; s++)
        {
            for (nint i = start; i < end; i += 8)
            {
                ushort* p = src + i;
                Vector128<ushort> a = Vector128.Load(p);
                Vector128<ushort> n = (Vector128.Load(p - 1) + Vector128.Load(p + 1)) + (Vector128.Load(p - stride) + Vector128.Load(p + stride));
                n = (n & Vector128.Load(m + i)) + a * Vector128.Load(k + i);
                Vector128<ushort> res = Vector128.ShiftRightLogical(a + Vector128.ShiftRightLogical(n, 2), 1);
                res.Store(dst + i);
            }
            ushort* t = src; src = dst; dst = t;
        }
        return src;
    }

    private static int Main(string[] args)
    {
        byte[] data = File.ReadAllBytes(args[0]);
        int pos = 0;
        int H = ReadInt(data, ref pos);
        int W = ReadInt(data, ref pos);
        int S = ReadInt(data, ref pos);

        const int OFF = 64;
        long stride = (long)W + 1;
        long total = OFF + (long)(H + 2) * stride + 64;
        nuint bytes = (nuint)total * 2;

        ushort* a = (ushort*)NativeMemory.AlignedAlloc(bytes, 64);
        ushort* b = (ushort*)NativeMemory.AlignedAlloc(bytes, 64);
        ushort* m = (ushort*)NativeMemory.AlignedAlloc(bytes, 64);
        ushort* k = (ushort*)NativeMemory.AlignedAlloc(bytes, 64);
        byte* valid = (byte*)NativeMemory.AlignedAlloc((nuint)total, 64);

        NativeMemory.Clear(a, bytes);
        NativeMemory.Clear(b, bytes);
        NativeMemory.Clear(m, bytes);
        NativeMemory.Clear(valid, (nuint)total);
        for (long i = 0; i < total; i++) k[i] = 4;

        int len = data.Length;
        for (int r = 0; r < H; r++)
        {
            while (pos < len && data[pos] <= (byte)' ') pos++;
            long rowBase = OFF + (long)(r + 1) * stride;
            for (int c = 0; c < W; c++)
            {
                if (pos >= len) break;
                byte ch = data[pos++];
                long idx = rowBase + c;
                if (ch == (byte)'.')
                {
                    valid[idx] = 1;
                    m[idx] = 0xFFFF;
                }
                else if (ch >= (byte)'1' && ch <= (byte)'9')
                {
                    valid[idx] = 1;
                    ushort v = (ushort)(1000 * (ch - (byte)'0'));
                    a[idx] = v;
                    b[idx] = v;
                }
            }
        }

        for (int r = 0; r < H; r++)
        {
            long rowBase = OFF + (long)(r + 1) * stride;
            for (int c = 0; c < W; c++)
            {
                long idx = rowBase + c;
                if (m[idx] != 0)
                {
                    int cnt = valid[idx - 1] + valid[idx + 1] + valid[idx - stride] + valid[idx + stride];
                    k[idx] = (ushort)(4 - cnt);
                }
            }
        }

        nint start = (nint)((OFF + stride) & ~31L);
        nint end = (nint)(OFF + (long)(H + 1) * stride);

        ushort* cur;
        if (Vector512.IsHardwareAccelerated)
            cur = Run512(a, b, m, k, start, end, (nint)stride, S);
        else if (Vector256.IsHardwareAccelerated)
            cur = Run256(a, b, m, k, start, end, (nint)stride, S);
        else
            cur = Run128(a, b, m, k, start, end, (nint)stride, S);

        long T = 0, K = 0;
        int V = -1, R = 0, C = 0;
        for (int r = 0; r < H; r++)
        {
            long rowBase = OFF + (long)(r + 1) * stride;
            long weightBase = (long)r * W + 1;
            for (int c = 0; c < W; c++)
            {
                long idx = rowBase + c;
                if (m[idx] != 0)
                {
                    int v = cur[idx];
                    T += v;
                    K += v * (weightBase + c);
                    if (v > V)
                    {
                        V = v;
                        R = r;
                        C = c;
                    }
                }
            }
        }

        StringBuilder sb = new StringBuilder(128);
        sb.Append("sum ").Append(T).Append('\n');
        sb.Append("max ").Append(V).Append(' ').Append(R).Append(' ').Append(C).Append('\n');
        sb.Append("checksum ").Append(K).Append('\n');

        Stream stdout = Console.OpenStandardOutput();
        byte[] outBytes = Encoding.ASCII.GetBytes(sb.ToString());
        stdout.Write(outBytes, 0, outBytes.Length);
        stdout.Flush();

        NativeMemory.AlignedFree(a);
        NativeMemory.AlignedFree(b);
        NativeMemory.AlignedFree(m);
        NativeMemory.AlignedFree(k);
        NativeMemory.AlignedFree(valid);
        return 0;
    }
}
