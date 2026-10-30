"""Prepare isolated author sessions; only the explicit run commands launch a model."""

import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from bench import config as C
from bench.common import append_csv, read_json, remove_tree, sha256, shim_command, utc_now, write_json
from bench.winjob import Accounting, Job


def session_files(author, task):
    files = {"SPEC.md": (C.BENCH / "tasks" / task / "SPEC.md").read_bytes()}
    for path in sorted((C.DATA / "samples" / task).glob("*")):
        if path.suffix in (".in", ".out"):
            files["samples/" + path.name] = path.read_bytes()
    for name in C.input_sets(task):
        if name.startswith("s") and not name.startswith("sweep"):
            for suffix in (".in", ".out"):
                if "samples/" + name + suffix not in files:
                    raise FileNotFoundError(f"Missing sample: {task}/{name}{suffix}")
    for path in sorted((C.BENCH / "template" / "rust").rglob("*")):
        if path.is_file():
            files["rust/" + path.relative_to(C.BENCH / "template" / "rust").as_posix()] = path.read_bytes()
    files["rust/.cargo/config.toml"] = ('[source.crates-io]\nreplace-with = "vendored-sources"\n\n'
                                           f"[source.vendored-sources]\ndirectory = '{C.VENDOR.as_posix()}'\n").encode()
    return files


def request_hash(author, task, files=None):
    files = session_files(author, task) if files is None else files
    author_config = dict(C.AUTHORS[author], private_cargo_home=C.SOL_PRIVATE_CARGO_HOME if author == "sol" else False)
    request = dict(author=author_config, prompt_sha256=sha256(C.BENCH / "AUTHOR_PROMPT.md"),
                   files={name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())})
    return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def prepare(author, task):
    files = session_files(author, task)
    folder = C.SESSIONS / author / task
    remove_tree(folder, C.SESSIONS)
    for name, contents in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    digest = request_hash(author, task, files)
    print(author, task, digest, flush=True)
    return folder, digest


def command_for(author, task):
    config = C.AUTHORS[author]
    executable = shutil.which(config["cli"])
    if executable is None:
        raise FileNotFoundError(config["cli"])
    folder = C.SESSIONS / author / task
    values = dict(session=str(folder), last=str(C.SESSIONS / author / f"{task}.last.md"))
    command = [executable] + [flag.format(**values) for flag in config["flags"]]
    # Popen uses CreateProcess on Windows; .cmd and .bat require the command interpreter.
    return shim_command(command), executable


def event_metadata(path):
    result = dict(reported_model=None, cost_usd=None, usage={}, turns=0, tool_calls=0, final_message="")
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if event.get("model"):
                result["reported_model"] = event["model"]
            if kind == "assistant":
                message = event.get("message", {})
                result["reported_model"] = message.get("model", result["reported_model"])
                blocks = message.get("content", [])
                result["tool_calls"] += sum(b.get("type") == "tool_use" for b in blocks)
                texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
                if texts:
                    result["final_message"] = "\n".join(texts)
            if kind == "result":
                result["cost_usd"] = event.get("total_cost_usd")
                result["usage"] = event.get("usage", {})
                result["turns"] = event.get("num_turns", result["turns"])
                result["final_message"] = event.get("result", result["final_message"])
            if kind == "turn.completed":
                result["turns"] += 1
                for key, value in event.get("usage", {}).items():
                    if isinstance(value, (float, int)):
                        result["usage"][key] = result["usage"].get(key, 0) + value
            if kind == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    result["final_message"] = item.get("text", "")
                elif item.get("type") in ("command_execution", "file_change", "mcp_tool_call", "web_search", "tool_call"):
                    result["tool_calls"] += 1
    return result


def inventory(folder):
    rows = []
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        if any(part in ("target", ".cargo-home") for part in relative.parts) or not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
            rows.append(dict(path=relative.as_posix(), skipped="symlink or outside session"))
            continue
        rows.append(dict(path=relative.as_posix(), bytes=path.stat().st_size, sha256=sha256(path)))
    return rows


