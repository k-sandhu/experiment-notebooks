// Routes: shortest road distances from several sources.
// Multi-source Dijkstra (one run per source) over an undirected graph.
// Go 1.27, standard library only.
//
// Graph is stored in CSR form: start[node..node+1) indexes into gto/gw.
// Distances are int: any simple path has at most N-1 edges of weight <= 1000,
// so a distance never exceeds (N-1)*1000 < 2^31. Totals need int (64-bit here).

package main

import (
	"os"
	"strconv"
	"strings"
)

var buf []byte
var pos int

func nextInt() int {
	for pos < len(buf) && buf[pos] <= 32 {
		pos++
	}
	neg := false
	if pos < len(buf) && buf[pos] == '-' {
		neg = true
		pos++
	}
	v := 0
	for pos < len(buf) && buf[pos] >= '0' && buf[pos] <= '9' {
		v = v*10 + int(buf[pos]-'0')
		pos++
	}
	if neg {
		v = -v
	}
	return v
}

const INF = int(^uint(0) >> 1) // math.MaxInt

var N, M, Q int
var start, gto, gw []int

func main() {
	var err error
	buf, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}

	N = nextInt()
	M = nextInt()
	Q = nextInt()

	deg := make([]int, N+1)
	eu := make([]int, M)
	ev := make([]int, M)
	ew := make([]int, M)
	for i := 0; i < M; i++ {
		u := nextInt()
		v := nextInt()
		w := nextInt()
		eu[i] = u
		ev[i] = v
		ew[i] = w
		deg[u]++
		deg[v]++
	}

	start = make([]int, N+1)
	for i := 0; i < N; i++ {
		start[i+1] = start[i] + deg[i]
	}

	totalEdges := 2 * M
	gto = make([]int, totalEdges)
	gw = make([]int, totalEdges)
	cur := make([]int, N)
	copy(cur, start)
	for i := 0; i < M; i++ {
		u := eu[i]
		v := ev[i]
		w := ew[i]
		p := cur[u]
		cur[u]++
		gto[p] = v
		gw[p] = w
		p = cur[v]
		cur[v]++
		gto[p] = u
		gw[p] = w
	}

	dist := make([]int, N)
	cap := 16
	if M > cap {
		cap = M
	}
	hd := make([]int, 0, cap)
	hn := make([]int, 0, cap)

	push := func(d, n int) {
		i := len(hd)
		hd = append(hd, d)
		hn = append(hn, n)
		for i > 0 {
			p := (i - 1) / 2
			if hd[p] <= d {
				break
			}
			hd[i] = hd[p]
			hn[i] = hn[p]
			i = p
		}
		hd[i] = d
		hn[i] = n
	}

	var sb strings.Builder
	for q := 0; q < Q; q++ {
		s := nextInt()
		for i := range dist {
			dist[i] = INF
		}
		dist[s] = 0
		hd = hd[:0]
		hn = hn[:0]
		push(0, s)
		for len(hd) > 0 {
			d := hd[0]
			u := hn[0]
			last := len(hd) - 1
			hd[0] = hd[last]
			hn[0] = hn[last]
			hd = hd[:last]
			hn = hn[:last]
			if len(hd) > 0 {
				movedD := hd[0]
				movedN := hn[0]
				i := 0
				for {
					l := 2*i + 1
					r := l + 1
					if l >= len(hd) {
						break
					}
					child := l
					if r < len(hd) && hd[r] < hd[l] {
						child = r
					}
					if hd[child] >= movedD {
						break
					}
					hd[i] = hd[child]
					hn[i] = hn[child]
					i = child
				}
				hd[i] = movedD
				hn[i] = movedN
			}
			if d > dist[u] {
				continue
			}
			for e := start[u]; e < start[u+1]; e++ {
				v := gto[e]
				nd := d + gw[e]
				if nd < dist[v] {
					dist[v] = nd
					push(nd, v)
				}
			}
		}

		R := 0
		total := int64(0)
		far := -1
		node := -1
		for i := 0; i < N; i++ {
			d := dist[i]
			if d != INF {
				R++
				total += int64(d)
				if d > far {
					far = d
					node = i
				}
			}
		}
		sb.WriteString(strconv.Itoa(s))
		sb.WriteByte(' ')
		sb.WriteString(strconv.Itoa(R))
		sb.WriteByte(' ')
		sb.WriteString(strconv.FormatInt(total, 10))
		sb.WriteByte(' ')
		sb.WriteString(strconv.Itoa(far))
		sb.WriteByte(' ')
		sb.WriteString(strconv.Itoa(node))
		sb.WriteByte('\n')
	}

	os.Stdout.WriteString(sb.String())
}
