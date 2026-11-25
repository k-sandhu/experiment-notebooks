// Heat on a grid: exact integer diffusion with walls and fixed sources.
//
// Values never exceed 9000 (each new value is a floor-average of values <= the largest source), so
// cells are uint16 in a zero-padded grid. With S = sum of the four neighbour terms (wall or outside
// neighbours replaced by the cell's own value), floor((4*o + S) / 8) == (o + (S >> 2)) >> 1 and
// S <= 36000, so every intermediate fits in 16 bits. That lets one uint64 hold four cells (SWAR):
// walls hold 0, so S = up+down+left+right + w*o with w the number of wall/outside neighbours.
//
// Each 4-cell chunk has precomputed lane masks: the bits of w (so w*o is three masked shifts of o),
// an open-cell mask, and the fixed value of sources (walls stay 0).
//
// The iteration is monotone non-decreasing, so a row whose neighbourhood of rows did not change in the
// previous step cannot change; such rows are skipped, and a step with no change ends the run.
package main

import (
	"bufio"
	"fmt"
	"os"
	"unsafe"
)

const (
	low14 = 0x3FFF3FFF3FFF3FFF
	notOp = 0x8000
)

// chunk holds the per-lane constants of four consecutive cells.
type chunk struct {
	b0, b1, b2 uint64 // 0xFFFF in lanes whose wall count has bit 0 / 1 / 2 set
	open       uint64 // 0x7FFF in open-cell lanes (also clears the bit shifted in from the next lane)
	fix        uint64 // source values
}

// stepRow computes cols 1..4*len(meta) of one row from src into dst; reports whether anything changed.
func stepRow(src, dst unsafe.Pointer, meta []chunk, stride uintptr) bool {
	var diff uint64
	up := unsafe.Add(src, -int(stride)*2)
	dn := unsafe.Add(src, int(stride)*2)
	for j := range meta {
		m := &meta[j]
		off := uintptr(j)*8 + 2
		o := *(*uint64)(unsafe.Add(src, off))
		l := *(*uint64)(unsafe.Add(src, off-2))
		r := *(*uint64)(unsafe.Add(src, off+2))
		u := *(*uint64)(unsafe.Add(up, off))
		d := *(*uint64)(unsafe.Add(dn, off))
		s := u + d + l + r + (o & m.b0) + ((o << 1) & m.b1) + ((o << 2) & m.b2)
		v := ((o+((s>>2)&low14))>>1)&m.open | m.fix
		*(*uint64)(unsafe.Add(dst, off)) = v
		diff |= v ^ o
	}
	return diff != 0
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	pos := 0
	readInt := func() int64 {
		for pos < len(data) && (data[pos] < '0' || data[pos] > '9') {
			pos++
		}
		var v int64
		for pos < len(data) && data[pos] >= '0' && data[pos] <= '9' {
			v = v*10 + int64(data[pos]-'0')
			pos++
		}
		return v
	}
	H := int(readInt())
	W := int(readInt())
	S := readInt()

	cpr := (W + 3) / 4 // 4-cell chunks per row
	n := cpr * 4
	stride := n + 2
	total := (H+2)*stride + 8
	a := make([]uint16, total)
	metaCell := make([]uint16, total)
	for i := range metaCell {
		metaCell[i] = notOp
	}
	for r := 0; r < H; r++ {
		for pos < len(data) && (data[pos] == '\r' || data[pos] == '\n' || data[pos] == ' ' || data[pos] == '\t') {
			pos++
		}
		base := (r+1)*stride + 1
		row := data[pos : pos+W]
		for c, ch := range row {
			i := base + c
			if ch == '#' {
				continue
			}
			if ch >= '1' && ch <= '9' {
				v := uint16(1000 * int(ch-'0'))
				metaCell[i] = notOp | v
				a[i] = v
			} else {
				metaCell[i] = 0
			}
		}
		pos += W
	}
	isWall := func(i int) uint16 {
		if metaCell[i] == notOp {
			return 1
		}
		return 0
	}
	for r := 1; r <= H; r++ {
		for c := 1; c <= W; c++ {
			i := r*stride + c
			if metaCell[i] == 0 {
				metaCell[i] = isWall(i-1) + isWall(i+1) + isWall(i-stride) + isWall(i+stride)
			}
		}
	}
	meta := make([]chunk, (H+2)*cpr)
	for r := 1; r <= H; r++ {
		for j := 0; j < cpr; j++ {
			ck := &meta[r*cpr+j]
			for k := 0; k < 4; k++ {
				m := metaCell[r*stride+1+4*j+k]
				shift := uint(16 * k)
				if m <= 4 {
					ck.open |= 0x7FFF << shift
					ck.b0 |= uint64(m&1) * 0xFFFF << shift
					ck.b1 |= uint64(m>>1&1) * 0xFFFF << shift
					ck.b2 |= uint64(m>>2&1) * 0xFFFF << shift
				} else {
					ck.fix |= uint64(m&^notOp) << shift
				}
			}
		}
	}
	b := make([]uint16, total)
	copy(b, a)

	changed := make([]bool, H+2)
	nextChanged := make([]bool, H+2)
	for r := 1; r <= H; r++ {
		changed[r] = true
	}
	bufs := [2][]uint16{a, b}
	ci := 0
	for step := int64(0); step < S; step++ {
		any := false
		for r := 1; r <= H; r++ {
			if !(changed[r-1] || changed[r] || changed[r+1]) {
				nextChanged[r] = false
				continue
			}
			off := r * stride
			ch := stepRow(unsafe.Pointer(&bufs[ci][off]), unsafe.Pointer(&bufs[ci^1][off]), meta[r*cpr:(r+1)*cpr], uintptr(stride))
			nextChanged[r] = ch
			any = any || ch
		}
		// Skipped rows hold equal values in both buffers, so swapping is safe.
		ci ^= 1
		changed, nextChanged = nextChanged, changed
		if !any {
			break
		}
	}

	cur := bufs[ci]
	var sum, checksum int64
	best, bestR, bestC := -1, 0, 0
	for r := 0; r < H; r++ {
		base := (r+1)*stride + 1
		idx0 := int64(r)*int64(W) + 1
		for c := 0; c < W; c++ {
			if metaCell[base+c] > 4 {
				continue
			}
			v := int(cur[base+c])
			sum += int64(v)
			checksum += int64(v) * (idx0 + int64(c))
			if v > best {
				best, bestR, bestC = v, r, c
			}
		}
	}
	out := bufio.NewWriter(os.Stdout)
	fmt.Fprintf(out, "sum %d\nmax %d %d %d\nchecksum %d\n", sum, best, bestR, bestC, checksum)
	out.Flush()
}
