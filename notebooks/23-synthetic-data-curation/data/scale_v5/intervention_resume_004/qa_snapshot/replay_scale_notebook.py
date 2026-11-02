"""Completion-gated offline nbconvert in a verified Notebook23-only temp clone.

Only the executed notebook is returned. All generated historical timing files,
figures and data stay in the clone. Real model CLI launches are blocked in both
nbconvert and its dedicated Python kernel by a temporary startup audit hook.
"""
import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from verify_scale_delivery import (SCALE_QA_FOLDER, SCALE_QA_NOTEBOOK, SCALE_QA_VERSION,
    scale_qa_baseline, scale_qa_cache_hashes, scale_qa_child, scale_qa_complete,
    scale_qa_files, scale_qa_hash, scale_qa_notebook, scale_qa_protected,
    scale_qa_read, scale_qa_sha, scale_qa_verify, scale_qa_write)

SCALE_QA_GUARD_VERSION = "scale-offline-process-and-network-guard-v1"
SCALE_QA_LIVE_PATTERN = re.compile(r"(?:^|_)(?:LIVE|ALLOW_LIVE|ENABLE_LIVE|LIVE_CALLS|COLLECT_LIVE|RUN_LIVE)$", re.I)
SCALE_QA_OFFLINE_PATTERN = re.compile(r"(?:^|_)OFFLINE$", re.I)
SCALE_QA_VOLATILE = {"offline_replay_validation.json", "offline_replay_cache_hashes.json.gz",
    "delivery_validation.json", "delivery_preflight_validation.json"}

SCALE_QA_GUARD_SOURCE = r"""
import ipaddress as _ipaddress
import json as _json
import os as _os
import re as _re
import socket as _socket
import sys as _sys
SCALE_QA_GUARD_VERSION = "scale-offline-process-and-network-guard-v1"
SCALE_QA_GUARD_PID = _os.getpid()
_tools = _re.compile(r"(?<![A-Za-z0-9_.-])(codex|claude|muse)(?:\.(?:exe|cmd|bat|ps1))?(?![A-Za-z0-9_.-])", _re.I)
def _emit(kind, **extra):
    path = _os.environ.get("SCALE_QA_GUARD_LOG")
    if path:
        with open(path, "a", encoding="utf-8", newline="\n") as stream:
            stream.write(_json.dumps({"kind": kind, "pid": _os.getpid(), **extra}) + "\n")
def _audit(event, args):
    command = None
    if event == "subprocess.Popen":
        command = args[:2]
    elif event == "os.system":
        command = args[:1]
    elif event in {"os.exec", "os.posix_spawn"}:
        command = args[:2]
    elif event == "os.spawn":
        command = args[1:3]
    if command is not None:
        flattened = _json.dumps(command, default=lambda value: value.decode(errors="replace") if isinstance(value, bytes) else str(value))
        match = _tools.search(flattened)
        if match:
            _emit("blocked_model_cli", tool=match.group(1).lower(), event=event)
            raise PermissionError("Offline QA blocks every codex/claude/muse process launch")
_sys.addaudithook(_audit)
_original_connect = _socket.socket.connect
_original_connect_ex = _socket.socket.connect_ex
def _check_address(address):
    if isinstance(address, tuple) and address:
        host = str(address[0])
        permitted = host.lower() == "localhost"
        if not permitted:
            try:
                permitted = _ipaddress.ip_address(host.split("%")[0]).is_loopback
            except ValueError:
                permitted = False
        if not permitted:
            _emit("blocked_external_network")
            raise PermissionError("Offline QA permits loopback socket connections only")
def _connect(self, address):
    _check_address(address)
    return _original_connect(self, address)
def _connect_ex(self, address):
    _check_address(address)
    return _original_connect_ex(self, address)
_socket.socket.connect = _connect
_socket.socket.connect_ex = _connect_ex
_emit("guard_loaded", kernel_candidate="-f" in _sys.argv)
"""


