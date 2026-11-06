package main

import (
	"bufio"
	"math"
	"os"
	"strconv"
)

// simulate advances the ring by steps time steps in one fused pass per step.
// x has length n+1: x[n] is the ghost x[0] + P closing the ring. The explicit
// float64() conversions stop the compiler from fusing a*b+c into an FMA, which
// would change the rounding the spec requires.
func simulate(n int, steps int64, dt, P float64, x, v, m, k, r, c []float64) {
	x = x[:n+1]
	v = v[:n]
	m = m[:n]
	k = k[:n]
	r = r[:n]
	c = c[:n]
	for s := int64(0); s < steps; s++ {
		x[n] = x[0] + P
		fprev := k[n-1] * float64(float64(x[n]-x[n-1])-r[n-1])
		for i := 0; i < n; i++ {
			xi := x[i]
			f := k[i] * float64(float64(x[i+1]-xi)-r[i])
			vi := v[i]
			F := float64(f-fprev) - float64(c[i]*vi)
			vi = vi + float64(dt*float64(F/m[i]))
			v[i] = vi
			x[i] = xi + float64(dt*vi)
			fprev = f
		}
	}
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	pos := 0
	token := func() string {
		for pos < len(data) && data[pos] <= ' ' {
			pos++
		}
		start := pos
		for pos < len(data) && data[pos] > ' ' {
			pos++
		}
		return string(data[start:pos])
	}
	num := func() float64 {
		f, _ := strconv.ParseFloat(token(), 64)
		return f
	}

	n, _ := strconv.Atoi(token())
	steps, _ := strconv.ParseInt(token(), 10, 64)
	dt := num()
	P := num()

	x := make([]float64, n+1)
	v := make([]float64, n)
	m := make([]float64, n)
	k := make([]float64, n)
	r := make([]float64, n)
	c := make([]float64, n)
	for i := 0; i < n; i++ {
		x[i] = num()
		v[i] = num()
		m[i] = num()
		k[i] = num()
		r[i] = num()
		c[i] = num()
	}

	simulate(n, steps, dt, P, x, v, m, k, r, c)

	var K, U, X float64
	best := -1.0
	J := 0
	x[n] = x[0] + P
	for i := 0; i < n; i++ {
		K += float64(float64(0.5*m[i])*v[i]) * v[i]
		st := float64(x[i+1]-x[i]) - r[i]
		U += float64(float64(0.5*k[i])*st) * st
		X += x[i]
		if a := math.Abs(v[i]); a > best {
			best = a
			J = i
		}
	}

	w := bufio.NewWriter(os.Stdout)
	w.WriteString("kinetic " + strconv.FormatFloat(K, 'e', -1, 64) + "\n")
	w.WriteString("potential " + strconv.FormatFloat(U, 'e', -1, 64) + "\n")
	w.WriteString("position " + strconv.FormatFloat(X, 'e', -1, 64) + "\n")
	w.WriteString("fastest " + strconv.Itoa(J) + "\n")
	w.Flush()
}
