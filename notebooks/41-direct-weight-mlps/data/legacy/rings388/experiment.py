"""Construct and test a deeper MLP whose candidate weights come only from a tool-free LLM."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from trace_calls import trace

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "tiny-sql-2208"
PRIVATE = Path(r"C:\Users\sandh\.codex\scratch\mlp-388-isolated-cli-home")
MODEL = "gpt-6-astra"
EFFORT = "xhigh"
SEED = 20261103
N_PER_CLASS = 5000
GRID_SIZE = 401
RADII = np.array([0.25, 0.5, 0.75], dtype=np.float64)
SHAPES = {"W1": [16,2], "b1": [16], "W2": [16,16], "b2": [16], "W3": [4,16], "b3": [4]}
assert sum(int(np.prod(shape)) for shape in SHAPES.values()) == 388


def array_schema(shape):
    if not shape:
        return {"type": "number"}
    return {"type": "array", "minItems": shape[0], "maxItems": shape[0], "items": array_schema(shape[1:])}


SCHEMA = {"type": "object", "additionalProperties": False, "required": list(SHAPES),
          "properties": {name: array_schema(shape) for name, shape in SHAPES.items()}}
PROMPT = '''You are the sole numerical weight author for a small deep neural-network classifier.
You have NO tools: no Python, code execution, calculators, shell, web, file access, skills,
plugins, MCP, or other agents. Everything you need is in this prompt. Reason internally.
The independent tester will load your complete numeric weights unchanged. It will not train,
optimize, repair, fill, truncate, or otherwise choose any candidate value for you.

TASK: FOUR CONCENTRIC RINGS
Input is a raw pair of real numbers (x1,x2) in the closed unit disk: x1^2+x2^2 <= 1.
Let r = sqrt(x1^2+x2^2). The desired class is:
  class 0: 0 <= r < 0.25
  class 1: 0.25 <= r < 0.50
  class 2: 0.50 <= r < 0.75
  class 3: 0.75 <= r <= 1.00
Examples: (0,0)->0; (0.1,-0.1)->0; (0.3,0)->1; (0,0.55)->2;
(-0.6,-0.6)->3; (0.25,0)->1; (0,-0.5)->2; (-0.75,0)->3.
The target rule is supplied so you can program weights directly. There is no training set to fit.
The tester will evaluate unseen points sampled uniformly by area within each ring, with equal
counts per class, plus a dense grid over the disk. A constant-class classifier scores 25% on the
balanced sample. Maximize classification accuracy across the disk. Approximation is acceptable.

EXACT ARCHITECTURE: 2 -> 16 -> 16 -> 4
All computation uses float64. There are 388 independent editable weights and biases.
Hidden layers use ReLU(z) = max(0,z), componentwise. The output layer is linear.
For a single two-element column vector x:
  h1 = ReLU(W1 @ x + b1)
  h2 = ReLU(W2 @ h1 + b2)
  scores = W3 @ h2 + b3
  prediction = index of the largest of the four scores, from 0 to 3.
Ties select the lowest index. There is no softmax, normalization, clipping, radius feature,
input transform, embedding, hand-written classifier, or any other operation at inference.
Only your three affine layers and two ReLU operations compute the four scores from raw x1,x2.

RETURN THESE SIX TENSORS IN JSON, AS EXPLICIT NUMERIC ARRAYS:
W1: 16 rows, each containing 2 numbers (32 values).
b1: 16 numbers.
W2: 16 rows, each containing 16 numbers (256 values).
b2: 16 numbers.
W3: 4 rows, each containing 16 numbers (64 values).
b3: 4 numbers.
Rows correspond to output neurons and columns to input neurons. Every value is editable,
including values you choose to make zero. Return all 388 values even if some neurons are unused.

Return ONLY a JSON object with keys W1,b1,W2,b2,W3,b3 and the exact shapes above.
Use finite JSON numbers only. No prose, code, formulas, comments, ellipses, symbolic constants,
repetition notation, omitted rows, or predictions. No intermediate evaluation is available.
'''


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def labels(x):
    return np.searchsorted(RADII, np.hypot(x[:,0], x[:,1]), side="right")


def prepare():
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "figures").mkdir(exist_ok=True)
    (ROOT / "prompt.txt").write_text(PROMPT, encoding="utf-8")
    dump(ROOT / "weights_schema.json", SCHEMA)
    manifest = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "model": MODEL, "reasoning_effort": EFFORT,
                "architecture": [2,16,16,4], "shapes": SHAPES, "total_parameters": 388,
                "previous_mlp_parameters": 17, "hidden_activation": "ReLU", "output": "four linear scores; argmax",
                "domain": "closed unit disk", "radius_boundaries": RADII.tolist(), "boundary_rule": "outer class at exact boundary",
                "seed": SEED, "n_per_class": N_PER_CLASS, "n_balanced": 4*N_PER_CLASS, "grid_axis_size": GRID_SIZE,
                "primary_metric": "accuracy on balanced random sample", "baseline_accuracy": 0.25,
                "secondary_metrics": ["accuracy per class", "grid accuracy", "accuracy at least 0.02 from a class boundary"],
                "teacher_has_tools": False, "teacher_sees_test_points": False, "teacher_sees_target_rule": True,
                "training_steps": 0, "tester_generates_candidate_weights": False,
                "preserve_cli_history": True, "automatic_cancellation_on_task_switch": False,
                "limitation": "Finite ReLU networks have piecewise linear boundaries, so circles require approximation."}
    if not (ROOT / "manifest.json").exists():
        dump(ROOT / "manifest.json", manifest)
    rng = np.random.default_rng(SEED)
    bounds = np.array([0,0.25,0.5,0.75,1.0])
    parts = []
    for k in range(4):
        r = np.sqrt(rng.uniform(bounds[k]**2, bounds[k+1]**2, N_PER_CLASS))
        angle = rng.uniform(-np.pi,np.pi,N_PER_CLASS)
        parts.append(np.column_stack([r*np.cos(angle),r*np.sin(angle)]))
    x = np.vstack(parts)
    x = x[rng.permutation(len(x))]
    y = labels(x)
    assert np.bincount(y,minlength=4).tolist() == [N_PER_CLASS]*4
    axis = np.linspace(-1,1,GRID_SIZE)
    xx, yy = np.meshgrid(axis,axis)
    whole_grid = np.column_stack([xx.ravel(),yy.ravel()])
    disk = (whole_grid**2).sum(axis=1) <= 1
    grid_x = whole_grid[disk]
    np.savez_compressed(ROOT / "data" / "test_points.npz", x=x, y=y, grid_x=grid_x,
                        grid_y=labels(grid_x), whole_grid=whole_grid, disk_mask=disk, axis=axis)
    print(json.dumps({"parameters":388,"balanced_points":len(x),"grid_points":len(grid_x),"prompt_bytes":len(PROMPT.encode())}),flush=True)


def generate():
    out = ROOT / "data" / "astra"
    out.mkdir(parents=True,exist_ok=True)
    command = json.loads((OLD / "generator_command.json").read_text(encoding="utf-8"))
    command.remove("--ephemeral")
    command[command.index("-m")+1] = MODEL
    command[command.index("-C")+1] = str(PRIVATE / "empty-workspace")
    command[command.index("--output-schema")+1] = str(ROOT / "weights_schema.json")
    for i,arg in enumerate(command):
        if arg.startswith("model_reasoning_effort="):
            command[i] = 'model_reasoning_effort=' + json.dumps(EFFORT)
        if arg.startswith("model_instructions_file="):
            command[i] = 'model_instructions_file=' + json.dumps(str(PRIVATE / "neutral.txt"))
    command = command[:-1] + ["--output-last-message",str(out / "cli_last_message.json"),"-"]
    for setting in ['web_search="disabled"',"mcp_servers={}","features.shell_tool=false","features.code_mode=false",
                    "features.code_mode_host=false","features.multi_agent=false","features.apps=false","features.plugins=false",
                    "skills.bundled.enabled=false","skills.include_instructions=false"]:
        assert setting in command
    request = {"model":MODEL,"reasoning_effort":EFFORT,"prompt":PROMPT,"schema":SCHEMA,"command":command,
               "tools_enabled":[],"cli_session_history_preserved":True}
    cache_key = hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
    cache = out / "editor_cache.json"
    if cache.exists():
        record = json.loads(cache.read_text(encoding="utf-8"))
        assert record["cache_key"] == cache_key
        validate(record)
        return
    (PRIVATE / "empty-workspace").mkdir(parents=True,exist_ok=True)
    (PRIVATE / "neutral.txt").write_text("You are a numerical weight generator. Return only the data requested by the user.\n",encoding="utf-8")
    env = os.environ.copy()
    original_home = Path(env.get("CODEX_HOME",str(Path.home()/".codex")))
    env["CODEX_HOME"] = str(PRIVATE)
    env.pop("CODEX_THREAD_ID",None)
    env.pop("CODEX_INTERNAL_ORIGINATOR_OVERRIDE",None)
    configs = []
    for i,arg in enumerate(command):
        if arg == "-c": configs += ["-c",command[i+1]]
    preflight = subprocess.run([command[0],"-C",str(PRIVATE / "empty-workspace")] + configs +
                              ["debug","prompt-input","PREFLIGHT; NO MODEL CALL."],env=env,capture_output=True,text=True,encoding="utf-8",timeout=60)
    (out / "preflight.json").write_text(preflight.stdout,encoding="utf-8")
    assert preflight.returncode == 0,preflight.stderr
    assert all(s not in preflight.stdout for s in ("<skills_instructions>","### Available skills","# AGENTS.md instructions"))
    credential = PRIVATE / "auth.json"
    assert not credential.exists(),"Another call owns this private home"
    shutil.copyfile(original_home / "auth.json",credential)
    dump(out / "request.json",request)
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.monotonic()
    events = []
    status = {"status":"running","model":MODEL,"effort":EFFORT,"started_utc":start.isoformat(),"cli_session_history_preserved":True}
    print(json.dumps(status),flush=True)
    try:
        with (out / "events.jsonl").open("w",encoding="utf-8") as log,(out / "stderr.txt").open("w",encoding="utf-8") as err:
            process = subprocess.Popen(command,env=env,cwd=PRIVATE / "empty-workspace",stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                       stderr=err,text=True,encoding="utf-8",bufsize=1)
            status["pid"] = process.pid
            dump(out / "process_status.json",status)
            process.stdin.write(PROMPT)
            process.stdin.close()
            for line in process.stdout:
                log.write(line); log.flush()
                event = json.loads(line)
                events.append(event)
                if event.get("type") == "thread.started":
                    status["thread_id"] = event["thread_id"]
                    dump(out / "process_status.json",status)
                print(json.dumps({"event":event.get("type"),"item_type":event.get("item",{}).get("type"),
                                  "elapsed_seconds":round(time.monotonic()-t0,2)}),flush=True)
            exit_code = process.wait()
    finally:
        if credential.is_file(): credential.unlink()
    end = dt.datetime.now(dt.timezone.utc)
    answers = [e["item"]["text"] for e in events if e.get("type")=="item.completed" and e.get("item",{}).get("type")=="agent_message"]
    usage = next((e["usage"] for e in events if e.get("type")=="turn.completed"),None)
    record = {"request":request,"cache_key":cache_key,"events":events,"answer":answers[-1] if len(answers)==1 else "",
              "usage":usage,"exit_code":exit_code,"started_utc":start.isoformat(),"finished_utc":end.isoformat(),"wall_seconds":time.monotonic()-t0}
    dump(cache,record)
    dump(out / "process_status.json",dict(status,status="exited",exit_code=exit_code,finished_utc=end.isoformat()))
    trace(cache_key,MODEL,request,record["answer"],start,end,usage)
    validate(record)


def validate(record):
    out = ROOT / "data" / "astra"
    (out / "weights_output.json").write_text(record["answer"],encoding="utf-8")
    error = None
    unexpected = [e for e in record["events"] if e.get("item",{}).get("type") not in (None,"reasoning","agent_message","error")]
    try:
        assert record["exit_code"] == 0,"CLI call failed"
        assert not unexpected,"Disallowed tool/item event"
        notices = [e["item"].get("message","") for e in record["events"] if e.get("item",{}).get("type")=="error"]
        assert all(n.startswith(("Under-development features enabled:","Code Mode is unavailable because code-mode host is disabled.")) for n in notices),"Unexpected CLI notice"
        payload = json.loads(record["answer"])
        assert isinstance(payload,dict) and set(payload)==set(SHAPES),"Wrong tensor keys"
        tensors = {}
        for name,shape in SHAPES.items():
            value = np.asarray(payload[name])
            assert list(value.shape)==shape,"Wrong shape: " + name
            assert value.dtype.kind in "ifu" and np.isfinite(value).all(),"Non-numeric or non-finite weight"
            tensors[name] = value.astype(np.float64)
        assert sum(v.size for v in tensors.values())==388
        np.savez(out / "candidate.npz",**tensors)
        with np.load(out / "candidate.npz") as saved:
            assert all(np.array_equal(saved[name],tensors[name]) for name in SHAPES)
    except (AssertionError,ValueError,TypeError) as exc:
        error = str(exc) or type(exc).__name__
    audit = {"model":MODEL,"reasoning_effort":EFFORT,"format_error":error,"tool_call_events":len(unexpected),
             "training_steps":0,"tester_changed_candidate_weights":False,"parameters":388,
             "saved_values_equal_response":error is None,"usage":record["usage"],"wall_seconds":record["wall_seconds"]}
    dump(out / "audit.json",audit)
    print(json.dumps(audit,indent=2),flush=True)
    if error is None: evaluate()


def infer(x,weights):
    h1 = np.maximum(0,x @ weights["W1"].T + weights["b1"])
    h2 = np.maximum(0,h1 @ weights["W2"].T + weights["b2"])
    scores = h2 @ weights["W3"].T + weights["b3"]
    assert np.isfinite(scores).all()
    return scores.argmax(axis=1)


def evaluate(out=None, model=MODEL, effort=EFFORT, display_name="Astra"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    plt.rcParams.update({"figure.dpi":130,"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    default_run = out is None
    out = ROOT / "data" / "astra" if default_run else Path(out)
    data = np.load(ROOT / "data" / "test_points.npz")
    weights = np.load(out / "candidate.npz")
    prediction = infer(data["x"],weights)
    grid_prediction = infer(data["grid_x"],weights)
    y = data["y"]
    correct = prediction == y
    distance = np.min(np.abs(np.hypot(data["x"][:,0],data["x"][:,1])[:,None] - RADII[None,:]),axis=1)
    away = distance >= 0.02
    confusion = np.zeros((4,4),dtype=int)
    np.add.at(confusion,(y,prediction),1)
    examples = []
    for index in list(np.flatnonzero(~correct)[:5]) + list(np.flatnonzero(correct)[:3]):
        examples.append({"test_id":"balanced-"+str(index).zfill(5),"x":data["x"][index].tolist(),"expected":int(y[index]),
                         "predicted":int(prediction[index]),"distance_to_nearest_boundary":float(distance[index])})
    audit = json.loads((out / "audit.json").read_text(encoding="utf-8"))
    results = {"model":model,"effort":effort,"parameters":388,"balanced_n":len(y),"correct":int(correct.sum()),
               "balanced_accuracy":float(correct.mean()),"constant_class_baseline":0.25,
               "per_class":[{"class":k,"n":int((y==k).sum()),"accuracy":float(correct[y==k].mean())} for k in range(4)],
               "grid_n":len(grid_prediction),"grid_accuracy":float((grid_prediction==data["grid_y"]).mean()),
               "away_from_boundary_n":int(away.sum()),"away_from_boundary_accuracy":float(correct[away].mean()),
               "confusion_rows_true_columns_predicted":confusion.tolist(),"examples":examples,
               "usage":audit["usage"],"editor_wall_seconds":audit["wall_seconds"],"training_steps":0}
    dump(out / "results.json",results)
    if default_run:
        dump(ROOT / "results.json",results)
    np.savez_compressed(out / "predictions.npz",prediction=prediction,grid_prediction=grid_prediction)
    colors = ListedColormap(["#3977b5","#63ac8e","#f4bd55","#b486bd"])
    fig,axs = plt.subplots(2,2,figsize=(10,9),constrained_layout=True)
    def panel(ax,values,title,cmap=colors):
        z = np.full(GRID_SIZE*GRID_SIZE,np.nan)
        z[data["disk_mask"]] = values
        ax.imshow(z.reshape(GRID_SIZE,GRID_SIZE),origin="lower",extent=[-1,1,-1,1],cmap=cmap,interpolation="nearest",vmin=0,vmax=3 if cmap is colors else 1)
        for radius in RADII:
            ax.add_patch(plt.Circle((0,0),radius,fill=False,color="black",linestyle="--",linewidth=0.7))
        ax.set(xlabel="Input x1",ylabel="Input x2",title=title,aspect="equal")
    panel(axs[0,0],data["grid_y"],"Target: classes 0, 1, 2, 3 from center outward")
    panel(axs[0,1],grid_prediction,display_name + "'s MLP predictions; dashed lines are target boundaries")
    panel(axs[1,0],(grid_prediction!=data["grid_y"]).astype(float),"Grid errors: dark areas are incorrect",ListedColormap(["#eeeeee","#a12b37"]))
    ax = axs[1,1]
    ax.imshow(confusion,cmap="Blues",vmin=0,vmax=N_PER_CLASS)
    for i in range(4):
        for j in range(4):
            ax.text(j,i,str(confusion[i,j]),ha="center",va="center",color="white" if confusion[i,j]>N_PER_CLASS/2 else "black")
    ax.set(xticks=range(4),yticks=range(4),xlabel="Predicted class",ylabel="Expected class",title="Balanced test: 5,000 points per class")
    fig.suptitle(f"388 directly authored weights: {correct.mean():.1%} balanced accuracy (constant baseline 25%)",fontsize=14)
    fig.savefig(ROOT / "figures" / ("rings_results.png" if default_run else out.name + "_rings_results.png"))
    plt.close(fig)
    print(json.dumps(results,indent=2),flush=True)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action",choices=("prepare","generate","evaluate"))
    action = parser.parse_args().action
    {"prepare":prepare,"generate":generate,"evaluate":evaluate}[action]()
