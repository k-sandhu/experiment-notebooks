"""Word pair counter: plain Python 3.13, standard library only."""

import re
import sys

_WORD_RE = re.compile(rb"[a-z]+")
_SENTENCE_RE = re.compile(rb"[.!?]")


def main() -> None:
    with open(sys.argv[1], "rb") as handle:
        data = handle.read().lower()

    # Intern words so pair keys are small integers (fast hashing, compact keys).
    word_index: dict[bytes, int] = {}
    words_list: list[bytes] = []
    pair_counts: dict[int, int] = {}
    get_pair = pair_counts.get

    word_count = 0
    pair_count = 0

    # Splitting on sentence enders yields one fragment per sentence; newlines and
    # other separators inside a fragment do not end the sentence.
    for fragment in _SENTENCE_RE.split(data):
        prev = -1
        for match in _WORD_RE.finditer(fragment):
            word = match.group(0)
            word_id = word_index.get(word)
            if word_id is None:
                word_id = len(words_list)
                word_index[word] = word_id
                words_list.append(word)
            word_count += 1
            if prev >= 0:
                key = (prev << 32) | word_id
                pair_counts[key] = get_pair(key, 0) + 1
                pair_count += 1
            prev = word_id

    items = [
        (count, key >> 32, key & 0xFFFFFFFF)
        for key, count in pair_counts.items()
    ]
    # Count descending, then first word, then second word, ascending byte order.
    items.sort(key=lambda item: (-item[0], words_list[item[1]], words_list[item[2]]))

    out = [
        f"words {word_count}",
        f"pairs {pair_count}",
        f"distinct {len(items)}",
    ]
    for count, first_id, second_id in items[:20]:
        out.append(
            "{} {} {}".format(
                count,
                words_list[first_id].decode("ascii"),
                words_list[second_id].decode("ascii"),
            )
        )
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
