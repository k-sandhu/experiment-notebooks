using System;
using System.IO;
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

public static class Program
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static long ReadNumber(byte[] data, ref int position)
    {
        while (data[position] <= 32)
            position++;

        long value = 0;
        while (position < data.Length)
        {
            uint digit = (uint)(data[position] - '0');
            if (digit > 9)
                break;

            value = value * 10 + digit;
            position++;
        }
        return value;
    }

    private static unsafe int[] Simulate(
        int[] first, int[] second, int[] coefficients,
        int stride, int height, long steps)
    {
        int begin = stride;
        int end = (height + 1) * stride;

        fixed (int* firstPointer = first)
        fixed (int* secondPointer = second)
        fixed (int* coefficientPointer = coefficients)
        {
            int* current = firstPointer;
            int* next = secondPointer;

            if (Avx2.IsSupported)
            {
                int vectorEnd = end - 8;

                for (long step = 0; step < steps; step++)
                {
                    int i = begin;
                    for (; i <= vectorEnd; i += 8)
                    {
                        Vector256<int> old = Avx.LoadVector256(current + i);
                        Vector256<int> coefficient =
                            Avx.LoadVector256(coefficientPointer + i);

                        Vector256<int> vertical = Avx2.Add(
                            Avx.LoadVector256(current + i - stride),
                            Avx.LoadVector256(current + i + stride));

                        Vector256<int> horizontal = Avx2.Add(
                            Avx.LoadVector256(current + i - 1),
                            Avx.LoadVector256(current + i + 1));

                        Vector256<int> total = Avx2.Add(
                            Avx2.MultiplyLow(old, coefficient),
                            Avx2.Add(vertical, horizontal));

                        Vector256<int> updated =
                            Avx2.ShiftRightLogical(total, 3);

                        // Fixed cells have coefficient -1; open cells have 4..8.
                        updated = Avx2.BlendVariable(
                            updated.AsByte(),
                            old.AsByte(),
                            coefficient.AsByte()).AsInt32();

                        Avx.Store(next + i, updated);
                    }

                    for (; i < end; i++)
                    {
                        int coefficient = coefficientPointer[i];
                        if (coefficient >= 0)
                        {
                            next[i] = (
                                coefficient * current[i]
                                + current[i - stride]
                                + current[i + stride]
                                + current[i - 1]
                                + current[i + 1]) >> 3;
                        }
                    }

                    int* temporary = current;
                    current = next;
                    next = temporary;
                }
            }
            else
            {
                for (long step = 0; step < steps; step++)
                {
                    for (int i = begin; i < end; i++)
                    {
                        int coefficient = coefficientPointer[i];
                        if (coefficient >= 0)
                        {
                            next[i] = (
                                coefficient * current[i]
                                + current[i - stride]
                                + current[i + stride]
                                + current[i - 1]
                                + current[i + 1]) >> 3;
                        }
                    }

                    int* temporary = current;
                    current = next;
                    next = temporary;
                }
            }

            return current == firstPointer ? first : second;
        }
    }

    public static void Main(string[] args)
    {
        byte[] input = File.ReadAllBytes(args[0]);
        int position = 0;

        int height = (int)ReadNumber(input, ref position);
        int width = (int)ReadNumber(input, ref position);
        long steps = ReadNumber(input, ref position);

        int stride = width + 2;
        int length = (height + 2) * stride;

        int[] values = new int[length];
        int[] coefficients = new int[length];
        Array.Fill(coefficients, -1);

        bool hasSource = false;

        for (int row = 0; row < height; row++)
        {
            while (input[position] <= 32)
                position++;

            int index = (row + 1) * stride + 1;
            for (int column = 0; column < width; column++, index++)
            {
                byte cell = input[position++];
                if (cell == (byte)'.')
                {
                    coefficients[index] = 4;
                }
                else if (cell != (byte)'#')
                {
                    values[index] = (cell - (byte)'0') * 1000;
                    hasSource = true;
                }
            }
        }

        if (steps > 0 && hasSource)
        {
            for (int row = 0; row < height; row++)
            {
                int index = (row + 1) * stride + 1;
                int end = index + width;

                for (; index < end; index++)
                {
                    if (coefficients[index] < 0)
                        continue;

                    int coefficient = 4;

                    int neighbor = index - stride;
                    if (coefficients[neighbor] < 0 && values[neighbor] == 0)
                        coefficient++;

                    neighbor = index + stride;
                    if (coefficients[neighbor] < 0 && values[neighbor] == 0)
                        coefficient++;

                    neighbor = index - 1;
                    if (coefficients[neighbor] < 0 && values[neighbor] == 0)
                        coefficient++;

                    neighbor = index + 1;
                    if (coefficients[neighbor] < 0 && values[neighbor] == 0)
                        coefficient++;

                    coefficients[index] = coefficient;
                }
            }

            int[] second = (int[])values.Clone();
            values = Simulate(
                values, second, coefficients, stride, height, steps);
        }

        long sum = 0;
        long checksum = 0;
        long weight = 1;
        int maximum = -1;
        int bestRow = 0;
        int bestColumn = 0;

        for (int row = 0; row < height; row++)
        {
            int index = (row + 1) * stride + 1;
            for (int column = 0; column < width; column++, index++, weight++)
            {
                if (coefficients[index] < 0)
                    continue;

                int value = values[index];
                sum += value;
                checksum += value * weight;

                if (value > maximum)
                {
                    maximum = value;
                    bestRow = row;
                    bestColumn = column;
                }
            }
        }

        Console.Write(
            $"sum {sum}\nmax {maximum} {bestRow} {bestColumn}\nchecksum {checksum}\n");
    }
}