def scale_qa_force_offline(source):
    """Change only live/offline knob value spans, never frozen helper bodies."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError("Offline QA requires ordinary Python cells, not unparsed magics") from exc
    lines = source.splitlines(keepends=True)
    offsets, total = [], 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    def span(node):
        # AST columns count UTF-8 bytes, not Python Unicode characters.
        start = offsets[node.lineno - 1] + len(lines[node.lineno - 1].encode()[:node.col_offset].decode())
        end = offsets[node.end_lineno - 1] + len(lines[node.end_lineno - 1].encode()[:node.end_col_offset].decode())
        return start, end
    replacements = {}
    knobs = []
    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            pass
        def visit_AsyncFunctionDef(self, node):
            pass
        def visit_ClassDef(self, node):
            pass
        def replace(self, value, forced, name):
            if isinstance(value, ast.Constant) and value.value is forced:
                return
            replacements[span(value)] = "True" if forced else "False"
            knobs.append({"name": name, "forced_value": forced})
        def visit_Assign(self, node):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            for name in names:
                if SCALE_QA_LIVE_PATTERN.search(name): self.replace(node.value, False, name)
                elif SCALE_QA_OFFLINE_PATTERN.search(name): self.replace(node.value, True, name)
            self.visit(node.value)
        def visit_AnnAssign(self, node):
            if isinstance(node.target, ast.Name) and node.value is not None:
                if SCALE_QA_LIVE_PATTERN.search(node.target.id): self.replace(node.value, False, node.target.id)
                elif SCALE_QA_OFFLINE_PATTERN.search(node.target.id): self.replace(node.value, True, node.target.id)
            if node.value is not None: self.visit(node.value)
        def visit_Call(self, node):
            for keyword in node.keywords:
                if keyword.arg in {"live", "allow_live", "live_calls"}:
                    self.replace(keyword.value, False, "call." + keyword.arg)
            self.generic_visit(node)
    Visitor().visit(tree)
    # An assignment override subsumes any nested call keyword override.
    spans = sorted(replacements)
    outer = [(start, end) for start, end in spans if not any(a <= start and end <= b and (a,b) != (start,end) for a,b in spans)]
    for start, end in reversed(outer):
        source = source[:start] + replacements[start,end] + source[end:]
    return source, knobs


def scale_qa_guard_assertion(source):
    tree = ast.parse(source)
    insertion = 0
    for index, node in enumerate(tree.body):
        if ((index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))
                or isinstance(node, ast.ImportFrom) and node.module == "__future__"):
            insertion = node.end_lineno
        else:
            break
    lines = source.splitlines(keepends=True)
    assertion = ("assert getattr(__import__('sys').modules.get('sitecustomize'), 'SCALE_QA_GUARD_VERSION', None) == "
        + repr(SCALE_QA_GUARD_VERSION) + ", 'Offline startup guard was not loaded'\n"
        + "assert getattr(__import__('sys').modules.get('sitecustomize'), 'SCALE_QA_GUARD_PID', None) == __import__('os').getpid(), 'Kernel guard PID mismatch'\n")
    return "".join(lines[:insertion]) + assertion + "".join(lines[insertion:])


def scale_qa_snapshot(folder):
    return {name: scale_qa_sha(path) for name, path in scale_qa_files(folder).items()}


def scale_qa_continuation_diagnostics(folder):
    """Validate the narrowly allowed operational receipts, never model data."""
    folder = Path(folder)
    prefix = "data/scale_v5/main/continuation_diagnostics/"
    pattern = re.compile(re.escape(prefix) + r"([0-9a-f]{12})/(?:chunk_\d{3}|original)_([0-9a-f]{12})\.json$")
    paths = {name: path for name, path in scale_qa_files(folder).items() if name.startswith(prefix)}
    interruption = scale_qa_intervention_diagnostics(folder)
    if not paths:
        return interruption
    data = folder / "data/scale_v5"
    amendments = {}
    for path in (data / "infrastructure_resume").glob("*.json"):
        item = scale_qa_read(path)
        if item.get("amendment_version") != "23-scale-capacity-continuation-v1":
            continue
        digest = scale_qa_sha(path)
        if digest[:12] in amendments:
            raise RuntimeError("Ambiguous continuation amendment hash prefix")
        if item.get("protocol") != "23-scale-v5" or item.get("source_freeze_sha256") != scale_qa_sha(data / "source_freeze.json"):
            raise RuntimeError("Continuation amendment has changed frozen-source lineage")
        implementation = item.get("implementation")
        if not isinstance(implementation, dict):
            raise RuntimeError("Continuation diagnostics need byte-bound implementation provenance")
        relative = Path(implementation["path"])
        target = (data / relative).resolve()
        if relative.is_absolute() or relative.drive or ".." in relative.parts or not target.is_relative_to(data.resolve()):
            raise RuntimeError("Continuation implementation path escapes study data")
        if scale_qa_sha(target) != implementation["sha256"]:
            raise RuntimeError("Continuation implementation bytes changed")
        amendments[digest[:12]] = (digest, implementation["sha256"])
    result = {}
    for name, path in paths.items():
        match = pattern.fullmatch(name)
        if not match or match[1] not in amendments:
            raise RuntimeError("Unrecognized or unbound continuation diagnostic: " + name)
        value = scale_qa_read(path)
        required = {"new_cli_subprocesses_this_run", "replayed_requests_this_run", "offline"}
        if (not isinstance(value, dict) or not required.issubset(value) or set(value) - required - {"note"}
                or any(type(value[key]) is not int or value[key] < 0 for key in required - {"offline"})
                or type(value["offline"]) is not bool or "note" in value and not isinstance(value["note"], str)):
            raise RuntimeError("Continuation diagnostics may contain only operational validation counters")
        digest = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        if digest[:12] != match[2]:
            raise RuntimeError("Continuation diagnostic payload hash changed")
        amendment_hash, implementation_hash = amendments[match[1]]
        result[name] = {"sha256": scale_qa_sha(path), "amendment_sha256": amendment_hash,
            "implementation_sha256": implementation_hash, "offline": value["offline"],
            "new_cli_subprocesses_this_run": value["new_cli_subprocesses_this_run"]}
    return {**result, **interruption}


def scale_qa_intervention_diagnostics(folder):
    """Only amendment002/003/004-bound counters may vary, never caches."""
    folder = Path(folder)
    prefix = "data/scale_v5/main/intervention_continuation_diagnostics/"
    pattern = re.compile(re.escape(prefix)+r"([0-9a-f]{12})/validation_([0-9a-f]{12})\.json$")
    paths = {name: path for name, path in scale_qa_files(folder).items() if name.startswith(prefix)}
    if not paths:
        return {}
    data = folder / "data/scale_v5"
    amendment_path = data / "intervention_resume/amendment_002.json"
    amendment = scale_qa_read(amendment_path)
    if (amendment.get("protocol") != "23-scale-v5" or
            amendment.get("amendment_version") != "23-scale-intervention-interruption-v1"):
        raise RuntimeError("Unrecognized intervention continuation amendment")
    def bound(item):
        relative = Path(item["path"])
        target = (data / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(data.resolve()):
            raise RuntimeError("Intervention continuation binding escapes study data")
        digest = item["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or scale_qa_sha(target) != digest:
            raise RuntimeError("Intervention continuation bound bytes changed: "+item["path"])
        return target
    protected = {item["path"]: item for item in amendment["protected_files"]}
    required = {"source_freeze.json", "intervention_start_declaration.json",
                "infrastructure_resume/amendment_001.json", "main/dispatch.json"}
    if len(protected) != len(amendment["protected_files"]) or not required.issubset(protected):
        raise RuntimeError("Intervention continuation lacks frozen protocol/gate bindings")
    for item in protected.values():
        bound(item)
    gate = scale_qa_read(data / "intervention_start_declaration.json")
    if (gate.get("protocol") != "23-scale-v5" or gate.get("phase") != "interventions_authorized_after_independent_audit"
            or len(gate.get("sha256", {})) != 38):
        raise RuntimeError("The original 38-binding pre-intervention gate is required")
    for relative, digest in gate["sha256"].items():
        bound({"path": relative, "sha256": digest})
    first = scale_qa_read(data / "infrastructure_resume/amendment_001.json")
    if (first.get("amendment_version") != "23-scale-capacity-continuation-v1" or
            first.get("source_freeze_sha256") != scale_qa_sha(data / "source_freeze.json")):
        raise RuntimeError("Intervention continuation changed amendment001/source lineage")
    bound(amendment["implementation"])
    bound(amendment["analysis_plan"])
    digest = scale_qa_sha(amendment_path)
    amendments = {digest[:12]: (digest, amendment)}
    third_path = data / "intervention_resume_003/amendment_003.json"
    if third_path.exists():
        third = scale_qa_read(third_path)
        if (third.get("protocol") != "23-scale-v5" or third.get("amendment_version") != "23-scale-intervention-interruption-v2"
                or third.get("predecessor") != {"path": "intervention_resume/amendment_002.json", "sha256": digest}):
            raise RuntimeError("Unrecognized third continuation predecessor/version")
        required_third = {"source_freeze.json", "intervention_start_declaration.json", "main/dispatch.json", "main/selection.json"}
        third_protected = third["protected_files"]
        if len({x["path"] for x in third_protected}) != len(third_protected) or not required_third <= {x["path"] for x in third_protected}:
            raise RuntimeError("Third continuation lacks selection/dispatch/source bindings")
        for item in third_protected:
            bound(item)
        for name in ("implementation", "analysis_plan", "process_proof", "cache_inventory"):
            bound(third[name])
        third_digest = scale_qa_sha(third_path)
        amendments[third_digest[:12]] = (third_digest, third)
    fourth_path = data / "intervention_resume_004/amendment_004.json"
    if fourth_path.exists():
        if not third_path.exists():
            raise RuntimeError("Fourth continuation requires its third predecessor")
        fourth = scale_qa_read(fourth_path)
        if (fourth.get("protocol") != "23-scale-v5" or fourth.get("amendment_version") != "23-scale-intervention-timeout-continuation-v1"
                or fourth.get("predecessor") != {"path": "intervention_resume_003/amendment_003.json", "sha256": third_digest}
                or fourth.get("analysis_plan") != third["analysis_plan"]):
            raise RuntimeError("Fourth continuation changed predecessor/version/analysis plan")
        required_fourth = {"source_freeze.json", "intervention_start_declaration.json", "main/dispatch.json", "main/selection.json", "intervention_resume_003/continuation_start_003.json"}
        fourth_protected = fourth["protected_files"]
        if len({x["path"] for x in fourth_protected}) != len(fourth_protected) or not required_fourth <= {x["path"] for x in fourth_protected}:
            raise RuntimeError("Fourth continuation lacks frozen source/dispatch/selection/gate bindings")
        for item in fourth_protected:
            bound(item)
        for name in ("implementation", "analysis_plan", "process_proof", "cache_inventory", "stop_record", "sleep_event", "error_metadata", "handling_plan"):
            bound(fourth[name])
        for relative, digest in fourth["provenance_sha256"].items():
            bound({"path": relative, "sha256": digest})
        fourth_digest = scale_qa_sha(fourth_path)
        amendments[fourth_digest[:12]] = (fourth_digest, fourth)
    result = {}
    for name, path in paths.items():
        match = pattern.fullmatch(name)
        if not match or match[1] not in amendments:
            raise RuntimeError("Unrecognized or unbound intervention continuation receipt: "+name)
        receipt_digest, receipt_amendment = amendments[match[1]]
        value = scale_qa_read(path)
        required_keys = {"new_cli_subprocesses_this_run", "replayed_requests_this_run", "offline"}
        if (not isinstance(value, dict) or not required_keys.issubset(value)
                or set(value)-required_keys-{"note"}
                or any(type(value[key]) is not int or value[key] < 0 for key in required_keys-{"offline"})
                or type(value["offline"]) is not bool or "note" in value and not isinstance(value["note"], str)):
            raise RuntimeError("Intervention continuation receipts permit only operational counters")
        if scale_qa_hash(value)[:12] != match[2]:
            raise RuntimeError("Intervention continuation receipt payload hash changed")
        result[name] = {"sha256": scale_qa_sha(path), "amendment_sha256": receipt_digest,
            "implementation_sha256": receipt_amendment["implementation"]["sha256"],
            "analysis_plan_sha256": receipt_amendment["analysis_plan"]["sha256"],
            "offline": value["offline"], "new_cli_subprocesses_this_run": value["new_cli_subprocesses_this_run"]}
    return result


def scale_qa_v5_outputs(folder):
    operational = scale_qa_continuation_diagnostics(folder)
    return {name: scale_qa_sha(path) for name, path in scale_qa_files(folder).items()
        if name.startswith(("data/scale_v5/", "figures/scale_v5/"))
        and name not in operational
        and Path(name).name not in SCALE_QA_VOLATILE
        and "run_validation" not in Path(name).name}


def scale_qa_continuation_changes(before, after):
    changes = scale_qa_differences({name: row["sha256"] for name, row in before.items()},
                                  {name: row["sha256"] for name, row in after.items()})
    for difference in changes:
        row = after.get(difference["path"])
        if not row or not row["offline"] or row["new_cli_subprocesses_this_run"] != 0:
            raise RuntimeError("Removed continuation receipt or changed receipt claiming live calls: " + difference["path"])
    return changes


def scale_qa_differences(before, after):
    return [{"path": name, "before": before.get(name), "after": after.get(name)}
        for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]


def scale_qa_prepare_guard(session, env):
    guard = session / "startup_guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(SCALE_QA_GUARD_SOURCE, encoding="utf-8", newline="\n")
    log = session / "guard_events.jsonl"
    env.update(SCALE_QA_GUARD_LOG=str(log), PYTHONNOUSERSITE="1",
        PYTHONPATH=str(guard) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""))
    # PATH shims supplement the Python audit hook, including shell invocations.
    for tool in ("codex", "claude", "muse"):
        if os.name == "nt":
            (guard / (tool + ".cmd")).write_text('@echo off\necho Offline QA blocked model CLI 1>&2\nexit /b 91\n', encoding="utf-8", newline="\n")
        else:
            path = guard / tool
            path.write_text('#!/bin/sh\necho "Offline QA blocked model CLI" >&2\nexit 91\n', encoding="utf-8", newline="\n")
            path.chmod(0o700)
    env["PATH"] = str(guard) + os.pathsep + env.get("PATH", "")
    kernel = session / "kernels" / "scale-qa-python"
    kernel.mkdir(parents=True)
    scale_qa_write(kernel / "kernel.json", {"argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Scale offline QA", "language": "python"})
    env["JUPYTER_PATH"] = str(session) + (os.pathsep + env["JUPYTER_PATH"] if env.get("JUPYTER_PATH") else "")
    return log



def scale_qa_run_replay(baseline, cell_timeout=1200, overall_timeout=7200, temp_parent=None):
    folder = Path(baseline["source"]).resolve()
    scale_qa_complete(folder)
    initial = scale_qa_verify(folder, baseline, require_notebook=False)
    missing = [name for name in ("nbconvert", "nbformat", "ipykernel", "matplotlib", "numpy") if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError("Offline replay dependencies are missing: " + ", ".join(missing))
    import nbformat
    before_files = scale_qa_snapshot(folder)
    before_caches = scale_qa_cache_hashes(folder)
    before_v5 = scale_qa_v5_outputs(folder)
    before_diagnostics = scale_qa_continuation_diagnostics(folder)
    original_notebook_hash = before_files[SCALE_QA_NOTEBOOK]
    parent = Path(temp_parent).resolve() if temp_parent else Path(tempfile.gettempdir()).resolve()
    if not parent.is_dir():
        raise ValueError("Temporary clone parent must already exist")
    session = Path(tempfile.mkdtemp(prefix="notebook23-scale-replay-", dir=parent)).resolve()
    session.relative_to(parent)
    clone = session / "notebooks" / SCALE_QA_FOLDER
    clone.mkdir(parents=True)
    report = {**initial, "status": "running", "clone": str(clone), "temporary_session": str(session),
        "only_notebook23_copied": True, "new_model_calls": None, "returned_executed_notebook": False,
        "historical_artifacts_returned_from_clone": 0, "clone_retained_for_review": True}
    cache_receipt = folder / "data/scale_v5/offline_replay_cache_hashes.json.gz"
    validation_receipt = folder / "data/scale_v5/offline_replay_validation.json"
    clone_before_caches, clone_after_caches, guard_events = {}, {}, []
    failure = None
    try:
        for name, source in scale_qa_files(folder).items():
            destination = scale_qa_child(clone, name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        clone_before_files = scale_qa_snapshot(clone)
        if clone_before_files != before_files:
            raise RuntimeError("Temporary clone bytes differ from the source snapshot before replay")
        clone_before_caches = scale_qa_cache_hashes(clone)
        if clone_before_caches != before_caches:
            raise RuntimeError("Clone response caches differ before replay")
        notebook_path = clone / SCALE_QA_NOTEBOOK
        notebook = nbformat.read(notebook_path, as_version=4)
        prepared_sources, overrides = {}, []
        first_code = None
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code" or not cell.source.strip():
                continue
            cell.source, changes = scale_qa_force_offline(cell.source)
            prepared_sources[index] = cell.source
            overrides.extend({"cell_index": index, **change} for change in changes)
            if first_code is None:
                first_code = index
        if first_code is None:
            raise RuntimeError("The completed notebook has no executable code cells")
        notebook.cells[first_code].source = scale_qa_guard_assertion(notebook.cells[first_code].source)
        notebook_path.write_text(nbformat.writes(notebook), encoding="utf-8", newline="\n")
        env = dict(os.environ)
        for name in list(env):
            if SCALE_QA_LIVE_PATTERN.search(name): env[name] = "0"
            elif SCALE_QA_OFFLINE_PATTERN.search(name): env[name] = "1"
        for name in ("NB_LIVE", "NB_HARD_LIVE", "NB_SOL_LIVE", "NB_HIGH_LIVE", "NB_SCALE_LIVE", "SCALE_LIVE", "LIVE_CALLS", "ALLOW_LIVE"):
            env[name] = "0"
        for name in ("NB_SMOKE", "NB_HARD_SMOKE", "NB_SOL_SMOKE", "NB_HIGH_SMOKE", "NB_SCALE_SMOKE"):
            env[name] = "0"
        env["NB_OFFLINE"] = "1"
        guard_log = scale_qa_prepare_guard(session, env)
        command = [sys.executable, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace",
            f"--ExecutePreprocessor.timeout={cell_timeout}", "--ExecutePreprocessor.kernel_name=scale-qa-python", SCALE_QA_NOTEBOOK]
        report.update(command=command, execution_log=str(session / "nbconvert.log"), live_knob_overrides=overrides)
        kwargs = {"cwd": clone, "env": env, "stderr": subprocess.STDOUT}
        if os.name == "nt": kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else: kwargs["start_new_session"] = True
        with (session / "nbconvert.log").open("w", encoding="utf-8", newline="\n") as log:
            process = subprocess.Popen(command, stdout=log, **kwargs)
            try:
                returncode = process.wait(timeout=overall_timeout)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
                else:
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                raise RuntimeError("Offline nbconvert exceeded its bounded overall timeout")
        if guard_log.exists():
            guard_events = [json.loads(line) for line in guard_log.read_text(encoding="utf-8").splitlines() if line]
        blocked = [event for event in guard_events if event["kind"].startswith("blocked_")]
        report.update(nbconvert_returncode=returncode,
            guarded_processes=sum(event["kind"] == "guard_loaded" for event in guard_events),
            blocked_model_cli_attempts=sum(event["kind"] == "blocked_model_cli" for event in guard_events),
            blocked_external_network_attempts=sum(event["kind"] == "blocked_external_network" for event in guard_events))
        if returncode:
            raise RuntimeError("Offline nbconvert failed; inspect the retained execution log")
        if blocked or report["guarded_processes"] < 2:
            raise RuntimeError("A forbidden launch/network attempt occurred or the parent/kernel guard was not verified")
        notebook = nbformat.read(notebook_path, as_version=4)
        notebook.cells[first_code].source = prepared_sources[first_code]
        notebook_path.write_text(nbformat.writes(notebook), encoding="utf-8", newline="\n")
        execution = scale_qa_notebook(clone)
        clone_after_caches = scale_qa_cache_hashes(clone)
        if clone_after_caches != before_caches:
            raise RuntimeError("Offline replay changed or created response-cache files")
        after_diagnostics = scale_qa_continuation_diagnostics(clone)
        diagnostic_changes = scale_qa_continuation_changes(before_diagnostics, after_diagnostics)
        report["operational_continuation_diagnostic_changes"] = diagnostic_changes
        v5_differences = scale_qa_differences(before_v5, scale_qa_v5_outputs(clone))
        report["v5_output_differences"] = v5_differences
        if v5_differences:
            raise RuntimeError("New V5 outputs differ in the replay clone; no notebook returned")
        changed_validations = []
        clone_after_files = scale_qa_snapshot(clone)
        for name, after_hash in clone_after_files.items():
            if "run_validation" not in Path(name).name or not name.endswith(".json") or clone_before_files.get(name) == after_hash:
                continue
            value = scale_qa_read(clone / name)
            counters = {key: value[key] for key in ("new_cli_subprocesses_this_run", "live_new_requests_this_run", "new_model_requests") if key in value}
            if any(counter != 0 for counter in counters.values()):
                raise RuntimeError("A changed replay validation claims new model calls: " + name)
            changed_validations.append({"path": name, "new_call_counters": counters})
        historical_differences = [name for name in baseline["source_files"] if name not in {SCALE_QA_NOTEBOOK, "README.md", ".gitattributes"}
            and clone_after_files.get(name) != before_files.get(name)]
        if scale_qa_cache_hashes(folder) != before_caches or scale_qa_v5_outputs(folder) != before_v5:
            raise RuntimeError("Worktree caches or V5 outputs changed concurrently during isolated replay")
        scale_qa_protected(folder, baseline)
        if scale_qa_sha(folder / SCALE_QA_NOTEBOOK) != original_notebook_hash:
            raise RuntimeError("The source notebook was edited during replay; refusing to overwrite it")
        temporary = folder / (SCALE_QA_NOTEBOOK + ".scale-replay.tmp")
        if temporary.exists():
            raise RuntimeError("The replay notebook staging path already exists")
        shutil.copy2(notebook_path, temporary)
        if scale_qa_sha(temporary) != scale_qa_sha(notebook_path):
            raise RuntimeError("Executed notebook staging bytes differ")
        os.replace(temporary, folder / SCALE_QA_NOTEBOOK)
        report.update(status="passed", **execution, returned_executed_notebook=True, new_model_calls=0,
            all_response_cache_files_unchanged=len(before_caches), v5_outputs_equivalent=True,
            historical_clone_artifact_differences_not_propagated=len(historical_differences),
            historical_clone_difference_examples=historical_differences[:20], changed_validation_reports=changed_validations)
    except Exception as exc:
        failure = exc
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        after_worktree_caches = scale_qa_cache_hashes(folder)
        if not clone_after_caches and (clone / "data/scale_v5/main/manifest.json").exists():
            clone_after_caches = scale_qa_cache_hashes(clone)
        cache_record = {"qa_version": SCALE_QA_VERSION, "algorithm": "SHA-256 exact bytes, allversions/cache files",
            "worktree_before": before_caches, "clone_before": clone_before_caches,
            "clone_after": clone_after_caches, "worktree_after": after_worktree_caches}
        scale_qa_write(cache_receipt, cache_record)
        report.update(finished_at_utc=datetime.now(timezone.utc).isoformat(),
            cache_hash_receipt="data/scale_v5/offline_replay_cache_hashes.json.gz",
            cache_hash_receipt_sha256=scale_qa_sha(cache_receipt),
            worktree_cache_hash_index_before=scale_qa_hash(before_caches),
            worktree_cache_hash_index_after=scale_qa_hash(after_worktree_caches),
            worktree_caches_unchanged=before_caches == after_worktree_caches,
            clone_cache_files_after=len(clone_after_caches))
        if before_caches != after_worktree_caches:
            failure = failure or RuntimeError("Worktree response cache bytes changed during QA")
            report.update(status="failed", error=str(failure))
        try:
            scale_qa_protected(folder, baseline)
        except Exception as exc:
            failure = failure or exc
            report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        scale_qa_write(validation_receipt, report)
    if failure is not None:
        raise RuntimeError(str(failure) + "; QA receipt: " + str(validation_receipt)) from failure
    return report


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=base / "scale_baseline_manifest.json")
    parser.add_argument("--cell-timeout", type=int, default=1200)
    parser.add_argument("--overall-timeout", type=int, default=7200)
    parser.add_argument("--temp-parent", type=Path, help="Existing directory for the verified temporary clone; retained for review")
    args = parser.parse_args()
    if args.cell_timeout < 1 or args.overall_timeout < 1:
        parser.error("Timeouts must be positive")
    report = scale_qa_run_replay(scale_qa_baseline(args.baseline), args.cell_timeout, args.overall_timeout, args.temp_parent)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
