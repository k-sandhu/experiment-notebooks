package main

import (
	"os"
)

// ---- word table: open addressing, ids into a byte arena ----
var (
	wSlot  []int32   // id+1, 0 = empty
	wHash  []uint32
	wOff   []int32
	wLen   []int32
	wArena []byte
	wMask  uint32
	wCount int32
)

func wGrow() {
	cap := uint32(len(wSlot))
	cap2 := cap * 2
	s2 := make([]int32, cap2)
	h2 := make([]uint32, cap2)
	m2 := cap2 - 1
	for i := uint32(0); i < cap; i++ {
		if wSlot[i] != 0 {
			j := wHash[i] & m2
			for s2[j] != 0 {
				j = (j + 1) & m2
			}
			s2[j] = wSlot[i]
			h2[j] = wHash[i]
		}
	}
	wSlot = s2
	wHash = h2
	wMask = m2
}

func wordFindOrAdd(w []byte, h uint32) int32 {
	i := h & wMask
	for wSlot[i] != 0 {
		id := wSlot[i] - 1
		o, l := wOff[id], wLen[id]
		if wHash[i] == h && uint32(l) == uint32(len(w)) {
			arenaWords := wArena[o : o+l]
			eq := true
			for k := range w {
				if arenaWords[k] != w[k] {
					eq = false
					break
				}
			}
			if eq {
				return id
			}
		}
		i = (i + 1) & wMask
	}
	if int64(wCount+1)*3 > int64(wMask+1)*2 {
		wGrow()
		i = h & wMask
		for wSlot[i] != 0 {
			i = (i + 1) & wMask
		}
	}
	id := wCount
	o := int32(len(wArena))
	wArena = append(wArena, w...)
	wOff = append(wOff, o)
	wLen = append(wLen, int32(len(w)))
	wSlot[i] = id + 1
	wHash[i] = h
	wCount = id + 1
	return int32(id)
}

func cmpWords(a, b int32) int {
	la, lb := wLen[a], wLen[b]
	oa, ob := wOff[a], wOff[b]
	m := la
	if lb < m {
		m = lb
	}
	for i := int32(0); i < m; i++ {
		d := int(wArena[oa+i]) - int(wArena[ob+i])
		if d != 0 {
			if d < 0 {
				return -1
			}
			return 1
		}
	}
	if la != lb {
		if la < lb {
			return -1
		}
		return 1
	}
	return 0
}

// ---- pair table: open addressing on packed (id1,id2) ----
const pEmpty = uint64(0xFFFFFFFFFFFFFFFF)

var (
	pKey  []uint64
	pCnt  []int32
	pMask uint64
	pCount int64
)

func mixKey(x uint64) uint64 {
	x *= 0x9E3779B97F4A7C15
	x ^= x >> 32
	x *= 0xBF58476D1CE4E5B9
	x ^= x >> 29
	return x
}

func pGrow() {
	cap := pMask + 1
	cap2 := cap * 2
	k2 := make([]uint64, cap2)
	c2 := make([]int32, cap2)
	for i := range k2 {
		k2[i] = pEmpty
	}
	for i := uint64(0); i < cap; i++ {
		if pKey[i] != pEmpty {
			j := mixKey(pKey[i]) & (cap2 - 1)
			for k2[j] != pEmpty {
				j = (j + 1) & (cap2 - 1)
			}
			k2[j] = pKey[i]
			c2[j] = pCnt[i]
		}
	}
	pKey = k2
	pCnt = c2
	pMask = cap2 - 1
}

func pairAdd(key uint64) {
	i := mixKey(key) & pMask
	for pKey[i] != pEmpty {
		if pKey[i] == key {
			pCnt[i]++
			return
		}
		i = (i + 1) & pMask
	}
	if (pCount+1)*3 > int64(pMask+1)*2 {
		pGrow()
		i = mixKey(key) & pMask
		for pKey[i] != pEmpty {
			i = (i + 1) & pMask
		}
	}
	pKey[i] = key
	pCnt[i] = 1
	pCount++
}

// negative if (c1,w1) ranks better (earlier in output) than (c2,w2)
func worse(c1, i1a, i1b, c2, i2a, i2b int32) int {
	if c1 != c2 {
		return int(c2) - int(c1)
	}
	d := cmpWords(i1a, i2a)
	if d != 0 {
		return d
	}
	return cmpWords(i1b, i2b)
}

