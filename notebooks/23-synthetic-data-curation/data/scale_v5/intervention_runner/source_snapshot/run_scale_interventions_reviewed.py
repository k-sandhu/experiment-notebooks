"""Interventions-only entry point using the approved scale-v5 continuation dispatcher.

Offline cache replay is the default. --live authorizes only an initial arm-phase
launch after the byte-bound independent material and runner reviews pass. This
runner never collects originals, retries requests, or changes frozen job order.
"""
import argparse
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

RUNNER_VERSION="23-scale-reviewed-interventions-runner-v1"
RUNNER_ARCHIVE="intervention_runner/source_snapshot/run_scale_interventions_reviewed.py"
SOURCE_REVIEW="scale_original_failure_review.json"
RUNNER_REVIEW="intervention_runner/implementation_review.json"
COMPANION_ARCHIVE="infrastructure_resume/source_snapshot/scale_resume.py"
AMENDMENT_ARCHIVE="infrastructure_resume/amendment_001.json"
GATE_PHASE="interventions_authorized_after_independent_audit"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    path=Path(path)
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",encoding="utf-8-sig") as stream:return json.load(stream)


def bound_path(data,relative):
    if not isinstance(relative,str) or not relative:
        raise ValueError("Gate paths must be nonempty strings")
    candidate=Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("Gate path must stay within data/scale_v5")
    path=(data/candidate).resolve()
    if not path.is_relative_to(data.resolve()):raise ValueError("Gate path escapes data/scale_v5")
    return path


def utc_timestamp(value,label):
    if not isinstance(value,str):raise ValueError(label+" must be an explicit timestamp")
    parsed=datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:raise ValueError(label+" must include a timezone")
    return parsed


def passed_review(value,zero_field,label):
    if value.get("passed") is not True or type(value.get(zero_field)) is not int or value[zero_field]!=0:
        raise ValueError(label+" must pass with zero live/model calls")
    issues=value.get("issues")
    if issues is not None and (not isinstance(issues,(list,dict,str)) or len(issues)):
        raise ValueError(label+" has unresolved or invalid issues")


def verify_initial_live_launch(data):
    """No first-launch runner can restart an existing intervention stage."""
    main=data/"main"
    if (main/"manifest.json").exists():
        raise ValueError("Live interventions refused: a main completion manifest already exists")
    for path in sorted((main/"cache").glob("*.json.gz")):
        cache=read_json(path)
        request=cache.get("request")
        if not isinstance(request,dict) or request.get("stage")!="generate" or type(request.get("sample")) is not int or request["sample"]!=0:
            raise ValueError("Live interventions refused: existing intervention-stage/unknown cache; no restart or retry")


