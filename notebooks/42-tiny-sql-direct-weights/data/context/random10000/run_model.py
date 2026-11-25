"""Initialize an exactly 10,000-parameter GPT-2 and sample ten tokens. No training."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import time
import urllib.request

import requests
import torch
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import WhitespaceSplit
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast


ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "model"
VOCAB_REVISION = "d0736d492489198e4f9d650c7ab4143bc14c1e9e"
VOCAB_URL = (
    "https://raw.githubusercontent.com/first20hours/google-10000-english/"
    f"{VOCAB_REVISION}/google-10000-english.txt"
)
INIT_SEED = 20261102
SAMPLE_SEED = 42
N_STEPS = 10
PROMPT = "the world is"


def trace_fresh_call(cache_key, request, response, start, end):
    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3300").rstrip("/")
    auth = (
        os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
        os.environ.get("LANGFUSE_SECRET_KEY", ""),
    )
    if not all(auth):
        return
    try:
        if not requests.get(f"{host}/api/public/health", timeout=2).ok:
            return

        def attr(key, value):
            return {"key": key, "value": {"stringValue": value if isinstance(value, str) else json.dumps(value)}}

        span = {
            "traceId": hashlib.sha256(f"tiny-10000|{cache_key}".encode()).hexdigest()[:32],
            "spanId": hashlib.sha256(f"tiny-10000|{cache_key}|gen|0".encode()).hexdigest()[:16],
            "name": "10,000-parameter untrained GPT-2: ten generation steps",
            "kind": 1,
            "startTimeUnixNano": str(int(start.timestamp() * 1e9)),
            "endTimeUnixNano": str(int(end.timestamp() * 1e9)),
            "attributes": [
                attr("langfuse.observation.type", "generation"),
                attr("langfuse.observation.model.name", "local/random-gpt2-10000"),
                attr("langfuse.observation.input", request),
                attr("langfuse.observation.output", response),
                attr("langfuse.observation.usage_details", {"input": len(request["prompt_ids"]), "output": N_STEPS}),
                attr("langfuse.observation.cost_details", {"total": 0}),
                attr("langfuse.trace.metadata.cache_key", cache_key),
            ],
        }
        requests.post(
            f"{host}/api/public/otel/v1/traces",
            json={"resourceSpans": [{"resource": {"attributes": [attr("service.name", "local-tiny-model-experiments")]}, "scopeSpans": [{"scope": {"name": "tiny-10000"}, "spans": [span]}]}]},
            auth=auth,
            timeout=10,
        )
    except requests.RequestException:
        pass


ROOT.mkdir(parents=True, exist_ok=True)
source_file = ROOT / "word_frequency_source.txt"
if not source_file.exists():
    with urllib.request.urlopen(VOCAB_URL, timeout=20) as response:
        source_file.write_bytes(response.read())
source_bytes = source_file.read_bytes()
words = list(dict.fromkeys(source_bytes.decode("utf-8").split()))[:1022]
assert len(words) == 1022
tokens = ["<BOS>", "<UNK>"] + words
vocab = {word: i for i, word in enumerate(tokens)}
assert len(vocab) == 1024
(ROOT / "vocabulary.json").write_text(json.dumps(vocab, indent=2), encoding="utf-8")

backend = Tokenizer(WordLevel(vocab=vocab, unk_token="<UNK>"))
backend.pre_tokenizer = WhitespaceSplit()
tokenizer = PreTrainedTokenizerFast(
    tokenizer_object=backend,
    bos_token="<BOS>",
    unk_token="<UNK>",
    model_max_length=64,
)

torch.set_num_threads(1)
torch.manual_seed(INIT_SEED)
config = GPT2Config(
    vocab_size=1024,
    n_positions=64,
    n_ctx=64,
    n_embd=8,
    n_layer=1,
    n_head=2,
    n_inner=56,
    activation_function="gelu_new",
    resid_pdrop=0.0,
    embd_pdrop=0.0,
    attn_pdrop=0.0,
    initializer_range=0.02,
    bos_token_id=0,
    eos_token_id=None,
    tie_word_embeddings=True,
    use_cache=False,
)
model = GPT2LMHeadModel(config).eval()
assert model.lm_head.weight.data_ptr() == model.transformer.wte.weight.data_ptr()
parameter_counts = {name: value.numel() for name, value in model.named_parameters()}
total_parameters = sum(parameter_counts.values())
assert total_parameters == 10000, total_parameters
model.save_pretrained(MODEL_DIR, safe_serialization=True)
tokenizer.save_pretrained(MODEL_DIR)
checkpoint_sha = hashlib.sha256((MODEL_DIR / "model.safetensors").read_bytes()).hexdigest()

prompt_ids = [tokenizer.bos_token_id] + tokenizer.encode(PROMPT, add_special_tokens=False)
assert tokenizer.unk_token_id not in prompt_ids
versions = {name: importlib.metadata.version(name) for name in ("torch", "transformers", "tokenizers", "safetensors")}
request = {
    "model": "local/random-gpt2-10000",
    "checkpoint_sha256": checkpoint_sha,
    "config": config.to_dict(),
    "init_seed": INIT_SEED,
    "sampling_seed": SAMPLE_SEED,
    "prompt": PROMPT,
    "prompt_ids": prompt_ids,
    "max_new_tokens": N_STEPS,
    "temperature": 1.0,
    "top_k": None,
    "top_p": 1.0,
    "device": "cpu",
    "dtype": "float32",
    "vocabulary_source": VOCAB_URL,
    "vocabulary_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "runtime": versions,
    "python": platform.python_version(),
}
cache_key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
cache_dir = ROOT / "cache"
cache_dir.mkdir(exist_ok=True)
cache_file = cache_dir / f"{cache_key}.json"
if cache_file.exists():
    result = json.loads(cache_file.read_text(encoding="utf-8"))
else:
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.perf_counter()
    torch.manual_seed(SAMPLE_SEED)
    current = torch.tensor([prompt_ids], dtype=torch.long)
    generated = []
    trace = []
    with torch.inference_mode():
        for step in range(1, N_STEPS + 1):
            logits = model(current, use_cache=False).logits[0, -1, :]
            probabilities = logits.softmax(dim=-1)
            next_id = int(torch.multinomial(probabilities, num_samples=1).item())
            top_probs, top_ids = probabilities.topk(5)
            generated.append(next_id)
            trace.append({
                "step": step,
                "input_tokens": current.shape[1],
                "token_id": next_id,
                "token": tokens[next_id],
                "sampled_token_probability": float(probabilities[next_id]),
                "entropy_bits": float(-(probabilities * probabilities.log2()).sum()),
                "top_5": [{"token_id": int(i), "token": tokens[int(i)], "probability": float(p)} for i, p in zip(top_ids, top_probs)],
                "continuation_so_far": tokenizer.decode(generated, skip_special_tokens=False),
            })
            current = torch.cat([current, torch.tensor([[next_id]])], dim=1)
    end = dt.datetime.now(dt.timezone.utc)
    result = {
        "request": request,
        "cache_key": cache_key,
        "parameter_count": total_parameters,
        "parameter_breakdown": parameter_counts,
        "training_steps": 0,
        "generated_token_ids": generated,
        "continuation": tokenizer.decode(generated, skip_special_tokens=False),
        "full_output": tokenizer.decode(prompt_ids[1:] + generated, skip_special_tokens=False),
        "trace": trace,
        "generation_seconds": time.perf_counter() - t0,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "model_api_spend_usd": 0,
    }
    cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    trace_fresh_call(cache_key, request, result["continuation"], start, end)

# Check that the exported checkpoint reproduces the original model on the prompt.
reloaded = GPT2LMHeadModel.from_pretrained(MODEL_DIR, local_files_only=True).eval()
with torch.inference_mode():
    inputs = torch.tensor([prompt_ids], dtype=torch.long)
    assert torch.equal(model(inputs).logits, reloaded(inputs).logits)
assert sum(p.numel() for p in reloaded.parameters()) == 10000
assert len(result["trace"]) == len(result["generated_token_ids"]) == 10
result["verification"] = {"checkpoint_reload_logits_identical": True, "generated_steps": 10}
(ROOT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({
    "parameters": total_parameters,
    "vocabulary_size": len(vocab),
    "parameter_breakdown": parameter_counts,
    "prompt": PROMPT,
    "continuation": result["continuation"],
    "steps": [{"step": x["step"], "token": x["token"], "probability_percent": round(100*x["sampled_token_probability"], 4), "entropy_bits": round(x["entropy_bits"], 4)} for x in result["trace"]],
    "generation_seconds": result["generation_seconds"],
    "verification": result["verification"],
    "results_file": str(ROOT / "results.json"),
    "checkpoint": str(MODEL_DIR / "model.safetensors"),
}, indent=2))
