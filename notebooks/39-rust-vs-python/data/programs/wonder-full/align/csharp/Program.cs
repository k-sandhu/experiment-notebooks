using System;
using System.IO;
using System.Text;

byte[] data = File.ReadAllBytes(args[0]);
int pos = 0;

static bool IsWs(byte c) => c == (byte)' ' || c == (byte)'\n' || c == (byte)'\r' || c == (byte)'\t';

void SkipWs() { while (pos < data.Length && IsWs(data[pos])) pos++; }

(int start, int len) NextToken()
{
    SkipWs();
    int start = pos;
    while (pos < data.Length && !IsWs(data[pos])) pos++;
    return (start, pos - start);
}

int NextInt()
{
    SkipWs();
    int v = 0;
    while (pos < data.Length && data[pos] >= (byte)'0' && data[pos] <= (byte)'9')
        v = v * 10 + (data[pos++] - (byte)'0');
    return v;
}

var (aStart, A) = NextToken();
int[] idx = new int[256];
for (int i = 0; i < A; i++) idx[data[aStart + i]] = i;

int[] ins = new int[A], del = new int[A], sub = new int[A * A];
for (int i = 0; i < A; i++) ins[i] = NextInt();
for (int i = 0; i < A; i++) del[i] = NextInt();
for (int i = 0; i < A * A; i++) sub[i] = NextInt();
int P = NextInt();

StringBuilder outSb = new StringBuilder(P * 8 + 32);
long total = 0;
int[] sIdx = Array.Empty<int>(), tIdx = Array.Empty<int>();
int[] prev = Array.Empty<int>(), curr = Array.Empty<int>(), colIns = Array.Empty<int>(), subCols = Array.Empty<int>();

for (int p = 0; p < P; p++)
{
    var (sStart, sLen) = NextToken();
    var (tStart, tLen) = NextToken();
    long ans;
    bool equal = sLen == tLen && data.AsSpan(sStart, sLen).SequenceEqual(data.AsSpan(tStart, tLen));
    if (equal)
    {
        ans = 0;
    }
    else
    {
        if (sIdx.Length < sLen) sIdx = new int[sLen];
        if (tIdx.Length < tLen) tIdx = new int[tLen];
        for (int i = 0; i < sLen; i++) sIdx[i] = idx[data[sStart + i]];
        for (int i = 0; i < tLen; i++) tIdx[i] = idx[data[tStart + i]];

        int[] rowStr, colStr, rowCost, colCost;
        int R, C;
        bool transposed;
        if (tLen <= sLen)
        {
            rowStr = sIdx; colStr = tIdx; R = sLen; C = tLen;
            rowCost = del; colCost = ins; transposed = false;
        }
        else
        {
            rowStr = tIdx; colStr = sIdx; R = tLen; C = sLen;
            rowCost = ins; colCost = del; transposed = true;
        }

        if (colIns.Length < C + 1) colIns = new int[C + 1];
        for (int j = 0; j < C; j++) colIns[j + 1] = colCost[colStr[j]];

        if (subCols.Length < A * C) subCols = new int[A * C];
        if (!transposed)
        {
            for (int a = 0; a < A; a++)
            {
                int b = a * C, sb = a * A;
                for (int j = 0; j < C; j++) subCols[b + j] = sub[sb + colStr[j]];
            }
        }
        else
        {
            for (int b = 0; b < A; b++)
            {
                int bs = b * C;
                for (int j = 0; j < C; j++) subCols[bs + j] = sub[colStr[j] * A + b];
            }
        }

        if (prev.Length < C + 1) { prev = new int[C + 1]; curr = new int[C + 1]; }
        prev[0] = 0;
        for (int j = 1; j <= C; j++) prev[j] = prev[j - 1] + colIns[j];

        ans = SolveDp(prev, curr, colIns, subCols, rowStr, rowCost, R, C);
    }
    total += ans;
    outSb.Append(ans).Append('\n');
}
outSb.Append("total ").Append(total).Append('\n');
Console.Out.Write(outSb.ToString());

static int SolveDp(int[] prevA, int[] currA, int[] colIns, int[] subCols, int[] rowStr, int[] rowCost, int R, int C)
{
    ref int prev = ref System.Runtime.InteropServices.MemoryMarshal.GetArrayDataReference(prevA);
    ref int curr = ref System.Runtime.InteropServices.MemoryMarshal.GetArrayDataReference(currA);
    ref int cins = ref System.Runtime.InteropServices.MemoryMarshal.GetArrayDataReference(colIns);
    ref int sc0 = ref System.Runtime.InteropServices.MemoryMarshal.GetArrayDataReference(subCols);
    for (int i = 0; i < R; i++)
    {
        int rc = rowStr[i];
        int d = rowCost[rc];
        ref int sc = ref System.Runtime.CompilerServices.Unsafe.Add(ref sc0, rc * C);
        int diag = prev;
        int left = diag + d;
        curr = left;
        for (int j = 1; j <= C; j++)
        {
            int up = System.Runtime.CompilerServices.Unsafe.Add(ref prev, j);
            int x1 = diag + System.Runtime.CompilerServices.Unsafe.Add(ref sc, j - 1);
            int x2 = up + d;
            int x3 = left + System.Runtime.CompilerServices.Unsafe.Add(ref cins, j);
            int diff = x1 - x2;
            int best = x2 + (diff & (diff >> 31));
            diff = best - x3;
            best = x3 + (diff & (diff >> 31));
            System.Runtime.CompilerServices.Unsafe.Add(ref curr, j) = best;
            diag = up;
            left = best;
        }
        ref int tmp = ref prev; prev = ref curr; curr = ref tmp;
    }
    return System.Runtime.CompilerServices.Unsafe.Add(ref prev, C);
}
