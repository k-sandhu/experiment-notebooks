package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

func main() {
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	defer f.Close()

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1024*1024), 1024*1024)
	sc.Split(bufio.ScanWords)

	nextInt := func() int {
		sc.Scan()
		v, _ := strconv.Atoi(sc.Text())
		return v
	}
	nextFloat := func() float64 {
		sc.Scan()
		v, _ := strconv.ParseFloat(sc.Text(), 64)
		return v
	}

	N := nextInt()
	S := nextInt()
	dt := nextFloat()
	P := nextFloat()

	x := make([]float64, N)
	v := make([]float64, N)
	m := make([]float64, N)
	k := make([]float64, N)
	r := make([]float64, N)
	c := make([]float64, N)
	ff := make([]float64, N)
	for i := 0; i < N; i++ {
		x[i] = nextFloat()
		v[i] = nextFloat()
		m[i] = nextFloat()
		k[i] = nextFloat()
		r[i] = nextFloat()
		c[i] = nextFloat()
	}

	nm1 := N - 1
	for step := 0; step < S; step++ {
		// Stretches and spring forces from the old positions (read-only).
		for i := 0; i < nm1; i++ {
			ff[i] = k[i] * ((x[i+1] - x[i]) - r[i])
		}
		ff[nm1] = k[nm1] * (((x[0] + P) - x[nm1]) - r[nm1])

		// Forces, then velocities, then positions. ff is read-only here.
		F := (ff[0] - ff[nm1]) - (c[0] * v[0])
		v[0] = v[0] + dt*(F/m[0])
		x[0] = x[0] + dt*v[0]
		for i := 1; i < N; i++ {
			F = (ff[i] - ff[i-1]) - (c[i] * v[i])
			v[i] = v[i] + dt*(F/m[i])
			x[i] = x[i] + dt*v[i]
		}
	}

	var K, U, X float64
	J := 0
	best := -1.0
	for i := 0; i < N; i++ {
		var xnext float64
		if i + 1 < N {
			xnext = x[i+1]
		} else {
			xnext = x[0] + P
		}
		s := (xnext - x[i]) - r[i]
		U += ((0.5 * k[i]) * s) * s
		K += ((0.5 * m[i]) * v[i]) * v[i]
		X += x[i]
		av := v[i]
		if av < 0 {
			av = -av
		}
		if av > best { // strict: on a tie the smallest index wins
			best = av
			J = i
		}
	}

	fmt.Printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", K, U, X, J)
}
