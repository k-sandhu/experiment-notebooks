package main

import (
	"os"
)

// Word pairs: count adjacent word pairs within sentences, report totals and top 20.

var buf []byte

// pair table: open addressing, key -> count, cnt 0 = empty slot
var pKeys []uint64
var pCnt []uint32
var pMask uint64
var pFilled uint64

// word interning: words live inside the lowercased input buffer
var wTab []int32 // slot -> id + 1
var wOff, wLen []int32
var wHsh []uint32
var wMask uint64
var wCount int32

var words, pairs uint64

func isLetter(c byte) bool { return (c|32)-'a' <= 25 }

func mix64(x uint64) uint64 {
	x += 0x9E3779B97F4A7C15
	x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9
	x = (x ^ (x >> 27)) * 0x94D049BB133111EB
	return x ^ (x >> 31)
}

func addPair(key uint64) {
	if (pFilled+1)*4 > (pMask+1)*3 {
		growPairs()
	}
	i := mix64(key) & pMask
	for {
		if pCnt[i] == 0 {
			pKeys[i] = key
			pCnt[i] = 1
			pFilled++
			return
		}
		if pKeys[i] == key {
			pCnt[i]++
			return
		}
		i = (i + 1) & pMask
	}
}

func growPairs() {
	ok := pKeys
	oc := pCnt
	ns := uint64(len(ok)) * 2
	pKeys = make([]uint64, ns)
	pCnt = make([]uint32, ns)
	pMask = ns - 1
	for j := range ok {
		if c := oc[j]; c != 0 {
			key := ok[j]
			i := mix64(key) & pMask
			for pCnt[i] != 0 {
				i = (i + 1) & pMask
			}
			pKeys[i] = key
			pCnt[i] = c
		}
	}
}

func intern(o, l int32, h uint32) int32 {
	if uint64(wCount+1)*2 > wMask+1 {
		growWords()
	}
	i := uint64(h) & wMask
	for {
		slot := wTab[i]
		if slot == 0 {
			id := wCount
			wCount++
			wOff[id] = o
			wLen[id] = l
			wHsh[id] = h
			wTab[i] = id + 1
			return id
		}
		id := slot - 1
		if wHsh[id] == h && wLen[id] == l && eqBytes(wOff[id], o, l) {
			return id
		}
		i = (i + 1) & wMask
	}
}

func eqBytes(a, b, l int32) bool {
	for k := int32(0); k < l; k++ {
		if buf[a+k] != buf[b+k] {
			return false
		}
	}
	return true
}

func growWords() {
	ot := wTab
	ns := uint64(len(ot)) * 2
	wTab = make([]int32, ns)
	wMask = ns - 1
	for j := range ot {
		if slot := ot[j]; slot != 0 {
			id := slot - 1
			i := uint64(wHsh[id]) & wMask
			for wTab[i] != 0 {
				i = (i + 1) & wMask
			}
			wTab[i] = id + 1
		}
	}
}

func cmpWord(a, b int32) int {
	o1, l1, o2, l2 := wOff[a], wLen[a], wOff[b], wLen[b]
	m := l1
	if l2 < m {
		m = l2
	}
	for k := int32(0); k < m; k++ {
		if d := int(buf[o1+k]) - int(buf[o2+k]); d != 0 {
			return d
		}
	}
	return int(l1) - int(l2)
}

func cmpWords(a, b uint64) int {
	if c := cmpWord(int32(a>>32), int32(b>>32)); c != 0 {
		return c
	}
	return cmpWord(int32(a), int32(b))
}

func worse(ka uint64, ca uint32, kb uint64, cb uint32) bool {
	if ca != cb {
		return ca < cb
	}
	return cmpWords(ka, kb) > 0
}

