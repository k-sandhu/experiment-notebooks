"""Preserve the unchanged partial response of an already-invalid stopped stream."""
import datetime as dt
import hashlib
import json

from model_and_test import ROOT
from trace_calls import trace

r = ROOT / "round-04-nemotron-free"
request = json.loads((r / "editor_request.json").read_text(encoding="utf-8"))
cache_key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
events = [json.loads(line) for line in (r / "stream_events.jsonl").read_text(encoding="utf-8").splitlines() if line]
answer = (r / "streamed_last_message.json").read_text(encoding="utf-8")
assert answer.startswith('{"weights":[')
assert "]" not in answer and answer.count(",") > 2208
finished = dt.datetime.now(dt.timezone.utc)
started = dt.datetime.fromtimestamp((r / "editor_request.json").stat().st_mtime, dt.timezone.utc)
usage = next((event["usage"] for event in reversed(events) if event.get("usage")), None)
error = {"tester_aborted": True, "reason": "The first weights array already contains more than 2208 entries; the response cannot satisfy the requested schema.",
         "completed_values_lower_bound": answer.count(",")}
record = {"cache_key": cache_key, "request": request, "events": events, "answer": answer,
          "stream_done": False, "http_status": 200, "error": error, "usage": usage,
          "started_utc": started.isoformat(), "finished_utc": finished.isoformat(),
          "wall_seconds": (finished-started).total_seconds(), "canonical_slug": "nvidia/nemotron-3-ultra-550b-a55b-20260604"}
(r / "editor_cache.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
(r / "generator_weights_output.json").write_text(answer, encoding="utf-8")
audit = {"model": request["model"], "format_error": "Too many weight values; stopped early by tester",
         "completed_values_lower_bound": answer.count(","), "response_complete": False,
         "candidate_saved": False, "candidate_values_modified_by_tester": False, "sql_execution": False,
         "training_or_optimization_steps": 0, "usage": usage, "price_cap": 0, "paid_fallback": False,
         "tool_call_events": sum(bool(choice.get("delta", {}).get("tool_calls")) for event in events for choice in event.get("choices", []))}
(r / "generator_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
trace(cache_key, request["model"], request, answer, started, finished, usage)
print(json.dumps(audit, indent=2))
