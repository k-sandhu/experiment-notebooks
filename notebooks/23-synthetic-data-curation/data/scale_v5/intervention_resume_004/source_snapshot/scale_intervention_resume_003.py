"""Second explicit collector-loss overlay. No recorded request is resubmitted."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import threading

# The archived predecessor is loaded by its amendment binding, not imported from
# the repository. This also supports embedding the companion in a notebook cell.
VERSION = "23-scale-intervention-interruption-v2"


def predecessor(root, amendment):
    data = Path(root).resolve() / "data/scale_v5"
    path = Path(amendment["predecessor"]["path"])
    if path.as_posix() != "intervention_resume/amendment_002.json":
        raise ValueError("Exact predecessor amendment required")
    import hashlib
    raw = (data/path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != amendment["predecessor"]["sha256"]:
        raise ValueError("Predecessor amendment changed")
    info = json.loads(raw)
    source = data/info["implementation"]["path"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != info["implementation"]["sha256"]:
        raise ValueError("Predecessor implementation changed")
    source_bytes = source.read_bytes()
    embedded = globals().get("SCALE_INTERVENTION_PREDECESSOR_SOURCE")
    if embedded is not None:
        if not isinstance(embedded, str) or hashlib.sha256(embedded.encode("utf-8")).hexdigest() != info["implementation"]["sha256"]:
            raise ValueError("Embedded predecessor differs from bound implementation")
        source_bytes = embedded.encode("utf-8")
    old = {"__name__": "archived_intervention_resume_002"}
    exec(compile(source_bytes, str(source), "exec"), old)
    return old


def scale_intervention_resume_003_verify(root, amendment_path):
    root = Path(root).resolve(); data = root/"data/scale_v5"; main = data/"main"
    amendment_path = Path(amendment_path).resolve()
    if not amendment_path.is_relative_to(data): raise ValueError("Amendment outside study")
    amendment = json.loads(amendment_path.read_bytes())
    if amendment.get("protocol") != "23-scale-v5" or amendment.get("amendment_version") != VERSION:
        raise ValueError("Wrong amendment version")
    old = predecessor(root, amendment)
    first = old["scale_intervention_resume_verify"](root, data/amendment["predecessor"]["path"])
    bound, read, sha, hash_ = (old[n] for n in ("sir_bound", "sir_read", "sir_sha", "sir_hash"))
    declared = old["sir_time"](amendment["declared_at_utc"])
    lost = old["sir_time"](amendment["loss_observed_at_utc"])
    if not lost < declared <= datetime.now(timezone.utc): raise ValueError("Invalid declaration time")
    required = {"source_freeze.json", "intervention_start_declaration.json", "main/dispatch.json", "main/selection.json"}
    protected = amendment["protected_files"]
    if len({x["path"] for x in protected}) != len(protected) or not required <= {x["path"] for x in protected}:
        raise ValueError("Missing protected source/selection/dispatch bindings")
    for item in protected: bound(data,item)
    for name in ("implementation", "analysis_plan", "process_proof", "cache_inventory"): bound(data,amendment[name])
    for item in amendment.get("tests",[]): bound(data,item)
    proof = read(bound(data,amendment["process_proof"]))
    if (proof.get("owned_workers") != 0 or proof.get("collector_session_available") is not False
            or proof.get("inaccessible_owned_candidates") != 0
            or not lost <= old["sir_time"](proof["checked_at_utc"]) < declared):
        raise ValueError("Affirmative process absence proof required")
    inventory = read(bound(data,amendment["cache_inventory"]))
    prefix = inventory.get("requests",{})
    dispatch = read(main/"dispatch.json")["jobs"]
    original = set(read(main/"original_manifest.json")["request_keys"])
    if (inventory.get("protocol") != "23-scale-v5" or inventory.get("count") != 1540 or len(prefix) != 1540
            or len(dispatch) != 1200 or len({x["request_key"] for x in dispatch}) != 1200
            or set(prefix) != original | {x["request_key"] for x in dispatch[:420]}):
        raise ValueError("Exact 1540-cache / 420-slot prefix required")
    if any(prefix.get(k) != v for k,v in first["inventory"].items()): raise ValueError("Old 1240-prefix changed")
    pending = {}; terminals=0
    for key,digest in prefix.items():
        if sha(main/"cache"/(key+".json.gz")) != digest: raise ValueError("Recorded cache changed; no reissue")
        cache=read(main/"cache"/(key+".json.gz"))
        if cache["key"] != key or hash_(cache["request"]) != key or len(cache["attempts"]) != 1:
            raise ValueError("Request identity or attempt count changed")
        attempt=cache["attempts"][0]
        if attempt.get("pending") is True:
            if set(attempt) != {"pending","started_at","timeout_s"} or attempt["timeout_s"] != 900 or old["sir_time"](attempt["started_at"]) >= lost:
                raise ValueError("Invalid pending telemetry")
            pending[key]=cache
        elif attempt.get("pending") is not False or not attempt.get("finished_at") or old["sir_time"](attempt["finished_at"]) >= declared:
            raise ValueError("Invalid terminal metadata")
        elif key not in original: terminals+=1
    expected_pending={x["request_key"] for x in dispatch[116:120]+dispatch[416:420]}
    if set(pending) != expected_pending or terminals != 412: raise ValueError("Only exact eight unknown attempts qualify")
    plans={}
    for item in first["amendment"]["request_plans"]:
        plans.update({x["request_key"]:x for x in read(bound(data,item))})
    indexed={x["request_key"]:x for x in dispatch}; approved={}; pairs={}
    for item in amendment["unavailable_requests"]:
        key=item["request_key"]
        if key in approved or key not in pending or item["cache_sha256"] != prefix[key]: raise ValueError("Invalid unknown request")
        req=pending[key]["request"]; plan=plans[key]; job=indexed[key]
        profile={"model":"gpt-6.1-sol","reasoning_effort":"high","protocol":"23-scale-v5","timeout_s":900}
        actual={k:req.get(k) for k in profile if k != "timeout_s"};actual["timeout_s"]=req.get("runner_limits",{}).get("timeout_s")
        stage,sample=("generate",1) if item["arm"]=="fresh_retry" else ("repair",0)
        if (item["arm"] not in {"fresh_retry","feedback_repair"} or actual != profile or item["profile"] != profile
                or req["stage"] != stage or req["sample"] != sample or req["expected_case_ids"] != [item["case_id"]]
                or any(plan[k] != item[k] for k in ("case_id","arm","stage","sample"))
                or plan["source_hash"] != item["content_hash"] or req["case_inputs"][0]["case_id"] != item["case_id"]
                or len(req["case_inputs"]) != 1 or hash_(req["case_inputs"]) != item["request_input_hash"]
                or hash_(req["feedback"]) != item["feedback_hash"] or job["input_hash"] != item["request_input_hash"]
                or job["feedback_hash"] != item["feedback_hash"] or job["case_id"] != item["case_id"] or job["arm"] != item["arm"]):
            raise ValueError("Unknown request differs from frozen request identity")
        approved[key]=item;pairs.setdefault(item["case_id"],set()).add(item["arm"])
    if set(approved) != expected_pending or len(pairs)!=4 or any(v!={"fresh_retry","feedback_repair"} for v in pairs.values()):
        raise ValueError("Require four whole unavailable pairs")
    for key,item in first["approved"].items():
        if approved[key] != item: raise ValueError("Prior four unknown identities changed")
    return dict(root=root,data=data,main=main,amendment=amendment,amendment_sha256=sha(amendment_path),
                inventory=prefix,approved=approved,old=old,predecessor_state=first)


def scale_intervention_resume_003_install(root, amendment_path, namespace=None):
    state=scale_intervention_resume_003_verify(root,amendment_path);old=state["old"]
    if namespace is None:
        prior=old["scale_intervention_resume_install"](root,state["data"]/state["amendment"]["predecessor"]["path"])
        namespace=prior["namespace"]
    else:
        old["scale_intervention_resume_install"](root,state["data"]/state["amendment"]["predecessor"]["path"],namespace)
    if namespace.get("SCALE_INTERVENTION_RESUME_003_INSTALLED"): raise ValueError("Fresh namespace required")
    # The reviewed predecessor closures already implement immutable-cache replay,
    # unavailable projections, four-worker draining and stop-on-new-error. Extend
    # only their explicitly bound inventory/unknown identities in memory.
    prior_state=namespace["SCALE_INTERVENTION_RESUME_INSTALLED"]
    prior_state["inventory"]=state["inventory"]
    prior_state["approved"]=state["approved"]
    prior_state["amendment_sha256"]=state["amendment_sha256"]
    prior_run=namespace["scale_run_interventions"]
    state["namespace"]=namespace
    def run(root=Path("."),live=False,progress=None):
        if Path(root).resolve()!=state["root"]:raise ValueError("Wrong root")
        if live:
            if (state["main"]/"manifest.json").exists():raise ValueError("Already complete")
            current={p.name.removesuffix(".json.gz"):old["sir_sha"](p) for p in (state["main"]/"cache").glob("*.json.gz")}
            if current!=state["inventory"]:raise ValueError("Exact current inventory required")
            # Persistent exclusive one-shot receipt blocks manual/automatic restart
            # even if a first call never writes a new cache or the process dies.
            receipt=state["main"]/("intervention_resume_003_start_"+state["amendment_sha256"][:12]+".json")
            with receipt.open("x",encoding="utf-8") as f:json.dump(dict(amendment_sha256=state["amendment_sha256"],started_at_utc=datetime.now(timezone.utc).isoformat(),automatic_restart=False),f)
        return prior_run(root=root,live=live,progress=progress)
    namespace.update(scale_run_interventions=run,SCALE_INTERVENTION_RESUME_003_INSTALLED=state)
    return state


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("phase",choices=["interventions"])
    parser.add_argument("--root",type=Path,required=True);parser.add_argument("--amendment",type=Path,required=True);parser.add_argument("--live",action="store_true")
    args=parser.parse_args();state=scale_intervention_resume_003_install(args.root,args.amendment);count=[0]
    def progress(event):
        count[0]+=1;print(json.dumps(dict(event="request_terminal_or_unavailable",completed_this_phase=count[0],**event)),flush=True)
    result=state["namespace"]["scale_run_interventions"](root=args.root,live=args.live,progress=progress)
    print(json.dumps(dict(phase=result["manifest"]["phase"],amendment_sha256=state["amendment_sha256"])),flush=True)
if __name__=="__main__":main()
