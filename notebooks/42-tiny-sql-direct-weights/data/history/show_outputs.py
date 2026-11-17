"""Save the CLI's exact numbers and show raw model generations. No SQL execution."""
import datetime as dt
import hashlib
import json
import torch
from model_and_test import ROOT, save_candidate, vocabulary, schema_prompt, encode, decode
from trace_calls import trace

events = [json.loads(line) for line in (ROOT / "generator_events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
allowed = {None, "reasoning", "agent_message", "error"}
unexpected_items = [event for event in events if event.get("item", {}).get("type") not in allowed]
assert not unexpected_items, "Unexpected tool event"
notices = [event["item"].get("message", "") for event in events if event.get("item", {}).get("type") == "error"]
assert all(notice.startswith(("Under-development features enabled:", "Code Mode is unavailable because code-mode host is disabled.")) for notice in notices)
assert any(event.get("type") == "turn.completed" for event in events), "Generator has not completed successfully"
answers = [event["item"]["text"] for event in events if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
assert len(answers) == 1
answer = answers[0]
(ROOT / "generator_weights_output.json").write_text(answer, encoding="utf-8")
payload = json.loads(answer)
assert set(payload) == {"weights"}
model = save_candidate(payload["weights"], ROOT / "sol_candidate.safetensors")
candidate_sha = hashlib.sha256((ROOT / "sol_candidate.safetensors").read_bytes()).hexdigest()
frozen_sha = hashlib.sha256(model.frozen_embeddings.numpy().tobytes()).hexdigest()
vocab = vocabulary()
cases = json.loads((ROOT / "generation_inputs.json").read_text(encoding="utf-8"))[:8]
records = []
for case in cases:
    prompt = schema_prompt(case["table"], case["columns"])
    initial_ids = encode(prompt, vocab)
    request = {"model": "sol-weights/frozen-glove-sql-2208", "checkpoint_sha256": candidate_sha,
               "prompt": prompt, "prompt_ids": initial_ids, "decoding": "unconstrained_greedy",
               "max_new_tokens": 32, "dtype": "float64", "sql_execution": False}
    key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    cache = ROOT / "generation_cache" / f"{key}.json"
    if cache.exists():
        record = json.loads(cache.read_text(encoding="utf-8"))
    else:
        started = dt.datetime.now(dt.timezone.utc)
        ids = list(initial_ids)
        generated = []
        steps = []
        eos = False
        error = None
        with torch.inference_mode():
            for step in range(min(32, 64-len(ids))):
                logits = model(torch.tensor([ids]))[0, -1]
                if not torch.isfinite(logits).all():
                    error = "Non-finite logits"
                    break
                token = int(logits.argmax())
                if token == vocab["<EOS>"]:
                    eos = True
                    break
                generated.append(token)
                ids.append(token)
                steps.append({"step": step+1, "token_id": token, "text": decode([token], vocab)})
        record = {"case": case, "request": request, "cache_key": key,
                  "raw_output": decode(generated, vocab), "generated_ids": generated,
                  "terminated_with_eos": eos, "inference_error": error, "steps": steps}
        cache.write_text(json.dumps(record, indent=2), encoding="utf-8")
        trace(key, "local/sol-weights-frozen-glove-sql-2208", request, record["raw_output"], started,
              dt.datetime.now(dt.timezone.utc), {"input": len(initial_ids), "output": len(generated)})
    records.append(record)
assert frozen_sha == hashlib.sha256(model.frozen_embeddings.numpy().tobytes()).hexdigest()
audit = {"model": "gpt-6.1-sol", "tool_call_events": len(unexpected_items),
         "cli_notices": notices, "output_values": len(payload["weights"]),
         "candidate_values_modified_by_tester": False, "frozen_embedding_sha256": frozen_sha,
         "sql_execution": False, "training_or_optimization_steps": 0,
         "usage": next(event["usage"] for event in events if event.get("type") == "turn.completed")}
(ROOT / "generator_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
result = {"audit": audit, "candidate_sha256": candidate_sha, "outputs": records}
(ROOT / "raw_outputs.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"audit": audit, "outputs": [{"schema": x["case"], "raw_output": x["raw_output"],
                  "terminated_with_eos": x["terminated_with_eos"], "inference_error": x["inference_error"]}
                  for x in records]}, indent=2))
