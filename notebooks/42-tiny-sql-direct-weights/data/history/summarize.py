"""Report unmodified submitted weights and measured results, including failures."""
import hashlib
import json
from collections import Counter
import torch
from safetensors.torch import load_file
from model_and_test import ROOT

baseline = json.loads((ROOT / "baseline_results.json").read_text())
candidate = json.loads((ROOT / "sol_candidate_results.json").read_text())
weights = json.loads((ROOT / "generator_weights_output.json").read_text())["weights"]
layout = json.loads((ROOT / "tensor_layout.json").read_text())
saved = load_file(str(ROOT / "sol_candidate.safetensors"))
original = load_file(str(ROOT / "baseline.safetensors"))
frozen_identical = torch.equal(saved["frozen_embeddings"], original["frozen_embeddings"])
flattened = torch.cat([saved[entry["name"]].reshape(-1) for entry in layout])
assert torch.equal(flattened, torch.tensor(weights, dtype=torch.float64))
assert frozen_identical
per_tensor = []
for entry in layout:
    name = entry["name"]
    per_tensor.append({"name": name, "entries": entry["count"],
                       "changed_entries": int((saved[name] != original[name]).sum())})
heldout = [record for record in candidate["records"] if record["case"]["id"].startswith("heldout")]
summary = {
    "generator": "gpt-6.1-sol via Codex CLI", "generator_calls": 1,
    "generator_tool_calls": json.loads((ROOT / "generator_audit.json").read_text())["tool_event_count"],
    "editable_values": len(weights), "frozen_embedding_values": saved["frozen_embeddings"].numel(),
    "frozen_embedding_values_identical": frozen_identical, "saved_weights_match_cli_numbers_exactly": True,
    "training_or_optimization_steps": 0,
    "baseline": {k: baseline[k] for k in ["cases", "executable_select", "correct_projection", "terminated_with_eos"]},
    "candidate": {k: candidate[k] for k in ["cases", "executable_select", "correct_projection", "terminated_with_eos", "inference_errors"]},
    "heldout": {"cases": len(heldout), "executable_select": sum(x["validation"]["executable_select"] for x in heldout),
                "correct_projection": sum(x["validation"]["correct_projection"] for x in heldout)},
    "error_counts": dict(Counter(x["validation"]["error"] for x in candidate["records"])),
    "changed_weights": per_tensor,
    "raw_output_examples": [{"schema": x["case"], "output": x["raw_output"], "validation": x["validation"]} for x in candidate["records"][:3]],
    "candidate_sha256": hashlib.sha256((ROOT / "sol_candidate.safetensors").read_bytes()).hexdigest(),
}
(ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
