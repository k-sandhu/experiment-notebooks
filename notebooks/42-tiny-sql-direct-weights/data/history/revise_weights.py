"""Provide observational feedback to the tool-free CLI; load its revised numbers verbatim."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import torch
from safetensors.torch import load_file
from model_and_test import ROOT, save_candidate, vocabulary, encode, decode, schema_prompt
from trace_calls import trace

ATTEMPT = int(os.environ.get("SOL_SQL_ATTEMPT", "1"))
ROUND = ROOT / "round-02"
if ATTEMPT > 1:
    ROUND = ROUND / f"attempt-{ATTEMPT:02d}"
ROUND.mkdir(parents=True, exist_ok=True)
PRIV = Path(r"C:\Users\sandh\.codex\scratch\sql-2208-isolated-cli-home")
EMPTY = PRIV / "empty-workspace"
command = json.loads((ROOT / "generator_command.json").read_text())
if ATTEMPT > 1:
    assert command[-1] == "-"
    command = command[:-1] + ["--output-last-message", str(ROUND / "cli_last_message.json"), "-"]
assert command[command.index("-m")+1] == "gpt-6.1-sol"
assert "--ignore-user-config" in command and "--ephemeral" in command
for restriction in ["features.shell_tool=false", "features.code_mode=false", "features.code_mode_host=false",
                    "features.multi_agent=false", "features.apps=false", "features.plugins=false",
                    "features.skill_search=false", "skills.bundled.enabled=false", "skills.include_instructions=false",
                    'web_search="disabled"', "mcp_servers={}"]:
    assert restriction in command, restriction

previous = json.loads((ROOT / "raw_outputs.json").read_text(encoding="utf-8"))
feedback_lines = [
    "VERBAL FEEDBACK FROM THE INDEPENDENT TESTER, AFTER YOUR FIRST WEIGHT SUBMISSION",
    "Your first response was loaded exactly as returned: all 2,208 values, no training, repair, optimization or manual edits.",
    "The frozen embedding matrix was unchanged. We used the specified unconstrained greedy generation.",
    "No SQL database was used for this feedback. The following are exact observed input/output pairs.",
    "For readability, the desired outputs below use ordinary SQL whitespace. Equivalent spacing/capitalization is acceptable.",
    "",
]
for number, sample in enumerate(previous["outputs"], start=1):
    case = sample["case"]
    expected = 'select ' + ','.join('"'+col+'"' for col in case["columns"]) + ' from "' + case["table"] + '";'
    feedback_lines += [f"Example {number}:",
                       "Input: " + sample["request"]["prompt"],
                       "Your model actually emitted: " + json.dumps(sample["raw_output"]),
                       "Stopped with <EOS>: " + str(sample["terminated_with_eos"]),
                       "Requested output: " + expected + "<EOS>", ""]
feedback_lines += [
    'All eight schemas produced exactly the same text: select"name"from"data"; followed by <EOS>.',
    "The first schema happened to match those identifiers. On the other seven, the output did not use the supplied table name and supplied columns.",
    "On inputs with two or three columns, it also omitted requested columns. The observed failure is a constant query, not schema-dependent SQL generation.",
    "Please update your previous weights so the actual generated token sequence depends on the provided table and every provided column, in order.",
    "Keep the same architecture, all frozen embeddings, vocabulary, tensor layout, ordinary argmax decoder and output limit.",
    "The tester will not add an SQL template, grammar mask, copying helper, token substitution or output repair.",
    "You still have no tools, web access, code execution, file access, skills or other agents. You cannot request evaluation during this turn.",
    "Return your revised COMPLETE 2,208 weights, not deltas, with every scalar explicitly present in the same row-major order.",
    'Return only {"weights":[2208 finite JSON numbers]}. No code, commentary, formulas, ellipses or repetition notation.',
]
feedback = "\n".join(feedback_lines)
(ROUND / "verbal_feedback.txt").write_text(feedback, encoding="utf-8")
old_answer = (ROOT / "generator_weights_output.json").read_text(encoding="utf-8")
# The original call was ephemeral. Supply its exact specification and response explicitly.
prompt = (ROOT / "generator_prompt.txt").read_text(encoding="utf-8")
prompt += "\n\nYOUR PREVIOUS COMPLETE WEIGHT RESPONSE\n" + old_answer + "\n\n" + feedback
(ROUND / "generator_prompt.txt").write_text(prompt, encoding="utf-8")
request = {"model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "prompt": prompt,
           "command": command, "tools_enabled": [], "feedback": feedback,
           "round": 2, "attempt": ATTEMPT, "sql_execution": False, "previous_response_sha256": hashlib.sha256(old_answer.encode()).hexdigest()}
cache_key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
cache = ROUND / "editor_cache.json"
env = os.environ.copy()
env["CODEX_HOME"] = str(PRIV)
env["PYTHONIOENCODING"] = "utf-8"
env.pop("CODEX_THREAD_ID", None)
env.pop("CODEX_INTERNAL_ORIGINATOR_OVERRIDE", None)

if cache.exists():
    record = json.loads(cache.read_text(encoding="utf-8"))
    assert record["cache_key"] == cache_key
    events = record["events"]
    print("Replaying cached round-02 CLI response.", flush=True)
else:
    preflight = subprocess.run([command[0], "-C", str(EMPTY), "debug", "prompt-input", "PREFLIGHT; NO MODEL CALL."],
                               env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    (ROUND / "prompt_preflight.stdout.json").write_text(preflight.stdout, encoding="utf-8")
    (ROUND / "prompt_preflight.stderr.txt").write_text(preflight.stderr, encoding="utf-8")
    assert preflight.returncode == 0, preflight.stderr
    for phrase in ["<skills_instructions>", "### Available skills", "# AGENTS.md instructions", "<recommended_plugins>"]:
        assert phrase not in preflight.stdout, phrase
    print(json.dumps({"preflight_passed": True, "model": "gpt-6.1-sol", "prompt_bytes": len(prompt.encode()),
                      "feedback_examples": len(previous["outputs"]), "editable_values": 2208}), flush=True)
    original_home = Path(os.environ.get("CODEX_HOME", str(Path.home()/".codex")))
    credential = PRIV / "auth.json"
    assert not credential.exists(), "Another isolated CLI call is using this credential path"
    shutil.copyfile(original_home / "auth.json", credential)
    events = []
    started = dt.datetime.now(dt.timezone.utc)
    t0 = time.time()
    try:
        with (ROUND / "generator_events.jsonl").open("w", encoding="utf-8") as out, (ROUND / "generator_stderr.txt").open("w", encoding="utf-8") as err:
            process = subprocess.Popen(command, env=env, cwd=EMPTY, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=err, text=True, encoding="utf-8", bufsize=1)
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                out.write(line)
                out.flush()
                try:
                    event = json.loads(line)
                    events.append(event)
                    print(json.dumps({"event": event.get("type"), "item_type": event.get("item", {}).get("type"),
                                      "elapsed_seconds": round(time.time()-t0, 1)}), flush=True)
                except json.JSONDecodeError:
                    pass
            status = process.wait()
    finally:
        if credential.is_file():
            credential.unlink()
    finished = dt.datetime.now(dt.timezone.utc)
    record = {"request": request, "cache_key": cache_key, "events": events,
              "exit_code": status, "started_utc": started.isoformat(), "finished_utc": finished.isoformat(),
              "wall_seconds": time.time()-t0}
    cache.write_text(json.dumps(record, indent=2), encoding="utf-8")
    final_messages = [event["item"]["text"] for event in events if event.get("type") == "item.completed"
                      and event.get("item", {}).get("type") == "agent_message"]
    usage = next((event.get("usage") for event in events if event.get("type") == "turn.completed"), None)
    trace(cache_key, "gpt-6.1-sol", request, final_messages[-1] if final_messages else "", started, finished, usage)

assert record["exit_code"] == 0, "CLI invocation failed"
unexpected = [event for event in events if event.get("item", {}).get("type") not in {None, "reasoning", "agent_message", "error"}]
assert not unexpected, "Disallowed tool/item event"
notices = [event["item"].get("message", "") for event in events if event.get("item", {}).get("type") == "error"]
assert all(notice.startswith(("Under-development features enabled:", "Code Mode is unavailable because code-mode host is disabled.")) for notice in notices)
answers = [event["item"]["text"] for event in events if event.get("type") == "item.completed"
           and event.get("item", {}).get("type") == "agent_message"]
assert len(answers) == 1
answer = answers[0]
(ROUND / "generator_weights_output.json").write_text(answer, encoding="utf-8")
payload = json.loads(answer)
assert set(payload) == {"weights"}
model = save_candidate(payload["weights"], ROUND / "sol_candidate.safetensors")
layout = json.loads((ROOT / "tensor_layout.json").read_text())
flat = torch.cat([dict(model.named_parameters())[entry["name"]].reshape(-1) for entry in layout])
assert torch.equal(flat, torch.tensor(payload["weights"], dtype=torch.float64))
first_state = load_file(str(ROOT / "sol_candidate.safetensors"))
assert torch.equal(model.frozen_embeddings, first_state["frozen_embeddings"])
changed = sum(int((dict(model.named_parameters())[entry["name"]] != first_state[entry["name"]]).sum()) for entry in layout)
checkpoint_sha = hashlib.sha256((ROUND / "sol_candidate.safetensors").read_bytes()).hexdigest()
vocab = vocabulary()
cases = json.loads((ROOT / "generation_inputs.json").read_text())[:12]
outputs = []
for case in cases:
    prompt_text = schema_prompt(case["table"], case["columns"])
    initial_ids = encode(prompt_text, vocab)
    generation_request = {"model": "sol-weights/frozen-glove-sql-2208", "checkpoint_sha256": checkpoint_sha,
                          "prompt": prompt_text, "prompt_ids": initial_ids, "decoding": "unconstrained_greedy",
                          "max_new_tokens": 32, "dtype": "float64", "sql_execution": False}
    generation_key = hashlib.sha256(json.dumps(generation_request, sort_keys=True).encode()).hexdigest()
    generation_cache = ROOT / "generation_cache" / f"{generation_key}.json"
    if generation_cache.exists():
        sample = json.loads(generation_cache.read_text(encoding="utf-8"))
    else:
        generation_start = dt.datetime.now(dt.timezone.utc)
        ids = list(initial_ids)
        generated = []
        steps = []
        eos = False
        inference_error = None
        with torch.inference_mode():
            for step in range(min(32, 64-len(ids))):
                logits = model(torch.tensor([ids]))[0, -1]
                if not torch.isfinite(logits).all():
                    inference_error = "Non-finite logits"
                    break
                token = int(logits.argmax())
                if token == vocab["<EOS>"]:
                    eos = True
                    break
                generated.append(token)
                ids.append(token)
                steps.append({"step": step+1, "token_id": token, "text": decode([token], vocab)})
        sample = {"case": case, "request": generation_request, "cache_key": generation_key,
                  "raw_output": decode(generated, vocab), "generated_ids": generated,
                  "terminated_with_eos": eos, "inference_error": inference_error, "steps": steps}
        generation_cache.write_text(json.dumps(sample, indent=2), encoding="utf-8")
        trace(generation_key, "local/sol-weights-frozen-glove-sql-2208", generation_request,
              sample["raw_output"], generation_start, dt.datetime.now(dt.timezone.utc),
              {"input": len(initial_ids), "output": len(generated)})
    sample["provided_as_feedback"] = case["id"] in {item["case"]["id"] for item in previous["outputs"]}
    outputs.append(sample)
usage = next(event["usage"] for event in events if event.get("type") == "turn.completed")
audit = {"round": 2, "attempt": ATTEMPT, "model": "gpt-6.1-sol", "tool_call_events": 0, "output_values": len(payload["weights"]),
         "changed_values_vs_round_1": changed, "candidate_values_modified_by_tester": False,
         "frozen_embeddings_unchanged": True, "sql_execution": False, "training_or_optimization_steps": 0,
         "feedback_examples": len(previous["outputs"]), "generation_examples": len(outputs),
         "fresh_examples_not_in_feedback": sum(not sample["provided_as_feedback"] for sample in outputs),
         "usage": usage, "wall_seconds": record.get("wall_seconds"), "cli_notices": notices}
(ROUND / "generator_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
(ROUND / "raw_outputs.json").write_text(json.dumps({"audit": audit, "outputs": outputs}, indent=2), encoding="utf-8")
print(json.dumps({"audit": audit, "outputs": [{"schema": sample["case"], "raw_output": sample["raw_output"],
                  "provided_as_feedback": sample["provided_as_feedback"], "terminated_with_eos": sample["terminated_with_eos"],
                  "inference_error": sample["inference_error"]} for sample in outputs]}, indent=2), flush=True)