def verify_gate(root,amendment_path,live=False):
    """Verify metadata/bytes before loading a namespace or invoking a phase."""
    root=Path(root).resolve();data=root/"data"/"scale_v5"
    amendment_path=Path(amendment_path).resolve()
    if amendment_path!=bound_path(data,AMENDMENT_ARCHIVE):
        raise ValueError("Use the exact recorded infrastructure amendment for this root")
    gate_path=data/"intervention_start_declaration.json"
    gate=read_json(gate_path)
    if (gate.get("protocol")!="23-scale-v5" or gate.get("phase")!=GATE_PHASE or
            gate.get("material_review_passed") is not True):
        raise ValueError("An independently reviewed intervention-start declaration is required")
    declared=utc_timestamp(gate.get("declared_at_utc"),"Intervention declaration")
    if declared>datetime.now(timezone.utc):raise ValueError("Intervention declaration is future-dated")
    hashes=gate.get("sha256")
    required={RUNNER_ARCHIVE,AMENDMENT_ARCHIVE,COMPANION_ARCHIVE,SOURCE_REVIEW,RUNNER_REVIEW,
              "source_freeze.json","main/protocol.json","main/allocation.json",
              "main/original_manifest.json","main/selection.json"}
    if not isinstance(hashes,dict) or not required.issubset(hashes):
        raise ValueError("Intervention gate does not bind every required runner/review/input")
    for relative,digest in hashes.items():
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise ValueError("Malformed gate SHA256 binding")
        if sha256(bound_path(data,relative))!=digest:
            raise ValueError("Intervention gate binding changed: "+relative)
    runner_sha=sha256(Path(__file__).resolve())
    if runner_sha!=hashes[RUNNER_ARCHIVE]:raise ValueError("Executing runner bytes differ from reviewed archived runner")
    amendment=read_json(amendment_path)
    if amendment.get("protocol")!="23-scale-v5" or amendment.get("amendment_version")!="23-scale-capacity-continuation-v1":
        raise ValueError("Unsupported approved infrastructure amendment")
    if utc_timestamp(amendment.get("declared_at_utc"),"Infrastructure amendment")>declared:
        raise ValueError("Intervention gate predates the infrastructure amendment")
    implementation=amendment.get("implementation")
    if (not isinstance(implementation,dict) or implementation.get("path")!=COMPANION_ARCHIVE or
            implementation.get("sha256")!=hashes[COMPANION_ARCHIVE]):
        raise ValueError("Gate does not bind the amendment's byte-reviewed implementation")
    passed_review(read_json(bound_path(data,SOURCE_REVIEW)),"model_calls","Original source/failure review")
    passed_review(read_json(bound_path(data,RUNNER_REVIEW)),"live_model_calls","Intervention runner review")
    if read_json(bound_path(data,"main/original_manifest.json")).get("phase")!="originals_complete":
        raise ValueError("All originals and audit must complete before intervention calls")
    if live:verify_initial_live_launch(data)
    companion_path=bound_path(data,COMPANION_ARCHIVE)
    companion_bytes=companion_path.read_bytes()
    if hashlib.sha256(companion_bytes).hexdigest()!=hashes[COMPANION_ARCHIVE]:
        raise ValueError("Approved companion bytes changed during verification")
    return {"root":root,"data":data,"amendment_path":amendment_path,
            "companion_path":companion_path,"companion_bytes":companion_bytes,
            "gate_sha256":sha256(gate_path),"amendment_sha256":hashes[AMENDMENT_ARCHIVE],
            "companion_sha256":hashes[COMPANION_ARCHIVE],"runner_sha256":runner_sha}


def load_approved_companion(verified):
    namespace={"__name__":"scale_interventions_approved_companion","__file__":str(verified["companion_path"])}
    exec(compile(verified["companion_bytes"].decode("utf-8-sig"),str(verified["companion_path"]),"exec"),namespace)
    return namespace


def run(root,amendment_path,live=False,progress=None):
    verified=verify_gate(root,amendment_path,live=live)
    print(json.dumps({"event":"verified_intervention_runner","runner_version":RUNNER_VERSION,
        "live":bool(live),"gate_sha256":verified["gate_sha256"],"amendment_sha256":verified["amendment_sha256"],
        "companion_sha256":verified["companion_sha256"],"runner_sha256":verified["runner_sha256"]}),flush=True)
    companion=load_approved_companion(verified)
    namespace=companion["scale_resume_load"](verified["root"])
    companion["scale_resume_install"](verified["root"],verified["amendment_path"],namespace)
    if namespace.get("SCALE_ARMS")!=["fresh_retry","feedback_repair"]:
        raise ValueError("Frozen intervention arms changed")
    # Frozen scale_run_interventions constructs arms only. The installed approved
    # dispatcher preserves four-job waves/order and stops on every NEW failure.
    # Its old-failure exception requires arm=original and cannot match this phase.
    return namespace["scale_run_interventions"](root=verified["root"],live=live,progress=progress)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--amendment",type=Path,required=True)
    parser.add_argument("--live",action="store_true",help="Explicit initial live arm-phase launch; default is cache-only replay")
    args=parser.parse_args();completed=[0]
    def progress(event):
        completed[0]+=1
        safe={key:event[key] for key in ("arm","case_id","cached","transport_failure") if key in event}
        print(json.dumps({"event":"request_terminal","completed_this_phase":completed[0],**safe}),flush=True)
    result=run(args.root,args.amendment,live=args.live,progress=progress)
    # Frozen engine returns only after every scheduled arm request is terminal.
    print(json.dumps({"phase":"interventions","manifest":result["manifest"],"metrics":result["metrics"]},indent=2),flush=True)


if __name__=="__main__":main()
