"""Save the straightforward reference solutions as standalone programs of a pseudo-author "reference".

The measurement scripts then time them like any model-written plain.py, as the "simple Python" baseline.
"""

from bench import config as C
from bench.common import write_json, write_text, sha256


def main():
    body = (C.BENCH / "reference.py").read_text(encoding="utf-8").split("\ndef batch():")[0]
    for task in C.TASKS:
        folder = C.PROGRAMS / "reference" / task
        main_block = (f'\nif __name__ == "__main__":\n'
                      f'    output = solve({task!r}, sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)\n'
                      f'    print(output, end="")\n')
        write_text(folder / "plain.py", body + main_block)
        write_json(folder / "meta.json", dict(
            author="reference", task=task, source="bench/reference.py",
            source_sha256=sha256(C.BENCH / "reference.py"),
            note="Straightforward standard-library solution written for clarity by GPT-6.1 Sol in the harness pass; "
                 "it defines the expected outputs and is timed as the simple-Python baseline."))
        print(folder / "plain.py")


if __name__ == "__main__":
    main()
