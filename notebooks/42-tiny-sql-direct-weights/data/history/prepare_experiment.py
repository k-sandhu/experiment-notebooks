"""Prepare immutable embeddings, a random baseline, a specification and held-out tests."""
import gzip
import hashlib
import json
import random
import string

import torch
from safetensors.torch import load_file, save_file
from model_and_test import ROOT, FrozenGloveSQL, schema_prompt, encode

old_root = ROOT.parent / "tiny-10000"
old_vocab = json.loads((old_root / "vocabulary.json").read_text())
vocab = dict(old_vocab)
additions = ["<EOS>", "<PAD>", "<TABLE>", "<COLUMNS>", "<SQL>"]
additions += list(string.ascii_letters + string.digits + string.punctuation + " \n\t")
additions += "select from where count distinct as and or not null is order by asc desc limit join on group having sum avg min max".split()
for token in additions:
    if token not in vocab:
        vocab[token] = len(vocab)
assert all(vocab[k] == v for k, v in old_vocab.items())
(ROOT / "vocabulary.json").write_text(json.dumps(vocab, indent=2), encoding="utf-8")

needed = {token.lower() for token in vocab if not token.startswith("<") and not token.isspace()}
vectors = {}
with gzip.open(ROOT / "glove-wiki-gigaword-50.gz", "rt", encoding="utf-8") as source:
    for line in source:
        fields = line.rstrip().split(" ")
        if len(fields) == 51 and fields[0] in needed:
            vectors[fields[0]] = [float(x) for x in fields[1:]]
missing = sorted(needed-set(vectors))
generator = torch.Generator().manual_seed(853120)
frozen = torch.empty(len(vocab), 50, dtype=torch.float64)
rows = []
fallback_tokens = []
for token, index in vocab.items():
    if token.lower() in vectors:
        frozen[index] = torch.tensor(vectors[token.lower()], dtype=torch.float64)
        origin = "glove.6B.50d"
    else:
        frozen[index] = torch.randn(50, generator=generator, dtype=torch.float64) * 0.1
        origin = "fixed_random_special_or_missing"
        fallback_tokens.append(token)
    rows.append({"id": index, "token": token, "vector": frozen[index].tolist(), "origin": origin})
save_file({"embeddings": frozen.contiguous()}, str(ROOT / "frozen_embeddings.safetensors"))
(ROOT / "embedding_rows.json").write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")

torch.manual_seed(20261102)
model = FrozenGloveSQL(frozen)
original = load_file(str(old_root / "model" / "model.safetensors"))
with torch.no_grad():
    # This is only the untrained baseline, never the submitted candidate.
    model.projection.normal_(mean=0.0, std=0.02)
    for name, parameter in model.transformer.named_parameters():
        parameter.copy_(original["transformer." + name].to(torch.float64))
save_file({k: v.contiguous() for k, v in model.state_dict().items()}, str(ROOT / "baseline.safetensors"))
layout = []
offset = 0
for name, parameter in model.named_parameters():
    layout.append({"name": name, "shape": list(parameter.shape), "count": parameter.numel(), "offset": offset})
    offset += parameter.numel()
assert offset == 2208
(ROOT / "tensor_layout.json").write_text(json.dumps(layout, indent=2))

rng = random.Random(220820261102)
name_pool = [token for token in old_vocab if token.isalpha() and token.islower() and 3 <= len(token) <= 10]
cases = [
    {"id": "example-1", "table": "data", "columns": ["name"]},
    {"id": "example-2", "table": "users", "columns": ["name", "date"]},
    {"id": "example-3", "table": "products", "columns": ["name", "price"]},
]
for i in range(120):
    table, *columns = rng.sample(name_pool, 1 + 1 + i % 3)
    cases.append({"id": f"heldout-{i:03d}", "table": table, "columns": columns})
for case in cases:
    assert max(encode(schema_prompt(case["table"], case["columns"]), vocab)) < len(vocab)
    assert vocab["<UNK>"] not in encode(schema_prompt(case["table"], case["columns"]), vocab)
(ROOT / "test_cases.json").write_text(json.dumps(cases, indent=2))

