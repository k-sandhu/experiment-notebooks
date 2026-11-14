"""Protocol v2 for the one-reply programming experiment."""
import argparse
import concurrent.futures
import contextlib
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import tempfile
import time

import requests
from bench import config as C, sessions, openrouter_proxy
from bench.common import manifest, read_json, remove_tree, shim_command, write_json, write_text
from bench.compare import compare
from bench.winjob import Accounting, Job, run as job_run
from bench.oneshot import extract, request_hash, read_raw, trace_call, write_csv


def models():
    return {**C.ONESHOT_V2_MODELS, **C.ONESHOT_V2_EXTRA_MODELS}


def languages():
    return read_json(C.BENCH / "oneshot_languages_v2.json")


def prompt_for(task, variant):
    lang = languages()[variant]
    examples = []
    paths = [p for p in sorted((C.DATA / "samples" / task).glob("*.in")) if p.stat().st_size <= C.ONESHOT_V2_SAMPLE_LIMIT]
    paths += sorted((C.ONESHOT_V2 / "examples" / task).glob("*.in"))
    def strip_one(s): return s[:-1] if s.endswith("\n") else s
    for p in paths:
        inp, out = strip_one(read_raw(p)), strip_one(read_raw(p.with_suffix(".out")))
        worker = "\nRun with `WORKERS` = 4." if task == "walkers" else ""
        examples.append(f"\nExample `{p.stem}` input:\n\n<input>\n{inp}\n</input>{worker}\n\nExpected output:\n\n<output>\n{out}\n</output>\n")
    values = dict(language=lang["language"], language_block=lang["block"], file=lang["file"],
                  run_command=lang["run"] + (" WORKERS" if task == "walkers" else ""),
                  arguments="`INPUT_PATH` is the path of the input file" + (" and `WORKERS` is an integer from 1 to 32 (see the task)." if task == "walkers" else "."),
                  spec=read_raw(C.BENCH / "tasks" / task / "SPEC.md").rstrip(),
                  contract=read_raw(C.BENCH / "oneshot_contracts" / (task + ".md")).rstrip(), examples="".join(examples))
    text = read_raw(C.BENCH / "ONESHOT_PROMPT_V2.md")
    for key, value in values.items(): text = text.replace("{" + key + "}", value)
    return text.rstrip("\n") + "\n"


