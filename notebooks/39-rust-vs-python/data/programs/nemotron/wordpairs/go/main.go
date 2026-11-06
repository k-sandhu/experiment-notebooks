package main

import (
	"fmt"
	"math"
	"os"
	"sort"
)

// Open-addressing map from lowercased word bytes to id.
var wordSlots []int // id + 1, 0 means empty
var wordMask int
var wordCount int
var words [][]byte // id -> lowercase word bytes

func wordHash(buf []byte, n int) uint64 {
	h := uint64(2166136261)
	for i := 0; i < n; i++ {
		h ^= uint64(buf[i])
		h *= 16777619
	}
	return h
}

func growWords() {
	old := wordSlots
	n := len(old) * 2
	wordSlots = make([]int, n)
	wordMask = n - 1
	wordCount = 0
	for _, v := range old {
		if v == 0 {
			continue
		}
		w := words[v-1]
		h := int(wordHash(w, len(w)) & uint64(wordMask))
		for wordSlots[h] != 0 {
			h = (h + 1) & wordMask
		}
		wordSlots[h] = v
		wordCount++
	}
}

func intern(buf []byte, n int) int {
	if wordCount*4 >= len(wordSlots)*3 {
		growWords()
	}
	h := int(wordHash(buf, n) & uint64(wordMask))
	for {
		v := wordSlots[h]
		if v == 0 {
			id := wordCount
			wordCount++
			copy := append([]byte(nil), buf[:n]...)
			words = append(words, copy)
			wordSlots[h] = id + 1
			return id
		}
		w := words[v-1]
		if len(w) == n {
			eq := true
			for i := 0; i < n; i++ {
				if w[i] != buf[i] {
					eq = false
					break
				}
			}
			if eq {
				return v - 1
			}
		}
		h = (h + 1) & wordMask
	}
}

// Open-addressing map from packed (id1, id2) pair key to count.
var pairKeys []uint64 // math.MaxUint64 means empty (keys are always < 2^63)
var pairCounts []uint32
var pairMask int
var pairCount int

func pairHash(k uint64) uint64 {
	k ^= k >> 33
	k *= 0xff51afd7ed558ccd
	k ^= k >> 33
	k ^= k >> 32
	return k
}

func growPairs() {
	oldK := pairKeys
	oldC := pairCounts
	n := len(oldK) * 2
	pairKeys = make([]uint64, n)
	pairCounts = make([]uint32, n)
	pairMask = n - 1
	for i := range pairKeys {
		pairKeys[i] = math.MaxUint64
	}
	pairCount = 0
	for i, k := range oldK {
		if k == math.MaxUint64 {
			continue
		}
		h := int(pairHash(k) & uint64(pairMask))
		for pairKeys[h] != math.MaxUint64 {
			h = (h + 1) & pairMask
		}
		pairKeys[h] = k
		pairCounts[h] = oldC[i]
		pairCount++
	}
}

func pairInsert(key uint64) int {
	if (pairCount+1)*4 >= len(pairKeys)*3 {
		growPairs()
	}
	h := int(pairHash(key) & uint64(pairMask))
	for pairKeys[h] != math.MaxUint64 {
		if pairKeys[h] == key {
			return h
		}
		h = (h + 1) & pairMask
	}
	pairKeys[h] = key
	pairCounts[h] = 0
	pairCount++
	return h
}

func wordCmp(x, y []byte) int {
	n := len(x)
	if len(y) < n {
		n = len(y)
	}
	for i := 0; i < n; i++ {
		if x[i] != y[i] {
			return int(x[i]) - int(y[i])
		}
	}
	return len(x) - len(y)
}

var wordsCount uint64
var pairsCount uint64
var prevId = -1

func noteWord(buf []byte, n int) {
	id := intern(buf, n)
	wordsCount++
	if prevId >= 0 {
		pairsCount++
		key := uint64(prevId)<<32 | uint64(id)
		pairCounts[pairInsert(key)]++
	}
	prevId = id
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}

	wordSlots = make([]int, 1<<14)
	wordMask = len(wordSlots) - 1
	words = make([][]byte, 0, 1024)
	pairKeys = make([]uint64, 1<<16)
	pairCounts = make([]uint32, 1<<16)
	pairMask = len(pairKeys) - 1
	for i := range pairKeys {
		pairKeys[i] = math.MaxUint64
	}

	buf := make([]byte, 0, 64)
	for _, c := range data {
		if (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') {
			buf = append(buf, c|0x20)
		} else {
			if len(buf) > 0 {
				noteWord(buf, len(buf))
				buf = buf[:0]
			}
			if c == '.' || c == '!' || c == '?' {
				prevId = -1
			}
		}
	}
	if len(buf) > 0 {
		noteWord(buf, len(buf))
	}

	distinct := pairCount
	type entry struct {
		c, a, b uint32
	}
	ents := make([]entry, 0, distinct)
	for i, k := range pairKeys {
		if k != math.MaxUint64 {
			ents = append(ents, entry{uint32(pairCounts[i]), uint32(k >> 32), uint32(k)})
		}
	}
	sort.Slice(ents, func(i, j int) bool {
		if ents[i].c != ents[j].c {
			return ents[i].c > ents[j].c
		}
		cmp := wordCmp(words[ents[i].a], words[ents[j].a])
		if cmp != 0 {
			return cmp < 0
		}
		return wordCmp(words[ents[i].b], words[ents[j].b]) < 0
	})

	fmt.Printf("words %d\npairs %d\ndistinct %d\n", wordsCount, pairsCount, distinct)
	limit := 20
	if int64(distinct) < int64(limit) {
		limit = int(distinct)
	}
	for i := 0; i < limit; i++ {
		fmt.Printf("%d %s %s\n", ents[i].c, words[ents[i].a], words[ents[i].b])
	}
}
