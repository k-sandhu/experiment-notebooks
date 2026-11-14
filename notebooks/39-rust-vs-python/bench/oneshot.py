"""Standalone one-reply programming experiment; only `run` calls models."""
import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

import requests
from bench import config as C, sessions
from bench.common import read_json, remove_tree, shim_command, write_json, write_text
from bench.compare import compare
from bench.winjob import Accounting, Job, run as job_run

NOTEBOOK = "39-rust-vs-python"
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3300").rstrip("/")
LANGFUSE_AUTH = (os.environ.get("LANGFUSE_PUBLIC_KEY", ""), os.environ.get("LANGFUSE_SECRET_KEY", ""))

def _langfuse_running():
    if not all(LANGFUSE_AUTH):
        return False
    try:
        return requests.get(f"{LANGFUSE_HOST}/api/public/health", timeout=2).ok
    except requests.RequestException:
        return False

LANGFUSE_ON = _langfuse_running()

def trace_call(cache_key, name, model, request, response, start, end, usage=None, cost_usd=None,
               session_id=None, metadata=None, error=None):
    """Send one fresh generation in OTLP format; tracing must never interrupt a run."""
    try:
        if not LANGFUSE_ON:
            return
        def attr(k, v):
            return {"key": k, "value": {"stringValue": v if isinstance(v, str) else json.dumps(v, default=str)}}
        tags = {"key": "langfuse.trace.tags", "value": {"arrayValue": {"values": [{"stringValue": f"nb{NOTEBOOK[:2]}"}]}}}
        attrs = [attr("langfuse.observation.type", "generation"), attr("langfuse.observation.model.name", model),
                 attr("langfuse.observation.input", request), attr("langfuse.observation.output", response),
                 attr("langfuse.trace.name", f"{NOTEBOOK[:2]} {name}"), tags,
                 attr("langfuse.environment", "notebook"), attr("langfuse.trace.metadata.notebook", NOTEBOOK),
                 attr("langfuse.trace.metadata.cache_key", cache_key)]
        if usage: attrs.append(attr("langfuse.observation.usage_details", usage))
        if cost_usd is not None: attrs.append(attr("langfuse.observation.cost_details", {"total": cost_usd}))
        if session_id: attrs.append(attr("langfuse.session.id", f"{NOTEBOOK}/{session_id}"))
        if error: attrs += [attr("langfuse.observation.level", "ERROR"), attr("langfuse.observation.status_message", str(error))]
        for k, v in (metadata or {}).items(): attrs.append(attr(f"langfuse.observation.metadata.{k}", v))
        span = {"traceId": hashlib.sha256(f"{NOTEBOOK}|{cache_key}".encode()).hexdigest()[:32],
                "spanId": hashlib.sha256(f"{NOTEBOOK}|{cache_key}|gen|0".encode()).hexdigest()[:16],
                "name": name, "kind": 1, "attributes": attrs,
                "startTimeUnixNano": str(int(start.timestamp() * 1e9)), "endTimeUnixNano": str(int(end.timestamp() * 1e9))}
        body = {"resourceSpans": [{"resource": {"attributes": [attr("service.name", "experiment-notebooks")]},
                                   "scopeSpans": [{"scope": {"name": NOTEBOOK}, "spans": [span]}]}]}
        requests.post(f"{LANGFUSE_HOST}/api/public/otel/v1/traces", json=body, auth=LANGFUSE_AUTH, timeout=10)
    except Exception:
        pass


def languages():
    return read_json(C.BENCH / "oneshot_languages.json")

