package main

import (
	"bufio"
	"fmt"
	"os"
	"runtime"
	"sort"
)

type pairEntry struct {
	key   uint64
	count uint64
}

type pairTable struct {
	entries []pairEntry
	used    int
	limit   int
}

func pairHash(x uint64) uint64 {
	x ^= x >> 30
	x *= 0xbf58476d1ce4e5b9
	x ^= x >> 27
	x *= 0x94d049bb133111eb
	return x ^ (x >> 31)
}

func (t *pairTable) grow() {
	next := make([]pairEntry, len(t.entries)*2)
	mask := len(next) - 1

	for i := range t.entries {
		e := t.entries[i]
		if e.key == 0 {
			continue
		}
		j := int(pairHash(e.key)) & mask
		for next[j].key != 0 {
			j = (j + 1) & mask
		}
		next[j] = e
	}

	t.entries = next
	t.limit = len(next) * 3 / 4
}

func (t *pairTable) add(key uint64) {
	mask := len(t.entries) - 1
	i := int(pairHash(key)) & mask

	for {
		e := &t.entries[i]
		if e.key == key {
			e.count++
			return
		}
		if e.key == 0 {
			if t.used >= t.limit {
				t.grow()
				t.add(key)
				return
			}
			e.key = key
			e.count = 1
			t.used++
			return
		}
		i = (i + 1) & mask
	}
}

type result struct {
	key   uint64
	count uint64
	order uint64
}

func main() {
	runtime.GOMAXPROCS(1)

	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	n := len(data)
	data = append(data, 0)

	hint := 1024
	if n >= 1<<20 {
		hint = 65536
	}

	dictionary := make(map[string]uint32, hint)
	words := make([]string, 1, hint)

	table := pairTable{
		entries: make([]pairEntry, 1024),
		limit:   768,
	}

	var wordCount, pairCount uint64
	var previous uint32

	for i := 0; i < n; {
		c := data[i]
		lower := c | 0x20

		if lower-'a' <= 'z'-'a' {
			start := i
			for {
				data[i] = lower
				i++
				lower = data[i] | 0x20
				if lower-'a' > 'z'-'a' {
					break
				}
			}

			id := dictionary[string(data[start:i])]
			if id == 0 {
				word := string(data[start:i])
				id = uint32(len(words))
				dictionary[word] = id
				words = append(words, word)
			}

			wordCount++
			if previous != 0 {
				table.add(uint64(previous)<<32 | uint64(id))
				pairCount++
			}
			previous = id
			c = data[i]
		}

		if c == '.' || c == '!' || c == '?' {
			previous = 0
		}
		i++
	}

	out := bufio.NewWriterSize(os.Stdout, 4096)
	fmt.Fprintln(out, "words", wordCount)
	fmt.Fprintln(out, "pairs", pairCount)
	fmt.Fprintln(out, "distinct", table.used)

	if table.used == 0 {
		out.Flush()
		return
	}

	ids := make([]uint32, len(words)-1)
	for i := range ids {
		ids[i] = uint32(i + 1)
	}
	sort.Slice(ids, func(i, j int) bool {
		return words[ids[i]] < words[ids[j]]
	})

	ranks := make([]uint32, len(words))
	for rank, id := range ids {
		ranks[id] = uint32(rank)
	}

	top := make([]result, 0, 20)

	for i := range table.entries {
		e := table.entries[i]
		if e.key == 0 {
			continue
		}

		if len(top) == 20 && e.count < top[19].count {
			continue
		}

		order := uint64(ranks[uint32(e.key>>32)])<<32 |
			uint64(ranks[uint32(e.key)])

		if len(top) == 20 &&
			e.count == top[19].count &&
			order >= top[19].order {
			continue
		}

		pos := len(top)
		if pos < 20 {
			top = append(top, result{})
		} else {
			pos = 19
		}

		for pos > 0 {
			p := top[pos-1]
			if p.count > e.count || (p.count == e.count && p.order < order) {
				break
			}
			top[pos] = p
			pos--
		}

		top[pos] = result{
			key:   e.key,
			count: e.count,
			order: order,
		}
	}

	for _, e := range top {
		fmt.Fprintln(out, e.count, words[uint32(e.key>>32)], words[uint32(e.key)])
	}
	out.Flush()
}
