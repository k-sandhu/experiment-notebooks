"""Model scaffold and independent tests. This module does not design candidate weights."""
from __future__ import annotations

import hashlib
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path

import torch
from torch import nn
from transformers import GPT2Config, GPT2Model
from safetensors.torch import load_file, save_file
from trace_calls import trace

ROOT = Path(__file__).resolve().parent
torch.set_num_threads(1)


class FrozenGloveSQL(nn.Module):
    def __init__(self, frozen_embeddings):
        super().__init__()
        self.projection = nn.Parameter(torch.empty(50, 8, dtype=torch.float64))
        self.register_buffer("frozen_embeddings", frozen_embeddings.to(torch.float64))
        config = GPT2Config(vocab_size=len(frozen_embeddings), n_positions=64, n_ctx=64,
                            n_embd=8, n_layer=1, n_head=2, n_inner=56,
                            activation_function="gelu_new", resid_pdrop=0.0,
                            embd_pdrop=0.0, attn_pdrop=0.0, layer_norm_epsilon=1e-5,
                            use_cache=False, bos_token_id=0, eos_token_id=None)
        config._attn_implementation = "eager"
        self.transformer = GPT2Model(config).to(torch.float64)
        # All input embeddings are supplied explicitly. Remove the unused learned table.
        self.transformer.wte = None
        self.eval()
        assert sum(p.numel() for p in self.parameters()) == 2208

    def forward(self, token_ids):
        embedding = self.frozen_embeddings @ self.projection
        x = embedding[token_ids]
        hidden = self.transformer(inputs_embeds=x, use_cache=False).last_hidden_state
        return hidden @ embedding.T


def vocabulary():
    return json.loads((ROOT / "vocabulary.json").read_text(encoding="utf-8"))


def encode(text, vocab):
    pieces = re.findall(r"<[A-Z_]+>|[A-Za-z]+|[0-9]+|\s|[^\w\s]|_", text)
    ids = []
    for piece in pieces:
        if piece in vocab:
            ids.append(vocab[piece])
        else:
            ids.extend(vocab.get(char, vocab["<UNK>"]) for char in piece)
    return ids


def decode(ids, vocab):
    inverse = {i: token for token, i in vocab.items()}
    return "".join(inverse[i] for i in ids)


def schema_prompt(table, columns):
    return f"<BOS><TABLE>{table}<COLUMNS>{','.join(columns)}<SQL>"


def load_model(checkpoint):
    data = load_file(str(checkpoint))
    model = FrozenGloveSQL(data["frozen_embeddings"])
    model.load_state_dict(data, strict=True)
    return model.eval()


def save_candidate(flat_values, destination):
    """Only reshape supplied values; do not pad, repair, optimize or substitute any value."""
    specification = json.loads((ROOT / "tensor_layout.json").read_text())
    if len(flat_values) != 2208:
        raise ValueError(f"Expected 2208 values, received {len(flat_values)}")
    values = torch.tensor(flat_values, dtype=torch.float64)
    if not torch.isfinite(values).all():
        raise ValueError("Non-finite weight")
    baseline = load_file(str(ROOT / "baseline.safetensors"))
    model = FrozenGloveSQL(baseline["frozen_embeddings"])
    offset = 0
    with torch.no_grad():
        for entry in specification:
            target = dict(model.named_parameters())[entry["name"]]
            assert tuple(target.shape) == tuple(entry["shape"])
            count = entry["count"]
            target.copy_(values[offset:offset+count].reshape(target.shape))
            offset += count
    assert offset == 2208
    assert torch.equal(model.frozen_embeddings, baseline["frozen_embeddings"])
    save_file({k: v.contiguous() for k, v in model.state_dict().items()}, str(destination))
    return model


