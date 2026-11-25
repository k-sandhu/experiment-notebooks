You are writing three versions of the same program, one in Rust and two in Python, for a comparison of how
fast and how memory-hungry each version is.

The task is described in SPEC.md in this folder. The folder samples/ holds example inputs (`*.in`), each with
the exact expected output (`*.out`).

Write these three files:

1. `rust/src/main.rs`: Rust, compiled with rustc 1.99 (edition 2024). The Cargo project in `rust/` is set
   up. The only crates you may use are serde (with derive), serde_json, regex and rayon. They are already
   listed in `rust/Cargo.toml` and vendored, so build offline with `cargo build --release --offline` inside
   `rust/`. Do not add other dependencies. You may change the `[profile.release]` settings in
   `rust/Cargo.toml`.
2. `plain.py`: Python 3.13, standard library only.
3. `fast.py`: Python 3.13, standard library plus NumPy 2.2.

Each program is run with the path of one input file as its argument (SPEC.md says if a task takes more
arguments). It reads that file and writes the answer to standard output exactly as SPEC.md describes. The
Python versions are run as `C:\Python313\python.exe plain.py INPUT_PATH` and
`C:\Python313\python.exe fast.py INPUT_PATH`, and the Rust version as the release binary
`rust/target/release/solution.exe INPUT_PATH`.

Your goals, in order:

1. Every version must print the correct output for any valid input as SPEC.md defines it, not only for the
   samples.
2. Make each version as fast as you can. Write each one the way a skilled developer in that language would
   write fast code, using that language's own strengths.

Use a single thread and a single process unless SPEC.md says otherwise. Do not precompute or embed answers,
start other programs, or read any file other than the input.

The programs will be run on Windows 11 on a 16-core laptop, on larger inputs of the same kind; SPEC.md gives
the benchmark size. Test all three versions against every sample before you finish. Work only inside this
folder, and take at most about 45 minutes. Other programs run on this machine at the same time:
never stop a process you did not start yourself, so do not kill processes by name (for example
`taskkill /IM python.exe` or `Stop-Process -Name python`); stop only your own processes, by process ID.

When you are done, reply with a short summary: the algorithm, the main choices you made for speed in each
version, and which samples each version passes.
