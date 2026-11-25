"""Prepare isolated author sessions; only the explicit run commands launch a model."""

import argparse
import concurrent.futures
import contextlib
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

from bench import config as C
from bench import openrouter_proxy
from bench.common import append_csv, read_json, remove_tree, sha256, shim_command, utc_now, write_json
from bench.winjob import Accounting, Job


def verify_vendor():
    for name, entry in read_json(C.VENDOR_LANGS_MANIFEST).items():
        path = C.VENDOR_LANGS / name
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise ValueError(f"Missing or mismatched vendor file: {path}")


def render_template(path):
    text = path.read_text(encoding="utf-8")
    for name, value in C.TOOLCHAINS.items():
        text = text.replace("{{" + name + "}}", str(value))
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def session_files(author, task, kind="main"):

    files = {"SPEC.md": (C.BENCH / "tasks" / task / "SPEC.md").read_bytes()}
    for path in sorted((C.DATA / "samples" / task).glob("*")):
        if path.suffix in (".in", ".out"):
            files["samples/" + path.name] = path.read_bytes()
    for name in C.input_sets(task):
        if name.startswith("s") and not name.startswith("sweep"):
            for suffix in (".in", ".out"):
                if "samples/" + name + suffix not in files:
                    raise FileNotFoundError(f"Missing sample: {task}/{name}{suffix}")
    if kind == "langs":
        verify_vendor()
        for lang in C.LANG_VARIANTS:
            base = C.BENCH / "template" / lang
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    name = path.relative_to(base).as_posix()
                    files[lang + "/" + (name[:-5] if name.endswith(".tmpl") else name)] = render_template(path) if name.endswith(".tmpl") else path.read_bytes()
        for name in read_json(C.VENDOR_LANGS_MANIFEST):
            target = "cpp/include/" + name[4:] if name.startswith("cpp/") else "java/lib/" + name[5:]
            files[target] = (C.VENDOR_LANGS / name).read_bytes()
        return files
    for path in sorted((C.BENCH / "template" / "rust").rglob("*")):
        if path.is_file():
            files["rust/" + path.relative_to(C.BENCH / "template" / "rust").as_posix()] = path.read_bytes()
    files["rust/.cargo/config.toml"] = ('[source.crates-io]\nreplace-with = "vendored-sources"\n\n'
                                           f"[source.vendored-sources]\ndirectory = '{C.VENDOR.as_posix()}'\n").encode()
    return files


def request_object(author, task, files=None, kind="main", config=None, prompt=None):
    files = session_files(author, task, kind) if files is None else files
    config = C.AUTHORS[author] if config is None else config
    author_config = dict(config, private_cargo_home=C.SOL_PRIVATE_CARGO_HOME if config["cli"] == "codex" else False)
    prompt = C.SESSION_KINDS[kind]["prompt"].read_text(encoding="utf-8") if prompt is None else prompt
    return dict(author=author_config, prompt=prompt,
                files={name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())})


def hash_request(request):
    payload = dict(author=request["author"], prompt_sha256=hashlib.sha256(request["prompt"].encode("utf-8")).hexdigest(), files=request["files"])
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def request_hash(author, task, files=None, kind="main"):
    return hash_request(request_object(author, task, files, kind))


def prepare(author, task, kind="main"):
    files = session_files(author, task, kind)
    root = C.SESSION_KINDS[kind]["sessions"]
    folder = root / author / task
    remove_tree(folder, root)
    for name, contents in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    digest = request_hash(author, task, files, kind)
    print(author, task, digest, flush=True)
    return folder, digest


