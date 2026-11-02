"""Resumable build, correctness and timing commands for Windows."""

import argparse
import ast
import hashlib
import io
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import tokenize
import tomllib
from pathlib import Path

import psutil

from bench import config as C
from bench.common import append_csv, manifest, read_csv, remove_tree, sha256, utc_now, vendor_config, write_json, write_text
from bench.compare import compare
from bench.winjob import cpu_sets, run

ACCOUNT_FIELDS = ["wall_seconds", "user_seconds", "kernel_seconds", "cpu_seconds", "cpu_wall_ratio", "peak_job_commit",
                  "peak_process_commit", "peak_working_set", "processes", "exit_code", "timed_out", "affinity", "active_at_exit",
                  "other_busy_cores"]
RUN_FIELDS = ["key", "author", "task", "variant", "input", "workers", "repeat", "status", "detail", "input_sha256", "expected_sha256", "binary_sha256", "harness_version",
              "source_sha256", "stdout", "stderr", "stdout_path", "stderr_path", "started_utc"] + ACCOUNT_FIELDS
BUILD_FIELDS = ["key", "author", "task", "status", "compiler_errors", "clean_seconds", "incremental_seconds", "binary_bytes",
                "binary_sha256", "crates_kept", "pruned_crates", "unpruned_fallback", "source_sha256"]
LOC_FIELDS = ["key", "author", "task", "variant", "file", "total_lines", "code_lines", "bytes", "unsafe_blocks", "detail"]


def fingerprint(folder):
    digest = hashlib.sha256()
    if folder.exists():
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix in (".py", ".rs", ".toml") and "target" not in path.parts:
                digest.update(path.relative_to(folder).as_posix().encode())
                digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def key_for(*values):
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(map(toml_value, value)) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{json.dumps(k)} = {toml_value(v)}" for k, v in value.items()) + " }"
    raise ValueError(f"Unsupported Cargo TOML value: {value!r}")


def dependencies(document):
    """Include target-specific, dev and build dependencies in the allow-list check."""
    result = []
    for key, value in document.items():
        if key in ("dependencies", "dev-dependencies", "build-dependencies"):
            result.append(value)
        elif isinstance(value, dict):
            result.extend(dependencies(value))
    return result


def rust_without_comments(text, keep_literals=True):
    """Strip nested block and line comments, preserving strings and line numbers."""
    # Strings must stay intact for LOC; comment delimiters within quoted strings are not comments.
    result, i, depth = [], 0, 0
    while i < len(text):
        if depth:
            if text.startswith("/*", i):
                depth += 1
                result.extend("  ")
                i += 2
            elif text.startswith("*/", i):
                depth -= 1
                result.extend("  ")
                i += 2
            else:
                result.append("\n" if text[i] == "\n" else " ")
                i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            if end == -1:
                end = len(text)
            result.extend(" " * (end - i))
            i = end
        elif text.startswith("/*", i):
            depth, i = 1, i + 2
            result.extend("  ")
        elif (raw := re.match(r'(?:br|r)(#*)"', text[i:])):
            terminator = '"' + raw[1]
            end = text.find(terminator, i + raw.end())
            end = len(text) if end < 0 else end + len(terminator)
            result.extend(text[i:end] if keep_literals else "".join("\n" if c == "\n" else " " for c in text[i:end]))
            i = end
        elif text[i] == '"':
            end = i + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                elif text[end] == '"':
                    end += 1
                    break
                else:
                    end += 1
            result.extend(text[i:end] if keep_literals else "".join("\n" if c == "\n" else " " for c in text[i:end]))
            i = end
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def python_code_lines(text):
    docstrings = set()
    detail = ""
    try:
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    docstrings.add((first.lineno, first.col_offset, first.end_lineno, first.end_col_offset))
    except SyntaxError as exc:
        detail = f"syntax error: {exc}"
    rows = set()
    ignored = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING}
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type not in ignored:
                if any((r1, c1) <= token.start and token.end <= (r2, c2) for r1, c1, r2, c2 in docstrings):
                    continue
                rows.update(range(token.start[0], token.end[0] + 1))
    except (tokenize.TokenError, IndentationError) as exc:
        detail = f"tokenization error: {exc}"
    return len(rows), detail


