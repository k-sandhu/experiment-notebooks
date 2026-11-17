"""Test a free, tool-free open-weight editor; never generate or repair its weights."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import time

import requests
import torch
from safetensors.torch import load_file

from model_and_test import ROOT, save_candidate, vocabulary, encode, decode, schema_prompt
from trace_calls import trace

MODEL = os.environ.get("FREE_SQL_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
CONFIGS = {
    "nvidia/nemotron-3-ultra-550b-a55b:free": ("nvidia/nemotron-3-ultra-550b-a55b-20260604", "round-04-nemotron-free", "NVIDIA Nemotron 3 Ultra"),
    "nvidia/nemotron-3.5-super-vl:free": ("nvidia/nemotron-3.5-super-vl-20261015", "round-05-nemotron-super-free", "NVIDIA Nemotron 3.5 Super VL"),
}
CANONICAL, DIRECTORY, EDITOR_NAME = CONFIGS[MODEL]
ROUND = ROOT / DIRECTORY
ROUND.mkdir(parents=True, exist_ok=True)
URL = "https://openrouter.ai/api/v1"
ATTEMPT = int(os.environ.get("FREE_SQL_ATTEMPT", "1"))
if ATTEMPT > 1:
    ROUND = ROUND / f"attempt-{ATTEMPT:02d}"
    ROUND.mkdir(parents=True, exist_ok=True)

prompt = (ROOT / "round-03-astra" / "generator_prompt.txt").read_text(encoding="utf-8")
prompt = prompt.replace("FOR GPT-6 ASTRA", "FOR " + EDITOR_NAME.upper())
prompt = prompt.replace("You are Astra, a new weight editor.", "You are " + EDITOR_NAME + ", a new weight editor.")
prompt += ("\n\nTESTER CLARIFICATION: The experiment now only displays raw generated text. "
           "No SQL is executed and no SQL tables are created. The desired text and model specification "
           "are unchanged. The earlier sentence about executable-SQL scoring is superseded. "
           "Only return the complete numeric JSON object; do not output a program that computes it.\n")
(ROUND / "generator_prompt.txt").write_text(prompt, encoding="utf-8")
request = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
           "temperature": 0, "max_tokens": 65536,
           "reasoning": {"effort": "high", "exclude": True},
           "tool_choice": "none", "plugins": [],
           "provider": {"only": ["nvidia"], "allow_fallbacks": False,
                        "max_price": {"prompt": 0, "completion": 0, "request": 0}},
           "stream": True, "stream_options": {"include_usage": True}}
if "3.5-super" in MODEL:
    request["max_tokens"] = 32768
    request["reasoning"] = {"enabled": True, "exclude": True}
    request["response_format"] = {"type": "json_schema", "json_schema": {
        "name": "complete_model_weights", "strict": True, "schema": {
            "type": "object", "additionalProperties": False,
            "properties": {"weights": {"type": "array", "items": {"type": "number"}, "minItems": 2208, "maxItems": 2208}},
            "required": ["weights"]}}}
cache_key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
(ROUND / "editor_request.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
cache = ROUND / "editor_cache.json"

if cache.exists():
    record = json.loads(cache.read_text(encoding="utf-8"))
    assert record["cache_key"] == cache_key
    print("Replaying cached free-model response.", flush=True)
else:
    metadata = requests.get(URL + "/models", timeout=30).json()
    model_info = next(item for item in metadata["data"] if item["id"] == MODEL)
    assert model_info["canonical_slug"] == CANONICAL
    assert int(model_info["context_length"]) >= 1000000
    assert all(float(model_info["pricing"][key]) == 0 for key in ("prompt", "completion"))
    endpoints = requests.get(URL + "/models/" + MODEL + "/endpoints", timeout=30).json()
    (ROUND / "model_metadata.json").write_text(json.dumps({"model": model_info, "endpoints": endpoints}, indent=2), encoding="utf-8")
    assert any(ep["provider_name"].lower() == "nvidia"
               and int(ep["context_length"]) >= 1000000
               and all(float(ep["pricing"][key]) == 0 for key in ("prompt", "completion"))
               for ep in endpoints["data"]["endpoints"])
    print(json.dumps({"preflight_passed": True, "model": MODEL, "canonical_slug": CANONICAL,
                      "prompt_bytes": len(prompt.encode()), "max_output_tokens": request["max_tokens"],
                      "tools": [], "paid_fallback": False, "max_price": 0}), flush=True)
    started = dt.datetime.now(dt.timezone.utc)
    t0 = time.monotonic()
    events = []
    parts = []
    done = False
    failure = None
    first_content_seconds = None
    last_progress = t0
    http_status = None
    try:
        with requests.post(URL + "/chat/completions", json=request,
                           headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
                           stream=True, timeout=(20, 120)) as response:
            http_status = response.status_code
            with (ROUND / "stream_events.jsonl").open("w", encoding="utf-8") as log, \
                    (ROUND / "streamed_last_message.json").open("w", encoding="utf-8") as answer_file:
                if not response.ok:
                    failure = {"http_status": response.status_code, "body": response.text}
                else:
                    response.encoding = "utf-8"
                    for line in response.iter_lines(decode_unicode=True, chunk_size=1):
                        if not line:
                            continue
                        if time.monotonic() - last_progress > 40:
                            print(json.dumps({"status": "stream_open", "elapsed_seconds": round(time.monotonic()-t0, 1),
                                              "visible_characters": sum(map(len, parts))}), flush=True)
                            last_progress = time.monotonic()
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            done = True
                            break
                        event = json.loads(data)
                        events.append(event)
                        log.write(json.dumps(event) + "\n")
                        log.flush()
                        if "error" in event:
                            failure = event["error"]
                        for choice in event.get("choices", []):
                            delta = choice.get("delta", {})
                            content = delta.get("content")
                            if content:
                                if first_content_seconds is None:
                                    first_content_seconds = time.monotonic()-t0
                                parts.append(content)
                                answer_file.write(content)
                                answer_file.flush()
    except (requests.RequestException, ValueError) as exc:
        failure = {"exception_type": type(exc).__name__, "message": str(exc)}
    finished = dt.datetime.now(dt.timezone.utc)
    usage = next((event["usage"] for event in reversed(events) if event.get("usage")), None)
    record = {"cache_key": cache_key, "request": request, "canonical_slug": CANONICAL,
              "events": events, "answer": "".join(parts), "stream_done": done, "error": failure,
              "http_status": http_status, "usage": usage, "started_utc": started.isoformat(),
              "finished_utc": finished.isoformat(), "wall_seconds": time.monotonic()-t0,
              "first_content_seconds": first_content_seconds}
    cache.write_text(json.dumps(record, indent=2), encoding="utf-8")
    trace(cache_key, MODEL, request, record["answer"], started, finished, usage)

events = record["events"]
tools = [choice["delta"]["tool_calls"] for event in events for choice in event.get("choices", [])
         if choice.get("delta", {}).get("tool_calls")]
finish_reasons = [choice["finish_reason"] for event in events for choice in event.get("choices", [])
                  if choice.get("finish_reason")]
actual_models = sorted({event["model"] for event in events if event.get("model")})
providers = sorted({event["provider"] for event in events if event.get("provider")})
answer = record["answer"]
(ROUND / "generator_weights_output.json").write_text(answer, encoding="utf-8")
audit = {"model": MODEL, "canonical_slug": CANONICAL, "actual_models": actual_models,
         "providers": providers, "usage": record.get("usage"), "wall_seconds": record["wall_seconds"],
         "first_content_seconds": record.get("first_content_seconds"), "http_status": record["http_status"],
         "finish_reasons": finish_reasons, "stream_done": record["stream_done"], "error": record["error"],
         "tool_call_events": len(tools), "candidate_values_modified_by_tester": False,
         "sql_execution": False, "training_or_optimization_steps": 0}
format_error = None
payload = None
try:
    assert not record["error"], "Transport/provider error"
    assert record["stream_done"], "Response did not finish"
    assert not tools, "Unexpected tool-call output (no tools were executed)"
    assert actual_models == [MODEL], "Unexpected model"
    assert providers == ["Nvidia"], "Unexpected provider"
    # The final usage-bearing chunk can repeat the preceding finish_reason.
    assert finish_reasons and set(finish_reasons) == {"stop"}, "Response did not stop normally"
    payload = json.loads(answer)
    assert isinstance(payload, dict) and set(payload) == {"weights"}, "Wrong JSON schema"
    assert isinstance(payload["weights"], list), "Weights must be a list"
    audit["output_values"] = len(payload["weights"])
    assert len(payload["weights"]) == 2208, "Wrong number of weights"
    assert all(type(value) in (int, float) and math.isfinite(value) for value in payload["weights"]), "Non-numeric/non-finite weight"
except (AssertionError, json.JSONDecodeError) as exc:
    format_error = str(exc)
audit["format_error"] = format_error
if format_error:
    (ROUND / "generator_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2), flush=True)
    raise SystemExit(2)

model = save_candidate(payload["weights"], ROUND / "nemotron_candidate.safetensors")
layout = json.loads((ROOT / "tensor_layout.json").read_text())
parameters = dict(model.named_parameters())
flat = torch.cat([parameters[entry["name"]].reshape(-1) for entry in layout])
assert torch.equal(flat, torch.tensor(payload["weights"], dtype=torch.float64))
last_sol_dir = ROOT / "round-02" / "attempt-02"
old_state = load_file(str(last_sol_dir / "sol_candidate.safetensors"))
assert torch.equal(model.frozen_embeddings, old_state["frozen_embeddings"])
audit["frozen_embeddings_unchanged"] = True
audit["changed_values_vs_latest_sol"] = sum(int((parameters[entry["name"]] != old_state[entry["name"]]).sum()) for entry in layout)
checkpoint_sha = hashlib.sha256((ROUND / "nemotron_candidate.safetensors").read_bytes()).hexdigest()
vocab = vocabulary()
cases = json.loads((ROOT / "generation_inputs.json").read_text())[:16]
feedback_ids = {item["case"]["id"] for item in json.loads((last_sol_dir / "raw_outputs.json").read_text())["outputs"]}
outputs = []
torch.set_num_threads(2)
for case in cases:
    prompt_text = schema_prompt(case["table"], case["columns"])
    initial_ids = encode(prompt_text, vocab)
    generation_request = {"model": "nemotron-weights/frozen-glove-sql-2208", "checkpoint_sha256": checkpoint_sha,
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
        trace(generation_key, "local/nemotron-weights-frozen-glove-sql-2208", generation_request,
              sample["raw_output"], generation_start, dt.datetime.now(dt.timezone.utc),
              {"input": len(initial_ids), "output": len(generated)})
    sample["provided_as_feedback"] = case["id"] in feedback_ids
    outputs.append(sample)
audit["generation_examples"] = len(outputs)
audit["fresh_examples_not_in_feedback"] = sum(not item["provided_as_feedback"] for item in outputs)
(ROUND / "generator_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
(ROUND / "raw_outputs.json").write_text(json.dumps({"audit": audit, "outputs": outputs}, indent=2), encoding="utf-8")
print(json.dumps({"audit": audit, "outputs": [{"schema": item["case"], "raw_output": item["raw_output"],
                  "provided_as_feedback": item["provided_as_feedback"], "terminated_with_eos": item["terminated_with_eos"],
                  "inference_error": item["inference_error"]} for item in outputs]}, indent=2), flush=True)