def validate_sql(sql, table, columns):
    result = {"executable_select": False, "correct_projection": False,
              "error": None, "columns_returned": None, "rows_returned": None}
    if not re.match(r"\s*select\b", sql, flags=re.I):
        result["error"] = "Output does not start with SELECT"
        return result
    connection = sqlite3.connect(":memory:")
    quoted = lambda name: '"' + name.replace('"', '""') + '"'
    definitions = ",".join(quoted(c) + " INTEGER" for c in columns)
    connection.execute(f"CREATE TABLE {quoted(table)} ({definitions})")
    expected_rows = [tuple(1000 * row + i + 1 for i in range(len(columns))) for row in range(1, 4)]
    connection.executemany(f"INSERT INTO {quoted(table)} VALUES ({','.join('?' for _ in columns)})", expected_rows)
    reads = set()

    def authorize(action, arg1, arg2, database, trigger):
        if action == sqlite3.SQLITE_READ:
            reads.add(arg1)
            return sqlite3.SQLITE_OK if arg1 == table else sqlite3.SQLITE_DENY
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorize)
    ticks = [0]
    def progress():
        ticks[0] += 1
        return ticks[0] > 100
    connection.set_progress_handler(progress, 1000)
    try:
        cursor = connection.execute(sql)
        rows = cursor.fetchmany(100)
        returned_columns = [x[0] for x in cursor.description]
        result.update(executable_select=True, columns_returned=returned_columns, rows_returned=rows)
        result["correct_projection"] = (returned_columns == columns and rows == expected_rows and table in reads)
    except sqlite3.Error as error:
        result["error"] = str(error)
    finally:
        connection.close()
    return result


def evaluate(checkpoint, label):
    vocab = vocabulary()
    model = load_model(checkpoint)
    cases = json.loads((ROOT / "test_cases.json").read_text())
    checkpoint_hash = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()
    cache_dir = ROOT / "generation_cache"
    cache_dir.mkdir(exist_ok=True)
    records = []
    for case in cases:
        prompt = schema_prompt(case["table"], case["columns"])
        prompt_ids = encode(prompt, vocab)
        request = {"model": "frozen-glove-sql-2208", "checkpoint_sha256": checkpoint_hash,
                   "prompt": prompt, "prompt_ids": prompt_ids, "decoding": "greedy",
                   "max_new_tokens": 32, "context_limit": 64, "dtype": "float64"}
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        path = cache_dir / f"{key}.json"
        if path.exists():
            record = json.loads(path.read_text())
        else:
            started = dt.datetime.now(dt.timezone.utc)
            generated = []
            terminated = False
            inference_error = None
            with torch.inference_mode():
                ids = list(prompt_ids)
                for _ in range(min(32, 64-len(ids))):
                    logits = model(torch.tensor([ids]))[0, -1]
                    if not torch.isfinite(logits).all():
                        inference_error = "Non-finite logits"
                        break
                    next_id = int(logits.argmax())
                    if next_id == vocab["<EOS>"]:
                        terminated = True
                        break
                    generated.append(next_id)
                    ids.append(next_id)
            raw_sql = decode(generated, vocab)
            record = {"request": request, "cache_key": key, "generated_ids": generated,
                      "raw_output": raw_sql, "terminated_with_eos": terminated,
                      "inference_error": inference_error,
                      "validation": validate_sql(raw_sql, case["table"], case["columns"])}
            path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            trace(key, "local/frozen-glove-sql-2208", request, record["raw_output"], started,
                  dt.datetime.now(dt.timezone.utc), {"input": len(prompt_ids), "output": len(generated)})
        records.append({"case": case, **record})
    summary = {"label": label, "cases": len(records),
               "executable_select": sum(x["validation"]["executable_select"] for x in records),
               "correct_projection": sum(x["validation"]["correct_projection"] for x in records),
               "terminated_with_eos": sum(x["terminated_with_eos"] for x in records),
               "inference_errors": sum(x["inference_error"] is not None for x in records),
               "checkpoint_sha256": checkpoint_hash,
               "editable_parameters": sum(p.numel() for p in model.parameters()),
               "frozen_values": model.frozen_embeddings.numel(),
               "records": records}
    (ROOT / f"{label}_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2), flush=True)
    for example in records[:5]:
        print(json.dumps({"schema": example["case"], "output": example["raw_output"], "validation": example["validation"]}), flush=True)
    return summary


if __name__ == "__main__":
    import sys
    evaluate(Path(sys.argv[1]), sys.argv[2])