def version(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=C.VERSION_TIMEOUT, env=C.environment())
        return (result.stdout or result.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return str(exc)


def machine(path):
    import numpy as np
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
        cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    battery = psutil.sensors_battery()
    write_json(path, dict(cpu_name=cpu_name, physical_cores=psutil.cpu_count(logical=False), logical_processors=psutil.cpu_count(),
                          **cpu_sets(), ram_bytes=psutil.virtual_memory().total, windows=platform.platform(),
                          windows_build=sys.getwindowsversion().build, active_power_plan=version(["powercfg", "/getactivescheme"]),
                          on_ac_power=None if battery is None else battery.power_plugged, python_version=sys.version,
                          numpy_version=np.__version__, rustc_version=version(["rustc", "--version"]),
                          cargo_version=version(["cargo", "--version"]), date_utc=utc_now()))


class Harness:
    def __init__(self, *, selftest=False, tasks=C.TASKS, authors=None, repeats=None):
        self.selftest = selftest
        self.programs = C.WORK / "selftest_programs" if selftest else C.PROGRAMS
        self.results = C.WORK / "selftest_results" if selftest else C.RESULTS
        self.build_root = C.WORK / "selftest_build" if selftest else C.BUILD
        self.run_root = C.WORK / "selftest_runs" if selftest else C.RUNS
        self.tasks = tuple(tasks)
        self.authors = tuple(authors or (["selftest"] if selftest else C.AUTHORS))
        self.repeats = repeats
        self.entries = manifest()
        self.cpu = cpu_sets()
        self.single_processors = self.cpu["p_cores"] if self.cpu["affinity_detection"].startswith("GetSystemCpuSetInformation") else None
        self.done = {}
        self.verified_inputs = set()

    def rows(self, table):
        return read_csv(self.results / f"{table}.csv")

    def append(self, table, row, fields):
        append_csv(self.results / f"{table}.csv", row, fields)
        self.done.setdefault(table, set()).add(row["key"])

    def has(self, table, key):
        if table not in self.done:
            self.done[table] = {r["key"] for r in self.rows(table)}
        return key in self.done[table]

    def source(self, author, task):
        return self.programs / author / task

    def binary(self, author, task):
        return self.build_root / author / task / "target/release/solution.exe"

    def program_list(self, task):
        return [(a, v) for a in self.authors for v in C.VARIANTS]

    def entry(self, task, name):
        return next(e for e in self.entries if e["task"] == task and e["name"] == name)

    def build(self):
        for author in self.authors:
            for task in self.tasks:
                source = self.source(author, task) / "rust"
                source_hash = fingerprint(source)
                key = key_for("build", author, task, source_hash, C.BUILD_REPEATS, str(C.VENDOR))
                previous = next((r for r in self.rows("builds") if r["key"] == key), None)
                if previous and (previous["status"] != "ok" or self.binary(author, task).exists()):
                    continue
                row = dict.fromkeys(BUILD_FIELDS, "")
                row.update(key=key, author=author, task=task, source_sha256=source_hash, status="missing", unpruned_fallback=False)
                if not (source / "src/main.rs").exists() or not (source / "Cargo.toml").exists():
                    self.append("builds", row, BUILD_FIELDS)
                    continue
                try:
                    document = tomllib.loads((source / "Cargo.toml").read_text(encoding="utf-8"))
                    dep_tables = dependencies(document)
                    disallowed = [k for table in dep_tables for k, v in table.items()
                                  if k not in C.ALLOWED_CRATES or isinstance(v, dict) and
                                  (v.get("package", k) not in C.ALLOWED_CRATES or "path" in v or "git" in v)]
                    if disallowed:
                        row.update(status="disallowed_dependency", compiler_errors=", ".join(sorted(set(disallowed))))
                        self.append("builds", row, BUILD_FIELDS)
                        continue
                    project = self.build_root / author / task
                    remove_tree(project, self.build_root)
                    project.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(source / "src", project / "src")
                    vendor_config(project)
                    original = (source / "Cargo.toml").read_text(encoding="utf-8")
                    code = "\n".join(rust_without_comments(p.read_text(encoding="utf-8"), keep_literals=False) for p in source.rglob("*.rs"))
                    named = {k for table in dep_tables for k in table if re.search(rf"(?<![\w:])(?:::)?{re.escape(k)}\s*(?:::|!)|\b(?:use|extern\s+crate)\s+(?:::)?{re.escape(k)}\b", code)}
                    all_crates = {k for table in dep_tables for k in table}
                    for table in dep_tables:
                        for name in list(table):
                            if name not in named:
                                del table[name]
                    pruned = "\n".join(f"{json.dumps(k)} = {toml_value(v)}" for k, v in document.items()) + "\n"
                    write_text(project / "Cargo.toml", pruned)
                    kept = named
                    clean_times, errors = [], ""

                    def compile_one(label):
                        scratch = self.run_root / "build" / author / task / label
                        result = run(["cargo", "build", "--release", "--offline"], project,
                                     scratch / "stdout.txt", scratch / "stderr.txt", C.BUILD_TIMEOUT)
                        error = (scratch / "stderr.txt").read_text(encoding="utf-8", errors="replace")
                        return result, "\n".join(error.splitlines()[:40])

                    for repeat in range(C.BUILD_REPEATS):
                        remove_tree(project / "target", self.build_root)
                        result, errors = compile_one(f"clean_{repeat}")
                        if result["exit_code"] or result["timed_out"]:
                            if repeat == 0 and named != all_crates:
                                write_text(project / "Cargo.toml", original)
                                remove_tree(project / "target", self.build_root)
                                fallback, fallback_errors = compile_one("unpruned")
                                if fallback["exit_code"] == 0 and not fallback["timed_out"]:
                                    row["unpruned_fallback"] = True
                                    kept = all_crates
                                    result = fallback
                                else:
                                    errors += "\nUnpruned:\n" + fallback_errors
                                    break
                            else:
                                break
                        clean_times.append(result["wall_seconds"])
                    row.update(clean_seconds=json.dumps(clean_times), crates_kept=json.dumps(sorted(kept)),
                               pruned_crates=json.dumps(sorted(all_crates - kept)))
                    if len(clean_times) != C.BUILD_REPEATS:
                        row.update(status="build_failed", compiler_errors=errors)
                    else:
                        # Ensure an observable timestamp change even on coarse filesystems.
                        main = project / "src/main.rs"
                        stamp = time.time() + 1
                        os.utime(main, (stamp, stamp))
                        incremental, errors = compile_one("incremental")
                        if incremental["exit_code"] or incremental["timed_out"]:
                            row.update(status="build_failed", compiler_errors=errors)
                        else:
                            binary = self.binary(author, task)
                            row.update(status="ok", incremental_seconds=incremental["wall_seconds"],
                                       binary_bytes=binary.stat().st_size, binary_sha256=sha256(binary))
                except (ValueError, OSError, tomllib.TOMLDecodeError) as exc:
                    row.update(status="build_failed", compiler_errors=str(exc))
                row["compiler_errors"] = "\n".join(str(row["compiler_errors"]).splitlines()[:40])
                self.append("builds", row, BUILD_FIELDS)
                print("build", author, task, row["status"], row["crates_kept"], flush=True)

    def loc(self):
        for author in self.authors:
            for task in self.tasks:
                source = self.source(author, task)
                files = [("rust", p) for p in sorted((source / "rust/src").rglob("*.rs"))]
                files += [(v, source / f"{v}.py") for v in ("plain", "fast") if (source / f"{v}.py").exists()]
                for variant, path in files:
                    relative = path.relative_to(source).as_posix()
                    key = key_for("loc", author, task, relative, sha256(path))
                    if self.has("loc", key):
                        continue
                    text = path.read_text(encoding="utf-8")
                    if variant == "rust":
                        code = rust_without_comments(text)
                        code_lines, detail = sum(bool(line.strip()) for line in code.splitlines()), ""
                        unsafe = len(re.findall(r"\bunsafe\s*\{", rust_without_comments(text, keep_literals=False)))
                    else:
                        code_lines, detail = python_code_lines(text)
                        unsafe = ""
                    self.append("loc", dict(key=key, author=author, task=task, variant=variant, file=relative,
                                            total_lines=len(text.splitlines()), code_lines=code_lines,
                                            bytes=path.stat().st_size, unsafe_blocks=unsafe, detail=detail), LOC_FIELDS)

    def availability(self, author, task, variant):
        source = self.source(author, task)
        if variant != "rust":
            return "" if (source / f"{variant}.py").exists() else "missing"
        builds = [r for r in self.rows("builds") if r["author"] == author and r["task"] == task
                  and r["source_sha256"] == fingerprint(source / "rust")]
        if not (source / "rust/src/main.rs").exists():
            return "missing"
        return "" if builds and builds[-1]["status"] == "ok" and self.binary(author, task).exists() else "build_failed"

    def run_one(self, table, author, task, variant, name, workers, repeat, timeout):
        entry = self.entry(task, name)
        source = self.source(author, task)
        source_hash = fingerprint(source / "rust") if variant == "rust" else (sha256(source / f"{variant}.py") if (source / f"{variant}.py").exists() else "missing")
        # Executable hash captures compiler/profile changes, not just source edits.
        binary_hash = sha256(self.binary(author, task)) if variant == "rust" and self.binary(author, task).exists() else ""
        expected_path = C.DATA / "expected" / task / f"{name}.out"
        expected_hash = sha256(expected_path)
        key = key_for(table, author, task, variant, name, workers, repeat, entry["sha256"], source_hash,
                      binary_hash, expected_hash, self.cpu["p_cores"], C.THREAD_ENV, C.HARNESS_VERSION)
        cached = next((r for r in self.rows(table) if r["key"] == key), None)
        if cached:
            return cached
        row = dict.fromkeys(RUN_FIELDS, "")
        row.update(key=key, author=author, task=task, variant=variant, input=name, workers=workers, repeat=repeat,
                   source_sha256=source_hash, input_sha256=entry["sha256"], expected_sha256=expected_hash,
                   binary_sha256=binary_hash, harness_version=C.HARNESS_VERSION, started_utc=utc_now())
        unavailable = self.availability(author, task, variant)
        if unavailable:
            row["status"] = unavailable
        else:
            if (task, name) not in self.verified_inputs:
                if sha256(C.input_path(task, name)) != entry["sha256"]:
                    raise ValueError(f"Input hash differs from manifest: {task}/{name}")
                self.verified_inputs.add((task, name))
            scratch = self.run_root / table / author / task / variant / f"{name}_w{workers}_r{repeat}"
            stdout, stderr = scratch / "stdout.txt", scratch / "stderr.txt"
            program = self.binary(author, task) if variant == "rust" else source / f"{variant}.py"
            command = [str(program)] if variant == "rust" else [str(C.PYTHON), "-X", "utf8", str(program)]
            command.append(str(C.input_path(task, name)))
            if task == "walkers":
                command.append(str(workers))
            result = run(command, scratch, stdout, stderr, timeout, processors=None if task == "walkers" else self.single_processors)
            row.update(result, stdout_path=str(stdout), stderr_path=str(stderr))
            # Decode strictly: invalid UTF-8 is an unreadable reply, not a silent replacement.
            try:
                if stdout.stat().st_size > C.OUTPUT_LIMIT_BYTES:
                    with stdout.open("rb") as stream:
                        got = stream.read(2048).decode("utf-8", errors="replace")
                    decode_error = "stdout exceeds output size limit"
                else:
                    got = stdout.read_text(encoding="utf-8")
                    decode_error = None
            except UnicodeDecodeError as exc:
                got, decode_error = stdout.read_bytes().decode("utf-8", errors="replace"), str(exc)
            with stderr.open("rb") as stream:
                error_excerpt = stream.read(2048).decode("utf-8", errors="replace")[:500]
            row.update(stdout=got[:500], stderr=error_excerpt)
            if result["timed_out"]:
                row["status"] = "timeout"
            elif result["exit_code"]:
                row["status"] = "crashed"
            elif decode_error:
                row.update(status="unreadable", detail=decode_error)
            else:
                row["status"], row["detail"] = compare(task, got, expected_path.read_text(encoding="utf-8"))
        self.append(table, row, RUN_FIELDS)
        print(table, author, task, variant, name, workers, repeat, row["status"], row["wall_seconds"], flush=True)
        return row

    def correct(self):
        for task in self.tasks:
            entries = [e for e in self.entries if e["task"] == task and not e["name"].startswith("sweep")]
            for entry in entries:
                for author, variant in self.program_list(task):
                    workers = [C.CORRECT_WORKERS] if task == "walkers" else [1]
                    if task == "walkers" and entry["name"] == "t1":
                        workers += list(C.CORRECT_EXTRA_WORKERS)
                    for count in workers:
                        self.run_one("correctness", author, task, variant, entry["name"], count, 0, C.CORRECT_TIMEOUT)

    def correct_programs(self, task):
        result = []
        for author, variant in self.program_list(task):
            if self.availability(author, task, variant):
                continue
            source = self.source(author, task)
            digest = fingerprint(source / "rust") if variant == "rust" else sha256(source / f"{variant}.py")
            rows = [r for r in self.rows("correctness") if r["author"] == author and r["task"] == task and r["variant"] == variant
                    and r["source_sha256"] == digest and r["input"] in ("t1", "full")
                    and r["input_sha256"] == self.entry(task, r["input"])["sha256"]]
            rows = [r for r in rows if r["expected_sha256"] == sha256(C.DATA / "expected" / task / f'{r["input"]}.out')
                    and r["harness_version"] == C.HARNESS_VERSION
                    and (variant != "rust" or r["binary_sha256"] == sha256(self.binary(author, task)))]
            by_key = {(r["input"], int(r["workers"])): r for r in rows}
            required = [("t1", C.CORRECT_WORKERS), ("full", C.CORRECT_WORKERS)] if task == "walkers" else [("t1", 1), ("full", 1)]
            if task == "walkers":
                required += [("t1", w) for w in C.CORRECT_EXTRA_WORKERS]
            if all(key in by_key and by_key[key]["status"] == "correct" for key in required):
                result.append((author, variant))
        return result

    def timed(self, table, task_names, input_names, worker_counts, default_repeats):
        rng = random.Random(C.ORDER_SEED)
        for task in task_names:
            if task not in self.tasks:
                continue
            programs = self.correct_programs(task)
            # Warm-ups are persisted too: interrupted commands never discard measured work.
            repeats = {}
            for name in input_names:
                for workers in worker_counts:
                    for author, variant in programs:
                        warm = self.run_one(table + "_warmups", author, task, variant, name, workers, -1, C.MEASURE_TIMEOUT)
                        count = self.repeats or default_repeats
                        if table == "runs" and self.repeats is None and float(warm["wall_seconds"]) > C.SLOW_SECONDS:
                            count = C.SLOW_REPEATS
                        repeats[author, variant, name, workers] = count if warm["status"] == "correct" else 0
            for repeat in range(max(repeats.values(), default=0)):
                # Randomise across sizes/workers as well as programs at each repeat.
                jobs = [key for key, count in repeats.items() if repeat < count]
                rng.shuffle(jobs)
                for author, variant, name, workers in jobs:
                    self.run_one(table, author, task, variant, name, workers, repeat, C.MEASURE_TIMEOUT)

    def bench(self):
        self.timed("runs", self.tasks, ["full"], [1], C.BENCH_REPEATS)

    def sweep(self):
        self.timed("sweep", C.SWEEP_TASKS, list(C.SWEEPS), [1], C.OTHER_REPEATS)

    def scaling(self):
        self.timed("scaling", ["walkers"], ["full"], C.WORKER_COUNTS, C.OTHER_REPEATS)

    def baseline(self):
        project = self.build_root / "baseline" / "template"
        if not (project / "target/release/solution.exe").exists():
            project.mkdir(parents=True, exist_ok=True)
            shutil.copytree(C.BENCH / "template/rust", project, dirs_exist_ok=True)
            vendor_config(project)
            scratch = self.run_root / "baseline_build"
            result = run(["cargo", "build", "--release", "--offline"], project, scratch / "stdout.txt", scratch / "stderr.txt", C.BUILD_TIMEOUT)
            if result["exit_code"] or result["timed_out"]:
                raise RuntimeError((scratch / "stderr.txt").read_text())
        commands = {"python": [str(C.PYTHON), "-X", "utf8", "-c", "pass"],
                    "numpy": [str(C.PYTHON), "-X", "utf8", "-c", "import numpy"],
                    "rust": [str(project / "target/release/solution.exe")]}
        fields = ["key", "variant", "repeat", "started_utc"] + ACCOUNT_FIELDS
        for repeat in range(C.BASELINE_REPEATS):
            for variant, command in commands.items():
                key = key_for("baseline", variant, repeat, command, self.cpu["p_cores"])
                if self.has("baseline", key):
                    continue
                scratch = self.run_root / "baseline" / variant / str(repeat)
                result = run(command, scratch, scratch / "stdout.txt", scratch / "stderr.txt", C.MEASURE_TIMEOUT,
                             processors=self.single_processors)
                self.append("baseline", dict(key=key, variant=variant, repeat=repeat, started_utc=utc_now(), **result), fields)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["machine", "baseline", "build", "loc", "correct", "bench", "sweep", "scaling", "all"])
    parser.add_argument("--selftest", action="store_true", help="Use WORK/selftest_programs and WORK/selftest_results only")
    parser.add_argument("--tasks", nargs="+", choices=C.TASKS, default=C.TASKS)
    parser.add_argument("--authors", nargs="+")
    parser.add_argument("--repeats", type=int)
    args = parser.parse_args()
    if args.repeats is not None and args.repeats < 1:
        parser.error("--repeats must be positive")
    harness = Harness(selftest=args.selftest, tasks=args.tasks, authors=args.authors, repeats=args.repeats)
    commands = ["machine", "baseline", "build", "loc", "correct", "bench", "sweep", "scaling"] if args.command == "all" else [args.command]
    for command in commands:
        if command == "machine":
            path = harness.results / "machine.json" if args.selftest else C.DATA / "machine.json"
            machine(path)
        else:
            getattr(harness, command)()


if __name__ == "__main__":
    main()
