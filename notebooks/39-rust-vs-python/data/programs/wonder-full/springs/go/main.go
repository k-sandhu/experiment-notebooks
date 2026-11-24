package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
)

func main() {
	dataBytes, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	data := string(dataBytes)
	pos := 0
	nextToken := func() string {
		for pos < len(data) && data[pos] <= ' ' {
			pos++
		}
		start := pos
		for pos < len(data) && data[pos] > ' ' {
			pos++
		}
		return data[start:pos]
	}
	nextInt := func() int64 {
		n, _ := strconv.ParseInt(nextToken(), 10, 64)
		return n
	}
	nextFloat := func() float64 {
		f, _ := strconv.ParseFloat(nextToken(), 64)
		return f
	}

	N := int(nextInt())
	S := nextInt()
	dt := nextFloat()
	P := nextFloat()

	if N <= 0 {
		fmt.Print("kinetic 0.000000000000e+00\npotential 0.000000000000e+00\nposition 0.000000000000e+00\nfastest 0\n")
		return
	}

	x := make([]float64, N)
	v := make([]float64, N)
	m := make([]float64, N)
	k := make([]float64, N)
	r := make([]float64, N)
	c := make([]float64, N)
	a := make([]float64, N) // dt / m

	for i := 0; i < N; i++ {
		x[i] = nextFloat()
		v[i] = nextFloat()
		m[i] = nextFloat()
		k[i] = nextFloat()
		r[i] = nextFloat()
		c[i] = nextFloat()
		a[i] = dt / m[i]
	}
	data = ""

	nm1 := N - 1
	// Bounds-check hints (all slices have length N)
	_ = x[nm1]
	_ = v[nm1]
	_ = k[nm1]
	_ = r[nm1]
	_ = c[nm1]
	_ = a[nm1]

	for step := int64(0); step < S; step++ {
		fLast := k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1])
		fPrev := fLast
		xcur := x[0]
		for i := 0; i < nm1; i++ {
			xnext := x[i+1]
			fi := k[i] * ((xnext - xcur) - r[i])
			vi := v[i]
			nv := vi + a[i]*((fi-fPrev)-c[i]*vi)
			v[i] = nv
			x[i] = xcur + dt*nv
			fPrev = fi
			xcur = xnext
		}
		// last mass (also correct for N==1: fPrev == fLast)
		{
			i := nm1
			F := (fLast - fPrev) - c[i]*v[i]
			nv := v[i] + a[i]*F
			v[i] = nv
			x[i] = x[i] + dt*nv
		}
	}

	var K, U, X float64
	J := 0
	best := math.Abs(v[0])
	for i := 0; i < N; i++ {
		K += ((0.5 * m[i]) * v[i]) * v[i]
		X += x[i]
		av := math.Abs(v[i])
		if av > best {
			best = av
			J = i
		}
	}
	for i := 0; i < nm1; i++ {
		s := (x[i+1] - x[i]) - r[i]
		U += ((0.5 * k[i]) * s) * s
	}
	{
		s := ((x[0] + P) - x[nm1]) - r[nm1]
		U += ((0.5 * k[nm1]) * s) * s
	}

	fmt.Printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", K, U, X, J)
}
