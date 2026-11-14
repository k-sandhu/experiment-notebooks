package main

import (
	"bytes"
	"os"
	"strconv"
)

func mix64(x uint64) uint64 {
	x ^= x >> 32
	x *= 0xd6e8feb86659fd93
	x ^= x >> 32
	return x
}
func isLetter(c byte) bool { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') }
func toLow(c byte) byte {
	if c >= 'A' && c <= 'Z' {
		return c + 32
	}
	return c
}

func main() {
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(buf)

	wcap := 1 << 17
	wmask := wcap - 1
	wtab := make([]int32, wcap)
	for i := range wtab {
		wtab[i] = -1
	}
	whash := make([]uint32, wcap)
	arena := make([]byte, 0, 1<<19)
	woff := make([]uint32, 0, 45000)
	wlen := make([]uint32, 0, 45000)
	var vocab int32

	pcap := 1 << 21
	pmask := pcap - 1
	pkeys := make([]uint64, pcap)
	for i := range pkeys {
		pkeys[i] = ^uint64(0)
	}
	pcounts := make([]uint32, pcap)
	psize := 0

	pairGrow := func() {
		ncap := pcap * 2
		nmask := ncap - 1
		nk := make([]uint64, ncap)
		for i := range nk {
			nk[i] = ^uint64(0)
		}
		nc := make([]uint32, ncap)
		for i := 0; i < pcap; i++ {
			k := pkeys[i]
			if k == ^uint64(0) {
				continue
			}
			idx := int(mix64(k)) & nmask
			for nk[idx] != ^uint64(0) {
				idx = (idx + 1) & nmask
			}
			nk[idx] = k
			nc[idx] = pcounts[i]
		}
		pkeys, pcounts, pcap, pmask = nk, nc, ncap, nmask
	}
	wordGrow := func() {
		ncap := wcap * 2
		nmask := ncap - 1
		nt := make([]int32, ncap)
		for i := range nt {
			nt[i] = -1
		}
		nh := make([]uint32, ncap)
		for i := 0; i < wcap; i++ {
			id := wtab[i]
			if id < 0 {
				continue
			}
			idx := int(whash[i]) & nmask
			for nt[idx] != -1 {
				idx = (idx + 1) & nmask
			}
			nt[idx] = id
			nh[idx] = whash[i]
		}
		wtab, whash, wcap, wmask = nt, nh, ncap, nmask
	}

	var W, T int64
	prev := int32(-1)
	i := 0
	for i < n {
		c := buf[i]
		if isLetter(c) {
			start := i
			var h uint32 = 2166136261
			for i < n && isLetter(buf[i]) {
				h ^= uint32(toLow(buf[i]))
				h *= 16777619
				i++
			}
			length := i - start
			var id int32
			idx := int(h) & wmask
			for {
				cur := wtab[idx]
				if cur < 0 {
					id = vocab
					vocab++
					off := uint32(len(arena))
					for j := start; j < i; j++ {
						arena = append(arena, toLow(buf[j]))
					}
					woff = append(woff, off)
					wlen = append(wlen, uint32(length))
					wtab[idx] = id
					whash[idx] = h
					if int(vocab)*2 > wcap {
						wordGrow()
					}
					break
				}
				if whash[idx] == h && int(wlen[cur]) == length {
					off := int(woff[cur])
					eq := true
					for j := 0; j < length; j++ {
						if arena[off+j] != toLow(buf[start+j]) {
							eq = false
							break
						}
					}
					if eq {
						id = cur
						break
					}
				}
				idx = (idx + 1) & wmask
			}
			W++
			if prev >= 0 {
				T++
				key := (uint64(uint32(prev)) << 32) | uint64(uint32(id))
				pi := int(mix64(key)) & pmask
				for {
					k := pkeys[pi]
					if k == ^uint64(0) {
						pkeys[pi] = key
						pcounts[pi] = 1
						psize++
						if psize*10 > pcap*7 {
							pairGrow()
						}
						break
					}
					if k == key {
						pcounts[pi]++
						break
					}
					pi = (pi + 1) & pmask
				}
			}
			prev = id
		} else {
			if c == '.' || c == '!' || c == '?' {
				prev = -1
			}
			i++
		}
	}

	wordCmp := func(a, b int32) int {
		if a == b {
			return 0
		}
		oa, ob := int(woff[a]), int(woff[b])
		la, lb := int(wlen[a]), int(wlen[b])
		m := la
		if lb < m {
			m = lb
		}
		c := bytes.Compare(arena[oa:oa+m], arena[ob:ob+m])
		if c != 0 {
			return c
		}
		if la < lb {
			return -1
		} else if la > lb {
			return 1
		}
		return 0
	}
	type cand struct {
		count uint32
		a, b  int32
	}
	better := func(x, y cand) bool {
		if x.count != y.count {
			return x.count > y.count
		}
		c := wordCmp(x.a, y.a)
		if c != 0 {
			return c < 0
		}
		return wordCmp(x.b, y.b) < 0
	}
	var top [20]cand
	tsz := 0
	for k := 0; k < pcap; k++ {
		key := pkeys[k]
		if key == ^uint64(0) {
			continue
		}
		cd := cand{pcounts[k], int32(key >> 32), int32(key & 0xffffffff)}
		if tsz < 20 {
			pos := tsz
			tsz++
			for pos > 0 && better(cd, top[pos-1]) {
				top[pos] = top[pos-1]
				pos--
			}
			top[pos] = cd
		} else {
			if !better(cd, top[19]) {
				continue
			}
			pos := 19
			for pos > 0 && better(cd, top[pos-1]) {
				top[pos] = top[pos-1]
				pos--
			}
			top[pos] = cd
		}
	}

	var out bytes.Buffer
	out.Grow(1024)
	out.WriteString("words ")
	out.WriteString(strconv.FormatInt(W, 10))
	out.WriteByte('\n')
	out.WriteString("pairs ")
	out.WriteString(strconv.FormatInt(T, 10))
	out.WriteByte('\n')
	out.WriteString("distinct ")
	out.WriteString(strconv.Itoa(psize))
	out.WriteByte('\n')
	for k := 0; k < tsz; k++ {
		out.WriteString(strconv.Itoa(int(top[k].count)))
		out.WriteByte(' ')
		out.Write(arena[woff[top[k].a] : woff[top[k].a]+wlen[top[k].a]])
		out.WriteByte(' ')
		out.Write(arena[woff[top[k].b] : woff[top[k].b]+wlen[top[k].b]])
		out.WriteByte('\n')
	}
	os.Stdout.Write(out.Bytes())
}
