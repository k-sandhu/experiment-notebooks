package main

import (
	"os"
)

var buf []byte
var pos int

func readInt() int {
	for buf[pos] < '0' || buf[pos] > '9' {
		pos++
	}
	x := 0
	for buf[pos] >= '0' && buf[pos] <= '9' {
		x = x*10 + int(buf[pos]-'0')
		pos++
	}
	return x
}

func putLong(ob []byte, op int, x int64) int {
	if x == 0 {
		ob[op] = '0'
		return op + 1
	}
	t := op
	for x > 0 {
		ob[op] = byte('0' + x%10)
		op++
		x /= 10
	}
	for a, b := t, op-1; a < b; a, b = a+1, b-1 {
		ob[a], ob[b] = ob[b], ob[a]
	}
	return op
}

func main() {
	buf, _ = os.ReadFile(os.Args[1])
	n := readInt()
	m := readInt()
	q := readInt()

	eu := make([]int32, m)
	ev := make([]int32, m)
	ew := make([]int32, m)
	start := make([]int32, n+1)
	for i := 0; i < m; i++ {
		u := readInt()
		v := readInt()
		w := readInt()
		eu[i] = int32(u)
		ev[i] = int32(v)
		ew[i] = int32(w)
		start[u+1]++
		start[v+1]++
	}
	for i := 0; i < n; i++ {
		start[i+1] += start[i]
	}
	e2 := start[n]
	adjV := make([]int32, e2)
	adjW := make([]int32, e2)
	posArr := make([]int32, n)
	copy(posArr, start[:n])
	for i := 0; i < m; i++ {
		u, v, w := eu[i], ev[i], ew[i]
		adjV[posArr[u]] = v
		adjW[posArr[u]] = w
		posArr[u]++
		adjV[posArr[v]] = u
		adjW[posArr[v]] = w
		posArr[v]++
	}

	// Dial's bucket queue: weights are 1..1000, so a circular array of 1001
	// buckets (singly linked lists through the arena slice) holds all pending
	// distances. Stale entries are skipped via the dist check.
	const nb = 1001
	arena := make([]int32, 2*m+2)
	nextIn := make([]int32, 2*m+2)
	head := make([]int32, nb)

	dist := make([]int32, n)
	settled := make([]bool, n)
	ob := make([]byte, q*80+16)
	op := 0

	for qi := 0; qi < q; qi++ {
		s := readInt()
		for i := range dist {
			dist[i] = -1
		}
		for i := range settled {
			settled[i] = false
		}
		for i := range head {
			head[i] = -1
		}
		cnt := 0
		dist[s] = 0
		arena[cnt] = int32(s)
		nextIn[cnt] = -1
		head[0] = int32(cnt)
		cnt++
		remaining := 1
		idx := 0
		d := 0
		for remaining > 0 {
			e := int(head[idx])
			if e < 0 {
				idx++
				if idx == nb {
					idx = 0
				}
				d++
				continue
			}
			head[idx] = nextIn[e]
			remaining--
			v := int(arena[e])
			if settled[v] || int(dist[v]) != d {
				continue
			}
			settled[v] = true
			end := start[v+1]
			for i := start[v]; i < end; i++ {
				u := int(adjV[i])
				if settled[u] {
					continue
				}
				nd := d + int(adjW[i])
				du := int(dist[u])
				if du < 0 || nd < du {
					dist[u] = int32(nd)
					b := nd % nb
					arena[cnt] = int32(u)
					nextIn[cnt] = head[b]
					head[b] = int32(cnt)
					cnt++
					remaining++
				}
			}
		}
		var total int64
		var far int64
		farNode := s
		r := 0
		for v := 0; v < n; v++ {
			dd := dist[v]
			if dd >= 0 {
				r++
				total += int64(dd)
				if int64(dd) > far || (int64(dd) == far && v < farNode) {
					far = int64(dd)
					farNode = v
				}
			}
		}
		op = putLong(ob, op, int64(s))
		ob[op] = ' '
		op++
		op = putLong(ob, op, int64(r))
		ob[op] = ' '
		op++
		op = putLong(ob, op, total)
		ob[op] = ' '
		op++
		op = putLong(ob, op, far)
		ob[op] = ' '
		op++
		op = putLong(ob, op, int64(farNode))
		ob[op] = '\n'
		op++
	}
	os.Stdout.Write(ob[:op])
}