def run(author, task, force=False):
    digest = request_hash(author, task)
    destination = C.PROGRAMS / author / task
    meta_path = destination / "meta.json"
    if meta_path.exists() and read_json(meta_path).get("request_hash") == digest and not force:
        print(author, task, "cached", digest, flush=True)
        return
    folder, digest = prepare(author, task)
    command, executable = command_for(author, task)
    env = C.session_environment()
    if author == "sol" and C.SOL_PRIVATE_CARGO_HOME:
        env["CARGO_HOME"] = str(folder / ".cargo-home")
    log = C.DATA / "sessions" / author / f"{task}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    stderr_path = C.SESSIONS / author / f"{task}.stderr.txt"
    # stdin is a file so prompt bytes (including existing line endings) pass unchanged.
    started, start = utc_now(), time.perf_counter()
    timed_out = False
    with Job() as job, log.open("wb") as stdout, stderr_path.open("wb") as stderr, (C.BENCH / "AUTHOR_PROMPT.md").open("rb") as prompt:
        process = job.launch(command, cwd=folder, env=env, stdin=prompt, stdout=stdout, stderr=stderr)
        try:
            process.wait(timeout=C.SESSION_TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True
            job.kill()
            process.wait()
        if job.query(1, Accounting).ActiveProcesses:
            job.kill()
        exit_code = process.returncode
        process._handle.Close()
    ended, wall = utc_now(), time.perf_counter() - start
    gz_path = log.with_suffix(".jsonl.gz")
    with log.open("rb") as source, gz_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            shutil.copyfileobj(source, compressed)
    log.unlink()
    version_command = shim_command([executable, "--version"])
    version = subprocess.run(version_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=C.VERSION_TIMEOUT, env=env, text=True, encoding="utf-8", errors="replace").stdout.strip()
    remove_tree(destination, C.PROGRAMS)
    destination.mkdir(parents=True, exist_ok=True)
    wanted = ["rust/Cargo.toml", "plain.py", "fast.py"]
    wanted += [p.relative_to(folder).as_posix() for p in sorted((folder / "rust/src").rglob("*.rs"))]
    if "rust/src/main.rs" not in wanted:
        wanted.append("rust/src/main.rs")
    missing = []
    for name in wanted:
        source = folder / name
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(folder.resolve()):
            missing.append(name)
        else:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    meta = dict(author=author, task=task, request_hash=digest, cli_version=version,
                requested_model=C.AUTHORS[author]["model"], effort=C.AUTHORS[author]["effort"],
                start_utc=started, end_utc=ended, wall_seconds=wall, exit_code=exit_code,
                timed_out=timed_out, files=inventory(folder), missing=missing,
                private_cargo_home=author == "sol" and C.SOL_PRIVATE_CARGO_HOME, **event_metadata(gz_path))
    write_json(meta_path, meta)


def table():
    path = C.DATA / "sessions.csv"
    fields = ["author", "task", "request_hash", "cli_version", "requested_model", "reported_model", "effort",
              "start_utc", "end_utc", "wall_seconds", "exit_code", "timed_out", "cost_usd", "turns", "tool_calls", "usage", "missing"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields, lineterminator="\n").writeheader()
    for meta_path in sorted(C.PROGRAMS.glob("*/*/meta.json")):
        meta = read_json(meta_path)
        row = {key: meta.get(key) for key in fields}
        for key in ("usage", "missing"):
            row[key] = json.dumps(row[key], sort_keys=True)
        append_csv(path, row, fields)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        p = sub.add_parser(name)
        p.add_argument("author", choices=C.AUTHORS)
        p.add_argument("task", choices=C.TASKS)
        if name == "run":
            p.add_argument("--force", action="store_true")
    p = sub.add_parser("run-all")
    p.add_argument("--jobs", type=int, help="Total concurrent sessions; default two per author")
    p.add_argument("--force", action="store_true")
    sub.add_parser("dry-run")
    sub.add_parser("table")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.author, args.task)
    elif args.command == "run":
        run(args.author, args.task, args.force)
    elif args.command == "run-all":
        if args.jobs is not None and args.jobs < 1:
            parser.error("--jobs must be positive")
        limits = {a: threading.Semaphore(C.SESSION_JOBS_PER_AUTHOR) for a in C.AUTHORS}

        def worker(author, task):
            with limits[author]:
                run(author, task, args.force)

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs or len(C.AUTHORS) * C.SESSION_JOBS_PER_AUTHOR) as pool:
            futures = [pool.submit(worker, a, t) for t in C.TASKS for a in C.AUTHORS]
            for future in concurrent.futures.as_completed(futures):
                future.result()
    elif args.command == "dry-run":
        hashes = [dict(author=a, task=t, request_hash=prepare(a, t)[1]) for a in C.AUTHORS for t in C.TASKS]
        write_json(C.DATA / "preparation_hashes.json", hashes)
    else:
        table()


if __name__ == "__main__":
    main()