def command_for(author, task, kind="main", muse_session=None):
    config = C.AUTHORS[author]
    executable = shutil.which(config["cli"])
    if executable is None:
        raise FileNotFoundError(config["cli"])
    root = C.SESSION_KINDS[kind]["sessions"]
    folder = root / author / task
    values = dict(session=str(folder), last=str(root / author / f"{task}.last.md"),
                  prompt=str(C.SESSION_KINDS[kind]["prompt"].resolve()))
    flags = [flag.format(**values) for flag in config["flags"]]
    if config["cli"] == "muse" and muse_session:
        # Added at run time so the id stays out of the request hash; it lets `muse export` find the session afterwards.
        flags[1:1] = ["--session-id", muse_session]
    return shim_command([executable] + flags), executable


def openrouter_environment(author, task, kind, base=None):
    """Variables that point Claude Code at the local proxy. The session gets a dummy token; the proxy holds the real key."""
    model = C.AUTHORS[author]["model"]
    env = dict(ANTHROPIC_BASE_URL=f"http://127.0.0.1:{C.OPENROUTER_PROXY_PORT}", ANTHROPIC_AUTH_TOKEN="nb39-local-proxy",
               ANTHROPIC_API_KEY="", ANTHROPIC_CUSTOM_HEADERS=f"{openrouter_proxy.SESSION_HEADER}: {author}/{task}/{kind}",
               NO_PROXY=",".join(filter(None, [(base or {}).get("NO_PROXY"), "127.0.0.1,localhost"])))
    # No Claude model name is left for Claude Code's background calls.
    for name in ("ANTHROPIC_MODEL", "ANTHROPIC_SMALL_FAST_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                 "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL"):
        env[name] = model
    return env


def harvest_files(folder, kind):
    if kind == "main":
        wanted = ["rust/Cargo.toml", "plain.py", "fast.py", "rust/src/main.rs"]
        wanted += [p.relative_to(folder).as_posix() for p in sorted((folder / "rust/src").rglob("*.rs"))]
    else:
        wanted = ["cpp/main.cpp", "java/src/Main.java", "csharp/Program.cs", "csharp/solution.csproj", "go/main.go", "go/go.mod", "js/main.js"]
        skip = {"bin", "obj", "out", ".dotnet-home", ".nuget-packages", ".gocache", ".gopath"}
        for lang in C.LANG_VARIANTS:
            for path in sorted((folder / lang).rglob("*")):
                rel = path.relative_to(folder)
                if not path.is_file() or any(part in skip for part in rel.parts) or rel.parts[:3] == ("cpp", "include", "nlohmann"):
                    continue
                valid = (lang == "cpp" and path.suffix in (".cpp", ".cc", ".h", ".hpp") or
                         lang == "java" and len(rel.parts) > 2 and rel.parts[1] == "src" and path.suffix == ".java" or
                         lang == "csharp" and path.suffix == ".cs" or lang == "go" and path.suffix == ".go" or
                         lang == "js" and path.suffix in (".js", ".mjs", ".cjs"))
                if valid:
                    wanted.append(rel.as_posix())
    return sorted(set(wanted))


def trace():
    try:
        host = os.environ.get("LANGFUSE_HOST")
        if not host and os.name == "nt":
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    host = winreg.QueryValueEx(key, "LANGFUSE_HOST")[0]
            except OSError:
                pass
        host = (host or "http://localhost:3300").rstrip("/")
        with urllib.request.urlopen(host + "/api/public/health", timeout=2) as response:
            if response.status != 200:
                raise RuntimeError(f"health: {response.status}")
        script = Path(os.environ.get("NB39_LANGFUSE_BACKFILL", r"D:\projects\langfuse\backfill\backfill_traces.py"))
        if not script.is_file():
            raise FileNotFoundError(script)
        # Langfuse stores a resent span twice, so two backfills must never overlap (threads or processes).
        with TRACE_LOCK, exclusive_file(C.WORK / "trace.lock"):
            result = subprocess.run([sys.executable, str(script), "--only", "39"], capture_output=True, text=True, timeout=600)
        print("trace:", f"exit {result.returncode}", (result.stdout or result.stderr).strip().splitlines()[-1:] or [], flush=True)
    except Exception as exc:
        print("trace skipped:", exc, flush=True)


TRACE_LOCK = threading.Lock()


@contextlib.contextmanager
def exclusive_file(path, timeout=900):
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"lock held: {path}")
            time.sleep(1)
    try:
        yield
    finally:
        os.close(fd)
        os.unlink(path)


