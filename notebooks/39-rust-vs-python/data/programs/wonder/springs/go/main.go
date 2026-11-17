package main

import (
	"math"
	"os"
	"strconv"
	"strings"
)

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	// FieldsFunc-free fast tokenization using Fields on string (allocates tokens but input small)
	toks := strings.Fields(string(data))
	idx := 0
	nextF := func() float64 {
		f, _ := strconv.ParseFloat(toks[idx], 64)
		idx++
		return f
	}
	N64, _ := strconv.ParseInt(toks[0], 10, 64)
	S64, _ := strconv.ParseInt(toks[1], 10, 64)
	idx = 2
	dt := nextF()
	P := nextF()
	N := int(N64)
	S := S64
	x := make([]float64, N)
	v := make([]float64, N)
	m := make([]float64, N)
	k := make([]float64, N)
	r := make([]float64, N)
	c := make([]float64, N)
	dtm := make([]float64, N)
	for i := 0; i < N; i++ {
		x[i] = nextF()
		v[i] = nextF()
		m[i] = nextF()
		k[i] = nextF()
		r[i] = nextF()
		c[i] = nextF()
		dtm[i] = dt / m[i]
	}
	for step := int64(0); step < S; step++ {
		fLast := k[N-1] * (((x[0] + P) - x[N-1]) - r[N-1])
		prevF := fLast
		last := N - 1
		for i := 0; i < last; i++ {
			fi := k[i] * ((x[i+1] - x[i]) - r[i])
			F := (fi - prevF) - (c[i] * v[i])
			nv := v[i] + dtm[i]*F
			v[i] = nv
			x[i] = x[i] + dt*nv
			prevF = fi
		}
		i := last
		F := (fLast - prevF) - (c[i] * v[i])
		nv := v[i] + dtm[i]*F
		v[i] = nv
		x[i] = x[i] + dt*nv
	}
	var K, U, X float64
	for i := 0; i < N; i++ {
		K += ((0.5 * m[i]) * v[i]) * v[i]
		X += x[i]
	}
	for i := 0; i < N-1; i++ {
		s := (x[i+1] - x[i]) - r[i]
		U += ((0.5 * k[i]) * s) * s
	}
	{
		s := ((x[0] + P) - x[N-1]) - r[N-1]
		U += ((0.5 * k[N-1]) * s) * s
	}
	J := 0
	best := math.Abs(v[0])
	for i := 1; i < N; i++ {
		a := math.Abs(v[i])
		if a > best {
			best = a
			J = i
		}
	}
	buf := make([]byte, 0, 128)
	buf = append(buf, "kinetic "...)
	buf = strconv.AppendFloat(buf, K, 'e', 17, 64)
	buf = append(buf, "\npotential "...)
	buf = strconv.AppendFloat(buf, U, 'e', 17, 64)
	buf = append(buf, "\nposition "...)
	buf = strconv.AppendFloat(buf, X, 'e', 17, 64)
	buf = append(buf, "\nfastest "...)
	buf = strconv.AppendInt(buf, int64(J), 10)
	buf = append(buf, '\n')
	os.Stdout.Write(buf)
}