def flags_for(model):
    cfg = models()[model]
    if cfg["cli"] == "claude":
        return ["-p", "--safe-mode", "--model", cfg["model"], "--effort", cfg["effort"], "--tools", "", "--system-prompt", C.ONESHOT_SYSTEM, "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
    return ["exec", "-m", cfg["model"], "-c", f'model_reasoning_effort="{cfg["effort"]}"', "-c", 'model_instructions_file="{system_file}"', "-c", 'approval_policy="never"', "--ignore-user-config", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check", "-C", "{folder}", "--json", "-o", "{last_file}", "-"]


def request_for(model, task, variant):
    cfg = models()[model]
    prompt = prompt_for(task, variant)
    if cfg["cli"] == "openrouter-batch":
        body = dict(model=cfg["canonical"], messages=[dict(role="system", content=C.ONESHOT_SYSTEM), dict(role="user", content=prompt)], max_tokens=C.ONESHOT_BATCH["max_tokens"], reasoning=dict(effort="high"))
        return dict(endpoint="/v1/chat/completions", model=cfg["canonical"], provider=C.ONESHOT_BATCH["provider"], completion_window=C.ONESHOT_BATCH["completion_window"], body=body)
    return dict(cli=cfg["cli"], model=cfg["model"], effort=cfg["effort"], flags=flags_for(model), system=C.ONESHOT_SYSTEM, prompt=prompt, sample_limit=C.ONESHOT_V2_SAMPLE_LIMIT)


def token_values(usage, cli):
    if cli == "openrouter-batch":
        return dict(input_tokens=usage.get("prompt_tokens", 0) or 0, cached_input_tokens=(usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0, output_tokens=usage.get("completion_tokens", 0) or 0, reasoning_tokens=(usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0)
    from bench.oneshot import token_values as old
    return old(usage, cli)


def list_cost(cfg, usage):
    p = C.ONESHOT_PRICES[cfg["model"]]
    t = token_values(usage, cfg["cli"])
    if cfg["cli"] == "claude":
        return ((usage.get("input_tokens", 0) or 0)*p["input"] + (usage.get("cache_creation_input_tokens", 0) or 0)*p["cache_write"] + t["cached_input_tokens"]*p["cache_read"] + t["output_tokens"]*p["output"]) / 1e6
    return ((t["input_tokens"]-t["cached_input_tokens"])*p["input"] + t["cached_input_tokens"]*p["cache_read"] + t["output_tokens"]*p["output"]) / 1e6


def claude_reply(path):
    texts = []
    path = Path(path)
    with (gzip.open(path, "rt", encoding="utf-8", errors="replace") if path.suffix == ".gz" else path.open(encoding="utf-8", errors="replace")) as f:
        for line in f:
            try: event = json.loads(line)
            except ValueError: continue
            if isinstance(event, dict) and event.get("type") == "assistant":
                texts.extend(b.get("text", "") for b in event.get("message", {}).get("content", []) if b.get("type") == "text")
    return "".join(texts)


def claim(model, task, variant):
    path = C.ONESHOT_WORK / "claims" / "v2" / model / f"{task}.{variant}.claim"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as f: json.dump(dict(pid=os.getpid(), start=dt.datetime.now(dt.timezone.utc).isoformat()), f)
    except FileExistsError:
        print(model, task, variant, "claimed", flush=True)
        return None
    return path


def run_one(model, task, variant, force=False):
    path = claim(model, task, variant)
    if path is None: return
    try: _run_one(model, task, variant, force)
    finally: path.unlink(missing_ok=True)

def _run_one(model, task, variant, force=False):
    request = request_for(model, task, variant); digest = request_hash(request)
    cache = C.ONESHOT_V2 / "calls" / model / f"{task}.{variant}.json"
    if not force and cache.exists() and read_json(cache).get("request_hash") == digest:
        print(model, task, variant, "cached", flush=True); return
    cfg = models()[model]
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
    if cfg["cli"] == "claude": env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "64000"
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
    result_text = meta.get("final_message", "")
    reply = last.read_text(encoding="utf-8") if cfg["cli"] == "codex" and last.is_file() else claude_reply(log)
    meta.pop("final_message", None)
    code, parsed = extract(reply)
    target = C.ONESHOT_V2 / "programs" / model / task / languages()[variant]["path"]
    if code is None: target.unlink(missing_ok=True)
    else: write_text(target, code)
    try:
        version = subprocess.run(shim_command([exe, "--version"]), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=C.VERSION_TIMEOUT, encoding="utf-8", errors="replace").stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc: version = str(exc)
    row = dict(request=request, request_hash=digest, cli_version=version, start_utc=start.isoformat(), end_utc=end.isoformat(), wall_seconds=wall, exit_code=exit_code, timed_out=timed_out, reply=reply, parse=parsed, **meta)
    row["result_text"] = result_text
    row["cli_cost_usd"] = row.pop("cost_usd", None)
    row["list_cost_usd"] = list_cost(cfg, row["usage"])
    write_json(cache, row)
    t = token_values(row["usage"], cfg["cli"])
    usage = dict(input=max(0, t["input_tokens"]-t["cached_input_tokens"]), input_cache_read=t["cached_input_tokens"], output=max(0, t["output_tokens"]-t["reasoning_tokens"]), output_reasoning=t["reasoning_tokens"])
    trace_call(digest, f"oneshot {model} {task} {variant}", cfg["model"], request, reply, start, end, usage=usage, cost_usd=row["list_cost_usd"], session_id=f"oneshot/{model}")
    print(model, task, variant, parsed["status"], flush=True)

def program_command(folder, variant):
    target = folder / languages()[variant]["path"]
    project = folder / variant
    if variant in ("plain", "fast"): return [str(C.PYTHON), "-X", "utf8", str(target)]
    if variant == "rust": return [str(project / "target/release/solution.exe")]
    if variant == "java": return [str(C.TOOLCHAINS["JAVA"]), "-cp", str(project / "out") + ";" + str(project / "lib" / "*"), "Main"]
    if variant == "js": return [str(C.TOOLCHAINS["NODE"]), str(target)]
    if variant == "csharp": return [str(project / "out/solution.exe")]
    return [str(project / "solution.exe")]


def program_artifact(folder, variant):
    if variant in ("plain", "fast", "js"): return folder / languages()[variant]["path"]
    if variant == "java": return folder / variant / "out/Main.class"
    return Path(program_command(folder, variant)[0])


def check_one(model, task, variant, programs=None):
    programs = C.ONESHOT_V2 / "programs" if programs is None else Path(programs)
    source = programs / model / task / languages()[variant]["path"]
    folder = C.ONESHOT_WORK / "check" / model / task / variant
    remove_tree(folder, C.ONESHOT_WORK); folder.mkdir(parents=True)
    samples = sorted((C.DATA / "samples" / task).glob("*.in"))
    row = dict(model=model, task=task, variant=variant, program_sha256=hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else "", built=False, build_error="", samples_passed=0, samples_total=len(samples), samples={}, first_failure="")
    if not source.is_file():
        row["build_error"] = "program missing"
        row["first_failure"] = "no_program"
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
                row["first_failure"] = "build"
                row["samples"] = {p.stem: dict(status="error", message="build failed") for p in samples}
                return row
        row["built"] = True
        base = program_command(folder, variant)
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
                    status = "pass" if outcome == "correct" else outcome
            except (OSError, UnicodeError, ValueError) as exc: status, detail = "error", str(exc)
            if status != "pass" and not row["first_failure"]: row["first_failure"] = status
            row["samples"][sample.stem] = dict(status=status, message=detail[:300])
            row["samples_passed"] += status == "pass"
    except (OSError, ValueError) as exc:
        row["built"] = False; row["build_error"] = str(exc)[:500]; row["first_failure"] = "build"
        for p in samples: row["samples"].setdefault(p.stem, dict(status="error", message=str(exc)[:300]))
    return row



def check(models_selected, tasks, variants):
    path = C.ONESHOT_V2 / "checks.csv"
    old = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f: old = list(csv.DictReader(f))
    rows = []
    for task in tasks:
        for variant in variants:
            for model in models_selected:
                row = check_one(model, task, variant)
                print(model, task, variant, "built", row["built"], "samples", f'{row["samples_passed"]}/{row["samples_total"]}', row["first_failure"], flush=True)
                row["samples"] = json.dumps(row["samples"], ensure_ascii=True, sort_keys=True)
                rows.append(row)
    keys = {(r["model"], r["task"], r["variant"]) for r in rows}
    old = [r for r in old if (r["model"], r["task"], r["variant"]) not in keys]
    write_csv(path, old + rows, ["model", "task", "variant", "program_sha256", "built", "build_error", "samples", "samples_passed", "samples_total", "first_failure"])


HIDDEN_FIELDS = ["model", "task", "variant", "input", "workers", "program_sha256", "status", "message", "wall_seconds"]


def hidden_jobs(models_selected, tasks, variants):
    entries = {(e["task"], e["name"]): e for e in manifest()}
    inputs = {}
    for task in tasks:
        for name in ("t1", "full"):
            path = C.INPUTS / task / f"{name}.in"
            if hashlib.sha256(path.read_bytes()).hexdigest() != entries[task, name]["sha256"]:
                raise ValueError(f"Input hash differs from manifest: {task}/{name}")
            inputs[task, name] = path.resolve()
    jobs = []
    for task in tasks:
        for variant in variants:
            for model in models_selected:
                for name in ("t1", "full"):
                    counts = [C.CORRECT_WORKERS] if task == "walkers" else [1]
                    if task == "walkers" and name == "t1": counts += list(C.CORRECT_EXTRA_WORKERS)
                    jobs.extend((model, task, variant, name, count, inputs[task, name]) for count in counts)
    return jobs


def hidden_one(job, checks):
    model, task, variant, name, workers, input_path = job
    source = C.ONESHOT_V2 / "programs" / model / task / languages()[variant]["path"]
    folder = C.ONESHOT_WORK / "check" / model / task / variant
    row = dict(model=model, task=task, variant=variant, input=name, workers=workers,
               program_sha256="", status="error", message="", wall_seconds="")
    try:
        if source.is_file(): row["program_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        check_row = checks.get((model, task, variant), {})
        if (not row["program_sha256"] or row["program_sha256"] != check_row.get("program_sha256")
                or str(check_row.get("built", "")).lower() != "true" or not program_artifact(folder, variant).is_file()):
            row["message"] = "not built"
            return row
        output_dir = C.ONESHOT_WORK / "hidden" / model / task / variant
        output_dir.mkdir(parents=True, exist_ok=True)
        stdout = output_dir / f"{name}.w{workers}.stdout"
        stderr = output_dir / f"{name}.w{workers}.stderr"
        command = program_command(folder, variant) + [str(input_path)] + ([str(workers)] if task == "walkers" else [])
        result = job_run(command, folder, stdout, stderr, C.CORRECT_TIMEOUT)
        row["wall_seconds"] = result["wall_seconds"]
        if result["timed_out"] or result["exit_code"]:
            detail = "timeout" if result["timed_out"] else f'exit {result["exit_code"]}: ' + stderr.read_text(encoding="utf-8", errors="replace")
        elif stdout.stat().st_size > C.OUTPUT_LIMIT_BYTES:
            detail = "stdout exceeds output size limit"
        else:
            outcome, detail = compare(task, stdout.read_text(encoding="utf-8"), (C.DATA / "expected" / task / f"{name}.out").read_text(encoding="utf-8"))
            row["status"] = "pass" if outcome == "correct" else outcome
        row["message"] = detail[:300]
    except Exception as exc:
        row["status"], row["message"] = "error", str(exc)[:300]
    return row


def hidden(models_selected, tasks, variants, jobs=4):
    if jobs < 1: raise ValueError("jobs must be positive")
    pending = hidden_jobs(models_selected, tasks, variants)
    checks_path = C.ONESHOT_V2 / "checks.csv"
    checks = {}
    if checks_path.exists():
        with checks_path.open(encoding="utf-8", newline="") as f:
            checks = {(r["model"], r["task"], r["variant"]): r for r in csv.DictReader(f)}
    path = C.ONESHOT_V2 / "checks_hidden.csv"
    old = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f: old = list(csv.DictReader(f))
    keys = {(m, t, v) for m, t, v, _, _, _ in pending}
    rows = [r for r in old if (r["model"], r["task"], r["variant"]) not in keys]
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(hidden_one, job, checks) for job in pending]
        for count, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = future.result(); rows.append(row)
            print(row["model"], row["task"], row["variant"], row["input"], f'w{row["workers"]}', row["status"], row["wall_seconds"], flush=True)
            if count % 20 == 0: write_csv(path, rows, HIDDEN_FIELDS)
    write_csv(path, rows, HIDDEN_FIELDS)


def summary():
    checks = {}
    path = C.ONESHOT_V2 / "checks.csv"
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f: checks = {(r["model"], r["task"], r["variant"]): r for r in csv.DictReader(f)}
    hidden_checks = {}
    hidden_path = C.ONESHOT_V2 / "checks_hidden.csv"
    if hidden_path.exists():
        with hidden_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                hidden_checks.setdefault((row["model"], row["task"], row["variant"]), []).append(row)
    rows = []
    for path in sorted((C.ONESHOT_V2 / "calls").glob("*/*.json")):
        model, stem = path.parent.name, path.stem
        task, variant = stem.rsplit(".", 1); data = read_json(path)
        cfg = models()[model]; cli = cfg["cli"]
        c = checks.get((model, task, variant), {})
        program = C.ONESHOT_V2 / "programs" / model / task / languages()[variant]["path"]
        if program.is_file():
            if c.get("program_sha256") != hashlib.sha256(program.read_bytes()).hexdigest(): c = {}
        elif c.get("first_failure") != "no_program": c = {}
        digest = hashlib.sha256(program.read_bytes()).hexdigest() if program.is_file() else ""
        hidden_rows = [r for r in hidden_checks.get((model, task, variant), []) if digest and r["program_sha256"] == digest]
        hidden_passed = sum(r["status"] == "pass" for r in hidden_rows) if hidden_rows else ""
        hidden_total = len(hidden_rows) if hidden_rows else ""
        hidden_first_failure = next((r["status"] for r in hidden_rows if r["status"] != "pass"), "")
        rows.append(dict(hidden_passed=hidden_passed, hidden_total=hidden_total, hidden_first_failure=hidden_first_failure, model=model, task=task, variant=variant, **token_values(data.get("usage", {}), cli),
                         wall_seconds=data.get("wall_seconds", ""), cost_usd=data.get("cost_usd") if cli == "openrouter-batch" else data.get("list_cost_usd"),
                         cli_cost_usd=data.get("cli_cost_usd"), cost_basis={"claude": "claude list price", "codex": "codex API list price (subscription)", "openrouter-batch": "openrouter batch charge"}[cli],
                         parse_status=data.get("parse", {}).get("status", ""), built=c.get("built", ""), build_error=c.get("build_error", ""),
                         samples=c.get("samples", ""), samples_passed=c.get("samples_passed", ""), samples_total=c.get("samples_total", ""), first_failure=c.get("first_failure", "")))
    fields = ["model", "task", "variant", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "wall_seconds", "cost_usd", "cli_cost_usd", "cost_basis", "parse_status", "built", "build_error", "samples", "samples_passed", "samples_total", "first_failure", "hidden_passed", "hidden_total", "hidden_first_failure"]
    write_csv(C.ONESHOT_V2 / "summary.csv", rows, fields)
    for model in sorted({r["model"] for r in rows}):
        subset = [r for r in rows if r["model"] == model]
        print(model, "programs", sum(r["parse_status"] == "ok" for r in subset), "readable replies", sum(r["parse_status"] == "ok" for r in subset), "built", sum(str(r["built"]).lower() == "true" for r in subset), "passed all", sum(r["samples_total"] not in ("", 0, "0") and str(r["samples_passed"]) == str(r["samples_total"]) for r in subset), *(f"{k}={sum(r['first_failure'] == k for r in subset)}" for k in ("no_program", "build", "wrong", "unreadable", "error")), f"hidden_passed_all={sum(r['hidden_total'] != '' and r['hidden_passed'] == r['hidden_total'] for r in subset)}")


BATCH_URL = "https://openrouter.ai/api/v1/batches"
BATCH_TERMINAL = ("completed", "failed", "cancelled", "expired")
BATCH_TIMEOUT = (30, 120)
BATCH_MAX_POLL_FAILURES = 20


def _headers():
    key = openrouter_proxy.api_key()
    if not key: raise RuntimeError("OPENROUTER_API_KEY is not set")
    return {"Authorization": f"Bearer {key}"}


def _json_or_raise(response, action):
    if not response.ok:
        raise RuntimeError(f"OpenRouter {action} failed with status {response.status_code}: {response.text[:300]}")
    return response.json()


def _post_batch(payload):
    return _json_or_raise(requests.post(BATCH_URL, json=payload, headers=_headers(), timeout=BATCH_TIMEOUT), "batch submission")


def _get_batch(batch_id):
    return _json_or_raise(requests.get(f"{BATCH_URL}/{batch_id}", headers=_headers(), timeout=BATCH_TIMEOUT), "batch poll")


def _batch_file(batch_id, suffix):
    return C.ONESHOT_V2 / "batches" / (re.sub(r"[^A-Za-z0-9_.-]", "_", str(batch_id)) + suffix)


def _utc(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc)
    if isinstance(value, str):
        try: moment = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError: return None
        return moment if moment.tzinfo else moment.replace(tzinfo=dt.timezone.utc)
    return None


def _iso(value):
    moment = _utc(value)
    return moment.isoformat() if moment else None


def _submit(model, cfg, jobs):
    payload = dict(endpoint="/v1/chat/completions", model=cfg["canonical"], provider=C.ONESHOT_BATCH["provider"], completion_window=C.ONESHOT_BATCH["completion_window"],
                   requests=[dict(custom_id=j["custom_id"], body=j["request"]["body"]) for j in jobs])
    now = dt.datetime.now(dt.timezone.utc)
    response = _post_batch(payload)
    if not isinstance(response, dict) or not response.get("id"):
        raise RuntimeError("OpenRouter batch submission returned no batch id")
    submission = dict(model=model, submitted_at=now.timestamp(), submitted_utc=now.isoformat(), response=response,
                      jobs=[dict(custom_id=j["custom_id"], task=j["task"], variant=j["variant"], request_hash=j["request_hash"]) for j in jobs])
    write_json(C.ONESHOT_V2 / "batches" / f"{model}-{now.strftime('%Y%m%dT%H%M%SZ')}.json", submission)
    print(model, "submitted batch", response["id"], len(jobs), "requests", flush=True)
    return submission


def _open_submissions(model, wanted):
    """Submissions of this model with no stored result that hold at least one wanted custom_id."""
    found = []
    for path in sorted((C.ONESHOT_V2 / "batches").glob(f"{model}-*.json")):
        try: submission = read_json(path)
        except (OSError, ValueError): continue
        response = submission.get("response") if isinstance(submission, dict) else None
        if submission.get("model") != model or not isinstance(response, dict) or not response.get("id"): continue
        if _batch_file(response["id"], ".result.json.gz").exists(): continue
        if wanted & {j["custom_id"] for j in submission.get("jobs", [])}: found.append(submission)
    return found


def _poll(model, batch_id):
    polls = _batch_file(batch_id, ".polls.jsonl")
    failures = 0
    while True:
        try:
            batch = _get_batch(batch_id); failures = 0
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            failures += 1
            print(model, "poll failed", f"{failures}/{BATCH_MAX_POLL_FAILURES}", type(exc).__name__, str(exc)[:200], flush=True)
            if failures >= BATCH_MAX_POLL_FAILURES: raise
            time.sleep(C.ONESHOT_BATCH["poll_seconds"]); continue
        polls.parent.mkdir(parents=True, exist_ok=True)
        with polls.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({k: v for k, v in batch.items() if k != "results"}, ensure_ascii=True, sort_keys=True) + "\n")
        counts = batch.get("request_counts") or {}
        print(model, batch.get("status"), f'{counts.get("completed", 0)}/{counts.get("total", 0)}', flush=True)
        if batch.get("status") in BATCH_TERMINAL: return batch
        time.sleep(C.ONESHOT_BATCH["poll_seconds"])


def _write_result(path, batch):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        compressed.write(json.dumps(batch, ensure_ascii=True, sort_keys=True).encode("ascii"))
    temporary.replace(path)


def _message_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list): return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return ""


def _item_fields(item, custom_id, batch_status):
    if item is None:
        return dict(status_code=None, usage=None, reply="", reasoning_text="", finish_reason=None, error=f"no result for {custom_id} (batch {batch_status})", response_model=None, response_provider=None)
    response = item.get("response") if isinstance(item.get("response"), dict) else {}
    body = response.get("body") if isinstance(response.get("body"), dict) else (response if "choices" in response else {})
    choice = (body.get("choices") or [{}])[0] or {}
    message = choice.get("message") or {}
    usage = body.get("usage") if isinstance(body.get("usage"), dict) and body.get("usage") else None
    return dict(status_code=response.get("status_code"), usage=usage, reply=_message_text(message.get("content")),
                reasoning_text=message.get("reasoning") or message.get("reasoning_content") or "", finish_reason=choice.get("finish_reason"),
                error=item.get("error") or response.get("error") or body.get("error") or None, response_model=body.get("model"), response_provider=body.get("provider"))


def _weight(usage):
    return (usage.get("prompt_tokens") or 0) + 5 * (usage.get("completion_tokens") or 0)


def _complete(model, cfg, submission, by_cid):
    batch_id = submission["response"]["id"]
    batch = _poll(model, batch_id)
    items = batch.get("results") if isinstance(batch.get("results"), list) else []
    results = {i.get("custom_id"): i for i in items if isinstance(i, dict)}
    fields = {j["custom_id"]: _item_fields(results.get(j["custom_id"]), j["custom_id"], batch.get("status")) for j in submission["jobs"]}
    total_cost = (batch.get("usage") or {}).get("cost")
    total_weight = sum(_weight(f["usage"]) for f in fields.values() if f["usage"])
    created, finalized = batch.get("created_at"), batch.get("finalized_at")
    start = _utc(created) or _utc(submission.get("submitted_at")) or dt.datetime.now(dt.timezone.utc)
    end = _utc(finalized) or dt.datetime.now(dt.timezone.utc)
    for custom_id, job in by_cid.items():
        f = fields[custom_id]
        task, variant, request, digest = job["task"], job["variant"], job["request"], job["request_hash"]
        cost = total_cost * _weight(f["usage"]) / total_weight if total_cost is not None and total_weight and f["usage"] else None
        code, parsed = extract(f["reply"])
        target = C.ONESHOT_V2 / "programs" / model / task / languages()[variant]["path"]
        if code is None: target.unlink(missing_ok=True)
        else: write_text(target, code)
        row = dict(request=request, request_hash=digest, batch_id=batch_id, custom_id=custom_id, batch_status=batch.get("status"),
                   created_at=created, finalized_at=finalized, created_utc=_iso(created), finalized_utc=_iso(finalized),
                   status_code=f["status_code"], usage=f["usage"] or {}, reply=f["reply"], reasoning_text=f["reasoning_text"], finish_reason=f["finish_reason"],
                   error=f["error"], response_model=f["response_model"], response_provider=f["response_provider"], parse=parsed, cost_usd=cost)
        write_json(C.ONESHOT_V2 / "calls" / model / f"{task}.{variant}.json", row)
        t = token_values(row["usage"], "openrouter-batch")
        usage = dict(input=max(0, t["input_tokens"]-t["cached_input_tokens"]), input_cache_read=t["cached_input_tokens"], output=max(0, t["output_tokens"]-t["reasoning_tokens"]), output_reasoning=t["reasoning_tokens"])
        trace_call(digest, f"oneshot {model} {task} {variant}", cfg["canonical"], request, f["reply"], start, end, usage=usage, cost_usd=cost, session_id=f"oneshot/{model}", error=f["error"])
        print(model, task, variant, parsed["status"], flush=True)
    # Written last: a crash before this point leaves the batch resumable.
    _write_result(_batch_file(batch_id, ".result.json.gz"), batch)


def run_batch(model, tasks, variants, force=False):
    cfg = models()[model]
    if cfg["cli"] != "openrouter-batch": raise ValueError(f"{model} is not a batch model")
    claims, jobs = [], []
    try:
        for task in tasks:
            for variant in variants:
                request = request_for(model, task, variant); digest = request_hash(request)
                cache = C.ONESHOT_V2 / "calls" / model / f"{task}.{variant}.json"
                if not force and cache.exists() and read_json(cache).get("request_hash") == digest:
                    print(model, task, variant, "cached", flush=True); continue
                path = claim(model, task, variant)
                if path is None: continue
                claims.append(path)
                jobs.append(dict(task=task, variant=variant, request=request, request_hash=digest, custom_id=f"nb39-v2-{model}-{task}-{variant}-{digest[:12]}"))
        if not jobs: return
        by_cid = {j["custom_id"]: j for j in jobs}
        submissions = _open_submissions(model, set(by_cid))
        if submissions:
            held = {j["custom_id"] for s in submissions for j in s["jobs"]} & set(by_cid)
            if len(held) < len(by_cid): print(model, len(by_cid) - len(held), "jobs are not in the open batch; run again after it finishes", flush=True)
        else:
            submissions = [_submit(model, cfg, jobs)]
        for submission in submissions:
            ids = {j["custom_id"] for j in submission["jobs"]}
            _complete(model, cfg, submission, {c: j for c, j in by_cid.items() if c in ids})
    finally:
        for path in claims: path.unlink(missing_ok=True)


def export(models_selected, force=False, programs=None):
    """Export cached standalone programs in the layout used by agent authors."""
    programs = C.ONESHOT_V2 / "programs" if programs is None else Path(programs)
    langs = languages()
    for author, model in C.ONESHOT_AUTHORS.items():
        if model not in models_selected:
            continue
        cfg = C.ONESHOT_V2_MODELS[model]
        for task in C.ONESHOT_V2_TASKS:
            with tempfile.TemporaryDirectory() as tmp:
                staged = Path(tmp) / "export"
                staged.mkdir()
                metadata = {}
                for variant in C.ONESHOT_V2_VARIANTS:
                    relative = langs[variant]["path"]
                    source = programs / model / task / relative
                    if not source.is_file():
                        continue
                    kind = "langs" if variant in C.LANG_VARIANTS else "main"
                    work = Path(tmp) / variant
                    work.mkdir()
                    if variant not in ("plain", "fast"):
                        for name, contents in sessions.session_files(model, task, kind=kind).items():
                            if name.startswith(variant + "/"):
                                target = work / name
                                target.parent.mkdir(parents=True, exist_ok=True)
                                target.write_bytes(contents)
                    target = work / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
                    for name in sessions.harvest_files(work, kind):
                        src = work / name
                        if src.is_file() and not src.is_symlink():
                            dest = staged / name
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(src, dest)
                    cache = read_json(C.ONESHOT_V2 / "calls" / model / f"{task}.{variant}.json")
                    metadata[variant] = dict(path=relative, sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                             request_hash=cache["request_hash"])
                if not metadata:
                    continue
                write_json(staged / "meta.json", dict(author=author, source="oneshot", protocol="v2",
                           model=cfg["model"], cli=cfg["cli"], effort=cfg["effort"], programs=metadata))
                destination = C.PROGRAMS / author / task
                def contents(folder):
                    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
                if destination.exists():
                    if destination.is_dir() and contents(destination) == contents(staged):
                        continue
                    if not force:
                        raise FileExistsError(f"Export differs from {destination}; use --force to replace it")
                    if destination.is_dir():
                        shutil.rmtree(destination)
                    else:
                        destination.unlink()
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(staged, destination)


def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prompts", "run", "check", "hidden"):
        p = sub.add_parser(name)
        if name != "prompts": p.add_argument("--models", nargs="+", choices=models(), default=list(C.ONESHOT_V2_MODELS))
        p.add_argument("--tasks", nargs="+", choices=C.TASKS, default=list(C.ONESHOT_V2_TASKS))
        p.add_argument("--variants", nargs="+", choices=C.VARIANTS, default=list(C.ONESHOT_V2_VARIANTS))
        if name == "hidden": p.add_argument("--jobs", type=int, default=4)
        if name == "run": p.add_argument("--force", action="store_true")
    p = sub.add_parser("export")
    p.add_argument("--models", nargs="+", choices=list(C.ONESHOT_AUTHORS.values()), default=list(C.ONESHOT_AUTHORS.values()))
    p.add_argument("--force", action="store_true")
    sub.add_parser("summary"); args = parser.parse_args()
    if args.command == "prompts":
        for task in args.tasks:
            for variant in args.variants:
                prompt = prompt_for(task, variant); write_text(C.ONESHOT_V2 / "prompts" / task / f"{variant}.md", prompt)
                print(task, variant, len(prompt.encode("utf-8")), "bytes")
    elif args.command == "run":
        C.ONESHOT_WORK.mkdir(parents=True, exist_ok=True)
        write_text(C.ONESHOT_WORK / "system.txt", C.ONESHOT_SYSTEM)
        # One pool per model: a batch's polling never waits behind CLI jobs, and no model borrows another's threads.
        with contextlib.ExitStack() as stack:
            futures = []
            for m in args.models:
                batch = models()[m]["cli"] == "openrouter-batch"
                pool = stack.enter_context(concurrent.futures.ThreadPoolExecutor(max_workers=1 if batch else C.ONESHOT_JOBS_PER_MODEL))
                if batch: futures.append(pool.submit(run_batch, m, args.tasks, args.variants, args.force))
                else: futures.extend(pool.submit(run_one, m, t, v, args.force) for t in args.tasks for v in args.variants)
            for future in futures: future.result()
    elif args.command == "export": export(args.models, args.force)
    elif args.command == "check": check(args.models, args.tasks, args.variants)
    elif args.command == "hidden":
        if args.jobs < 1: parser.error("--jobs must be positive")
        hidden(args.models, args.tasks, args.variants, args.jobs)
    else: summary()