def backfill_requests():
    import sys
    for author in (*C.AUTHORS, *C.PILOT_AUTHORS):
        config, prompt = None, None
        if author in C.PILOT_AUTHORS:
            prefix = "3685b2eb:notebooks/39-rust-vs-python/bench/"
            old = subprocess.check_output(["git", "-c", f"safe.directory={C.ROOT.parent.parent.as_posix()}", "show", prefix + "config.py"]).decode("utf-8")
            namespace = {"__file__": str(C.BENCH / "config.py")}
            exec(compile(old, "old_config.py", "exec"), namespace)
            config = namespace["AUTHORS"]["claude" if author == "opus" else author]
            prompt = subprocess.check_output(["git", "-c", f"safe.directory={C.ROOT.parent.parent.as_posix()}", "show", prefix + "AUTHOR_PROMPT.md"]).decode("utf-8")
        for task in (("heat",) if author in C.PILOT_AUTHORS else C.TASKS):
            path = C.PROGRAMS / author / task / "meta.json"
            meta = read_json(path)
            request = request_object(author, task, config=config, prompt=prompt)
            match = hash_request(request) == meta["request_hash"]
            if not match and author not in C.PILOT_AUTHORS:
                raise ValueError(f"Request mismatch: {author}/{task}")
            if not match:
                request["reconstructed"] = True
            meta["request"] = request
            write_json(path, meta)
            print(author, task, "matched" if match else "reconstructed")


def muse_event(event, result, state):
    """Fold one event of `muse exec --json` (payload_type + payload) into the result."""
    if event.get("id") is not None:
        if event["id"] in state["seen"]:  # Muse may print an event twice
            return
        state["seen"].add(event["id"])
    payload = event.get("payload") or {}
    kind = event["payload_type"]
    if kind == "run.model.configured":
        result["reported_model"] = payload.get("model_id") or result["reported_model"]
    elif kind == "run.usage":
        stream = (payload.get("run_stream") or {}).get("id") or payload.get("command_id") or ""
        state["usage"][stream] = (payload.get("models") or [{}])[0]
        if payload.get("allowance") is not None:
            state["allowance"] = payload["allowance"]
    elif kind == "task.lifecycle.proposed":
        task_kind = (payload.get("event") or {}).get("task_kind") or ""
        if task_kind.startswith("tool."):
            result["tool_calls"] += 1
        elif task_kind.startswith("model."):
            result["turns"] += 1
    elif kind == "run.terminal.completed":
        result["final_message"] = payload.get("text", "")


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def add_usage(total, usage):
    """Add a usage report into `total`: numbers are summed (nested dicts key by key), anything else keeps the last value."""
    for key, value in usage.items():
        old = total.get(key)
        if isinstance(value, dict):
            total[key] = add_usage(old if isinstance(old, dict) else {}, value)
        elif is_number(value) and is_number(old):
            total[key] = old + value
        else:
            total[key] = value
    return total


def event_metadata(path):
    result = dict(reported_model=None, cost_usd=None, usage={}, turns=0, tool_calls=0, final_message="")
    muse = dict(seen=set(), usage={}, allowance=None)
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(event, dict):
                continue
            if "payload_type" in event:
                muse_event(event, result, muse)
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
                # A session can emit several results (e.g. a continuation after a background command). Turns and usage
                # are per result and add up; the cost is cumulative, so the last one stands.
                result["result_events"] = result.get("result_events", 0) + 1
                result["cost_usd"] = event.get("total_cost_usd")
                if isinstance(event.get("usage"), dict):
                    add_usage(result["usage"], event["usage"])
                if isinstance(event.get("num_turns"), (int, float)):
                    result["turns"] += event["num_turns"]
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
    if muse["usage"]:
        # Muse reports no cost (subscription); sum the last usage report of each run.
        for report in muse["usage"].values():
            for key in ("input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens", "calls"):
                if isinstance(report.get(key), (int, float)):
                    result["usage"][key] = result["usage"].get(key, 0) + report[key]
        result["allowance"] = muse["allowance"]
    return result


