"""A tester for LLM-authored weights. No training, optimization, or weight repair."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import requests

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "tiny-sql-2208"
SEED = 20261102
N_RANDOM = 10000
N_GRID_AXIS = 201
MODEL_FREE = "nvidia/nemotron-3.5-super-vl:free"
CANONICAL_FREE = "nvidia/nemotron-3.5-super-vl-20261015"
TASKS = ("classification", "regression")
LANGFUSE_AUTH = (os.environ.get("LANGFUSE_PUBLIC_KEY", ""), os.environ.get("LANGFUSE_SECRET_KEY", ""))
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3300").rstrip("/")


def langfuse_running():
    if not all(LANGFUSE_AUTH):
        return False
    try:
        return requests.get(LANGFUSE_HOST + "/api/public/health", timeout=2).ok
    except requests.RequestException:
        return False


LANGFUSE_ON = langfuse_running()
SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {task + "_weights": {"type": "array", "items": {"type": "number"},
                                             "minItems": 17, "maxItems": 17} for task in TASKS},
          "required": [task + "_weights" for task in TASKS]}
PROMPT = '''You are the sole numerical weight author for two small neural networks.
You have NO tools, code execution, web, file access, skills, plugins, or other agents.
The independent tester will save your numbers unchanged and run inference. It will not train,
optimize, repair, pad, or otherwise choose weights for you. Reason internally, then output only JSON.

Use the SAME architecture for both tasks, but supply a separate complete weight set for each.
Architecture: 2 real-valued inputs, one hidden layer of 4 ReLU neurons, one linear scalar output.
For j = 0,1,2,3:
  h[j] = max(0, W1[j,0]*x1 + W1[j,1]*x2 + b1[j])
  output = W2[0]*h[0] + W2[1]*h[1] + W2[2]*h[2] + W2[3]*h[3] + b2
There is no other normalization, activation, embedding, or input preprocessing.
All 17 scalar parameters are editable. Evaluation uses float64.

EXACT FLATTENED ORDER FOR EACH 17-NUMBER ARRAY:
Indices 0..7: W1, row-major: W1[0,0],W1[0,1],W1[1,0],W1[1,1],W1[2,0],W1[2,1],W1[3,0],W1[3,1].
Indices 8..11: b1[0],b1[1],b1[2],b1[3].
Indices 12..15: W2[0],W2[1],W2[2],W2[3].
Index 16: b2.

TASK 1: CLASSIFICATION
Both x1 and x2 are in [-1,1] and are nonzero. Predict class 1 if they have OPPOSITE signs,
and class 0 if they have the SAME sign. This is a continuous-input XOR classification task.
The tester interprets output > 0 as class 1, and output <= 0 as class 0.
Examples: (-0.8,0.3)->1; (0.8,-0.3)->1; (0.8,0.3)->0; (-0.8,-0.3)->0.
The scalar output is a decision score, not a probability. Make this work across the stated domain.

TASK 2: REGRESSION
Both x1 and x2 are in [-1,1], including zero. Predict the real number:
  target = abs(x1) + 0.5*abs(x2)
Examples: (0,0)->0; (0.8,-0.4)->1; (-0.2,0.6)->0.5; (-1,-1)->1.5.
The tester compares the unmodified linear output with this target across the stated domain.

The evaluator will use fresh random points and a regular grid; you cannot query it in this turn.
Return exactly an object with keys "classification_weights" and "regression_weights".
Each value must be a complete array of exactly 17 finite JSON numbers in the order above.
No code, formulas, comments, prose, ellipses, or repetition notation. Do not return test predictions.
'''


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def key_of(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def trace(key, model, request, response, start, end, usage):
    """Optional local Langfuse trace. Credentials never enter saved requests."""
    if not LANGFUSE_ON:
        return
    try:
        def attr(k, v):
            return {"key": k, "value": {"stringValue": v if isinstance(v, str) else json.dumps(v)}}
        attrs = [attr("langfuse.observation.type", "generation"), attr("langfuse.observation.model.name", model),
                 attr("langfuse.observation.input", request), attr("langfuse.observation.output", response),
                 attr("langfuse.trace.name", "Direct weights: 17-parameter MLP"),
                 attr("langfuse.trace.metadata.cache_key", key), attr("langfuse.session.id", "tiny-mlp-17")]
        if usage:
            attrs.append(attr("langfuse.observation.usage_details", usage))
        span = {"traceId": hashlib.sha256(("tiny-mlp-17|" + key).encode()).hexdigest()[:32],
                "spanId": hashlib.sha256(("tiny-mlp-17|" + key + "|0").encode()).hexdigest()[:16],
                "name": model, "kind": 1, "startTimeUnixNano": str(int(start.timestamp()*1e9)),
                "endTimeUnixNano": str(int(end.timestamp()*1e9)), "attributes": attrs}
        requests.post(LANGFUSE_HOST + "/api/public/otel/v1/traces", auth=LANGFUSE_AUTH, timeout=10,
                      json={"resourceSpans": [{"resource": {"attributes": [attr("service.name", "tiny-model-experiments")]},
                                               "scopeSpans": [{"scope": {"name": "tiny-mlp-17"}, "spans": [span]}]}]})
    except requests.RequestException:
        pass


def prepare():
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "figures").mkdir(exist_ok=True)
    (ROOT / "prompt.txt").write_text(PROMPT, encoding="utf-8")
    dump(ROOT / "weights_schema.json", SCHEMA)
    manifest = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "architecture": [2, 4, 1], "hidden_activation": "ReLU", "output_activation": "linear",
                "parameters": {"W1": 8, "b1": 4, "W2": 4, "b2": 1}, "total_parameters": 17,
                "input_domain": [-1, 1], "classification": "opposite signs -> class 1; zero coordinates excluded",
                "class_threshold": "output > 0", "regression": "abs(x1) + 0.5*abs(x2)",
                "models": {"astra": "gpt-6-astra", "nemotron": MODEL_FREE},
                "free_canonical_slug": CANONICAL_FREE, "seed": SEED, "random_points": N_RANDOM,
                "grid_axis_size": N_GRID_AXIS, "regression_exact_tolerance": 1e-10,
                "teacher_tools": [], "training_steps": 0, "tester_assigns_candidate_values": False,
                "task_rules_visible_to_editors": True, "evaluation_points_visible_to_editors": False,
                "interpretation_limit": "Analytically specified toy tasks; success is not evidence of learning arbitrary data or SQL."}
    if not (ROOT / "manifest.json").exists():
        dump(ROOT / "manifest.json", manifest)
    rng = np.random.default_rng(SEED)
    random_x = rng.uniform(-1, 1, size=(N_RANDOM, 2))
    axis = np.linspace(-1, 1, N_GRID_AXIS)
    xx, yy = np.meshgrid(axis, axis)
    grid_x = np.column_stack([xx.ravel(), yy.ravel()])
    all_x = np.vstack([random_x, grid_x])
    class_mask = np.all(all_x != 0, axis=1)
    class_x = all_x[class_mask]
    class_y = np.logical_xor(class_x[:, 0] > 0, class_x[:, 1] > 0).astype(np.int64)
    regression_y = np.abs(all_x[:, 0]) + 0.5*np.abs(all_x[:, 1])
    np.savez_compressed(ROOT / "data" / "evaluation_points.npz", classification_x=class_x,
                        classification_y=class_y, regression_x=all_x, regression_y=regression_y,
                        grid_x=grid_x, grid_axis=axis, classification_is_random=np.flatnonzero(class_mask) < N_RANDOM)
    print(json.dumps({"parameters_per_network": 17, "classification_points": len(class_x),
                      "regression_points": len(all_x), "prompt_bytes": len(PROMPT.encode())}), flush=True)


def call_astra(out):
    command = json.loads((OLD / "generator_command.json").read_text())
    command[command.index("-m")+1] = "gpt-6-astra"
    command[command.index("--output-schema")+1] = str(ROOT / "weights_schema.json")
    for i, arg in enumerate(command):
        if arg.startswith("model_reasoning_effort="):
            command[i] = 'model_reasoning_effort="medium"'
    command = command[:-1] + ["--output-last-message", str(out / "cli_last_message.json"), "-"]
    for flag in ("features.shell_tool=false", "features.code_mode=false", "features.code_mode_host=false",
                 "features.multi_agent=false", "features.apps=false", "features.plugins=false",
                 "skills.bundled.enabled=false", "skills.include_instructions=false", 'web_search="disabled"', "mcp_servers={}"):
        assert flag in command
    request = {"model": "gpt-6-astra", "reasoning_effort": "medium", "prompt": PROMPT,
               "schema": SCHEMA, "command": command, "tools_enabled": []}
    key = key_of(request)
    cache = out / "editor_cache.json"
    if cache.exists():
        record = json.loads(cache.read_text())
        assert record["cache_key"] == key
        return record
    priv = Path(r"C:\Users\sandh\.codex\scratch\sql-2208-isolated-cli-home")
    empty = priv / "empty-workspace"
    env = os.environ.copy()
    original_home = Path(env.get("CODEX_HOME", str(Path.home()/".codex")))
    env["CODEX_HOME"] = str(priv)
    env.pop("CODEX_THREAD_ID", None)
    env.pop("CODEX_INTERNAL_ORIGINATOR_OVERRIDE", None)
    config_flags = []
    for i, arg in enumerate(command):
        if arg == "-c":
            config_flags += ["-c", command[i+1]]
    preflight = subprocess.run([command[0], "-C", str(empty)] + config_flags +
                               ["debug", "prompt-input", "PREFLIGHT; NO MODEL CALL."], env=env,
                               capture_output=True, text=True, encoding="utf-8", timeout=60)
    (out / "preflight.json").write_text(preflight.stdout, encoding="utf-8")
    assert preflight.returncode == 0, preflight.stderr
    assert all(text not in preflight.stdout for text in ("<skills_instructions>", "### Available skills", "# AGENTS.md instructions"))
    credential = priv / "auth.json"
    assert not credential.exists(), "Another CLI call owns the isolated home"
    shutil.copyfile(original_home / "auth.json", credential)
    dump(out / "request.json", request)
    events = []
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.monotonic()
    print(json.dumps({"editor": "astra", "status": "calling", "prompt_bytes": len(PROMPT.encode()), "tools": []}), flush=True)
    try:
        with (out / "events.jsonl").open("w", encoding="utf-8") as log, (out / "stderr.txt").open("w", encoding="utf-8") as err:
            process = subprocess.Popen(command, env=env, cwd=empty, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=err, text=True, encoding="utf-8", bufsize=1)
            process.stdin.write(PROMPT)
            process.stdin.close()
            for line in process.stdout:
                log.write(line)
                log.flush()
                event = json.loads(line)
                events.append(event)
                print(json.dumps({"event": event.get("type"), "item_type": event.get("item", {}).get("type"),
                                  "elapsed_seconds": round(time.monotonic()-t0, 2)}), flush=True)
            status = process.wait()
    finally:
        if credential.exists():
            credential.unlink()
    end = dt.datetime.now(dt.timezone.utc)
    answers = [event["item"]["text"] for event in events if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
    usage = next((event["usage"] for event in events if event.get("type") == "turn.completed"), None)
    unexpected = [event for event in events if event.get("item", {}).get("type") not in (None, "error", "reasoning", "agent_message")]
    notices = [event["item"].get("message", "") for event in events if event.get("item", {}).get("type") == "error"]
    unsafe_notices = [message for message in notices if not message.startswith(("Under-development features enabled:", "Code Mode is unavailable because code-mode host is disabled."))]
    record = {"request": request, "cache_key": key, "model": "gpt-6-astra", "events": events,
              "answer": answers[-1] if len(answers) == 1 else "", "usage": usage,
              "exit_code": status, "tool_call_events": len(unexpected), "unsafe_notices": unsafe_notices,
              "started_utc": start.isoformat(), "finished_utc": end.isoformat(), "wall_seconds": time.monotonic()-t0,
              "error": None if status == 0 and len(answers) == 1 else "CLI invocation did not produce one completed answer"}
    dump(cache, record)
    trace(key, "gpt-6-astra", request, record["answer"], start, end, usage)
    return record


def call_nemotron(out, reasoning=True):
    request = {"model": MODEL_FREE, "messages": [{"role": "user", "content": PROMPT}],
               "temperature": 0, "max_tokens": 8192, "reasoning": {"enabled": reasoning, "exclude": True},
               "response_format": {"type": "json_schema", "json_schema": {"name": "mlp_weights", "strict": True, "schema": SCHEMA}},
               "tool_choice": "none", "plugins": [],
               "provider": {"only": ["nvidia"], "allow_fallbacks": False, "max_price": {"prompt": 0, "completion": 0, "request": 0}}}
    key = key_of(request)
    cache = out / "editor_cache.json"
    if cache.exists():
        record = json.loads(cache.read_text())
        assert record["cache_key"] == key
        return record
    base = "https://openrouter.ai/api/v1"
    metadata_response = requests.get(base + "/models", timeout=20)
    metadata_response.raise_for_status()
    metadata = next(item for item in metadata_response.json()["data"] if item["id"] == MODEL_FREE)
    assert metadata["canonical_slug"] == CANONICAL_FREE
    assert all(float(metadata["pricing"][key]) == 0 for key in ("prompt", "completion"))
    dump(out / "model_metadata.json", metadata)
    dump(out / "request.json", request)
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.monotonic()
    print(json.dumps({"editor": "nemotron", "status": "calling", "tools": [], "max_price": 0}), flush=True)
    error = None
    try:
        response = requests.post(base + "/chat/completions", json=request,
                                 headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]}, timeout=(20, 180))
        raw = response.json()
        if not response.ok or raw.get("error"):
            error = raw.get("error", {"http_status": response.status_code})
    except requests.RequestException as exc:
        raw = {}
        error = {"type": type(exc).__name__, "message": str(exc)}
    end = dt.datetime.now(dt.timezone.utc)
    message = raw.get("choices", [{}])[0].get("message", {})
    record = {"request": request, "cache_key": key, "model": MODEL_FREE, "canonical_slug": CANONICAL_FREE,
              "response": raw, "answer": message.get("content") or "", "usage": raw.get("usage"),
              "tool_call_events": len(message.get("tool_calls") or []), "error": error,
              "started_utc": start.isoformat(), "finished_utc": end.isoformat(), "wall_seconds": time.monotonic()-t0}
    dump(cache, record)
    trace(key, MODEL_FREE, request, record["answer"], start, end, record["usage"])
    return record


def validate_and_save(editor, record):
    out = ROOT / "data" / editor
    answer = record["answer"]
    (out / "weights_output.json").write_text(answer, encoding="utf-8")
    error = None
    payload = None
    try:
        assert not record["error"], "Provider or CLI error"
        assert record["tool_call_events"] == 0, "Tool event appeared; no tool result is accepted"
        assert not record.get("unsafe_notices"), "Unrecognized CLI notice"
        if editor.startswith("nemotron"):
            assert record["response"].get("model") == MODEL_FREE, "Unexpected model identity"
            finish = record["response"]["choices"][0]["finish_reason"]
            assert finish == "stop", "Incomplete response; finish_reason=" + str(finish)
        payload = json.loads(answer)
        assert isinstance(payload, dict) and set(payload) == {t + "_weights" for t in TASKS}, "Wrong JSON keys"
        for task in TASKS:
            weights = payload[task + "_weights"]
            assert isinstance(weights, list) and len(weights) == 17, "Each task needs 17 values"
            assert all(type(v) in (float, int) and math.isfinite(v) for v in weights), "Non-finite or non-numeric weight"
    except (AssertionError, ValueError, KeyError) as exc:
        error = str(exc) or type(exc).__name__
    audit = {"model": record["model"], "format_error": error, "tool_call_events": record["tool_call_events"],
             "training_steps": 0, "candidate_values_changed_by_tester": False, "usage": record["usage"],
             "wall_seconds": record["wall_seconds"]}
    if error is None:
        for task in TASKS:
            flat = np.asarray(payload[task + "_weights"], dtype=np.float64)
            path = out / (task + ".npz")
            np.savez(path, W1=flat[:8].reshape(4, 2), b1=flat[8:12], W2=flat[12:16], b2=flat[16:17])
            with np.load(path) as saved:
                restored = np.concatenate([saved["W1"].ravel(), saved["b1"], saved["W2"], saved["b2"]])
            assert np.array_equal(flat, restored), "Saved values changed"
        audit["parameters_per_task"] = 17
        audit["saved_weights_equal_model_response"] = True
    dump(out / "audit.json", audit)
    print(json.dumps({"editor": editor, "audit": audit, "weights": payload if error is None else None}, indent=2), flush=True)


def infer(x, file):
    with np.load(file) as p:
        return np.maximum(0, x @ p["W1"].T + p["b1"]) @ p["W2"] + p["b2"][0]


def evaluate():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    data = np.load(ROOT / "data" / "evaluation_points.npz")
    class_x, class_y = data["classification_x"], data["classification_y"]
    reg_x, reg_y = data["regression_x"], data["regression_y"]
    example_x = np.array([[-0.8,0.3],[0.8,-0.3],[0.8,0.3],[-0.8,-0.3],[0,0],[-0.2,0.6],[0.8,-0.4],[-1,-1]], dtype=np.float64)
    results = []
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    from matplotlib.colors import ListedColormap
    for row, editor in enumerate(("astra", "nemotron")):
        run_name = "nemotron-no-reasoning" if editor == "nemotron" and (ROOT / "data" / "nemotron-no-reasoning" / "audit.json").exists() else editor
        out = ROOT / "data" / run_name
        if not (out / "audit.json").exists():
            for ax in axes[row]: ax.text(0.5,0.5,editor+": no completed response",ha="center",va="center"); ax.set_axis_off()
            continue
        audit = json.loads((out / "audit.json").read_text())
        attempts = [ROOT / "data" / name / "audit.json" for name in (("nemotron", "nemotron-no-reasoning") if editor == "nemotron" else ("astra",))]
        format_failed_calls = sum(json.loads(path.read_text())["format_error"] is not None for path in attempts if path.exists())
        if audit["format_error"] is not None:
            results.append({"editor": editor, "run_name": run_name, "format_error": audit["format_error"], "format_failed_calls": format_failed_calls, "readable": False})
            for ax in axes[row]: ax.text(0.5,0.5,editor+": unreadable response",ha="center",va="center"); ax.set_axis_off()
            continue
        class_score = infer(class_x, out / "classification.npz")
        reg_prediction = infer(reg_x, out / "regression.npz")
        assert np.isfinite(class_score).all() and np.isfinite(reg_prediction).all()
        classification = (class_score > 0).astype(np.int64)
        correct = classification == class_y
        error = reg_prediction - reg_y
        random_mask = data["classification_is_random"]
        samples = []
        example_class_score = infer(example_x, out / "classification.npz")
        example_reg = infer(example_x, out / "regression.npz")
        for i, x in enumerate(example_x):
            valid_class = bool(np.all(x != 0))
            samples.append({"x": x.tolist(), "class_expected": int((x[0] > 0) != (x[1] > 0)) if valid_class else None,
                            "class_predicted": int(example_class_score[i] > 0) if valid_class else None,
                            "class_score": float(example_class_score[i]), "regression_expected": float(abs(x[0])+0.5*abs(x[1])),
                            "regression_predicted": float(example_reg[i])})
        result = {"editor": editor, "run_name": run_name, "model": audit["model"], "readable": True, "format_error": None,
                  "format_failed_calls": format_failed_calls,
                  "classification_n": len(class_y), "classification_correct": int(correct.sum()),
                  "classification_accuracy": float(correct.mean()), "classification_random_accuracy": float(correct[random_mask].mean()),
                  "classification_grid_accuracy": float(correct[~random_mask].mean()),
                  "regression_n": len(reg_y), "regression_mae": float(np.abs(error).mean()),
                  "regression_rmse": float(np.sqrt(np.mean(error**2))), "regression_max_abs_error": float(np.abs(error).max()),
                  "regression_within_1e_10": int((np.abs(error) <= 1e-10).sum()),
                  "examples": samples, "usage": audit["usage"], "wall_seconds": audit["wall_seconds"]}
        results.append(result)
        dump(out / "results.json", result)
        np.savez_compressed(out / "predictions.npz", classification_scores=class_score, classification_predictions=classification,
                            regression_predictions=reg_prediction)
        grid = data["grid_x"]
        grid_pred = (infer(grid, out / "classification.npz") > 0).astype(float)
        grid_pred[np.any(grid == 0, axis=1)] = np.nan
        ax = axes[row, 0]
        ax.imshow(grid_pred.reshape(N_GRID_AXIS,N_GRID_AXIS), origin="lower", extent=[-1,1,-1,1],
                  cmap=ListedColormap(["#f3b45b", "#467ab9"]), vmin=0, vmax=1, interpolation="nearest", aspect="equal")
        ax.set(xlabel="Input x1", ylabel="Input x2", title=f"{editor}: {correct.sum():,}/{len(correct):,} classes correct\nBlue predicts 1; gold predicts 0")
        ax.text(-0.65,0.65,"Expected: 1",ha="center",color="black",bbox={"facecolor":"white","alpha":0.8,"edgecolor":"none"})
        ax.text(0.65,0.65,"Expected: 0",ha="center",color="black",bbox={"facecolor":"white","alpha":0.8,"edgecolor":"none"})
        ax.text(-0.65,-0.65,"Expected: 0",ha="center",color="black",bbox={"facecolor":"white","alpha":0.8,"edgecolor":"none"})
        ax.text(0.65,-0.65,"Expected: 1",ha="center",color="black",bbox={"facecolor":"white","alpha":0.8,"edgecolor":"none"})
        ax = axes[row, 1]
        ax.scatter(reg_y[:N_RANDOM], reg_prediction[:N_RANDOM], s=6, alpha=0.25, color="#467ab9", label="10,000 random points")
        ax.plot([0,1.5],[0,1.5],color="black",linestyle="--",label="Exact answer")
        ax.set(xlabel="Expected regression value", ylabel="MLP output", title=f"{editor}: maximum regression error {np.abs(error).max():.2g}")
        ax.legend(loc="upper left",fontsize=8)
    fig.suptitle("Directly authored weights tested on two 17-parameter MLP tasks", fontsize=14)
    fig.savefig(ROOT / "figures" / "mlp_results.png")
    plt.close(fig)
    dump(ROOT / "results.json", {"architecture": [2,4,1], "parameters_per_task": 17, "results": results})
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "astra", "nemotron", "nemotron-no-reasoning", "evaluate"))
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "evaluate":
        evaluate()
    else:
        out = ROOT / "data" / args.action
        out.mkdir(parents=True, exist_ok=True)
        record = call_astra(out) if args.action == "astra" else call_nemotron(out, reasoning=args.action == "nemotron")
        validate_and_save(args.action, record)
