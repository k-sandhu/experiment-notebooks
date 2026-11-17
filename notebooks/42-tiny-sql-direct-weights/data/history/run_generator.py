"""Run a tool-disabled CLI generator; save its text verbatim, then reshape and test it."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from model_and_test import ROOT, save_candidate, evaluate
from trace_calls import trace

CLI = Path(r"C:\Users\sandh\AppData\Roaming\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe")
PRIVATE = Path(r"C:\Users\sandh\.codex\scratch\sql-2208-isolated-cli-home")
EMPTY = PRIVATE / "empty-workspace"
PRIVATE.mkdir(parents=True, exist_ok=True)
EMPTY.mkdir(exist_ok=True)
neutral = PRIVATE / "neutral.txt"
neutral.write_text("You are a numerical weight generator. Return only the data requested by the user.", encoding="utf-8")
features = ["apps", "plugins", "remote_plugin", "hooks", "shell_tool", "unified_exec",
            "unified_exec_tty", "shell_snapshot", "view_image", "image_generation", "multi_agent",
            "multi_agent_v2", "browser_use", "browser_use_external", "browser_use_full_cdp_access",
            "in_app_browser", "computer_use", "code_mode", "code_mode_host", "skill_search",
            "skill_mcp_dependency_install", "sleep_tool", "tool_suggest", "goals", "worktrees",
            "workspace_dependencies", "memories", "agent_message_board", "daemon_auto_start"]
config = '\n'.join([
    'model = "gpt-6.1-sol"', 'model_reasoning_effort = "xhigh"',
    'approval_policy = "never"', 'sandbox_mode = "read-only"', 'web_search = "disabled"',
    'project_doc_max_bytes = 0', 'model_instructions_file = ' + json.dumps(str(neutral)),
    'mcp_servers = {}', '[skills.bundled]', 'enabled = false', '[skills]', 'include_instructions = false',
    '[features]', 'skip_host_skill_discovery = true',
] + [name + ' = false' for name in features])
(PRIVATE / "config.toml").write_text(config, encoding="utf-8")
(ROOT / "generator_cli_config.toml").write_text(config, encoding="utf-8")
env = os.environ.copy()
env["CODEX_HOME"] = str(PRIVATE)
env["PYTHONIOENCODING"] = "utf-8"
env.pop("CODEX_THREAD_ID", None)
env.pop("CODEX_INTERNAL_ORIGINATOR_OVERRIDE", None)

def preflight():
    output = subprocess.run([str(CLI), "-C", str(EMPTY), "debug", "prompt-input", "PREFLIGHT ONLY; NO MODEL CALL."],
                            env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    (ROOT / "prompt_preflight.stdout.json").write_text(output.stdout, encoding="utf-8")
    (ROOT / "prompt_preflight.stderr.txt").write_text(output.stderr, encoding="utf-8")
    if output.returncode:
        raise RuntimeError("CLI preflight failed: " + output.stderr[-2000:])
    forbidden = ["<skills_instructions>", "### Available skills", "# AGENTS.md instructions", "<recommended_plugins>"]
    found = [phrase for phrase in forbidden if phrase in output.stdout]
    if found:
        raise RuntimeError("Unwanted context in preflight: " + repr(found))
    print(json.dumps({"preflight_exit": output.returncode, "visible_context_bytes": len(output.stdout), "unwanted_context": found}), flush=True)


if "--preflight" in sys.argv:
    preflight()
    raise SystemExit(0)

preflight()
prompt = (ROOT / "generator_prompt.txt").read_text(encoding="utf-8")
request = {"model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "prompt": prompt,
           "output_schema": json.loads((ROOT / "weights_schema.json").read_text()),
           "cli_config": config, "tools_enabled": [], "forward_pass_feedback": False}
key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
cache_dir = ROOT / "editor_cache"
cache_dir.mkdir(exist_ok=True)
cache = cache_dir / f"{key}.json"
if cache.exists():
    record = json.loads(cache.read_text(encoding="utf-8"))
    answer = record["answer"]
    print("Replaying cached generator response.", flush=True)
else:
    original_home = Path(os.environ.get("CODEX_HOME", str(Path.home()/".codex")))
    credential_path = PRIVATE / "auth.json"
    # Authentication is read by the CLI, never exposed to the model or copied into experiment artifacts.
    shutil.copyfile(original_home / "auth.json", credential_path)
    command = [str(CLI), "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
               "--skip-git-repo-check", "--json", "--color", "never", "-C", str(EMPTY),
               "-m", "gpt-6.1-sol", "--output-schema", str(ROOT / "weights_schema.json")]
    # --ignore-user-config omits the isolated file too, so supply every setting explicitly.
    import tomllib
    parsed = tomllib.loads(config)
    def cli_value(value):
        return json.dumps(value, separators=(",", ":"))
    for name in ["model_reasoning_effort", "approval_policy", "sandbox_mode", "web_search", "project_doc_max_bytes", "model_instructions_file"]:
        command += ["-c", name + "=" + cli_value(parsed[name])]
    command += ["-c", "mcp_servers={}", "-c", "skills.bundled.enabled=false", "-c", "skills.include_instructions=false",
                "-c", "features.skip_host_skill_discovery=true"]
    for name in features:
        command += ["-c", "features." + name + "=false"]
    command.append("-")
    (ROOT / "generator_command.json").write_text(json.dumps(command, indent=2))
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.time()
    events = []
    try:
        with (ROOT / "generator_events.jsonl").open("w", encoding="utf-8") as event_file, (ROOT / "generator_stderr.txt").open("w", encoding="utf-8") as error_file:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error_file,
                                       env=env, cwd=EMPTY, text=True, encoding="utf-8", bufsize=1)
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                event_file.write(line)
                event_file.flush()
                try:
                    event = json.loads(line)
                    events.append(event)
                    item = event.get("item", {})
                    print(json.dumps({"event": event.get("type"), "item_type": item.get("type"),
                                      "elapsed_seconds": round(time.time()-t0, 1)}), flush=True)
                except json.JSONDecodeError:
                    pass
            status = process.wait()
    finally:
        # Remove only the explicit private credential copy after the subprocess exits.
        if credential_path.is_file():
            credential_path.unlink()
    end = dt.datetime.now(dt.timezone.utc)
    answers = [e["item"].get("text", "") for e in events
               if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"]
    answer = answers[-1] if answers else ""
    allowed_item_types = {"reasoning", "agent_message", "error"}
    other_items = [e for e in events if e.get("item", {}).get("type") not in allowed_item_types | {None}]
    usage = next((e.get("usage") for e in reversed(events) if e.get("type") == "turn.completed"), None)
    audit = {"model": "gpt-6.1-sol", "exit_code": status, "wall_seconds": time.time()-t0,
             "tool_event_count": len(other_items), "tool_events": other_items,
             "cli_notices": [e["item"].get("message") for e in events if e.get("item", {}).get("type") == "error"],
             "configured_tools_enabled": [], "usage": usage, "answer_bytes": len(answer.encode()),
             "prompt_bytes": len(prompt.encode()), "credential_copy_removed": not credential_path.exists(),
             "no_test_feedback": True}
    record = {"request": request, "answer": answer, "audit": audit, "start_utc": start.isoformat(), "end_utc": end.isoformat()}
    cache.write_text(json.dumps(record, indent=2), encoding="utf-8")
    (ROOT / "generator_audit.json").write_text(json.dumps(audit, indent=2))
    trace(key, "gpt-6.1-sol", request, answer, start, end, usage)
    if status != 0 or other_items:
        raise RuntimeError("Generator failed or emitted disallowed tool events; inspect audit.")

(ROOT / "generator_weights_output.json").write_text(answer, encoding="utf-8")
# Audit raw events independently, including when replaying an already saved response.
raw_events = [json.loads(line) for line in (ROOT / "generator_events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
non_message_items = [event for event in raw_events
                     if event.get("item", {}).get("type") not in {None, "reasoning", "agent_message", "error"}]
notices = [event["item"].get("message", "") for event in raw_events if event.get("item", {}).get("type") == "error"]
unexpected_errors = [notice for notice in notices if not notice.startswith(("Under-development features enabled:", "Code Mode is unavailable because code-mode host is disabled."))]
assert not non_message_items, "Disallowed tool/item event in CLI output"
assert not unexpected_errors, "Unexpected CLI error notice"
audit = dict(record["audit"])
audit.update(tool_event_count=len(non_message_items), tool_events=non_message_items, cli_notices=notices)
(ROOT / "generator_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
payload = json.loads(answer)
assert set(payload) == {"weights"}
save_candidate(payload["weights"], ROOT / "sol_candidate.safetensors")
print("Candidate values saved without modification; starting independent tests.", flush=True)
evaluate(ROOT / "sol_candidate.safetensors", "sol_candidate")