def compress(source, target):
    with Path(source).open("rb") as stream, Path(target).open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            shutil.copyfileobj(stream, compressed)


def muse_export(executable, session_id, author, task, suffix, env):
    """Export Muse's own transcript (its --json stream has no tool inputs); returns an error text or None."""
    export = C.WORK / "muse-exports" / author / f"{task}{suffix}.json"
    target = C.DATA / "sessions" / author / f"{task}{suffix}.muse-export.json.gz"
    export.parent.mkdir(parents=True, exist_ok=True)
    export.unlink(missing_ok=True)
    target.unlink(missing_ok=True)
    try:
        result = subprocess.run(shim_command([executable, "export", "--session", session_id, "--out", str(export)]), env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", timeout=C.MUSE_EXPORT_TIMEOUT)
        if result.returncode != 0 or not export.is_file():
            return f"exit {result.returncode}: {result.stdout.strip()[-500:]}"
        compress(export, target)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


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


def run(author, task, force=False, kind="main"):
    settings = C.SESSION_KINDS[kind]
    digest = request_hash(author, task, kind=kind)
    destination = C.PROGRAMS / author / task
    meta_path = destination / settings["meta"]
    if meta_path.exists() and read_json(meta_path).get("request_hash") == digest and not force:
        print(author, task, "cached", digest, flush=True)
        return
    config = C.AUTHORS[author]
    routed, muse = config.get("route") == "openrouter", config["cli"] == "muse"
    if routed:
        openrouter_proxy.start(C.OPENROUTER_PROXY_PORT)  # fails before the folder is touched if the key is missing
    folder, digest = prepare(author, task, kind)
    muse_session = str(uuid.uuid4()) if muse else None
    command, executable = command_for(author, task, kind, muse_session)
    env = C.session_environment()
    if routed:
        proxy_log = openrouter_proxy.log_path(author, task, kind)
        proxy_log.unlink(missing_ok=True)
        env.update(openrouter_environment(author, task, kind, env))
    if kind == "langs":
        env["PATH"] = os.pathsep.join(str(C.TOOLCHAINS[k].parent) for k in ("GO", "DOTNET", "NODE", "JAVA")) + os.pathsep + env.get("PATH", "")
        env.update(DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1", GOTOOLCHAIN="local")
    if config["cli"] == "codex" and C.SOL_PRIVATE_CARGO_HOME:
        env["CARGO_HOME"] = str(folder / ".cargo-home")
    log = C.DATA / "sessions" / author / f"{task}{settings['suffix']}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    stderr_path = settings["sessions"] / author / f"{task}.stderr.txt"
    # stdin is a file so prompt bytes (including existing line endings) pass unchanged; Muse reads --prompt-file instead.
    started, start = utc_now(), time.perf_counter()
    timed_out = False
    prompt_stdin = contextlib.nullcontext(subprocess.DEVNULL) if muse else settings["prompt"].open("rb")
    with Job() as job, log.open("wb") as stdout, stderr_path.open("wb") as stderr, prompt_stdin as prompt:
        process = job.launch(command, cwd=folder, env=env, stdin=prompt, stdout=stdout, stderr=stderr)
        try:
            process.wait(timeout=settings["timeout"])
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
    compress(log, gz_path)
    log.unlink()
    version_command = shim_command([executable, "--version"])
    version = subprocess.run(version_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=C.VERSION_TIMEOUT, env=env, text=True, encoding="utf-8", errors="replace").stdout.strip()
    destination.mkdir(parents=True, exist_ok=True)
    for name in (("rust", "plain.py", "fast.py") if kind == "main" else C.LANG_VARIANTS):
        path = destination / name
        if path.is_dir(): remove_tree(path, C.PROGRAMS)
        elif path.exists(): path.unlink()
    wanted = harvest_files(folder, kind)
    missing = []
    for name in wanted:
        source = folder / name
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(folder.resolve()):
            missing.append(name)
        else:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    meta = dict(author=author, task=task, request_hash=digest, request=request_object(author, task, kind=kind), cli_version=version,
                requested_model=config["model"], effort=config["effort"],
                start_utc=started, end_utc=ended, wall_seconds=wall, exit_code=exit_code,
                timed_out=timed_out, files=inventory(folder), missing=missing,
                private_cargo_home=config["cli"] == "codex" and C.SOL_PRIVATE_CARGO_HOME, **event_metadata(gz_path))
    if muse:
        meta.update(muse_session_id=muse_session,
                    muse_export_error=muse_export(executable, muse_session, author, task, settings["suffix"], env))
    if routed:
        compress(proxy_log if proxy_log.exists() else os.devnull, C.DATA / "sessions" / author / f"{task}{settings['suffix']}.openrouter.jsonl.gz")
        meta["openrouter"] = openrouter_proxy.summarize(proxy_log)
        # Claude Code prices every call at Claude rates, which means nothing here; OpenRouter's own figure is the cost.
        meta["claude_code_reported_cost_usd"], meta["cost_usd"] = meta["cost_usd"], meta["openrouter"]["cost_usd"]
    write_json(meta_path, meta)
    trace()


def table(kind="main"):
    path = C.DATA / ("sessions.csv" if kind == "main" else "sessions_langs.csv")
    fields = ["author", "task", "request_hash", "cli_version", "requested_model", "reported_model", "effort",
              "start_utc", "end_utc", "wall_seconds", "exit_code", "timed_out", "cost_usd", "turns", "tool_calls", "usage", "missing",
              "claude_code_reported_cost_usd", "openrouter"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields, lineterminator="\n").writeheader()
    for meta_path in sorted(C.PROGRAMS.glob("*/*/" + C.SESSION_KINDS[kind]["meta"])):
        if meta_path.parent.parent.name not in C.AUTHORS:
            continue  # the "reference" pseudo-author has no session
        meta = read_json(meta_path)
        row = {key: meta.get(key) for key in fields}
        for key in ("usage", "missing", "openrouter"):
            row[key] = json.dumps(row[key], sort_keys=True)
        append_csv(path, row, fields)


def session_metadata_files(data):
    """(metadata file, session log) pairs: programs/<author>/<task>/meta*.json and the kept failed runs."""
    pairs = []
    for kind in C.SESSION_KINDS.values():
        for meta_path in sorted((data / "programs").glob("*/*/" + kind["meta"])):
            log = data / "sessions" / meta_path.parent.parent.name / f"{meta_path.parent.name}{kind['suffix']}.jsonl.gz"
            pairs.append((meta_path, log))
    for meta_path in sorted((data / "failed_sessions").glob("*/*.meta.json")):
        pairs.append((meta_path, meta_path.with_name(meta_path.name[:-len(".meta.json")] + ".jsonl.gz")))
    return pairs


def refresh_metadata(data=C.DATA, dry_run=False):
    """Re-read each session log with event_metadata and update only turns, usage, tool_calls, result_events and cost_usd."""
    changed = []
    for meta_path, log in session_metadata_files(Path(data)):
        label = meta_path.relative_to(data).as_posix()
        if meta_path.parent.parent.name == "reference":
            continue  # the "reference" pseudo-author has no session
        if not log.is_file():
            print("no log, skipped:", label, flush=True)
            continue
        meta, fresh = read_json(meta_path), event_metadata(log)
        update = {key: fresh[key] for key in ("turns", "usage", "tool_calls", "result_events") if key in fresh}
        if meta.get("openrouter") is None:  # otherwise cost_usd is the OpenRouter charge
            update["cost_usd"] = fresh["cost_usd"]
        update = {key: value for key, value in update.items() if meta.get(key) != value or key not in meta}
        if not update:
            continue
        old_tokens, new_tokens = (m.get("usage", {}).get("output_tokens") for m in (meta, dict(meta, **update)))
        print(f"{label}: turns {meta.get('turns')} -> {update.get('turns', meta.get('turns'))}, "
              f"output_tokens {old_tokens} -> {new_tokens}, changed: {', '.join(sorted(update))}", flush=True)
        if not dry_run:
            write_json(meta_path, dict(meta, **update))
        changed.append(meta_path)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        p = sub.add_parser(name)
        p.add_argument("--kind", choices=C.SESSION_KINDS, default="main")
        p.add_argument("author", choices=C.AUTHORS)
        p.add_argument("task", choices=C.TASKS)
        if name == "run":
            p.add_argument("--force", action="store_true")
    p = sub.add_parser("run-all")
    p.add_argument("--kind", choices=C.SESSION_KINDS, default="main")
    p.add_argument("--authors", nargs="+", choices=C.AUTHORS, default=list(C.AUTHORS))
    p.add_argument("--jobs", type=int, default=C.SESSION_JOBS_TOTAL, help="Total concurrent sessions")
    p.add_argument("--force", action="store_true")
    for name in ("dry-run", "table"):
        sub.add_parser(name).add_argument("--kind", choices=C.SESSION_KINDS, default="main")
    sub.add_parser("backfill-requests")
    sub.add_parser("trace")
    sub.add_parser("refresh-metadata").add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.author, args.task, args.kind)
    elif args.command == "run":
        run(args.author, args.task, args.force, args.kind)
    elif args.command == "run-all":
        if args.jobs is not None and args.jobs < 1:
            parser.error("--jobs must be positive")
        limits = {a: threading.Semaphore(C.SESSION_JOBS.get(a, C.SESSION_JOBS_PER_AUTHOR)) for a in args.authors}
        pending, running, failures = [(a, t) for t in C.TASKS for a in args.authors], {}, []
        # Jobs start in order (task-outer, author-inner); one whose author is at its limit is skipped, not waited for,
        # so it never holds one of the --jobs slots.
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            while pending or running:
                for job in list(pending):
                    if len(running) < args.jobs and limits[job[0]].acquire(blocking=False):
                        pending.remove(job)
                        running[pool.submit(run, job[0], job[1], args.force, args.kind)] = job
                done, _ = concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    author, task = running.pop(future)
                    limits[author].release()
                    if future.exception() is not None:
                        failures.append(f"{author}/{task}: {future.exception()!r}")
                        print("FAILED", failures[-1], flush=True)
        if failures:
            raise RuntimeError(f"{len(failures)} session(s) failed: " + "; ".join(failures))
    elif args.command == "dry-run":
        hashes = [dict(author=a, task=t, request_hash=prepare(a, t, args.kind)[1]) for a in C.AUTHORS for t in C.TASKS]
        if args.kind == "main":
            ledger = read_json(C.DATA / "preparation_hashes.json")
            known = {row["author"] for row in ledger}  # authors added later have no ledger rows
            if [row for row in hashes if row["author"] in known] != ledger:
                raise ValueError("Main preparation hash ledger differs")
            for row in hashes:
                meta_path = C.PROGRAMS / row["author"] / row["task"] / "meta.json"
                if row["author"] in known or meta_path.exists():
                    if row["request_hash"] != read_json(meta_path)["request_hash"]:
                        raise ValueError(f"Main preparation hash changed: {row}")
    elif args.command == "table":
        table(args.kind)
    elif args.command == "trace":
        trace()
    elif args.command == "refresh-metadata":
        changed = refresh_metadata(dry_run=args.dry_run)
        print(f"{len(changed)} file(s) {'would change' if args.dry_run else 'rewritten'}")
    else:
        backfill_requests()


if __name__ == "__main__":
    main()