func main() {
	if len(os.Args) < 2 {
		os.Stderr.WriteString("usage: solution INPUT_PATH\n")
		os.Exit(1)
	}
	var err error
	buf, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Stderr.WriteString(err.Error() + "\n")
		os.Exit(1)
	}
	n := len(buf)
	for i := 0; i < n; i++ {
		c := buf[i]
		if c >= 'A' && c <= 'Z' {
			buf[i] = c + 32
		}
	}

	ps := uint64(1 << 20)
	for ps < uint64(n)/8 { // distinct pairs scale with input size; avoid rehashing
		ps <<= 1
	}
	pKeys = make([]uint64, ps)
	pCnt = make([]uint32, ps)
	pMask = ps - 1

	wTab = make([]int32, 1<<16)
	wMask = 1<<16 - 1
	wOff = make([]int32, 1<<16)
	wLen = make([]int32, 1<<16)
	wHsh = make([]uint32, 1<<16)

	var prev int32 = -1 // no previous word in current sentence
	i := 0
	for i < n {
		c := buf[i]
		if isLetter(c) {
			start := i
			h := uint32(0x811C9DC5)
			for {
				h = (h ^ uint32(buf[i])) * 0x01000193
				i++
				if i >= n || !isLetter(buf[i]) {
					break
				}
			}
			id := intern(int32(start), int32(i-start), h)
			words++
			if prev >= 0 {
				addPair(uint64(uint32(prev))<<32 | uint64(uint32(id)))
				pairs++
			}
			prev = id
		} else {
			if c == '.' || c == '!' || c == '?' {
				prev = -1
			}
			i++
		}
	}

	// Keep the 20 best pairs in a min-heap while scanning the pair table.
	hKey := make([]uint64, 20)
	hCnt := make([]uint32, 20)
	hn := 0
	for j := uint64(0); j <= pMask; j++ {
		cnt := pCnt[j]
		if cnt == 0 {
			continue
		}
		key := pKeys[j]
		if hn < 20 {
			k := hn
			hn++
			hKey[k] = key
			hCnt[k] = cnt
			for k > 0 {
				p := (k - 1) / 2
				if worse(hKey[k], hCnt[k], hKey[p], hCnt[p]) {
					hKey[p], hKey[k] = hKey[k], hKey[p]
					hCnt[p], hCnt[k] = hCnt[k], hCnt[p]
					k = p
				} else {
					break
				}
			}
		} else if worse(hKey[0], hCnt[0], key, cnt) {
			hKey[0] = key
			hCnt[0] = cnt
			k := 0
			for {
				l, r, m := 2*k+1, 2*k+2, k
				if l < hn && worse(hKey[l], hCnt[l], hKey[m], hCnt[m]) {
					m = l
				}
				if r < hn && worse(hKey[r], hCnt[r], hKey[m], hCnt[m]) {
					m = r
				}
				if m == k {
					break
				}
				hKey[m], hKey[k] = hKey[k], hKey[m]
				hCnt[m], hCnt[k] = hCnt[k], hCnt[m]
				k = m
			}
		}
	}
	for a := 0; a < hn; a++ {
		best := a
		for b := a + 1; b < hn; b++ {
			if hCnt[b] > hCnt[best] ||
				(hCnt[b] == hCnt[best] && cmpWords(hKey[b], hKey[best]) < 0) {
				best = b
			}
		}
		if best != a {
			hKey[a], hKey[best] = hKey[best], hKey[a]
			hCnt[a], hCnt[best] = hCnt[best], hCnt[a]
		}
	}

	out := make([]byte, 0, 4096)
	out = appendUint(out, "words ", words, '\n')
	out = appendUint(out, "pairs ", pairs, '\n')
	out = appendUint(out, "distinct ", pFilled, '\n')
	for k := 0; k < hn; k++ {
		key := hKey[k]
		w1, w2 := int32(key>>32), int32(key)
		out = appendUint(out, "", uint64(hCnt[k]), ' ')
		out = append(out, buf[wOff[w1]:wOff[w1]+wLen[w1]]...)
		out = append(out, ' ')
		out = append(out, buf[wOff[w2]:wOff[w2]+wLen[w2]]...)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}

func appendUint(dst []byte, prefix string, v uint64, suffix byte) []byte {
	dst = append(dst, prefix...)
	var tmp [24]byte
	k := len(tmp)
	for {
		k--
		tmp[k] = byte('0' + v%10)
		v /= 10
		if v == 0 {
			break
		}
	}
	dst = append(dst, tmp[k:]...)
	return append(dst, suffix)
}