def read_raw(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return stream.read().replace("\r\n", "\n")

def prompt_for(task, variant, limit=None):
    limit = C.ONESHOT_SAMPLE_LIMIT if limit is None else limit
    lang = languages()[variant]
    spec = read_raw(C.BENCH / "tasks" / task / "SPEC.md").rstrip()
    examples = []
    for path in sorted((C.DATA / "samples" / task).glob("*.in")):
        if path.stat().st_size <= limit:
            def strip_one(text): return text[:-1] if text.endswith("\n") else text
            inp, out = strip_one(read_raw(path)), strip_one(read_raw(path.with_suffix(".out")))
            examples.append(f"\nExample `{path.stem}` input:\n\n<input>\n{inp}\n</input>\n\nExpected output:\n\n<output>\n{out}\n</output>\n")
    text = read_raw(C.BENCH / "ONESHOT_PROMPT.md")
    for key, value in (("language", lang["language"]), ("language_block", lang["block"]), ("file", lang["file"]), ("spec", spec), ("examples", "".join(examples))):
        text = text.replace("{" + key + "}", value)
    return text.rstrip("\n") + "\n"

def flags_for(model):
    cfg = C.ONESHOT_MODELS[model]
    if cfg["cli"] == "claude":
        return ["-p", "--safe-mode", "--model", cfg["model"], "--effort", cfg["effort"], "--tools", "", "--system-prompt", C.ONESHOT_SYSTEM, "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
    return ["exec", "-m", cfg["model"], "-c", f'model_reasoning_effort="{cfg["effort"]}"', "-c", 'model_instructions_file="{system_file}"', "-c", 'approval_policy="never"', "--ignore-user-config", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "-C", "{folder}", "--json", "-o", "{last_file}", "-"]

def request_for(model, task, variant):
    cfg = C.ONESHOT_MODELS[model]
    return dict(cli=cfg["cli"], model=cfg["model"], effort=cfg["effort"], flags=flags_for(model), system=C.ONESHOT_SYSTEM, prompt=prompt_for(task, variant), sample_limit=C.ONESHOT_SAMPLE_LIMIT)

def request_hash(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def extract(reply):
    blocks = re.findall(r"(?ms)^[ \t]*(`{3,}|~{3,})[^\n]*\n(.*?)^[ \t]*\1[ \t]*(?:\n|$)", reply.replace("\r\n", "\n"))
    if not blocks:
        return None, dict(status="no_code_block", blocks=0, empty=not bool(reply.strip()))
    code = max((b[1] for b in blocks), key=len).rstrip("\n") + "\n"
    return code, dict(status="ok", blocks=len(blocks), empty=False)

def token_values(usage, cli):
    cached = usage.get("cache_read_input_tokens", 0) if cli == "claude" else usage.get("cached_input_tokens", usage.get("cached_tokens", 0))
    inp = usage.get("input_tokens", 0)
    if cli == "claude": inp += cached + usage.get("cache_creation_input_tokens", 0)
    # Claude Code reports thinking under output_tokens_details; Codex reports reasoning_output_tokens.
    reasoning = (usage.get("output_tokens_details") or {}).get("thinking_tokens", 0) if cli == "claude" else usage.get("reasoning_output_tokens", usage.get("reasoning_tokens", 0))
    return dict(input_tokens=inp, cached_input_tokens=cached, output_tokens=usage.get("output_tokens", 0), reasoning_tokens=reasoning or 0)

def run_one(model, task, variant, force=False):
    request = request_for(model, task, variant); digest = request_hash(request)
    cache = C.ONESHOT / "calls" / model / f"{task}.{variant}.json"
    if not force and cache.exists() and read_json(cache).get("request_hash") == digest:
        print(model, task, variant, "cached", flush=True); return
    cfg = C.ONESHOT_MODELS[model]
    exe = shutil.which(cfg["cli"])
    if not exe: raise FileNotFoundError(cfg["cli"])
    folder = C.ONESHOT_WORK / "calls" / model / f"{task}.{variant}"
    remove_tree(folder, C.ONESHOT_WORK); folder.mkdir(parents=True)
    system = C.ONESHOT_WORK / "system.txt"
    last = folder / "last.txt"
    replacements = {"{system_file}": system.as_posix(), "{folder}": str(folder), "{last_file}": str(last)}
    flags = [f for f in request["flags"]]
    for key, value in replacements.items(): flags = [f.replace(key, value) for f in flags]
    command = shim_command([exe] + flags)
    env = C.session_environment()
    log = C.ONESHOT_WORK / "logs" / model / f"{task}.{variant}.jsonl"
    err = log.with_suffix(".stderr.txt")
    input_file = C.ONESHOT_WORK / "inputs" / model / f"{task}.{variant}.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    write_text(input_file, request["prompt"])
    start = dt.datetime.now(dt.timezone.utc); clock = time.perf_counter(); timed_out = False
    with Job() as job, log.open("wb") as stdout, err.open("wb") as stderr, input_file.open("rb") as stdin:
        process = job.launch(command, cwd=folder, env=env, stdin=stdin, stdout=stdout, stderr=stderr)
        try: process.wait(timeout=C.ONESHOT_TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True; job.kill(); process.wait()
        if job.query(1, Accounting).ActiveProcesses: job.kill()
        exit_code = process.returncode; process._handle.Close()
    end = dt.datetime.now(dt.timezone.utc); wall = time.perf_counter() - clock
    cache.parent.mkdir(parents=True, exist_ok=True)
    gz = cache.with_suffix(".jsonl.gz"); sessions.compress(log, gz)
    meta = sessions.event_metadata(gz)
    reply = last.read_text(encoding="utf-8") if cfg["cli"] == "codex" and last.is_file() else meta.pop("final_message", "")
    meta.pop("final_message", None)
    code, parsed = extract(reply)
    target = C.ONESHOT / "programs" / model / task / languages()[variant]["path"]
    if code is None: target.unlink(missing_ok=True)
    else: write_text(target, code)
    try:
        version = subprocess.run(shim_command([exe, "--version"]), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=C.VERSION_TIMEOUT, encoding="utf-8", errors="replace").stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc: version = str(exc)
    row = dict(request=request, request_hash=digest, cli_version=version, start_utc=start.isoformat(), end_utc=end.isoformat(), wall_seconds=wall, exit_code=exit_code, timed_out=timed_out, reply=reply, parse=parsed, **meta)
    write_json(cache, row)
    t = token_values(row["usage"], cfg["cli"])
    usage = dict(input=max(0, t["input_tokens"]-t["cached_input_tokens"]), input_cache_read=t["cached_input_tokens"], output=max(0, t["output_tokens"]-t["reasoning_tokens"]), output_reasoning=t["reasoning_tokens"])
    trace_call(digest, f"oneshot {model} {task} {variant}", cfg["model"], request, reply, start, end, usage=usage, cost_usd=row["cost_usd"], session_id=f"oneshot/{model}")
    print(model, task, variant, parsed["status"], flush=True)

def check_one(model, task, variant, programs=None):
    programs = C.ONESHOT / "programs" if programs is None else Path(programs)
    source = programs / model / task / languages()[variant]["path"]
    folder = C.ONESHOT_WORK / "check" / model / task / variant
    remove_tree(folder, C.ONESHOT_WORK); folder.mkdir(parents=True)
    samples = sorted((C.DATA / "samples" / task).glob("*.in"))
    row = dict(model=model, task=task, variant=variant, program_sha256=hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else "", built=False, build_error="", samples_passed=0, samples_total=len(samples), samples={})
    if not source.is_file():
        row["build_error"] = "program missing"
        row["samples"] = {p.stem: dict(status="error", message="program missing") for p in samples}
        return row
    try:
        if variant not in ("plain", "fast"):
            kind = "main" if variant == "rust" else "langs"
            files = sessions.session_files(model, task, kind=kind)
            for name, contents in files.items():
                if name.startswith(variant + "/"):
                    path = folder / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(contents)
        target = folder / languages()[variant]["path"]
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        project = folder / variant
        if variant == "rust": command = ["cargo", "build", "--release", "--offline"]
        elif variant in ("cpp", "java", "csharp", "go"): command = shim_command([str(project / "build.cmd")])
        else: command = None
        if command:
            result = job_run(command, project, folder / "build.stdout", folder / "build.stderr", C.BUILD_TIMEOUT)
            if result["exit_code"] or result["timed_out"]:
                row["build_error"] = ((folder / "build.stdout").read_text(encoding="utf-8", errors="replace") + "\n" + (folder / "build.stderr").read_text(encoding="utf-8", errors="replace"))[:500] or "build timed out or failed"
                row["samples"] = {p.stem: dict(status="error", message="build failed") for p in samples}
                return row
        row["built"] = True
        if variant in ("plain", "fast"): base = [str(C.PYTHON), "-X", "utf8", str(target)]
        elif variant == "rust": base = [str(project / "target/release/solution.exe")]
        elif variant == "java": base = [str(C.TOOLCHAINS["JAVA"]), "-cp", str(project / "out") + ";" + str(project / "lib" / "*"), "Main"]
        elif variant == "js": base = [str(C.TOOLCHAINS["NODE"]), str(target)]
        elif variant == "csharp": base = [str(project / "out/solution.exe")]
        else: base = [str(project / "solution.exe")]
        for sample in samples:
            stdout, stderr = folder / (sample.stem + ".stdout"), folder / (sample.stem + ".stderr")
            command = base + [str(sample.resolve())] + ([str(C.CORRECT_WORKERS)] if task == "walkers" else [])
            try:
                result = job_run(command, folder, stdout, stderr, C.CORRECT_TIMEOUT)
                if result["timed_out"] or result["exit_code"]:
                    status, detail = "error", "timeout" if result["timed_out"] else f'exit {result["exit_code"]}: ' + stderr.read_text(encoding="utf-8", errors="replace")
                elif stdout.stat().st_size > C.OUTPUT_LIMIT_BYTES:
                    status, detail = "error", "stdout exceeds output size limit"
                else:
                    outcome, detail = compare(task, stdout.read_text(encoding="utf-8"), sample.with_suffix(".out").read_text(encoding="utf-8"))
                    status = "pass" if outcome == "correct" else "fail"
            except (OSError, UnicodeError, ValueError) as exc: status, detail = "error", str(exc)
            row["samples"][sample.stem] = dict(status=status, message=detail[:300])
            row["samples_passed"] += status == "pass"
    except (OSError, ValueError) as exc:
        row["built"] = False; row["build_error"] = str(exc)[:500]
        for p in samples: row["samples"].setdefault(p.stem, dict(status="error", message=str(exc)[:300]))
    return row

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

def check(models, tasks, variants):
    path = C.ONESHOT / "checks.csv"
    old = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f: old = list(csv.DictReader(f))
    rows = []
    for task in tasks:
        for variant in variants:
            for model in models:
                if not (C.ONESHOT / "programs" / model / task / languages()[variant]["path"]).is_file(): continue
                row = check_one(model, task, variant)
                print(model, task, variant, "built", row["built"], "samples", f'{row["samples_passed"]}/{row["samples_total"]}', flush=True)
                row["samples"] = json.dumps(row["samples"], ensure_ascii=True, sort_keys=True)
                rows.append(row)
    keys = {(r["model"], r["task"], r["variant"]) for r in rows}
    old = [r for r in old if (r["model"], r["task"], r["variant"]) not in keys]
    write_csv(path, old + rows, ["model", "task", "variant", "program_sha256", "built", "build_error", "samples", "samples_passed", "samples_total"])

def summary():
    checks = {}
    path = C.ONESHOT / "checks.csv"
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            checks = {(r["model"], r["task"], r["variant"]): r for r in csv.DictReader(f)}
    rows = []
    for path in sorted((C.ONESHOT / "calls").glob("*/*.json")):
        model, stem = path.parent.name, path.stem
        task, variant = stem.rsplit(".", 1); data = read_json(path)
        c = checks.get((model, task, variant), {})
        program = C.ONESHOT / "programs" / model / task / languages()[variant]["path"]
        if not program.is_file() or c.get("program_sha256") != hashlib.sha256(program.read_bytes()).hexdigest(): c = {}
        rows.append(dict(model=model, task=task, variant=variant, **token_values(data.get("usage", {}), data["request"]["cli"]),
                         wall_seconds=data["wall_seconds"], cost_usd=data.get("cost_usd") if data["request"]["cli"] == "claude" else None,
                         parse_status=data["parse"]["status"], built=c.get("built", ""), build_error=c.get("build_error", ""),
                         samples=c.get("samples", ""), samples_passed=c.get("samples_passed", ""), samples_total=c.get("samples_total", "")))
    fields = ["model", "task", "variant", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "wall_seconds", "cost_usd", "parse_status", "built", "build_error", "samples", "samples_passed", "samples_total"]
    write_csv(C.ONESHOT / "summary.csv", rows, fields)
    for group in ("model", "variant"):
        for name in sorted({r[group] for r in rows}):
            subset = [r for r in rows if r[group] == name]; n = len(subset)
            def totals(k): return sum(float(r[k] or 0) for r in subset)
            print(group, name, "calls", n, *(f'{k} mean={totals(k)/n:.2f} total={totals(k):.0f}' for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens")),
                  f'wall_mean={totals("wall_seconds")/n:.2f}', f'cost_usd={totals("cost_usd"):.6f}',
                  "parse_failures", sum(r["parse_status"] != "ok" for r in subset), "build_failures", sum(str(r["built"]).lower() == "false" for r in subset),
                  "sample_passes", f'{int(totals("samples_passed"))}/{int(totals("samples_total"))}')

def main_v1():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prompts", "run", "check"):
        p = sub.add_parser(name)
        if name != "prompts": p.add_argument("--models", nargs="+", choices=C.ONESHOT_MODELS, default=list(C.ONESHOT_MODELS))
        p.add_argument("--tasks", nargs="+", choices=C.TASKS, default=list(C.ONESHOT_TASKS))
        p.add_argument("--variants", nargs="+", choices=C.VARIANTS, default=list(C.ONESHOT_VARIANTS))
        if name == "run": p.add_argument("--force", action="store_true")
    sub.add_parser("summary"); args = parser.parse_args()
    if args.command == "prompts":
        for task in args.tasks:
            for variant in args.variants:
                prompt = prompt_for(task, variant); path = C.ONESHOT / "prompts" / task / f"{variant}.md"
                write_text(path, prompt); print(task, variant, len(prompt.encode("utf-8")), "bytes")
    elif args.command == "run":
        C.ONESHOT_WORK.mkdir(parents=True, exist_ok=True)
        write_text(C.ONESHOT_WORK / "system.txt", C.ONESHOT_SYSTEM)
        locks = {m: threading.Semaphore(C.ONESHOT_JOBS_PER_MODEL) for m in args.models}
        def work(model, task, variant):
            with locks[model]: run_one(model, task, variant, args.force)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(args.models) * C.ONESHOT_JOBS_PER_MODEL) as pool:
            futures = [pool.submit(work, m, t, v) for t in args.tasks for v in args.variants for m in args.models]
            for future in futures: future.result()
    elif args.command == "check": check(args.models, args.tasks, args.variants)
    else: summary()

def main():
    # The original entry point remains untouched for cache-compatible v1 replay.
    import sys
    args = sys.argv[1:]
    protocol = "v2"
    if "--protocol" in args:
        i = args.index("--protocol")
        if i + 1 >= len(args) or args[i + 1] not in ("v1", "v2"):
            raise SystemExit("--protocol requires v1 or v2")
        protocol = args[i + 1]
        del args[i:i + 2]
    sys.argv[1:] = args
    if protocol == "v1":
        main_v1()
    else:
        from bench import oneshot_v2
        oneshot_v2.main()

if __name__ == "__main__": main()