func siftDown(hCnt, hId1, hId2 []int32, size int) {
	p := 0
	for {
		l, r, s := 2*p+1, 2*p+2, p
		if l < size && worse(hCnt[l], hId1[l], hId2[l], hCnt[s], hId1[s], hId2[s]) > 0 {
			s = l
		}
		if r < size && worse(hCnt[r], hId1[r], hId2[r], hCnt[s], hId1[s], hId2[s]) > 0 {
			s = r
		}
		if s == p {
			break
		}
		hCnt[p], hCnt[s] = hCnt[s], hCnt[p]
		hId1[p], hId1[s] = hId1[s], hId1[p]
		hId2[p], hId2[s] = hId2[s], hId2[p]
		p = s
	}
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(data)
	var totalWords, totalPairs int64

	wSlot = make([]int32, 1<<16)
	wHash = make([]uint32, 1<<16)
	wMask = 1<<16 - 1
	wArena = make([]byte, 0, 1<<16)
	wOff = make([]int32, 0, 4096)
	wLen = make([]int32, 0, 4096)

	pMask = 1<<20 - 1
	pKey = make([]uint64, 1<<20)
	pCnt = make([]int32, 1<<20)
	for i := range pKey {
		pKey[i] = pEmpty
	}

	wbuf := make([]byte, 0, 64)
	prev := int32(-1)

	for i := 0; i < n; i++ {
		c := data[i]
		lc := c | 0x20
		if lc >= 'a' && lc <= 'z' {
			wbuf = append(wbuf, lc)
		} else {
			if len(wbuf) > 0 {
				totalWords++
				h := uint32(2166136261)
				for _, b := range wbuf {
					h = (h ^ uint32(b)) * 16777619
				}
				if h == 0 {
					h = 1
				}
				id := wordFindOrAdd(wbuf, h)
				if prev >= 0 {
					totalPairs++
					pairAdd(uint64(prev)<<32|uint64(id))
				}
				prev = id
				wbuf = wbuf[:0]
			}
			if c == '.' || c == '!' || c == '?' {
				prev = -1
			}
		}
	}
	if len(wbuf) > 0 {
		totalWords++
		h := uint32(2166136261)
		for _, b := range wbuf {
			h = (h ^ uint32(b)) * 16777619
		}
		if h == 0 {
			h = 1
		}
		id := wordFindOrAdd(wbuf, h)
		if prev >= 0 {
			totalPairs++
			pairAdd(uint64(prev)<<32|uint64(id))
		}
	}

	// top 20 via bounded min-heap (root = worst)
	hc := 0
	hCnt := make([]int32, 21)
	hId1 := make([]int32, 21)
	hId2 := make([]int32, 21)
	for i := uint64(0); i <= pMask; i++ {
		if pKey[i] == pEmpty {
			continue
		}
		c1 := pCnt[i]
		id1 := int32(pKey[i] >> 32)
		id2 := int32(pKey[i])
		if hc < 20 {
			q := hc
			hc++
			hCnt[q], hId1[q], hId2[q] = c1, id1, id2
			for q > 0 {
				par := (q - 1) / 2
				if worse(hCnt[q], hId1[q], hId2[q], hCnt[par], hId1[par], hId2[par]) <= 0 {
					break
				}
				hCnt[q], hCnt[par] = hCnt[par], hCnt[q]
				hId1[q], hId1[par] = hId1[par], hId1[q]
				hId2[q], hId2[par] = hId2[par], hId2[q]
				q = par
			}
		} else if worse(c1, id1, id2, hCnt[0], hId1[0], hId2[0]) < 0 {
			hCnt[0], hId1[0], hId2[0] = c1, id1, id2
			siftDown(hCnt, hId1, hId2, hc)
		}
	}

	m := hc
	rCnt := make([]int32, m)
	rId1 := make([]int32, m)
	rId2 := make([]int32, m)
	for idx := m - 1; idx >= 0; idx-- {
		rCnt[idx], rId1[idx], rId2[idx] = hCnt[0], hId1[0], hId2[0]
		hc--
		hCnt[0], hId1[0], hId2[0] = hCnt[hc], hId1[hc], hId2[hc]
		siftDown(hCnt, hId1, hId2, hc)
	}
	for a := 1; a < m; a++ {
		c, i1, i2 := rCnt[a], rId1[a], rId2[a]
		b := a - 1
		for b >= 0 && worse(rCnt[b], rId1[b], rId2[b], c, i1, i2) > 0 {
			rCnt[b+1], rId1[b+1], rId2[b+1] = rCnt[b], rId1[b], rId2[b]
			b--
		}
		rCnt[b+1], rId1[b+1], rId2[b+1] = c, i1, i2
	}

	// output
	out := make([]byte, 0, 4096)
	out = append(out, []byte("words ")...)
	out = appendInt(out, totalWords)
	out = append(out, '\n')
	out = append(out, []byte("pairs ")...)
	out = appendInt(out, totalPairs)
	out = append(out, '\n')
	out = append(out, []byte("distinct ")...)
	out = appendInt(out, pCount)
	out = append(out, '\n')
	for idx := 0; idx < m; idx++ {
		out = appendInt(out, int64(rCnt[idx]))
		out = append(out, ' ')
		out = append(out, wArena[wOff[rId1[idx]]:wOff[rId1[idx]]+wLen[rId1[idx]]]...)
		out = append(out, ' ')
		out = append(out, wArena[wOff[rId2[idx]]:wOff[rId2[idx]]+wLen[rId2[idx]]]...)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}

func appendInt(b []byte, v int64) []byte {
	if v < 0 {
		b = append(b, '-')
		v = -v
	}
	var tmp [20]byte
	i := len(tmp)
	for {
		i--
		tmp[i] = byte('0' + v%10)
		v /= 10
		if v == 0 {
			break
		}
	}
	return append(b, tmp[i:]...)
}