spec = """You are the sole numerical weight generator in a weight-space-programming experiment.
You have NO tools: no shell, Python, calculator, web, file operations, skills, plugins, MCP or other agents.
Everything you can use is in this prompt. Do not ask for tools. Do not emit code, recipes, formulas,
explanations, ellipses, repetition notation or suggested patches. Return only the requested JSON of numbers.
The independent tester will load those numbers without repairing, optimizing, training or choosing them.

TASK
Set all 2,208 editable scalar values of a tiny autoregressive transformer so that, given a table name
and one to three column names, it generates a legal SQLite SELECT of those columns in their given order
from that table. It should work for held-out combinations and names drawn from the supplied vocabulary.
Properly double-quote identifiers so reserved words are valid names. No WHERE condition is requested.
The actual generation is plain argmax over the entire vocabulary, with no grammar mask, SQL template,
retrieval, copying code, logits processor, external executor or repair in the generation path.
The tokenizer's decoder simply concatenates the emitted token strings. Therefore literal space tokens
must be generated wherever SQL requires spaces. Stop by generating <EOS>. The tester allows 32 new
tokens and a total context of 64. It scores both executable SQL and correct returned columns and rows.

INPUT FORMAT
The exact prompt is <BOS><TABLE>table_name<COLUMNS>column_1,column_2,column_3<SQL>.
There is no whitespace in the input. Use only as many columns as are supplied.
Markers are single tokens. A known whole word is one token; otherwise identifiers split into characters.
Examples (examples are task descriptions, not permitted external training):
<BOS><TABLE>data<COLUMNS>name<SQL> -> select "name" from "data";<EOS>
<BOS><TABLE>users<COLUMNS>name,date<SQL> -> select "name","date" from "users";<EOS>
<BOS><TABLE>products<COLUMNS>name,price<SQL> -> select "name","price" from "products";<EOS>
Other legal capitalization and whitespace are accepted if the output executes and returns the specified
columns in order. The real table's contents are unknown to you; copying constant result values cannot pass.

ARCHITECTURE (this is the entire model; no other trainable components)
All computation is deterministic float64, CPU, inference mode. The frozen matrix E is V x 50 and is
listed completely below, together with token strings and IDs. It cannot be changed. Original GloVe
values are unmodified. Special and missing-token vectors were randomly fixed before this request.
Your projection P is 50 x 8. Shared effective input/output embeddings are F = E @ P. No embedding
normalization or vocabulary bias is applied. On token IDs t[0..n-1], initialize X[i] = F[t[i]] + Wpos[i].
Wpos has shape [64,8]. There is one GPT-2 pre-layer-normalized block of width 8, two causal attention
heads of width 4 each, followed by one feed-forward layer of width 56 and a final LayerNorm.
LayerNorm(x,g,b) = g*(x-mean(x))/sqrt(mean((x-mean(x))^2)+1e-5)+b, over 8 dimensions.
A = LayerNorm(X, ln_1.weight, ln_1.bias).
QKV = A @ attn.c_attn.weight + attn.c_attn.bias, shape [n,24]. Split last axis into Q, K, V of width 8;
each splits into two consecutive 4-dimensional heads. In each head, C = softmax(Q @ K.T / 2 + causal_mask) @ V,
where future positions have mask -infinity and the diagonal is allowed. Concatenate the two heads to width 8.
X = X + C @ attn.c_proj.weight + attn.c_proj.bias.
B = LayerNorm(X, ln_2.weight, ln_2.bias).
Z = B @ mlp.c_fc.weight + mlp.c_fc.bias, shape [n,56].
GELU_new(z) = 0.5*z*(1+tanh(sqrt(2/pi)*(z+0.044715*z^3))).
X = X + GELU_new(Z) @ mlp.c_proj.weight + mlp.c_proj.bias.
H = LayerNorm(X, ln_f.weight, ln_f.bias).
Vocabulary logits = H @ F.T. Take argmax of the last position's logits, append that token and repeat.
There are no attention dropout, residual dropout, rotary embeddings, extra recurrence, or hidden tools.
All linear matrices use the [input_dimension, output_dimension] convention shown above.

OUTPUT CONTRACT
Return exactly {"weights":[2208 finite JSON numbers]}. The list is the concatenation of every tensor
in the following layout, in listed order, row-major (last index changes fastest). Every scalar must be
explicit. Do not omit zero entries or rely on default initialization. All 2,208 entries replace the
random baseline; these are the complete submitted editable weights, not deltas.
"""
spec += "\nTENSOR LAYOUT\n" + json.dumps(layout, separators=(",", ":"))
spec += "\nFROZEN EMBEDDING MATRIX AND VOCABULARY (complete)\n" + json.dumps(rows, separators=(",", ":"))
(ROOT / "generator_prompt.txt").write_text(spec, encoding="utf-8")
schema = {"type": "object", "properties": {"weights": {"type": "array", "items": {"type": "number"}, "minItems": 2208, "maxItems": 2208}}, "required": ["weights"], "additionalProperties": False}
(ROOT / "weights_schema.json").write_text(json.dumps(schema, indent=2))
manifest = {"original_vocabulary_preserved": True, "original_vocabulary_size": len(old_vocab),
            "expanded_vocabulary_size": len(vocab), "editable_parameters": 2208,
            "frozen_values": frozen.numel(), "glove_missing_lookup_tokens": missing,
            "fixed_fallback_tokens": fallback_tokens,
            "glove_source": "https://github.com/piskvorky/gensim-data/releases/download/glove-wiki-gigaword-50/glove-wiki-gigaword-50.gz",
            "glove_archive_sha256": hashlib.sha256((ROOT / "glove-wiki-gigaword-50.gz").read_bytes()).hexdigest(),
            "prompt_bytes": len(spec.encode()), "baseline_and_candidate_training_steps": 0,
            "test_cases": len(cases), "public_examples": 3, "heldout_cases": 120,
            "candidate_weights_author": "gpt-6.1-sol via tool-disabled Codex CLI only"}
(ROOT / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
