package main

import (
	"bufio"
	"os"
)

func isWs(b byte) bool {
	return b == ' ' || b == '\n' || b == '\r' || b == '\t' || b == '\f' || b == 11
}

var (
	buf    []byte
	pos    int
	tStart int
	tEnd   int
)

func token() []byte {
	for pos < len(buf) && isWs(buf[pos]) {
		pos++
	}
	tStart = pos
	for pos < len(buf) && !isWs(buf[pos]) {
		pos++
	}
	tEnd = pos
	return buf[tStart:tEnd]
}

func nextInt() int {
	for pos < len(buf) && isWs(buf[pos]) {
		pos++
	}
	v := 0
	for pos < len(buf) && !isWs(buf[pos]) {
		v = v*10 + int(buf[pos]-'0')
		pos++
	}
	return v
}

func writeUint(w *bufio.Writer, v uint64) {
	var tmp [20]byte
	k := 0
	if v == 0 {
		tmp[0] = '0'
		k = 1
	}
	for v > 0 {
		tmp[k] = byte('0' + v%10)
		k++
		v /= 10
	}
	for k > 0 {
		k--
		w.WriteByte(tmp[k])
	}
	w.WriteByte('\n')
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	buf = data
	w := bufio.NewWriterSize(os.Stdout, 1<<16)
	defer w.Flush()

	alpha := token()
	a := len(alpha)
	charId := make([]int, 128)
	for i := range charId {
		charId[i] = -1
	}
	for i := 0; i < a; i++ {
		charId[alpha[i]] = i
	}

	ins := make([]int, a)
	del := make([]int, a)
	sub := make([]int, a*a)
	for i := 0; i < a; i++ {
		ins[i] = nextInt()
	}
	for i := 0; i < a; i++ {
		del[i] = nextInt()
	}
	for i := 0; i < a*a; i++ {
		sub[i] = nextInt()
	}
	p := nextInt()

	total := int64(0)

	sIds := make([]int, 1100)
	tIds := make([]int, 1100)
	rowA := make([]int, 1101)
	rowB := make([]int, 1101)

	for q := 0; q < p; q++ {
		tok := token()
		n := len(tok)
		for i := 0; i < n; i++ {
			sIds[i] = charId[tok[i]]
		}
		tok = token()
		m := len(tok)
		for j := 0; j < m; j++ {
			tIds[j] = charId[tok[j]]
		}

		prev := rowA[:m+1]
		cur := rowB[:m+1]
		prev[0] = 0
		for j := 1; j <= m; j++ {
			prev[j] = prev[j-1] + ins[tIds[j-1]]
		}
		for i := 0; i < n; i++ {
			si := sIds[i]
			dc := del[si]
			subBase := si * a
			left := prev[0] + dc
			cur[0] = left
			diag := prev[0]
			for j := 1; j <= m; j++ {
				tj := tIds[j-1]
				best := prev[j] + dc
				if l := left + ins[tj]; l < best {
					best = l
				}
				if d := diag + sub[subBase+tj]; d < best {
					best = d
				}
				cur[j] = best
				left = best
				diag = prev[j]
			}
			prev, cur = cur, prev
		}
		total += int64(prev[m])
		writeUint(w, uint64(prev[m]))
	}

	w.WriteString("total ")
	writeUint(w, uint64(total))
}
