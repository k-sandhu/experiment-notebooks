"""Count adjacent words using only the Python standard library."""

from collections import Counter
import re
import sys


# Sentence ends become LF; an input LF is an ordinary separator.
TABLE = bytes(
    c + 32 if 65 <= c <= 90 else c if 97 <= c <= 122
    else 10 if c in (46, 33, 63) else 32
    for c in range(256)
)
BLOCK = 4 * 1024 * 1024
SPACES = re.compile(rb" {2,}")
BIGRAMS = re.compile(rb"\b(?=([a-z]+ [a-z]+))")
SENTENCES = re.compile(rb"(?m)^ ?[a-z]")
HEAD = re.compile(rb" ?[a-z]")


def main(path):
    counts = Counter()
    previous = b""
    sentence_count = 0
    carry = b""
    with open(path, "rb") as source:
        while True:
            raw = source.read(BLOCK)
            if raw:
                block = carry + raw.translate(TABLE)
                end = max(block.rfind(b" "), block.rfind(b"\n")) + 1
                carry = block[end:]
                block = block[:end]
            else:
                block = carry
            block = SPACES.sub(b" ", block)
            # Count nonempty sentences. A continued sentence at the beginning
            # of this chunk has already been counted in an earlier chunk.
            sentence_count += len(SENTENCES.findall(block))
            if previous and HEAD.match(block):
                sentence_count -= 1
            scan = previous + b" " + block.lstrip(b" ") if previous else block
            # Lookahead gives overlapping pairs; the boundary prevents suffixes
            # of words from matching. Counter's counting loop runs in C.
            counts.update(BIGRAMS.findall(scan))
            last_stop = block.rfind(b"\n")
            tail = block[last_stop + 1:].rsplit(b" ", 2)
            last_word = tail[-1] or (tail[-2] if len(tail) > 1 else b"")
            if last_word:
                previous = last_word
            elif last_stop >= 0:
                previous = b""
            if not raw:
                break

    pair_count = sum(counts.values())
    # Every nonempty sentence contributes exactly one more word than pairs.
    word_count = pair_count + sentence_count
    distinct = len(counts)
    best = []
    cutoff = 0
    for pair, count in counts.items():
        if count >= cutoff:
            # A space sorts before all letters, so the combined key has the
            # same lexical order as the tuple (first word, second word).
            item = (-count, pair)
            if len(best) < 20:
                best.append(item)
                if len(best) == 20:
                    best.sort()
                    cutoff = -best[-1][0]
            elif item < best[-1]:
                best[-1] = item
                best.sort()
                cutoff = -best[-1][0]
    best.sort()
    lines = [f"words {word_count}", f"pairs {pair_count}", f"distinct {distinct}"]
    lines.extend(f"{-count} {pair.decode('ascii')}" for count, pair in best)
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("ascii"))


if __name__ == "__main__":
    main(sys.argv[1])
