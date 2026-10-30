"""Posthoc v5 reporting. Read-only until the completed paired bundle exists.

Load frozen scale fixtures/experiment helpers first. This helper never calls a
model, replays an engine phase, or reads partial intervention efficacy.
"""
from pathlib import Path as _SRPath
from collections import Counter as _SRCounter
from statistics import median as _sr_median
import gzip as _sr_gzip
import hashlib as _sr_hashlib
import html as _sr_html
import json as _sr_json
import math as _sr_math
import copy as _sr_copy

SCALE_REPORT_VERSION = "23-scale-posthoc-v5-missing-006"
SCALE_REPORT_ARMS = ("fresh_retry", "feedback_repair")
SCALE_REPORT_CATEGORIES = ("original_success", "both_recover", "repair_only", "fresh_only", "neither_recovers")
SCALE_REPORT_LABELS = {"original_success":"Original success", "both_recover":"Both recover", "repair_only":"Repair only",
                       "fresh_only":"Fresh retry only", "neither_recovers":"Neither recovers"}
SCALE_REPORT_STYLE = {"figure.dpi":130,"savefig.dpi":160,"font.size":11,"axes.titlesize":13,
    "axes.labelsize":11,"axes.spines.top": False,"axes.spines.right": False,"figure.constrained_layout.use": True}
SCALE_REPORT_COLORS = {"original":"#63758c","fresh_retry":"#2584a5","feedback_repair":"#b8662c","truth":"#3c795d"}


def scale_report_hash(value):
    return _sr_hashlib.sha256(_sr_json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode()).hexdigest()


def scale_report_json(path, optional=False):
    path=_SRPath(path)
    if optional and not path.exists(): return None
    opener=_sr_gzip.open if path.suffix==".gz" else open
    with opener(path,"rt", encoding="utf-8-sig") as stream: return _sr_json.load(stream)


def scale_report_rows(path):
    path=_SRPath(path)
    if not path.exists() and path.suffix!=".gz" and path.with_name(path.name+".gz").exists():
        path=path.with_name(path.name+".gz")
    opener=_sr_gzip.open if path.suffix==".gz" else open
    with opener(path,"rt", encoding="utf-8-sig") as stream:
        return [_sr_json.loads(line) for line in stream if line.strip()]


def scale_report_save_analysis(report, root=None):
    """Save only deterministic derived analysis after the final availability gate."""
    if report.get("state")!="complete" or (report.get("manifest") or {}).get("phase")!="interventions_complete":
        raise ValueError("Saving missing-outcome analysis requires interventions_complete")
    analysis=report.get("missing_outcomes")
    if not isinstance(analysis, dict):
        raise ValueError("Completed missing-outcome analysis is required")
    # Serialize before creating directories. The analysis contains observed
    # statistics and explicitly hypothetical binary assignments, never source
    # objects, model answers, telemetry, local paths or generated timestamps.
    payload=(_sr_json.dumps(analysis, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode("utf-8")
    relative=_SRPath("data")/"scale_v5"/"presentation_results"/"missing_outcome_analysis.json"
    destination=_SRPath(root or report["root"])/relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return relative.as_posix()


def scale_report_table(headers, rows):
    def cell(v): return ("Unavailable" if v is None else str(v)).replace("|","\\|").replace("\n"," ")
    return "| "+" | ".join(headers)+" |\n| "+" | ".join("---" for _ in headers)+" |\n"+"\n".join("| "+" | ".join(cell(v) for v in row)+" |" for row in rows)


def scale_report_good(row):
    return bool(row and not row.get("outcome_unavailable") and not row["transport_error"] and row["response"] is not None and
                row["verification"]["valid_schema"] and row["verification"]["exact_fields"])


def scale_report_accepted(row):
    return bool(scale_report_good(row) and row["verification"]["accepted"])


def scale_report_readable(row):
    return bool(row and not row.get("outcome_unavailable") and not row["transport_error"] and
                row["response"] is not None and row["verification"]["valid_schema"])


def scale_report_readable_comparison(report):
    rows={arm:[r for r in report["interventions"] if r["arm"]==arm] for arm in SCALE_REPORT_ARMS}
    scores={arm:{"n":len(values),"readable":sum(scale_report_readable(r) for r in values),
                 "correct":sum(scale_report_good(r) for r in values)} for arm,values in rows.items()}
    if any(not r["n"] or not r["readable"] for r in scores.values()):
        return scores,"At least one arm has no readable replies, so readable-only ranking is unavailable."
    def direction(denominator):
        f,r=(scores[a] for a in SCALE_REPORT_ARMS)
        delta=r["correct"]*f[denominator]-f["correct"]*r[denominator]
        return 1 if delta>0 else -1 if delta<0 else 0
    ranking="changes" if direction("n")!=direction("readable") else "does not change"
    return scores,f"The recovery ranking {ranking} when only readable replies are scored. Readable-only rates describe different observed subsets and do not replace the paired operational comparison."


def scale_report_diagnostic_row(row):
    """Scientific diagnostic copy: transport failure is not measured field damage.

    The frozen operational row may retain a parsed answer even after timeout.
    Its validator was deliberately called with None, so those rejection flags
    cannot establish actual wrong fields or numeric regressions in that answer.
    """
    result=_sr_copy.deepcopy(row)
    if row["transport_error"]:
        result["numeric_absolute_errors"]={field:None for field in row["numeric_absolute_errors"]}
        for field in ("original_wrong_fields_fixed","new_wrong_fields","worsened_numeric_fields"):
            if field in result: result[field]=[]
        if "answer_unchanged" in result: result["answer_unchanged"]=False
        result["diagnostic_outcome"]="transport_failure_not_field_scored"
    return result


def scale_report_percent(n, d): return 100*n/d if d else float("nan")

def scale_report_interval(pair):
    values=pair["paired_bootstrap_95_interval_percentage_points"]
    return "Unavailable" if any(v is None for v in values) else f"[{values[0]:.2f}, {values[1]:.2f}]"


def scale_report_infrastructure_markdown(report):
    """Describe the saved infrastructure amendment, never partial efficacy."""
    amendment=report.get("infrastructure_amendment")
    if amendment is None: return ""
    timestamp=next((amendment[key] for key in ("declared_at_utc", "registered_at_utc", "created_at_utc",
                   "recorded_at_utc", "amended_at_utc", "timestamp_utc") if amendment.get(key)), None)
    timing=f" at {timestamp}" if timestamp else " with its timestamp preserved in the linked record"
    status=amendment.get("status")
    status_text=f" Saved amendment status: {status}." if status else ""
    cfg=(report.get("protocol") or {}).get("config") or (report.get("registration") or {}).get("main") or {}
    target=cfg.get("target_failures", 600);cap=cfg.get("collection_cap", 2048)
    text=("### Infrastructure stop and declared continuation\n\n"
          f"A [timestamped infrastructure-only amendment](data/scale_v5/infrastructure_resume/amendment_001.json) was recorded{timing}, before intervention outcomes were available.{status_text} "
          "The run encountered a provider capacity error with no answer. The amendment preserves that terminal failed attempt as a transport failure; it is not resubmitted or relabelled as an extraction error. "
          "It remains in attempt and service-failure counts and is ineligible for genuine value-failure accrual or paired selection.\n\n"
          "The declared continuation may send only previously unsent originals from the already frozen source/request plan. It does not alter sources, instructions, request identities, the requested model/profile, scoring or selection. "
          f"The {target:,}-failure target and {cap:,}-original cap remain unchanged. This is an explicit change to infrastructure handling of the stop, recorded before any intervention comparison. The original execution includes the retained service failure. ")
    if report.get("infrastructure_resume_helper_available"):
        text+="The [archived continuation companion](data/scale_v5/infrastructure_resume/source_snapshot/scale_resume.py) records the implementation separately from the original frozen runtime. "
    else:
        text+="The report does not claim that a continuation companion has been archived or activated while its saved source is absent. "
    return text+"This note reports the declared handling policy; it does not inspect partial intervention results or supply missing answers."


def scale_report_followup_transport_markdown(report):
    fifth=report.get("intervention_transport_amendment_005")
    amendment=fifth or report.get("intervention_transport_amendment_004")
    if amendment is None: return ""
    failures=amendment["retained_transport_failures"]
    plan=report.get("missing_outcomes_plan") or {}
    rows=[]
    for item in failures:
        meta=item.get("attempt_metadata",{})
        rows.append([item["arm"],item["request_key"],item["error"],meta.get("timed_out"),
                     meta.get("return_code"),meta.get("elapsed_s")])
    amendment_name="fifth" if fifth else "fourth"
    amendment_path="intervention_resume_005/amendment_005.json" if fifth else "intervention_resume_004/amendment_004.json"
    plural="failures" if len(failures)!=1 else "failure"
    return ("### Known follow-up transport stop and unchanged scoring\n\n"
            f"The [{amendment_name} amendment](data/scale_v5/{amendment_path}) retains {len(failures)} terminal follow-up transport {plural} without resubmission. "
            "The frozen 900-second timeout policy remains in force. The frozen policy scores non-recovery for a timeout even when a raw cache retains a parsed answer, usage or return code zero. "
            "The diagnostic label for either terminal service error is Transport failure; not field-scored. "
            "Elapsed wall-clock time can include host sleep and is not a measure of active inference compute. The linked amendment preserves the process and sleep evidence.\n\n"+
            scale_report_table(["Arm","Request key","Terminal error","Timed out","Return code","Elapsed seconds"],rows)+
            f"\n\nEach known failure stays in its observed pair and in operational request and usage totals. Neither a timeout nor a nonzero CLI exit is a measured extraction mistake. No known transport failure adds an unknown outcome: the {plan.get('unavailable_outcomes', 'declared')} unavailable outcomes in {plan.get('unavailable_whole_pairs', 'declared')} sources still use the unchanged amendment-003 sensitivity plan. "
            "A failure flag from validating no scored answer does not establish that the model returned seven wrong fields. Its retained parsed values are excluded from field-error, newly wrong-field and numeric-regression claims.")


def scale_report_validate_006(data,main,amendment,transport005,interruption003,plan,unavailable,prior_unavailable):
    """Bind the new missing-data plan and observed partner to exact saved bytes."""
    if transport005 is None or interruption003 is None or plan is None:
        raise ValueError("Amendment 006 requires the preserved 005/003 chain and new analysis plan")
    if amendment.get("previous_analysis_plan")!=interruption003.get("analysis_plan"):
        raise ValueError("Amendment 006 changed the analysis binding declared by amendment 003")
    if plan.get("previous_analysis_plan")!=amendment.get("previous_analysis_plan"):
        raise ValueError("Amendment 006 plan changed its declared analysis predecessor")
    for binding,key,path in ((amendment.get("predecessor",{}),"predecessor","intervention_resume_005/amendment_005.json"),
                             (amendment.get("previous_analysis_plan",{}),"previous plan","intervention_resume_003/analysis_plan.json"),
                             (amendment.get("analysis_plan",{}),"new plan","intervention_resume_006/analysis_plan.json")):
        if binding.get("path")!=path or binding.get("sha256")!=_sr_hashlib.sha256((data/path).read_bytes()).hexdigest():
            raise ValueError("Amendment 006 "+key+" bytes differ")
    if amendment.get("retained_transport_failures")!=transport005.get("retained_transport_failures"):
        raise ValueError("Amendment 006 changed known terminal service failures")
    binding=scale_missing_validate_plan_006(plan,unavailable,prior_unavailable)
    partner=binding["known_partner"]
    partner_path=main/"cache"/(partner["request_key"]+".json.gz")
    if _sr_hashlib.sha256(partner_path.read_bytes()).hexdigest()!=partner["cache_sha256"]:
        raise ValueError("Amendment 006 known partner cache bytes differ")
    return binding


def scale_report_load(root=_SRPath(".")):
    """Pending mode deliberately never opens intervention rows or raw caches."""
    root=_SRPath(root); data=root/"data"/"scale_v5"; main=data/"main"
    registration=scale_report_json(data/"preregistration.json", True)
    power=scale_report_json(data/"source_snapshot"/"scale_power_plan.json", True)
    pilot_protocol=scale_report_json(data/"pilot"/"protocol.json", True)
    ladder=scale_report_json(data/"pilot"/"ladder.json", True)
    pilot=[]
    if ladder:
        for block in ladder["tiers"]:
            directory=data/"pilot"/f"tier_{block['tier']}"
            pilot.append({"tier": block["tier"],"block": block,"metrics": scale_report_json(directory/"metrics.json")})
    protocol=scale_report_json(main/"protocol.json", True)
    manifest=scale_report_json(main/"manifest.json", True)
    amendment=scale_report_json(data/"infrastructure_resume"/"amendment_001.json", True)
    interruption002=scale_report_json(data/"intervention_resume"/"amendment_002.json", True)
    interruption003=scale_report_json(data/"intervention_resume_003"/"amendment_003.json", True)
    transport004=scale_report_json(data/"intervention_resume_004"/"amendment_004.json", True)
    transport005=scale_report_json(data/"intervention_resume_005"/"amendment_005.json", True)
    interruption006=scale_report_json(data/"intervention_resume_006"/"amendment_006.json", True)
    plan006=scale_report_json(data/"intervention_resume_006"/"analysis_plan.json", True) if interruption006 else None
    interruption=interruption006 or interruption003 or interruption002
    missing_plan=scale_report_json(data/"intervention_resume_003"/"analysis_plan.json", True) if interruption003 else None
    complete=bool(manifest and manifest.get("phase")=="interventions_complete")
    history=[]
    for path in sorted((main/"original_chunks").glob("chunk_*/manifest.json")):
        history.append(scale_report_json(path))
    report={"version": SCALE_REPORT_VERSION,"root": str(root),"data_root": str(data),
            "state":"complete" if complete else "pending","registration": registration,"power": power,
            "pilot_protocol": pilot_protocol,"pilot_ladder": ladder,"pilot": pilot,"protocol": protocol,
            "manifest": manifest,"accrual_history": history,"originals":[],"interventions":[],"cases": {},
            "source_metadata": {},"examples":[],"categories": {},"metrics": None,"selection": None,"ledger":[],
            "infrastructure_amendment": amendment,
            "intervention_interruption_amendment": interruption,
            "intervention_interruption_amendment_002": interruption002,
            "intervention_interruption_amendment_003": interruption003,
            "intervention_transport_amendment_004": transport004,
            "intervention_transport_amendment_005": transport005,
            "intervention_interruption_amendment_006": interruption006,
            "missing_outcomes_plan_006": plan006,
            "missing_outcomes_plan": missing_plan,
            "missing_outcomes": None,
            "infrastructure_resume_helper_available": (data/"infrastructure_resume"/"source_snapshot"/"scale_resume.py").is_file()}
    if not complete:
        return report
    # This gate precedes every efficacy-bearing intervention/cache access.
    originals=scale_report_rows(main/"candidates.jsonl")
    interventions=scale_report_rows(main/"interventions.jsonl")
    ledger=scale_report_rows(main/"request_ledger.jsonl")
    selection=scale_report_json(main/"selection.json")
    metrics=scale_report_json(main/"metrics.json")
    dispatch=scale_report_json(main/"dispatch.json")
    checked={"protocol_hash": scale_report_hash(protocol),"selection_hash": scale_report_hash(selection),
             "candidate_hash": scale_report_hash(originals),"interventions_hash": scale_report_hash(interventions),
             "dispatch_hash": scale_report_hash(dispatch)}
    if any(manifest.get(k)!=v for k, v in checked.items()): raise ValueError("Completed report bundle hash mismatch")
    if manifest["request_keys"]!=[r["request_key"] for r in ledger] or len({r["request_key"] for r in ledger})!=len(ledger):
        raise ValueError("Request ledger mismatch or double-counted requests")
    selected=set(selection["selected_case_ids"])
    if len(selected)!=len(selection["selected_case_ids"]): raise ValueError("Repeated paired case")
    grouped={arm: {r["case_id"]: r for r in interventions if r["arm"]==arm} for arm in SCALE_REPORT_ARMS}
    if any(set(rows)!=selected for rows in grouped.values()) or len(interventions)!=2*len(selected):
        raise ValueError("Incomplete/duplicate paired coverage")
    by_original={r["case_id"]: r for r in originals}
    by_candidate={r["candidate_id"]: r for r in originals}
    by_case={}
    for row in originals+interventions: by_case.setdefault(row["case_id"],[]).append(row)
    metadata={}
    for block in protocol["blocks"]:
        path=main/block["source_path"]
        for case in scale_iter_corpus(path, block["manifest"]):
            cid=case["case_id"]
            if cid not in by_case: continue
            metadata[cid]={k: case[k] for k in ("case_id","family","split","gold","content_hash","semantic_hash","base_shipments")}
            for row in by_case[cid]:
                if row["content_hash"]!=case["content_hash"] or row["semantic_hash"]!=case["semantic_hash"]:
                    raise ValueError("Reported response uses different source")
                verified=scale_validate_answer(case, row["response"] if not row["transport_error"] else None)
                if verified!=row["verification"]: raise ValueError("Saved verification no longer matches frozen rules")
    if set(metadata)!=set(by_case): raise ValueError("Missing called source case")
    for cid in selected:
        old=by_original[cid]
        if old["split"]!="collection" or not old["verification"]["valid_schema"] or old["verification"]["exact_fields"]:
            raise ValueError("Selected pair is not a genuine original collection value failure")
        for arm in SCALE_REPORT_ARMS:
            row=grouped[arm][cid]
            if row["original_candidate_id"]!=old["candidate_id"] or row["request_input_hash"]!=old["request_input_hash"]:
                raise ValueError("Intervention paired against different original/source")
    pairs=[(scale_report_good(grouped["fresh_retry"][cid]), scale_report_good(grouped["feedback_repair"][cid])) for cid in selection["selected_case_ids"]]
    observed=_SRCounter(pairs); p=metrics["paired_value_recovery"]
    expected={"n_pairs": len(pairs),"both_success": observed[True, True],"repair_only": observed[False, True],
              "fresh_only": observed[True, False],"neither_success": observed[False, False]}
    if any(p[k]!=v for k, v in expected.items()): raise ValueError("Saved paired counts mismatch")
    report.update(originals=originals, interventions=interventions, ledger=ledger, selection=selection, metrics=metrics,
                  source_metadata=metadata, accrual_history=selection["accrual_history"])
    # Keep every scheduled slot, usage record and frozen operational result.
    # Only the scientific view excludes unknown whole pairs. Missing raw caches
    # are never opened, including for examples.
    unavailable=(interruption or {}).get("unavailable_requests", [])
    prior_unavailable=(interruption003 or interruption002 or {}).get("unavailable_requests", [])
    historical_unknown_keys=sorted(r["request_key"] for r in prior_unavailable) if interruption006 else sorted(r["request_key"] for r in unavailable)
    historical_unknown_ids=sorted({r["case_id"] for r in prior_unavailable}) if interruption006 else sorted({r["case_id"] for r in unavailable})
    marked={r["request_key"] for r in interventions if r.get("outcome_unavailable")}
    if marked!={r["request_key"] for r in unavailable}:
        raise ValueError("Unavailable row markers differ from amendment allowlist")
    if transport004 is not None:
        retained=transport004.get("retained_transport_failures",[])
        if interruption003 is None or len(retained)!=1:
            raise ValueError("Amendment 004 requires its predecessor and one retained terminal transport failure")
        predecessor=transport004.get("predecessor",{})
        prior_path=data/"intervention_resume_003"/"amendment_003.json"
        if (predecessor.get("path")!="intervention_resume_003/amendment_003.json" or
            predecessor.get("sha256")!=_sr_hashlib.sha256(prior_path.read_bytes()).hexdigest()):
            raise ValueError("Amendment 004 predecessor bytes differ")
        plan_binding=transport004.get("analysis_plan",{})
        if (plan_binding.get("path")!="intervention_resume_003/analysis_plan.json" or
            plan_binding.get("sha256")!=_sr_hashlib.sha256((data/"intervention_resume_003"/"analysis_plan.json").read_bytes()).hexdigest()):
            raise ValueError("Amendment 004 changed its bound amendment-003 analysis plan")
        by_key={r["request_key"]:r for r in interventions}
        retained_keys=[item["request_key"] for item in retained]
        if ("retained_terminal_failure_request_keys" in transport004 and
            sorted(transport004["retained_terminal_failure_request_keys"])!=sorted(retained_keys)):
            raise ValueError("Amendment 004 retained terminal key list differs")
        for item in retained:
            row=by_key.get(item["request_key"])
            if (row is None or row.get("outcome_unavailable") or not row["transport_error"] or
                row["transport_error"]!=item["error"] or row["error_kind"]!="transport_failure" or
                any(row[key]!=item[key] for key in ("case_id","arm","stage","sample","content_hash","request_input_hash","feedback_hash"))):
                raise ValueError("Amendment 004 terminal failure differs from the frozen scored row")
        for key,expected in (("unavailable_request_keys",historical_unknown_keys),
                             ("unavailable_case_ids",historical_unknown_ids)):
            if key in transport004 and sorted(transport004[key])!=expected:
                raise ValueError("Amendment 004 expanded the unchanged unknown identities")
    if transport005 is not None:
        if transport004 is None or interruption003 is None:
            raise ValueError("Amendment 005 requires amendments 004 and 003")
        predecessor=transport005.get("predecessor",{})
        prior_path=data/"intervention_resume_004"/"amendment_004.json"
        if (predecessor.get("path")!="intervention_resume_004/amendment_004.json" or
            predecessor.get("sha256")!=_sr_hashlib.sha256(prior_path.read_bytes()).hexdigest()):
            raise ValueError("Amendment 005 predecessor bytes differ")
        plan_binding=transport005.get("analysis_plan",{})
        if (plan_binding!=transport004.get("analysis_plan") or
            plan_binding.get("path")!="intervention_resume_003/analysis_plan.json" or
            plan_binding.get("sha256")!=_sr_hashlib.sha256((data/"intervention_resume_003"/"analysis_plan.json").read_bytes()).hexdigest()):
            raise ValueError("Amendment 005 changed its bound amendment-003 analysis plan")
        retained=transport005.get("retained_transport_failures",[])
        retained_by_key={item["request_key"]:item for item in retained}
        if len(retained)!=2 or len(retained_by_key)!=2:
            raise ValueError("Amendment 005 requires exactly two retained terminal transport failures")
        if any(retained_by_key.get(item["request_key"])!=item for item in transport004["retained_transport_failures"]):
            raise ValueError("Amendment 005 changed the preserved amendment-004 terminal failure")
        by_key={r["request_key"]:r for r in interventions}
        for list_key in ("retained_terminal_failure_request_keys","retained_transport_failure_request_keys"):
            if list_key in transport005 and sorted(transport005[list_key])!=sorted(retained_by_key):
                raise ValueError("Amendment 005 retained terminal key list differs")
        for item in retained:
            row=by_key.get(item["request_key"])
            if (row is None or row.get("outcome_unavailable") or not row["transport_error"] or
                row["transport_error"]!=item["error"] or row["error_kind"]!="transport_failure" or
                any(row[key]!=item[key] for key in ("case_id","arm","stage","sample","content_hash","request_input_hash","feedback_hash"))):
                raise ValueError("Amendment 005 terminal failure differs from the frozen scored row")
        actual_errors={r["request_key"] for r in interventions if r["transport_error"] and not r.get("outcome_unavailable")}
        if actual_errors!=set(retained_by_key):
            raise ValueError("Amendment 005 has unnamed or missing terminal transport failures")
        for key,expected in (("unavailable_request_keys",historical_unknown_keys),
                             ("unavailable_case_ids",historical_unknown_ids)):
            if key in transport005 and sorted(transport005[key])!=expected:
                raise ValueError("Amendment 005 expanded the unchanged unknown identities")
    if interruption003 is not None:
        if not missing_plan:
            raise ValueError("Amendment 003 requires its bound missing-outcome analysis plan")
        declared_keys=interruption003.get("unavailable_request_keys")
        declared_ids=interruption003.get("unavailable_case_ids")
        historical_unavailable=prior_unavailable if interruption006 else unavailable
        keys=sorted(r["request_key"] for r in historical_unavailable)
        cids=sorted({r["case_id"] for r in historical_unavailable})
        if (keys!=sorted(declared_keys or []) or cids!=sorted(declared_ids or []) or
            keys!=sorted(missing_plan["unavailable_request_keys"]) or
            cids!=sorted(missing_plan["unavailable_case_ids"]) or
            len(historical_unavailable)!=missing_plan["unavailable_outcomes"] or
            len(cids)!=missing_plan["unavailable_whole_pairs"] or
            len(selected)!=missing_plan["scheduled_pairs"] or
            len(selected)-len(cids)!=missing_plan["available_pair_target"]):
            raise ValueError("Amendment 003 identities/counts differ from its bound analysis plan")
        prior={(r["case_id"],r["arm"],r["request_key"]) for r in (interruption002 or {}).get("unavailable_requests",[])}
        current={(r["case_id"],r["arm"],r["request_key"]) for r in historical_unavailable}
        if not prior.issubset(current):
            raise ValueError("Amendment 003 changed a preserved amendment-002 unknown identity")
        if any({r["arm"] for r in historical_unavailable if r["case_id"]==cid}!=set(SCALE_REPORT_ARMS) for cid in cids):
            raise ValueError("The bound amendment 003 requires unavailable whole pairs")
        if (protocol["config"]["bootstrap_seed"]!=missing_plan["bootstrap_seed"] or
            protocol["config"]["bootstrap_draws"]!=missing_plan["bootstrap_draws"]):
            raise ValueError("Amendment 003 changed frozen bootstrap settings")
    elif interruption is not None and (len(unavailable)!=4 or len({r["case_id"] for r in unavailable})!=2):
        raise ValueError("Amendment 002 requires exactly four slots in two whole pairs")
    if interruption006 is not None:
        scale_report_validate_006(data,main,interruption006,transport005,interruption003,
                                  plan006,unavailable,prior_unavailable)
        analysis=scale_missing_outcome_analysis_006(manifest,selection,interventions,unavailable,
                    protocol["config"],plan006,prior_unavailable,scale_paired_statistics)
    else:
        analysis=scale_missing_outcome_analysis(manifest, selection, interventions, unavailable,
                                               protocol["config"], scale_paired_statistics)
    report.update(scheduled_selection=selection, operational_interventions=interventions,
                  raw_metrics=metrics, missing_outcomes=analysis)
    if unavailable or any(row["transport_error"] for row in interventions):
        observed=set(analysis["observed_case_ids"])
        scientific_selection=_sr_copy.deepcopy(selection)
        scientific_selection["selected_case_ids"]=analysis["observed_case_ids"]
        scientific_rows=[scale_report_diagnostic_row(r) for r in interventions if r["case_id"] in observed]
        scientific_metrics=_sr_copy.deepcopy(metrics)
        scientific_metrics.update(scale_main_metrics([], originals, scientific_rows, scientific_selection,
                                                     ledger, protocol["config"], {}))
        scientific_metrics["exports"]=metrics["exports"]
        scientific_metrics["primary_decision"]=analysis["amended_primary_decision"]
        scientific_metrics["paired_value_recovery"]=analysis["paired_value_recovery"]
        report.update(selection=scientific_selection, interventions=scientific_rows, metrics=scientific_metrics)
    report["categories"]=scale_report_categories(report)
    report["examples"]=scale_report_select_examples(report)
    wanted={r["case_id"] for r in report["examples"]}
    for block in protocol["blocks"]:
        for case in scale_iter_corpus(main/block["source_path"], block["manifest"]):
            if case["case_id"] in wanted: report["cases"][case["case_id"]]=case
    return report


def scale_report_categories(report):
    groups={key:[] for key in SCALE_REPORT_CATEGORIES}
    groups["original_success"]=sorted(r["case_id"] for r in report["originals"] if r["split"]=="collection" and scale_report_good(r))
    arms={arm: {r["case_id"]: r for r in report["interventions"] if r["arm"]==arm} for arm in SCALE_REPORT_ARMS}
    for cid in report["selection"]["selected_case_ids"]:
        fresh, repair=(scale_report_good(arms[arm][cid]) for arm in SCALE_REPORT_ARMS)
        key="both_recover" if fresh and repair else "fresh_only" if fresh else "repair_only" if repair else "neither_recovers"
        groups[key].append(cid)
    return {key: sorted(values) for key, values in groups.items()}


def scale_report_select_examples(report):
    examples=[]; seen=set()
    diagnostic_ids={r["case_id"] for r in report["originals"]+report["interventions"]
                    if r.get("outcome_unavailable") or r["transport_error"]}
    for category, members in report["categories"].items():
        eligible=[cid for cid in members if cid not in diagnostic_ids]
        if eligible:
            examples.append({"case_id": eligible[0],"category": category}); seen.add(eligible[0])
    signatures=set()
    def signature(row):
        answer=row["response"].get("answer", {}) if type(row.get("response")) is dict else {}
        if type(answer) is not dict: answer={}
        gold=report["source_metadata"][row["case_id"]]["gold"]
        return tuple((f, answer[f]-gold[f] if type(answer.get(f)) is int and type(gold[f]) is int else "typed/non-numeric")
                     for f in SCALE_FIELDS if not row["verification"]["field_correct"][f])
    missing=set((report.get("missing_outcomes") or {}).get("unavailable_case_ids", []))|diagnostic_ids
    collection=sorted((r for r in report["originals"] if r["split"]=="collection" and r["response"] is not None and not r["transport_error"] and r["case_id"] not in missing), key=lambda r: r["case_id"])
    signatures.update(signature(r) for r in collection if r["case_id"] in seen)
    for row in collection:
        sig=signature(row)
        if len(examples)>=5: break
        if not sig or sig in signatures or sig in {(("quantity_units",-100),),(("quantity_units",-200),)} or row["case_id"] in seen: continue
        examples.append({"case_id": row["case_id"],"category":"additional error variety"}); seen.add(row["case_id"]); signatures.add(sig)
    for row in sorted(collection, key=lambda r:(r["error_kind"]!="value_failure", r["case_id"])):
        if len(examples)>=5: break
        if row["case_id"] not in seen:
            examples.append({"case_id": row["case_id"],"category":"additional original observation"}); seen.add(row["case_id"])
    return examples[:5]


def scale_report_pairs(report, omit_family=None):
    arms={arm: {r["case_id"]: r for r in report["interventions"] if r["arm"]==arm} for arm in SCALE_REPORT_ARMS}
    ids=[cid for cid in report["selection"]["selected_case_ids"] if report["source_metadata"][cid]["family"]!=omit_family]
    return [(scale_report_good(arms["fresh_retry"][cid]), scale_report_good(arms["feedback_repair"][cid])) for cid in ids]


def scale_report_pair_counts(pairs):
    counts=_SRCounter(pairs); n=len(pairs); r=counts[False, True]; f=counts[True, False]; d=r+f
    p=min(1.,2*sum(_sr_math.comb(d, i) for i in range(min(r, f)+1))/2**d) if d else 1.
    return {"n": n,"repair_only": r,"fresh_only": f,"difference_pp":100*(r-f)/n if n else None,"p": p if n else None}


def scale_report_leave_one_out(report):
    return [{"omitted_family": family,**scale_report_pair_counts(scale_report_pairs(report, family))} for family in SCALE_FAMILIES]


def scale_report_uncertainty(p, amended=False):
    if not p["n_pairs"]: return "No eligible pairs exist, so neither a recovery difference nor an advantage is estimated."
    lo, hi=p["paired_bootstrap_95_interval_percentage_points"]; d=p["discordant_pairs"]
    if not d: return "Neither arm has an exclusive recovery. The zero-width resampling interval repeats the observed ties; it does not establish equivalence or rule out differences on new sources."
    text=("The interval includes zero, so its range includes no recovery difference. " if lo<=0<=hi else "The interval excludes zero, but that alone does not establish an advantage. ")
    if lo==hi: text+="Its zero width cannot represent case differences absent from this sample. "
    text+=f"Only the {d} disagreements enter the exact test of equal repair-only versus fresh-only chances. "
    if p["exact_mcnemar_two_sided_p"]<.05:
        if amended:
            text+=("The observed complete-pair imbalance has a nominal p-value below 0.05. Its direction and uncertainty describe only the available cases; "
                   "the scheduled-cohort decision uses every missing-outcome completion. ")
        else:
            favored="repair" if p["repair_only"]>p["fresh_only"] else "fresh retry"
            text+=f"Their imbalance favors {favored} at the conventional 5% threshold within this selected cohort. "
    else: text+="Their imbalance does not give clear evidence of an arm advantage at the conventional 5% threshold. "
    if d<10: text+=f"Just {d} discordant sources carry this comparison, so even a large percentage difference can have weak support. "
    if lo<hi:
        if lo<=5<=hi: text+="The interval still includes the planned five-percentage-point gain, so this range does not rule that gain out. "
        elif hi<5: text+="A five-percentage-point repair gain is above this interval's upper end under the case-level assumptions. "
        else: text+="The interval lies above the five-percentage-point planning effect under the case-level assumptions. "
    return text+"Case-level inference is conditional on stopped accrual, pilot calibration and a shared generator; it does not establish a training or frontier-model gain."


def scale_report_numeric(report):
    selected=set(report["selection"]["selected_case_ids"])
    stages=[("original",[r for r in report["originals"] if r["case_id"] in selected])]
    stages += [(arm,[r for r in report["interventions"] if r["arm"]==arm]) for arm in SCALE_REPORT_ARMS]
    output=[]
    for name, rows in stages:
        for field in ("quantity_units","unit_price_cents"):
            values=[r["numeric_absolute_errors"][field] for r in rows if not r["transport_error"] and r["response"] is not None and r["numeric_absolute_errors"][field] is not None]
            output.append({"stage": name,"field": field,"values": values,"n": len(rows),"n_numeric": len(values),
                           "median":_sr_median(values) if values else None,"maximum": max(values) if values else None})
    return output


def scale_report_family_rows(report):
    rows=[]
    for family in SCALE_FAMILIES:
        original=[r for r in report["originals"] if r["split"]=="collection" and r["family"]==family]
        paired={arm:[r for r in report["interventions"] if r["arm"]==arm and r["family"]==family] for arm in SCALE_REPORT_ARMS}
        rows.append({"family": family,"original_n": len(original),"original_failures": sum(r["error_kind"]=="value_failure" for r in original),
                     "paired_n": len(paired["fresh_retry"]),**{arm: sum(scale_report_good(r) for r in values) for arm, values in paired.items()}})
    return rows


def scale_report_cache(report, row):
    path=_SRPath(report["root"])/"data"/"scale_v5"/"main"/"cache"/(row["request_key"]+".json.gz")
    cached=scale_report_json(path)
    if cached["key"]!=row["request_key"] or scale_report_hash(cached["request"])!=row["request_key"]:
        raise ValueError("Worked-example raw cache key mismatch")
    if scale_report_hash(cached["request"]["case_inputs"])!=row["request_input_hash"]:
        raise ValueError("Worked-example cached source differs from the parsed row")
    attempt=cached["attempts"][-1]
    if attempt.get("pending"): raise ValueError("Completed example has a pending raw cache")
    return cached, attempt, path.relative_to(_SRPath(report["root"])).as_posix()


def scale_report_example_rows(report, cid):
    old=next(r for r in report["originals"] if r["case_id"]==cid)
    arms={arm: next((r for r in report["interventions"] if r["case_id"]==cid and r["arm"]==arm), None) for arm in SCALE_REPORT_ARMS}
    return old, arms


def scale_report_excerpt(case, trace):
    record=case["source_record"]; lines=case["document"].splitlines()
    ids={trace["term_winners"][f]["approval"] for f in trace["term_winners"]}
    ret=next((e for e in trace["events"] if e["reason"]=="accepted_return" and e["net_dispatched_units"]), None)
    rate_key=allocation_key=None
    if ret:
        ids.update((ret["event_id"], ret["reference"]))
        shipment_revision=next(e["selected_revision"] for e in trace["events"] if e["event_id"]==ret["reference"])
        shipment=next(r for r in record["ledger"] if r["event_id"]==ret["reference"] and
                      r["row_revision"]==shipment_revision and r["recorded_at"]<=record["cutoff"])
        rate_key=(shipment["sku"], shipment["uom"], ret["uom_effective_from"])
        allocation_key=(shipment["allocation"], ret["allocation_effective_from"])
    reversed_row=next((e for e in trace["events"] if e["reason"]=="reversed_shipment"), None)
    if reversed_row:
        ids.add(reversed_row["event_id"])
        ids.update(e["event_id"] for e in trace["events"] if e["reason"]=="reversal_control" and e["reference"]==reversed_row["event_id"])
    selected={e["event_id"]: e["selected_revision"] for e in trace["events"]}
    keep=[]
    for line in lines:
        cells=[v.strip() for v in line.split("|")]; first=cells[0]
        if first in ids:
            if first in selected and (len(cells)<2 or cells[1]!=str(selected[first])): continue
            keep.append(line)
        elif first==record["target_line_id"]: keep.append(line)
        elif rate_key and tuple(cells[:3])==rate_key: keep.append(line)
        elif allocation_key and tuple(cells[:2])==allocation_key: keep.append(line)
        elif (len(cells)==10 and first==trace["price"]["plan"] and
              cells[2]==str(trace["price"]["tier_minimum"])): keep.append(line)
        elif line.startswith(("Target-","Cutoff-UTC:","Issued-UTC:")): keep.append(line)
    return "\n".join(dict.fromkeys(keep))


def scale_report_trace_text(case, trace):
    shipments=sum(max(e["net_dispatched_units"],0) for e in trace["events"])
    returns=-sum(min(e["net_dispatched_units"],0) for e in trace["events"])
    price=trace["price"]
    text=(f"Approved demand from {trace['term_winners']['ordered_units']['approval']} is {trace['ordered_units']:,} individual units. "
          f"Selected active shipments allocate {shipments:,}; accepted returns reopen {returns:,}. "
          f"Open balance is {trace['ordered_units']:,} - ({shipments:,} - {returns:,}) = {trace['open_units']:,}. "
          "The excerpt is a few literal source rows, not the complete ledger arithmetic. All selected/excluded events remain in the frozen packet and full trace. "
          f"Pricing plan {price['plan']} uses ordered demand at tier {price['tier_minimum']:,}: "
          f"{price['gross_pack_cents']:,} gross cents / {price['pack_units']} pricing units, then sequential rebates "
          f"{price['rebate_a_bps']}/10000 and {price['rebate_b_bps']}/10000. Add {price['fee_unit_cents']} cents/unit plus "
          f"{price['pack_fee_unit_cents']} converted pack-fee cents/unit, subtract {price['credit_unit_cents']} credit cents/unit. "
          f"Exact {price['unrounded_unit_cents']} cents becomes {price['rounded_unit_cents']} integer cents after one half-up rounding.")
    ret=next((e for e in trace["events"] if e["reason"]=="accepted_return" and e["net_dispatched_units"]), None)
    if ret:
        shipment=next(e for e in trace["events"] if e["event_id"]==ret["reference"])
        selected=[r for r in case["source_record"]["ledger"] if r["event_id"]==ret["reference"] and r["row_revision"]==shipment["selected_revision"] and r["recorded_at"]<=case["source_record"]["cutoff"]]
        occurred=selected[0]["occurred_at"]
        text+=(f" Return {ret['event_id']} uses selected shipment {ret['reference']} revision {shipment['selected_revision']} "
               f"at {occurred}, not a superseded shipment or the return-day master. Its {ret['selected_quantity']} handling units × "
               f"{ret['units_per_uom']} units/UOM × {ret['target_share_percent']}% reopens {-ret['net_dispatched_units']} units; "
               f"the dated factor/allocation versions are {ret['uom_effective_from']} and {ret['allocation_effective_from']}.")
    return text


def scale_report_examples_markdown(report):
    groups=report["categories"]
    end_to_end_id=next((e["case_id"] for e in report["examples"]
                        if all(scale_report_example_rows(report,e["case_id"])[1].values())),None)
    text=["### Worked inputs, answers and corrections\n\n"
          "Examples take the first stable ID in each observed category, add distinct original error signatures, then fill to five ordinary cases. "
          "Sources with an unavailable outcome or known service failure are excluded from these extraction examples and described separately in the transport record. "
          "The category counts still include observed service non-recoveries. This is purposeful coverage, not an unbiased sample. Missing categories are not filled with invented outcomes.\n\n"+
          scale_report_table(["Observed category","Available collection cases"],[[SCALE_REPORT_LABELS[k], len(groups[k])] for k in SCALE_REPORT_CATEGORIES])]
    text.append("The category counts cover original successes and the paired failure cohort separately. An absent recovery category means it was not observed here, rather than proving it impossible. "
                +"Absent categories: "+(", ".join(SCALE_REPORT_LABELS[k] for k in groups if not groups[k]) or "none")+".")
    for number, example in enumerate(report["examples"],1):
        cid=example["case_id"]; case=report["cases"][cid]; trace=scale_calculation_trace(case); old, arms=scale_report_example_rows(report, cid)
        excerpt=scale_report_excerpt(case, trace)
        if number==1 or cid==end_to_end_id:
            explanation=scale_report_trace_text(case, trace)
        else:
            excerpt="\n".join(excerpt.splitlines()[:5])
            shipments=sum(max(e["net_dispatched_units"],0) for e in trace["events"])
            returns=-sum(min(e["net_dispatched_units"],0) for e in trace["events"])
            explanation=(f"The complete selected ledger gives {trace['ordered_units']:,} approved units minus {shipments:,} shipped plus {returns:,} returned = {trace['open_units']:,} open units. "
                         f"The price calculation gives {trace['price']['rounded_unit_cents']} cents per unit. The short literal input excerpt does not contain every movement; the linked packet contains the full evidence.")
        text.append(f"#### Case {number}: {SCALE_REPORT_LABELS.get(example['category'], example['category'])}, {cid}\n\n"
                    f"Target order {case['gold']['order_id']}, line {case['source_record']['target_line_id']}, SKU {case['gold']['sku']}. "
                    f"Source SHA256: `{case['content_hash']}`. The full packet is in the [compressed collection corpus](data/scale_v5/main/sources/collection.jsonl.gz).\n\n"
                    "\x60\x60\x60text\n"+excerpt+"\n\x60\x60\x60\n\n"+explanation)
        def value(row, field):
            if row and row["transport_error"]: return "Transport failure; not field-scored"
            obj=row.get("response") if row else None
            if type(obj)is dict and type(obj.get("answer"))is dict:
                return "null" if obj["answer"].get(field) is None else obj["answer"][field]
            return "Unavailable"
        shown_fields=SCALE_FIELDS if number==1 or cid==end_to_end_id else ("quantity_units","unit_price_cents")
        text.append(scale_report_table(["Field","Expected","Original","Fresh retry","Feedback repair"],
                    [[f, case["gold"][f], value(old, f), value(arms["fresh_retry"], f), value(arms["feedback_repair"], f)] for f in shown_fields]))
        for label, row in [("Original", old),("Fresh retry", arms["fresh_retry"]),("Feedback repair", arms["feedback_repair"])]:
            if row is None:
                reason=("this original had all seven values right, so it was ineligible for failure-only intervention."
                        if scale_report_good(old) else "this original failure was outside the fixed selected ranking, so neither intervention was called.")
                text.append(label+": "+reason); continue
            if row["transport_error"]:
                text.append(f"{label}: known terminal transport failure ({row['transport_error']}). The frozen policy scores non-recovery even if the raw cache retains a parsed response. No wrong-field, newly wrong-field or numeric-regression claim is inferred from validator flags on this failed request.")
                continue
            v=row["verification"]; wrong=[f for f in SCALE_FIELDS if not v["field_correct"][f]]; citations=[f for f in SCALE_FIELDS if not v["evidence_correct"][f]]
            status=f"{label}: {sum(v['field_correct'].values())}/7 values correct; "+("accepted." if scale_report_accepted(row) else "rejected.")
            if wrong: status+=" Wrong fields: "+", ".join(wrong)+"."
            if citations: status+=" Insufficient citations: "+", ".join(citations)+"."
            q=value(row,"quantity_units"); expected=case["gold"]["quantity_units"]
            if type(q)is int and q!=expected:
                status+=f" Quantity differs by {q-expected:+,} units ({100*abs(q-expected)/expected:.3f}% of the true balance). Exact reconciliation rejects this answer."
            if row.get("new_wrong_fields"):status+=" Newly wrong fields: "+", ".join(row['new_wrong_fields'])+"."
            if row.get("worsened_numeric_fields"):status+=" Worsened numeric fields: "+", ".join(row['worsened_numeric_fields'])+"."
            text.append(status)
        if arms["feedback_repair"] and cid==end_to_end_id:
            raw,_,_=scale_report_cache(report, arms["feedback_repair"])
            feedback=raw["request"]["feedback"][cid]
            if feedback["original_output"]!=old["response"]: raise ValueError("Displayed repair uses different old answer")
            text.append("Actual field feedback supplied with that exact old answer:\n\n\x60\x60\x60json\n"+_sr_json.dumps(feedback["validator_feedback"], indent=2)+"\n\x60\x60\x60\n\nThe package names failed fields and citation/schema flags, without expected values. It therefore has privileged checking plus prior-answer exposure; the fresh retry has neither.")
        links=[f"[{label}](data/scale_v5/main/cache/{row['request_key']}.json.gz)"
               for label, row in [("original", old),("fresh retry", arms["fresh_retry"]),("feedback repair", arms["feedback_repair"])] if row is not None]
        text.append("Saved full-request gzip caches for this case: "+", ".join(links)+".")
    return "\n\n".join(text)


def scale_report_prompt_markdown(report):
    example=next((e for e in report["examples"] if all(scale_report_example_rows(report, e["case_id"])[1].values())), report["examples"][0] if report["examples"] else None)
    if example is None: return "### Exact supplied CLI input\n\nNo measured example is available."
    cid=example["case_id"]; number=report["examples"].index(example)+1; old, arms=scale_report_example_rows(report, cid)
    blocks=[f"### Inspect the supplied CLI inputs for Case {number}\n\nThe seven-field comparison table above is the parsed result for {cid}. "
            "These are verbatim excerpts of the supplied instructions and raw final responses. Linked caches preserve every prompt row and response. "
            "Each arm uses one CLI request; internal network reconnects are not separate inference draws."]
    shared=False
    for label, row in [("Original", old),("Fresh retry", arms["fresh_retry"]),("Feedback repair", arms["feedback_repair"])]:
        if row is None: continue
        raw, attempt, path=scale_report_cache(report, row); request=raw["request"]
        prompt="\n\n".join(m["content"] for m in request["messages"])
        if not shared:
            instruction=prompt.split("\n\nREQUEST DATA (JSON):\n",1)[0]
            instruction_excerpt=instruction[:400]
            task_rules=request["case_inputs"][0]["task_instructions"]
            excerpt=task_rules[:350]
            blocks.append("Verbatim output instruction supplied to every arm (excerpt):\n\n```text\n"+instruction_excerpt+"\n```\n\n"
                          "Task-rule excerpt (the complete rules and source packet are in every linked cache):\n\n```text\n"+excerpt+"\n```"+
                          ("\n\nThe task-rule excerpt ends here; the saved prompt continues." if len(task_rules)>len(excerpt) else ""))
            shared=True
        response=attempt.get("final_assistant_response", "")
        display=response[:200]
        blocks.append(f"{label}: {request['model']} via codex exec, effort {request['reasoning_effort']}, stage {request['stage']}, sample {request['sample']}. "
                      +(f"This request has a terminal transport error ({row['transport_error']}); any retained raw answer is excluded from recovery and field-error scoring. " if row["transport_error"] else "")+
                      f"[Full supplied prompt and raw response]({path}).\n\n"
                      f"<details><summary>{label}: raw final assistant response"+(" excerpt" if len(response)>len(display) else "")+"</summary>\n\n```json\n"+
                      display+"\n```\n\n"+
                      "</details>")
    return "\n\n".join(blocks)


def scale_report_pilot_markdown(report):
    ladder=report["pilot_ladder"]
    if not ladder: return "### Difficulty calibration\n\nThe frozen plan has 16 cases at 128 shipments, then 16 at 192 only if the first tier has fewer than six genuine value failures. No completed pilot ladder is saved yet. No difficulty threshold or selected tier is claimed."
    rows=[]
    for block in report["pilot"]:
        m=block["metrics"]
        rows.append([block["tier"], m["n_attempted_cases"], m["value_correct_valid_schema"], m["value_failure_cases"], m["accepted"], block["block"]["threshold_met"]])
    return ("### Difficulty calibration\n\nA genuine pilot failure requires a usable, schema-valid answer with at least one wrong typed value. Service, schema and citation-only failures do not qualify.\n\n"+
            scale_report_table(["Base shipments","Called","Seven values right","Genuine value failures","Fully accepted","At least six failures"], rows)+
            f"\n\nThe completed pilot made {ladder['physical_cli_requests']} CLI requests and selected {ladder['selected_tier']} shipments per packet: {ladder['selection_reason']}. "
            f"The threshold {'was' if ladder['threshold_met'] else 'was not'} met. Uncalled tiers: {ladder['uncalled_tiers']}. "
            "This is solver-relative calibration on fresh seeds, not a causal comparison of length. The pilot answers do not enter the paired main inference.")


def scale_report_power_markdown(report):
    plan=report["power"]
    if plan is None: return "### Planned precision\n\nThe frozen power plan is unavailable; no power figure is invented."
    selected=[r for r in plan["grid"]["rows"] if r["true_recovery_difference"] in {.05,.1}]
    rows=[[f"{100*r['true_recovery_difference']:.0f} pp", f"{100*r['discordance_probability']:.0f}%"]+
          [f"{100*r['primary_positive_direction_power_by_n_pairs'][str(n)]:.2f}%" for n in (200,400,600)] for r in selected]
    five=[r["primary_positive_direction_power_by_n_pairs"]["600"] for r in selected if r["true_recovery_difference"]==.05]
    ten=[r["primary_positive_direction_power_by_n_pairs"]["600"] for r in selected if r["true_recovery_difference"]==.1]
    missing=report.get("missing_outcomes")
    amendment_note=(f"The actual comparison has {missing['n_observed_pairs']} complete pairs and checks all {missing['n_completions']} possible completions of its unknown outcomes. The table describes the original fully observed design, not the power of that amended decision rule. " if missing and missing['n_unavailable_outcomes'] else "")
    return ("### Planned precision and the five-point limit\n\nPower is the chance that the predeclared test detects a repair-favoring difference when a specified true difference exists. "
            "A five-percentage-point effect means five extra corrected orders per 100 original failures. Discordance is the fraction of cases where exactly one arm succeeds; those cases drive the paired test. "
            "The saved exact-enumeration plan uses a positive recovery difference and a two-sided exact McNemar p-value below 0.05. These are planning scenarios, not observed effects.\n\n"+
            scale_report_table(["Assumed true gain","Assumed discordance","Power at 200 pairs","At 400","At 600"], rows)+
            f"\n\nAt 600 pairs, nominal power for a true five-point gain is only {100*min(five):.2f}–{100*max(five):.2f}%, "
            f"compared with {100*min(ten):.2f}–{100*max(ten):.2f}% for ten points. "
            "Thus 600 pairs do not guarantee a decisive answer about a small gain; a shortfall weakens the original plan further. "
            "The calculation assumes independent case pairs conditional on one fixed generator. Shared source programs/templates can violate that assumption. "
            + amendment_note +
            "Earlier v4 outcomes informed planning only and are not pooled into the new estimate. The full frozen grid is in [the saved power plan](data/scale_v5/source_snapshot/scale_power_plan.json).")


def scale_report_results_markdown(report):
    m=report["metrics"]; selection=report["selection"]; p=m["paired_value_recovery"]
    base=[m["original_collection"], m["audit"]]
    rows=[[name, r["n_attempted_cases"], r["valid_schema"], r["value_correct_valid_schema"], r["accepted"], r["value_failure_cases"]]
          for name, r in zip(("Collection originals","Fixed separate audit"), base)]
    arms=m["interventions"]
    readable,readable_note=scale_report_readable_comparison(report)
    baseline_note=""
    if all(r["n_attempted_cases"] for r in base):
        rates=[scale_report_percent(r["value_correct_valid_schema"],r["n_attempted_cases"]) for r in base]
        baseline_note=(f"Collection accuracy is {rates[0]:.2f}%; fixed-audit accuracy is {rates[1]:.2f}%, a difference of {rates[1]-rates[0]:+.2f} percentage points (audit minus collection). "
                       "The audit has its own seed and fewer cases. The collection percentage does not establish a stable accuracy rate on every new packet.\n\n")
    text=("### Original accuracy and failure-only recovery\n\nThe original baseline counts every called source in its split. An all-value success requires valid schema and all seven typed values exactly right. "
          "Full acceptance also needs sufficient source-group citations. For example, nine fully correct orders out of ten is 9/10 all-value success; it is different from 69 correct fields out of 70.\n\n"+
          scale_report_table(["Original split","Called","Schema valid","All values right","Fully accepted","Genuine value failures"], rows)+
          f"\n\nCollection originals solve {base[0]['value_correct_valid_schema']}/{base[0]['n_attempted_cases']} by all values; the fixed audit solves {base[1]['value_correct_valid_schema']}/{base[1]['n_attempted_cases']}. "
          "Collection accuracy is descriptive under failure-count stopping. The 96-case audit is a separate fixed baseline, not a post-training evaluation.\n\n"+baseline_note+
          scale_report_table(["Failure-only arm","Selected cases","All values right","Readable wrong values","Unreadable slots","Right/readable","Fully accepted","Old wrong fields fixed","Cases with new wrong fields","Cases with worse numeric error"],
             [[r["arm"].replace("_"," "), r["n_attempted_cases"], r["value_correct_valid_schema"], readable[r["arm"]]["readable"]-readable[r["arm"]]["correct"],
               readable[r["arm"]]["n"]-readable[r["arm"]]["readable"],
               f"{readable[r['arm']]['correct']}/{readable[r['arm']]['readable']}", r["accepted"], r["original_wrong_fields_fixed"], r["cases_with_new_wrong_fields"], r["cases_with_worsened_numeric_error"]] for r in arms])+
          "\n\nUnreadable slots include terminal service errors, refusals or missing answers and replies failing the required schema/types. They remain operational non-recoveries; readable wrong values are a different failure. " + readable_note)
    a={r["arm"]: r for r in arms}; fresh=a["fresh_retry"]; repair=a["feedback_repair"]
    text+=(f"\n\nFresh retry recovers {fresh['value_correct_valid_schema']}/{fresh['n_attempted_cases']} selected failures; the repair package recovers {repair['value_correct_valid_schema']}/{repair['n_attempted_cases']}. "
           "These are conditional recoveries on the same selected failures, not ordinary before/after accuracy. The package includes the prior answer and externally verified failed-field flags, so the contrast does not isolate feedback alone. "
           "Equal request counts also do not equalize prompt tokens or inference compute.\n\n"+
           scale_report_table(["","Repair fails","Repair succeeds"],[["Fresh fails", p["neither_success"], p["repair_only"]],["Fresh succeeds", p["fresh_only"], p["both_success"]]]))
    if p["n_pairs"]:
        text+=(f"\n\nBoth arms recover {p['both_success']} cases; repair alone {p['repair_only']}; fresh alone {p['fresh_only']}; neither {p['neither_success']}. "
               f"Repair minus fresh is {p['difference_percentage_points']:.2f} percentage points across {p['n_pairs']} pairs, with case-paired percentile-bootstrap 95% interval "
               f"{scale_report_interval(p)} pp ({p['bootstrap_draws']:,} whole-pair resamples, seed {p['bootstrap_seed']}). "
               f"The two-sided exact conditional McNemar p-value is {p['exact_mcnemar_two_sided_p']:.6g}, based on {p['discordant_pairs']} disagreements. "+scale_report_uncertainty(p, bool((report.get("missing_outcomes") or {}).get("n_unavailable_pairs"))))
    else: text+="\n\n"+scale_report_uncertainty(p, bool((report.get("missing_outcomes") or {}).get("n_unavailable_pairs")))
    clean=m["reconnect_sensitivity"]; retained=clean["paired_value_recovery"]
    text+=(f"\n\nThe predeclared reconnect sensitivity excludes {len(clean['excluded_case_ids'])} pairs with an observed reconnect in the original or either arm, retaining {retained['n_pairs']}/{p['n_pairs']}. ")
    if retained["n_pairs"]: text+=f"Retained repair-minus-fresh difference is {retained['difference_percentage_points']:.2f} pp, interval {scale_report_interval(retained)} pp. "
    else: text+="No pairs remain for that sensitivity estimate. "
    text+="This is a service-history sensitivity, not permission to discard ordinary CLI warnings or select favorable responses."
    return text


def scale_report_error_markdown(report):
    selected=set(report["selection"]["selected_case_ids"])
    stages=[("All collection originals",[r for r in report["originals"] if r["split"]=="collection"])]
    stages += [(arm.replace("_"," "),[r for r in report["interventions"] if r["arm"]==arm]) for arm in SCALE_REPORT_ARMS]
    rows=[]; paragraphs=[]
    for name, values in stages:
        counts=_SRCounter(r["error_kind"] for r in values)
        rows.append([name, len(values), counts["schema_failure"], counts["value_failure"], counts["evidence_only_failure"], counts["unusable_response"], counts["transport_failure"], sum(bool(r.get("new_wrong_fields")) for r in values if not r["transport_error"]), sum(bool(r.get("worsened_numeric_fields")) for r in values if not r["transport_error"])])
        fields=_SRCounter(f for r in values if r["response"] is not None and not r["transport_error"] and r["verification"]["valid_schema"] for f in SCALE_FIELDS if not r["verification"]["field_correct"][f])
        paragraphs.append(name+f" ({len(values)} cases) has wrong typed-value field counts among schema-valid replies: "+(", ".join(f"{f} {fields[f]}" for f in SCALE_FIELDS if fields[f]) or "none")+". These field counts may overlap within one rejected case.")
    text=("### Error size, type and newly damaged fields\n\nA malformed schema/type differs from a well-formed wrong value; a citation-only failure differs from both. Fixing one old error can still introduce another wrong field, and worsening an already wrong number is a separate harm.\n\n"+
          scale_report_table(["Stage","Cases","Schema/type failures","Value failures","Citations only","Unusable replies","Known transport failures","New wrong fields (cases)","Worse numeric error (cases)"], rows)+"\n\n"+"\n\n".join(paragraphs)+
          "\n\nA terminal transport failure remains a non-recovery in its observed pair. It is separate from a genuine wrong-value reply and from the unavailable controller-interrupted outcomes. Any parsed answer retained after a transport error is excluded from field-error and numeric-regression diagnostics; the frozen operational artifacts remain unchanged.")
    numeric=scale_report_numeric(report)
    text+="\n\n"+scale_report_table(["Selected-cohort stage","Field","Numeric/total","Median absolute error","Maximum"],[[r["stage"].replace("_"," "), r["field"], f"{r['n_numeric']}/{r['n']}", r["median"], r["maximum"]] for r in numeric])
    text+="\n\nQuantity errors are individual units; price errors are integer cents per individual unit. Medians include numeric successes at zero, and null/non-numeric outputs are excluded from magnitudes but remain unsuccessful answers. Coverage above prevents a missing numeric result from looking like zero error. "
    q=[r for r in numeric if r["field"]=="quantity_units"]
    text+="; ".join(f"{r['stage'].replace('_',' ')} has median {r['median']} and maximum {r['maximum']} units across {r['n_numeric']}/{r['n']} numeric quantities" for r in q)+"."
    original=[r for r in report["originals"] if r["split"]=="collection"]
    deltas=_SRCounter()
    relative=[]
    for row in original:
        if row["transport_error"]: continue
        obj=row.get("response"); answer=obj.get("answer") if type(obj)is dict else None
        gold=report["source_metadata"][row["case_id"]]["gold"]["quantity_units"]
        value=answer.get("quantity_units") if type(answer)is dict else None
        if type(value)is int and value!=gold:
            deltas[value-gold]+=1
            if gold: relative.append(abs(value-gold)/gold*100)
    if deltas:
        shown=sorted(deltas.items(), key=lambda item: (-item[1], item[0]))[:12]
        covered=sum(count for _, count in shown);total=sum(deltas.values());omitted=len(deltas)-len(shown)
        text+=f"\n\nThe {len(shown)} most frequent original signed quantity offsets (observed minus expected individual units) are: "+", ".join(f"{d:+,}: {n} cases" for d, n in shown)+". "
        text+=f"They cover {covered}/{total} wrong numeric quantities; {omitted} distinct offsets are omitted from this inline summary. Frequency ties use ascending signed offset. "
        text+="The [full original candidate rows](data/scale_v5/main/candidates.jsonl) retain every observed answer. "
        if relative: text+=f"Across all wrong numeric quantities, the median relative error is {_sr_median(relative):.3f}%, maximum {max(relative):.3f}%. "
        text+="Small relative offsets can still make an order unusable under exact reconciliation. A delta matching a return or shipment amount would be an arithmetic possibility, not proof of the model's internal process."
    return text


def scale_report_family_markdown(report):
    rows=scale_report_family_rows(report); loov=scale_report_leave_one_out(report)
    text=("### Scenario variants and descriptive sensitivity\n\nThe six labels describe overlapping variants of one generator program. Their sizes and outcomes can reveal where this sample differs; they are not six independent task programs or a causal ablation.\n\n"+
          scale_report_table(["Variant","Called originals","Original value failures","Selected pairs","Fresh recoveries","Repair recoveries"],
          [[r["family"], r["original_n"], r["original_failures"], r["paired_n"], r["fresh_retry"], r["feedback_repair"]] for r in rows]))
    original_rates=[(r['original_failures']/r['original_n'],r) for r in rows if r['original_n']]
    if original_rates:
        low=min(original_rates,key=lambda item:item[0])[1];high=max(original_rates,key=lambda item:item[0])[1]
        text+=f"\n\nOriginal failure counts range from {low['original_failures']}/{low['original_n']} for {low['family']} to {high['original_failures']}/{high['original_n']} for {high['family']}. Small groups and shared rules limit explanations based on these contrasts."
    text+="\n\n"+scale_report_table(["Omit one variant","Retained pairs","Repair minus fresh (pp)","Exact p (descriptive)"],[[r["omitted_family"], r["n"], f"{r['difference_pp']:.2f}" if r["n"] else "Unavailable", f"{r['p']:.6g}" if r["n"] else "Unavailable"] for r in loov])
    differences=[r["difference_pp"] for r in loov if r["n"]]
    if differences: text+=f"\n\nLeaving out one variant at a time gives differences from {min(differences):.2f} to {max(differences):.2f} pp. "
    text+="These overlapping subsets test numerical sensitivity to the observed composition; they do not estimate variation across independent generator programs, and their p-values are not separate confirmatory discoveries."
    return text


def scale_report_model_improvement_markdown(report):
    """Teach the gap between verified corrections and demonstrated new skill."""
    if report.get("state")!="complete":
        raise ValueError("Model-improvement interpretation requires completed results")
    m=report["metrics"]; original=m["original_collection"]; p=m["paired_value_recovery"]
    arms={r["arm"]:r for r in m["interventions"]}
    fresh,repair=(arms[arm] for arm in SCALE_REPORT_ARMS)
    pilot="; ".join(f"{block['metrics']['value_failure_cases']}/{block['metrics']['n_attempted_cases']} genuine value failures at {block['tier']} shipments"
                    for block in report["pilot"])
    source_count=sum(block["manifest"]["n_cases"] for block in report["protocol"]["blocks"])
    usable=[r for r in report["originals"] if r["split"]=="collection" and r["response"] is not None and not r["transport_error"]]
    quantities=sum(not r["verification"]["field_correct"]["quantity_units"] for r in usable)
    other=sum(not r["verification"]["field_correct"][field] for r in usable for field in SCALE_FIELDS if field!="quantity_units")
    text=("### Why improving an already capable model takes more than corrected answers\n\n"
          "A correction study needs examples on which the model gives a wrong answer. If the chosen tasks are already solved, there is little correction data to collect and little room to measure a benefit. "
          f"The pilot found {pilot or 'no saved pilot comparison'}. The selected setting was {report['protocol']['selected_tier']} shipments per packet. "
          "This calibration found a setting that produced errors for the requested model and prompt. The pilot samples are small and use different fresh cases; they do not isolate shipment count as the cause of the difference or establish a general difficulty curve.\n\n"
          f"The {source_count:,} potential main sources were checked before model calls using the independent arithmetic and rendered-text checks described above. "
          "That work is needed because a disagreement with a faulty expected answer would manufacture a model failure. The exact checker must also distinguish a wrong quantity from an unusable response, a malformed field or missing evidence. "
          "Here the generated records provide a known answer and visible rules, so a genuine value failure can be established without guessing what the model intended.\n\n"
          f"The calibrated collection produced {original['value_failure_cases']}/{original['n_attempted_cases']} genuine value failures. "
          f"Among its {len(usable)} usable replies, {quantities} have a wrong quantity and {other} other typed-field errors are recorded across the remaining fields. "
          "The field-error count can include several errors in one reply. This identifies what this sample makes difficult, rather than a general failure rate for the model. "
          "The clean records, fixed rules, text-only profile and one source generator define the scope of that finding.\n\n"
          f"Another attempt also matters: fresh retry recovers {fresh['value_correct_valid_schema']}/{p['n_pairs']} complete pairs, while the repair package recovers {repair['value_correct_valid_schema']}/{p['n_pairs']}. "
          f"The comparison turns on {p['repair_only']} repair-only and {p['fresh_only']} fresh-only successes, or {p['discordant_pairs']} disagreements; cases both methods solve cannot distinguish the two approaches. ")
    if p["n_pairs"]:
        text+=(f"The repair-minus-fresh difference is {p['difference_percentage_points']:.2f} percentage points, with a conditional 95% whole-pair bootstrap interval of {scale_report_interval(p)} pp. ")
    analysis=report["missing_outcomes"]; decision=analysis["amended_primary_decision"]
    text+=(f"The scheduled-cohort check separately enumerates all {decision['n_completions']} binary completions of {analysis['n_unavailable_outcomes']} unknown outcomes. "
           f"The positive-difference and exact-p-below-0.05 criterion is met in {decision['completions_meeting_criterion']}/{decision['n_completions']} completions. "
           "This compares the whole repair package, including the old answer and verified failed-field names, with fresh sampling. It does not identify which part of the package accounts for the difference.\n\n")
    good={arm:{r["semantic_hash"] for r in report["originals"]+report["interventions"]
               if r["split"]=="collection" and r["arm"]==arm and scale_report_accepted(r)}
          for arm in ("original",*SCALE_REPORT_ARMS)}
    union=set().union(*good.values()); overlap=good["fresh_retry"]&good["feedback_repair"]
    text+=(f"After full acceptance checks, the three arms provide {len(union)} distinct accepted collection sources. The two intervention arms overlap on {len(overlap)} accepted sources. "
           "Keeping both answers to the same source would increase record count without adding another solved order. Even the deduplicated count measures candidate correction data from one shared generator; no training step here has converted those records into a new skill.\n\n"
           "A follow-up would train on the verified correction records, compare against the same training budget using fresh-attempt records, and then test on unseen sources from separately written generators. "
           "That test should check exact answers and newly introduced errors without reusing the training sources or their generator rules. A claim that this process improves a frontier model would require a measured post-training gain on those new tasks; collecting accepted answers alone cannot supply that evidence.")
    return text


def scale_report_coverage_markdown(report):
    good={arm: {r["semantic_hash"] for r in report["originals"]+report["interventions"] if r["split"]=="collection" and r["arm"]==arm and scale_report_accepted(r)} for arm in ("original",*SCALE_REPORT_ARMS)}
    union=set().union(*good.values()); new=(good["fresh_retry"]|good["feedback_repair"])-good["original"]
    files=[]
    for arm,label in (("original","Original"),("fresh_retry","Fresh retry"),("feedback_repair","Feedback repair")):
        prefix=f"data/scale_v5/main/exports/{arm}/"
        files.append([label, f"[{len(good[arm])} accepted examples]({prefix}accepted_examples.jsonl.gz)",
                      "No intervention pairs" if arm=="original" else f"[{len(good[arm])} correct/wrong pairs]({prefix}value_preference_pairs.jsonl.gz)",
                      f"[Diagnostic rejection log]({prefix}rejected_examples.jsonl.gz)"])
    return (f"### Distinct usable correction data\n\nOriginals provide {len(good['original'])} fully accepted collection sources; fresh retry contributes {len(good['fresh_retry'])} accepted source answers and repair {len(good['feedback_repair'])}. "
            f"Their intervention overlap is {len(good['fresh_retry']&good['feedback_repair'])} sources. Deduplicating all three arms yields {len(union)} distinct accepted collection sources, including {len(new)} beyond original acceptance. "
            "The separate audit is excluded. Two successful answers for one source do not become two independently solved orders. Acceptance here requires the source-citation checks as well as correct values.\n\n"
            "A preference pair stores a verified correct follow-up and the actual wrong original answer to the same task. Its candidate and request IDs connect both answers to their raw caches. "
            "The rejection logs also retain service failures and unavailable attempts for accounting; those entries do not supply invented wrong answers.\n\n"+
            scale_report_table(["Arm","Accepted data","Preference data","Rejection record"],files)+
            "\n\nThe [deduplicated accepted corpus](data/scale_v5/main/exports/curated_unique.jsonl.gz) keeps one answer per source, preferring an accepted original, then feedback repair, then fresh retry. "
            "These are candidate correction and preference records. No model is trained and no held-out post-training gain is measured.")


def scale_report_usage_markdown(report):
    usage=report["metrics"]["usage"]; rows=[]
    for name, r in usage["by_arm"].items():
        rows.append([name, r["physical_cli_requests"], r["tokens"].get("input_tokens","Unknown"), r["tokens"].get("output_tokens","Unknown"),
                     f"{r['median_request_seconds']:.2f}" if r["median_request_seconds"] is not None else "Unknown", r["requests_with_observed_reconnects"]])
    missing=(report.get("missing_outcomes") or {}).get("n_unavailable_outcomes", 0)
    text=("### Calls, tokens and reproducible evidence\n\n"+scale_report_table(["Main request group","Request slots","Input tokens","Output tokens","Median seconds/request","Observed reconnects"], rows))
    text+=(f"\n\nThe complete main has {report['manifest']['physical_cli_requests']} distinct request slots and {report['manifest']['total_pilot_plus_main_requests']} pilot-plus-main scheduled slots. "
           f"Usage is present for {usage['requests_with_usage']} main requests and missing for {usage['requests_missing_usage']}. Dollar spend is unavailable, not zero. "
           "Input/output components are kept separate; cached-input and reasoning components must not be added again to totals that already include them. Equal arm request counts do not imply equal tokens or elapsed compute. "
           "These totals cover v5 only, not historical v1–v4. Source gzip files are saved once, while compressed full-request caches retain the observed stdin, replies, timestamps, CLI version/events and usage. "
           "Read a gzip JSON cache with gzip.open(path,'rt', encoding='utf-8') and json.load, or download/decompress the linked file. "
           "The normal report reads these files and makes no model calls. The frozen [preregistration](data/scale_v5/preregistration.json), [source locks](data/scale_v5/source_freeze.json) and [completed metrics](data/scale_v5/main/metrics.json) link the design to the evidence.")
    fresh=usage["by_arm"].get("fresh_retry"); repair=usage["by_arm"].get("feedback_repair")
    if fresh and repair:
        text+=(f" Fresh retry reports {fresh['tokens'].get('input_tokens', 'unknown')} input and {fresh['tokens'].get('output_tokens', 'unknown')} output tokens across {fresh['physical_cli_requests']} slots; "
               f"repair reports {repair['tokens'].get('input_tokens', 'unknown')} input and {repair['tokens'].get('output_tokens', 'unknown')} output tokens across {repair['physical_cli_requests']} slots. "
               "These are reported token components, not a dollar invoice or a guarantee of equal compute.")
    if missing:
        total=report['manifest']['total_pilot_plus_main_requests']
        text+=(f"\n\nThe {missing} interrupted slots were saved as pending before process launch. Their actual launch status is unknown. "
               f"There are {total-missing} terminal CLI records including pilot and {missing} unavailable attempt slots; actual physical starts are between {total-missing} and {total}. "
               "All scheduled slots count conservatively against the request budget. The frozen fields named physical_cli_requests retain slot counts for replay compatibility; they do not prove that every unavailable slot started. "
               "No finish time, return code, elapsed time, usage or CLI events are invented for those slots.")
    return text


def scale_report_missing_markdown(report):
    analysis=report.get("missing_outcomes")
    if not analysis or not analysis["n_unavailable_pairs"]: return ""
    n=analysis["n_scheduled_pairs"]; observed=analysis["n_observed_pairs"]
    missing=analysis["n_unavailable_pairs"]; decision=analysis["amended_primary_decision"]
    bounds=analysis["scheduled_difference_bounds_percentage_points"]
    unknown=analysis["n_unavailable_outcomes"]
    sixth=bool(report.get("intervention_interruption_amendment_006"))
    third=bool(report.get("intervention_interruption_amendment_003"))
    amendment_path=("intervention_resume_006/amendment_006.json" if sixth else
                    "intervention_resume_003/amendment_003.json" if third else "intervention_resume/amendment_002.json")
    amendment_name="sixth amendment" if sixth else "third amendment" if third else "second amendment"
    text=("### Controller interruption, unavailable outcomes and sensitivity\n\n"
          f"The pre-outcome ranking selected {n} pairs. Controller interruptions left {unknown} arm outcomes unavailable on {missing} sources, so the scientific recovery tables and figures use {observed} complete pairs. "
          f"The original accrual target shortfall is {report['scheduled_selection']['target_shortfall']}; {missing} unavailable pairs are a separate observation loss. "
          f"These {unknown} unknown responses are not model errors, extraction failures or provider failures. Their original pending cache bytes remain unchanged and no request was reissued. "
          f"The [{amendment_name}](data/scale_v5/{amendment_path}) fixes their identities and this missing-data analysis before continuation.\n\n")
    text+=(f"There are {analysis['n_wholly_unavailable_pairs']} wholly unavailable pairs and "
           f"{analysis['n_unavailable_pairs']-analysis['n_wholly_unavailable_pairs']} partially unavailable pairs. "
           "Every observed partner in a partial pair stays fixed in all scheduled-cohort sensitivity calculations. "
           "The exact source, arm and request identities are recorded in the linked amendment and full sensitivity JSON.\n\n")
    text+=(f"\n\nThe {observed}-pair comparison is available-case inference: it describes the sources with two observed outcomes. "
           "Missingness could depend on request duration or position in the interrupted wave, so it is not assumed random. "
           f"Across all {n} scheduled pairs, repair-minus-fresh recovery lies between {bounds[0]:.3f} and {bounds[1]:.3f} percentage points, regardless of the missing binary outcomes.\n\n"
           f"The analysis enumerates all 2^{unknown} = {decision['n_completions']} assignments of success or failure to the unknown outcomes, in frozen selected-source order. "
           "A completion lists the unknown cells in source order, fresh then repair; 1 means all-value success and 0 means failure. Observed counterparts remain fixed. These binary possibilities are not model answers or imputations. "
           "The amended claim requires a positive difference and exact two-sided McNemar p<0.05 for every completion.\n\n")
    all_completions=analysis["completion_sensitivity"]
    displayed=all_completions
    if len(all_completions)>16:
        chosen=[min(all_completions,key=lambda r:(r["difference_percentage_points"],r["completion_id"])),
                max(all_completions,key=lambda r:(r["difference_percentage_points"],r["completion_id"])),
                min(all_completions,key=lambda r:(r["exact_mcnemar_two_sided_p"],r["completion_id"])),
                max(all_completions,key=lambda r:(r["exact_mcnemar_two_sided_p"],r["completion_id"]))]
        displayed=list({r["completion_id"]:r for r in chosen}.values())
        text+=("The compact table shows completions with the smallest and largest recovery difference and exact p-value, removing repeated rows. "
               "Every completion, assignment and bootstrap interval is saved in the [full sensitivity results](data/scale_v5/presentation_results/missing_outcome_analysis.json).\n\n")
    text+=scale_report_table(["Hypothetical completion","Repair minus fresh (pp)","Exact p","Positive and p<0.05"],
          [[r["completion_id"], f"{r['difference_percentage_points']:.3f}", f"{r['exact_mcnemar_two_sided_p']:.6g}",
            "Yes" if r["primary_criterion_met"] else "No"] for r in displayed])
    conclusion=("The amended rule supports a conditional repair advantage." if decision["criterion_met"] else
                "The scheduled-cohort result is inconclusive under the amended rule; no repair advantage is claimed.")
    text+=f"\n\n{decision['completions_meeting_criterion']}/{decision['n_completions']} hypothetical completions meet the criterion. "+conclusion
    envelope=analysis.get("completion_bootstrap_endpoint_ranges")
    if envelope:
        lo, hi=envelope["lower_endpoint"], envelope["upper_endpoint"]
        text+=(f" Across the completions, lower 95% bootstrap endpoints range from {100*lo[0]:.3f} to {100*lo[1]:.3f} pp; "
               f"upper endpoints range from {100*hi[0]:.3f} to {100*hi[1]:.3f} pp. Each uses the frozen {analysis['bootstrap_draws']:,} whole-pair resamples and seed {analysis['bootstrap_seed']}; these endpoint ranges are sensitivity summaries, not a new confidence interval.")
    text+=(" The frozen operational metrics retain all scheduled slots and count unobserved success as absent for execution accounting. "
           "Their nominal primary_decision field is preserved for replay, but is not the amended scientific decision. "
           "No unavailable source enters the recovery categories, worked cases, numeric-error or scenario-recovery denominators.")
    return text



def scale_report_chart_specs(report):
    if report["state"]!="complete": return []
    m=report["metrics"]; p=m["paired_value_recovery"]; s=report["selection"]; cfg=report["protocol"]["config"]
    arms={r["arm"]: r for r in m["interventions"]}; b=m["original_collection"]; a=m["audit"]
    five=[r["primary_positive_direction_power_by_n_pairs"]["600"] for r in report["power"]["grid"]["rows"] if r["true_recovery_difference"]==.05]
    numeric=scale_report_numeric(report); families=scale_report_family_rows(report); loov=scale_report_leave_one_out(report)
    differences=[r["difference_pp"] for r in loov if r["n"]]
    difference_label=f"{p['difference_percentage_points']:.2f}" if p["n_pairs"] else "unavailable"
    descriptions={
      "nominal_power.png": f"The x-axis is the planned number of selected failure pairs; the y-axis is the probability of a positive repair difference passing the exact two-sided 5% test under the frozen assumptions. Solid lines assume five points, dashed lines ten; colors show 25%, 35% and 50% discordance. At 600 pairs, five-point power is {100*min(five):.2f}–{100*max(five):.2f}%. These are nominal planning values for independent cases within one generator, not measured recovery or assurance of detecting a small gain.",
      "accrual.png": f"Each point is a completed original tranche. The axes count called collection sources and accrued genuine value-failure cases. The 600-failure reference controls original accrual only. {s['n_accrued_collection']} called sources produced {s['n_eligible_failures']} eligible failures, from which {len(report.get('scheduled_selection', s)['selected_case_ids'])} were selected; target shortfall is {s['target_shortfall']}. {p['n_pairs']} complete pairs enter scientific recovery summaries; observation loss does not change accrual shortfall. Uncalled potential sources do not enter results; no intervention outcome affected stopping.",
      "baseline_recovery.png": f"Bar heights are all-value success percentages, with exact counts written on every bar. The left panel counts all original sources: {b['value_correct_valid_schema']}/{b['n_attempted_cases']} collection and {a['value_correct_valid_schema']}/{a['n_attempted_cases']} fixed audit. The right panel conditions on the same {p['n_pairs']} original failures: fresh retry {arms['fresh_retry']['value_correct_valid_schema']}/{arms['fresh_retry']['n_attempted_cases']}, repair {arms['feedback_repair']['value_correct_valid_schema']}/{arms['feedback_repair']['n_attempted_cases']}. The panels have different denominators; the right bars are not before/after accuracy gains.",
      "paired_outcomes.png": f"Rows are fresh-retry outcomes and columns repair outcomes; each source belongs to one cell. Both succeed on {p['both_success']}, repair alone on {p['repair_only']}, fresh alone on {p['fresh_only']}, and neither on {p['neither_success']}. Difference is {difference_label} pp, 95% interval {scale_report_interval(p)} pp. Only the {p['discordant_pairs']} off-diagonal cases determine the exact test; shared successes show overlap in corrected sources.",
      "numeric_errors.png":"Dots show absolute errors for selected originals and their two arms; black marks are medians including zero-error successes. Quantity is individual items; price is cents/item. "+"; ".join(f"{r['stage']}: quantity median {r['median']}, maximum {r['maximum']}, numeric coverage {r['n_numeric']}/{r['n']}" for r in numeric if r['field']=='quantity_units')+". Non-numeric outputs remain failed cases outside these dots. A labelled symlog scale preserves zero and compresses large errors. The table above also records price-error magnitudes.",
      "variants.png":"The upper panel shows original failure percentages; the lower panel shows fresh and repair recovery percentages on each variant's selected failures. Exact subgroup counts appear above. "+(f"The smallest selected group has {min(r['paired_n'] for r in families)} pairs and the largest {max(r['paired_n'] for r in families)}. " if families else '')+"Shared rules and unequal subgroup sizes prevent causal explanations or independent-task replication claims.",
      "leave_one_variant_out.png":("Each point removes one variant and recomputes the paired difference on retained sources. The vertical line is the full-sample difference. Retained differences range from "+f"{min(differences):.2f} to {max(differences):.2f} pp. " if differences else "No retained pairs exist for this sensitivity. ")+"These subsets overlap; the plot describes composition sensitivity and does not supply six independent program replications.",
    }
    if report["examples"]:
        example=next((e for e in report["examples"] if e["case_id"] in set(s["selected_case_ids"])), report["examples"][0])
        case=report["cases"][example["case_id"]]; trace=scale_calculation_trace(case); old, arms2=scale_report_example_rows(report, case["case_id"])
        q=old["response"].get("answer", {}).get("quantity_units") if type(old["response"])is dict else None
        descriptions["quantity_audit.png"]=(f"This is a source-truth panel for {case['case_id']}, not a model reasoning trace. Approved demand {trace['ordered_units']:,} minus net dispatch {trace['net_dispatched_units']:,} leaves {trace['open_units']:,} open units; the original returned {q}. "
            "The right table shows a few selected event revisions and their signed contributions. Negative accepted returns reopen demand; excluded or reversed shipments contribute zero. Full arithmetic uses the entire audited packet, not just these displayed rows.")
    # Keep readable spaces in generated numerical prose without altering IDs.
    return [{"name": name,"path":"figures/scale_v5/"+name,"interpretation": text} for name, text in descriptions.items()]


def scale_report_figures(report, root=None, write=False):
    """No plots or writes before the explicit completed-intervention gate."""
    if report["state"]!="complete": return []
    import matplotlib as _sr_mpl
    import matplotlib.pyplot as plt
    specs=scale_report_chart_specs(report); lookup={r["name"]: r for r in specs}; root=_SRPath(root or report["root"])
    if write:(root/"figures"/"scale_v5").mkdir(parents=True, exist_ok=True)
    m=report["metrics"]; p=m["paired_value_recovery"]; s=report["selection"]; cfg=report["protocol"]["config"]
    def save(name, fig):
        if write: fig.savefig(root/lookup[name]["path"], bbox_inches="tight")
        plt.close(fig)
    # Reset every rendering default, then apply the one shared v5 style. Backend
    # is execution infrastructure: rc_context deliberately does not restore it.
    # Leaving it alone avoids changing the notebook's backend after these plots.
    defaults={key: value for key, value in _sr_mpl.rcParamsDefault.items() if key!="backend"}
    with plt.rc_context(rc={**defaults, **SCALE_REPORT_STYLE}):
        fig, (ax, legend_ax)=plt.subplots(2,1, figsize=(10,6.8), gridspec_kw={"height_ratios":[4.8,1.4]})
        colors={.25:"#3c795d",.35:"#2584a5",.5:"#b8662c"}
        for row in report["power"]["grid"]["rows"]:
            if row["true_recovery_difference"] not in {.05,.1}: continue
            values=row["primary_positive_direction_power_by_n_pairs"]; xs=sorted(int(n) for n in values)
            ax.plot(xs,[100*values[str(n)] for n in xs], marker="o", linestyle="-" if row["true_recovery_difference"]==.05 else "--",
                    color=colors[row["discordance_probability"]], label=f"True gain {100*row['true_recovery_difference']:.0f} pp; discordance {100*row['discordance_probability']:.0f}%")
        ax.axhline(80, color="#777777", linestyle=":", label="80% planning reference")
        if p["n_pairs"]: ax.axvline(p["n_pairs"], color="#333333", linestyle=":", label=f"Attained {p['n_pairs']} pairs")
        ax.set(xlabel="Selected original-failure case pairs", ylabel="Nominal positive-direction power (%)", ylim=(0,103),
               title="Nominal power for five points remains limited at 600 pairs")
        legend_ax.axis("off")
        handles,labels=ax.get_legend_handles_labels()
        legend_ax.legend(handles, labels, loc="center", fontsize=9, ncol=2, frameon=False, columnspacing=1.8)
        save("nominal_power.png", fig)

        fig, ax=plt.subplots(figsize=(10,5))
        history=report["accrual_history"]
        ax.plot([0]+[r["n_accrued_cases"] for r in history],[0]+[r["n_accrued_value_failures"] for r in history], marker="o", color=SCALE_REPORT_COLORS["original"])
        for row in history: ax.annotate(f"{row['n_accrued_value_failures']}",(row["n_accrued_cases"], row["n_accrued_value_failures"]), xytext=(0,8), textcoords="offset points", ha="center", fontsize=9)
        ax.axhline(cfg["target_failures"], color=SCALE_REPORT_COLORS["feedback_repair"], linestyle="--", label=f"Target {cfg['target_failures']} eligible failures")
        ax.axvline(cfg["collection_cap"], color="#777777", linestyle=":", label=f"Cap {cfg['collection_cap']} collection sources")
        ax.set(xlabel="Called collection originals", ylabel="Accrued genuine value-failure cases", xlim=(0, cfg["collection_cap"]*1.03),
               title=f"{s['n_accrued_collection']} originals yielded {s['n_eligible_failures']} eligible failures\n{len(report.get('scheduled_selection', s)['selected_case_ids'])} pairs scheduled; {p['n_pairs']} observed")
        ax.legend(fontsize=9); save("accrual.png", fig)

        fig, axes=plt.subplots(1,2, figsize=(10,5.4), sharey=True)
        groups=[[("Collection", m["original_collection"]),("Fixed audit", m["audit"])],[(r["arm"].replace("_"," "), r) for r in m["interventions"]]]
        for ax, rows, title in zip(axes, groups,("All called\noriginal sources","Only selected\noriginal failures")):
            heights=[scale_report_percent(r["value_correct_valid_schema"], r["n_attempted_cases"]) for _, r in rows]
            bars=ax.bar(range(len(rows)), heights, color=[SCALE_REPORT_COLORS["original"]]*2 if ax is axes[0] else [SCALE_REPORT_COLORS["fresh_retry"], SCALE_REPORT_COLORS["feedback_repair"]])
            ax.set_xticks(range(len(rows)),[name.replace(" ","\n") for name,_ in rows]); ax.set_ylim(0,112); ax.set_title(title)
            for bar,(_, r) in zip(bars, rows):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2 if r["n_attempted_cases"] else 2,
                        f"{r['value_correct_valid_schema']}/{r['n_attempted_cases']}" if r["n_attempted_cases"] else "No pairs", ha="center")
        axes[0].set_ylabel("All seven values correct (%)")
        fig.suptitle("Original accuracy and conditional recovery\nuse different denominators")
        save("baseline_recovery.png", fig)

        fig, ax=plt.subplots(figsize=(7.8,5.8)); cells=[[p["neither_success"], p["repair_only"]],[p["fresh_only"], p["both_success"]]]
        im=ax.imshow(cells, cmap="Blues", vmin=0)
        for y, row in enumerate(cells):
            for x, n in enumerate(row): ax.text(x, y, str(n), ha="center", va="center", fontsize=23, color="white" if n>max(max(v) for v in cells)/2 else "#222222")
        ax.set_xticks([0,1],["Repair fails","Repair succeeds"]); ax.set_yticks([0,1],["Fresh fails","Fresh succeeds"])
        ax.set_title(f"Repair-only {p['repair_only']} versus fresh-only {p['fresh_only']}\nDifference {p['difference_percentage_points']:.2f} pp across {p['n_pairs']} pairs" if p["n_pairs"] else "No eligible paired failures")
        fig.colorbar(im, ax=ax, label="Distinct source cases"); save("paired_outcomes.png", fig)

        numeric=scale_report_numeric(report); fig, axes=plt.subplots(1,2, figsize=(11,6))
        for ax, field, unit in zip(axes,("quantity_units","unit_price_cents"),("individual units","cents per unit")):
            groups=[r for r in numeric if r["field"]==field]
            for x, row in enumerate(groups):
                jitter=[x+((i%17)-8)/65 for i in range(len(row["values"]))]
                ax.scatter(jitter, row["values"], s=12, alpha=.4, color=SCALE_REPORT_COLORS[row["stage"]], rasterized=True)
                if row["median"] is not None: ax.hlines(row["median"], x-.27, x+.27, color="black", linewidth=2)
            maximum=max((r["maximum"] or 0 for r in groups), default=0)
            if maximum>1000: ax.set_yscale("symlog", linthresh=1)
            ax.set_xticks(range(len(groups)),[r["stage"].replace("_","\n")+f"\n{r['n_numeric']}/{r['n']} numeric" for r in groups], fontsize=10)
            ax.set_ylabel("Absolute error ("+unit+")"+("; symlog" if maximum>1000 else ""))
            ax.set_title(field+f"\nMaximum observed error {maximum:,}")
        fig.suptitle("Exact numeric errors and numeric coverage\non the selected cohort"); save("numeric_errors.png", fig)

        families=scale_report_family_rows(report); fig, axes=plt.subplots(2,1, figsize=(11,8))
        x=list(range(len(families))); labels=[r["family"].replace("_","\n") for r in families]
        axes[0].bar(x,[scale_report_percent(r["original_failures"], r["original_n"]) for r in families], color=SCALE_REPORT_COLORS["original"])
        for i, r in enumerate(families):
            axes[0].text(i, scale_report_percent(r["original_failures"], r["original_n"])+1 if r["original_n"] else 1,
                         f"{r['original_failures']}/{r['original_n']}" if r["original_n"] else "No sources", ha="center", fontsize=9)
        axes[0].set(ylabel="Original value failures (%)", title="Original failure counts differ across overlapping scenario variants")
        for offset, arm in [(-.19,"fresh_retry"),(.19,"feedback_repair")]:
            axes[1].bar([i+offset for i in x],[scale_report_percent(r[arm], r["paired_n"]) for r in families], width=.36, color=SCALE_REPORT_COLORS[arm], label=arm.replace("_"," "))
        axes[1].set(ylabel="Conditional value recovery (%)", ylim=(0,112), title="Paired recovery within each variant; shared generator, no causal ablation")
        for ax in axes: ax.set_xticks(x, labels)
        axes[1].legend(); save("variants.png", fig)

        loov=scale_report_leave_one_out(report); fig, ax=plt.subplots(figsize=(10,5.8))
        for i, row in enumerate(loov):
            if row["n"]: ax.scatter(row["difference_pp"], i, s=65, color=SCALE_REPORT_COLORS["feedback_repair"]); ax.annotate(f"N={row['n']}",(row["difference_pp"], i), xytext=(9,0), textcoords="offset points", va="center", fontsize=9)
        if p["n_pairs"]: ax.axvline(p["difference_percentage_points"], color="#444444", linestyle="--", label=f"Full cohort {p['difference_percentage_points']:.2f} pp")
        ax.axvline(0, color="#999999", linewidth=.8); ax.set_yticks(range(len(loov)),[r["omitted_family"] for r in loov]); ax.invert_yaxis()
        ax.set(xlabel="Repair minus fresh recovery (percentage points)", title="Leaving out one variant describes composition sensitivity")
        if p["n_pairs"]: ax.legend(fontsize=9)
        ax.margins(x=.3); save("leave_one_variant_out.png", fig)

        if "quantity_audit.png" in lookup:
            example=next((e for e in report["examples"] if e["case_id"] in set(s["selected_case_ids"])), report["examples"][0])
            case=report["cases"][example["case_id"]]; trace=scale_calculation_trace(case); old,_=scale_report_example_rows(report, case["case_id"])
            shipped=sum(max(e["net_dispatched_units"],0) for e in trace["events"]); returned=-sum(min(e["net_dispatched_units"],0) for e in trace["events"])
            fig, axes=plt.subplots(1,2, figsize=(12,5.8), gridspec_kw={"width_ratios":[1,1.5]})
            amounts=[trace["ordered_units"], shipped, returned, trace["open_units"]]
            bars=axes[0].bar(range(4), amounts, color=["#63758c","#b8662c","#2584a5","#3c795d"])
            axes[0].set_xticks(range(4),["Ordered","Shipments","Returns","Open"], rotation=20); axes[0].set_ylabel("Individual units")
            for bar, n in zip(bars, amounts): axes[0].text(bar.get_x()+bar.get_width()/2, n+max(amounts)*.02, f"{n:,}", ha="center", fontsize=9)
            axes[0].set_ylim(0, max(amounts)*1.16)
            event_rows=[]
            for reason in ("shipment","accepted_return","reversed_shipment","void","future_occurrence","other_line_allocation"):
                event=next((e for e in trace["events"] if e["reason"]==reason), None)
                if event: event_rows.append([event["event_id"], event["selected_revision"], event["reason"].replace("_"," "), event["net_dispatched_units"]])
            axes[1].axis("off"); table=axes[1].table(cellText=event_rows, colLabels=["Event","Rev","Selected status","Net units"], loc="center", cellLoc="left", colWidths=[.18,.1,.49,.23]); table.auto_set_font_size(False); table.set_fontsize(9); table.scale(1,1.8)
            original_q=old["response"].get("answer", {}).get("quantity_units") if type(old["response"])is dict else None
            displayed_quantity=f"{original_q:,}" if type(original_q)is int else str(original_q)
            fig.suptitle(f"Source truth: {trace['open_units']:,} open units; original returned {displayed_quantity}\n {case['case_id']}")
            save("quantity_audit.png", fig)
    return specs


def scale_report_workflow(report):
    complete=report["state"]=="complete"; ladder=report["pilot_ladder"]
    pilot_n=ladder["physical_cli_requests"] if ladder else "up to 32"
    n=report["metrics"]["original_collection"]["n_attempted_cases"] if complete else "512 then fixed 256 chunks, cap 2,048"
    pairs=len(report.get("scheduled_selection", report["selection"])["selected_case_ids"]) if complete else "target 600, actual pending"
    slots=2*pairs if complete else "target 1,200, actual pending"
    availability=(f"{report['missing_outcomes']['n_observed_pairs']} complete pairs; {report['missing_outcomes']['n_unavailable_pairs']} unavailable pairs" if complete and report.get("missing_outcomes") else "wait for terminal observation records")
    tier=report["protocol"]["selected_tier"] if report["protocol"] else "128 or 192"
    return f"""```mermaid
flowchart TD
    source["Frozen generator, rules and seeds<br/>all 32 potential pilot sources fully audited"]
    source --> pilot["Sol, high reasoning via codex exec<br/>{pilot_n} one-case pilot requests<br/>returns seven typed fields + citations"]
    pilot --> main_sources["Chosen tier: freeze all 2,144 potential main sources<br/>independent rendered-text audits before main calls"]
    main_sources --> originals["Sol, high reasoning via codex exec<br/>{n} collection originals; tier {tier}<br/>returns seven typed fields + citations"]
    originals --> accrue["Accrue by genuine original value failures only<br/>freeze seeded ranking and selected {pairs} sources"]
    accrue --> audit["Sol, high reasoning via codex exec<br/>96 fixed audit originals, after selection freezes<br/>returns seven typed fields + citations"]
    audit --> gate["Wait: all called originals + audit terminal<br/>source and original-output review before interventions"]
    gate --> fresh["Sol, high reasoning fresh retry via codex exec<br/>{pairs} scheduled request slots, one per selected source<br/>returns seven typed fields + citations"]
    gate --> repair["Sol, high reasoning repair package via codex exec<br/>{pairs} scheduled request slots<br/>same source + exact old answer + failed-field flags"]
    fresh --> wait["{slots} total intervention request slots<br/>four-worker waves: both arms for two sources<br/>no sibling sharing; wait for final availability before efficacy"]
    repair --> wait
    wait --> available["{availability}<br/>preserve unknown outcomes separately"]
    available --> score["Exact typed values, citations and numeric harms<br/>complete-pair difference/CI/test + all-completion sensitivity<br/>unique accepted sources; no model training"]
```"""


def scale_report_intro():
    return ("A purchasing team needs to know how much of an order is still open. A dispatch register can contain an original shipment, a correction to that shipment, and a return recorded several days later. "
            "Counting every row as a new movement would give the wrong balance. Another order or line can carry the same item code, so matching the item name is not enough.\n\n"
            "For an illustrative small order, suppose 1,000 individual units were approved. A selected shipment allocates 72 units to the target line and an accepted return reopens 24. The open balance is 1,000 - (72 - 24) = 952 units. "
            "This is a teaching calculation, not a measured model response. In the actual packets, changing packaging and allocation schedules mean the return must use its original shipment's dated conversion and selected revision.\n\n"
            "A useful answer identifies the order and item code (SKU), open individual-unit quantity, unit price in cents, currency, ship date and order status. It also cites the source groups supporting those seven fields. "
            "The ordinary approach joins the order, approvals, item master, allocation schedule, pricing and warehouse ledger in a database, then checks the arithmetic. A text-only language model has to carry out the same explicit reconciliation across a long packet. "
            "One missed correction can leave an otherwise useful answer with a wrong quantity. A wrong price can approve an invoice at the wrong unit amount.\n\n"
            "This follow-up asks whether a failed answer is more often corrected by another fresh attempt or by a repair package containing the old answer and verified failed-field names. Both request the same Sol alias (gpt-6.1-sol) at high reasoning effort through codex exec. We perform no training here; the provider alias is not an immutable model snapshot. "
            "The data are fresh code-generated records with exact independently checked truth; individual cases are not authored by a model. The comparison produces candidate correction data, not a trained or improved model.")


def scale_report_models_markdown(report):
    protocol=report.get("protocol") or {}
    model=protocol.get("model","gpt-6.1-sol")
    effort=protocol.get("reasoning_effort","high")
    rows=[["GPT Sol (measured solver)",f"Requested {model}; mutable provider alias, immutable revision unavailable",
           "OpenAI; codex exec", "Not published",f"{effort} reasoning; one source/request; tools disabled; 900-second timeout",
           "The capable solver whose failed answers are compared under fresh retry and the repair package"],
          ["GPT Luna (process reviewer only)","Requested gpt-6-luna; immutable revision unavailable",
           "OpenAI; collaboration spawn_agent during authoring, outside measured CLI requests", "Not published",
           "High reasoning; source, method and continuation review",
           "Independent review of the study process; no Luna task-solving score is reported"]]
    return ("### Model and settings\n\n"+
            scale_report_table(["Model and role","Pinned version or version limit","Provider and call path","Size and precision","Output settings","Why included"],rows)+
            "\n\nBoth measured arms request the same Sol alias and reasoning setting. The saved requests pin that name and profile, rather than an immutable provider weight version. "
            "Luna is an authoring reviewer, outside experiment request and token counts. The requested reviewer name was gpt-6.1-luna; the available reviewer ID was gpt-6-luna. "
            "The code-generated cases have no model-authored item text. Freshness follows their experiment creation, rather than an assumed model training cutoff.")


def scale_report_render(report):
    intro=scale_report_intro(); complete=report["state"]=="complete"
    if not complete:
        history=report["accrual_history"]
        progress=(f"The last completed original tranche has {history[-1]['n_accrued_cases']} collection sources and {history[-1]['n_accrued_value_failures']} genuine value failures." if history else "No completed original tranche is saved yet.")
        pending="The final interventions_complete marker is absent. Partial intervention files/caches are deliberately unopened; no paired efficacy estimate or final figure is produced."
        text="\n\n".join(part for part in [intro,"### Study status\n\n"+pending+" "+progress,
                         scale_report_infrastructure_markdown(report), scale_report_followup_transport_markdown(report), scale_report_workflow(report),
                         scale_report_pilot_markdown(report), scale_report_power_markdown(report)] if part)
        return {"state":"pending","pending_reason": pending,"markdown": text,"readme_appendix": text,"headline":"V5 paired main results are pending; no repair advantage is claimed.","summary": {"complete": False,"infrastructure_amended": report.get("infrastructure_amendment") is not None},"example_case_ids":[],"figures":[]}
    m=report["metrics"]; p=m["paired_value_recovery"]; s=report["selection"]; cfg=report["protocol"]["config"]
    analysis=report["missing_outcomes"]; scheduled=analysis["n_scheduled_pairs"]
    fresh=next(r for r in m["interventions"] if r["arm"]=="fresh_retry"); repair=next(r for r in m["interventions"] if r["arm"]=="feedback_repair")
    headline=(f"Fresh retry recovered {fresh['value_correct_valid_schema']}/{p['n_pairs']} selected failures; the repair package recovered {repair['value_correct_valid_schema']}/{p['n_pairs']}. "
              + (f"Difference {p['difference_percentage_points']:.2f} percentage points, 95% interval {scale_report_interval(p)} percentage points." if p["n_pairs"] else "No eligible pairs were available."))
    readable,readable_note=scale_report_readable_comparison(report)
    if any(row["n"]!=row["readable"] for row in readable.values()):
        headline+=(" Unreadable outcomes: "+"; ".join(f"{arm.replace('_',' ')} {row['n']-row['readable']}/{row['n']}" for arm,row in readable.items())+". "+readable_note)
    if analysis["n_unavailable_pairs"]:
        bounds=analysis["scheduled_difference_bounds_percentage_points"]
        decision=analysis["amended_primary_decision"]
        headline+=(f" These are {p['n_pairs']} complete pairs out of {scheduled} scheduled, with {analysis['n_unavailable_pairs']} unavailable pairs. "
                   f"The scheduled-cohort difference is bounded by {bounds[0]:.3f} to {bounds[1]:.3f} percentage points. "
                   +( "Every binary completion meets the amended repair-advantage rule." if decision["criterion_met"] else
                      "The scheduled-cohort result is inconclusive under the amended rule; no repair advantage is claimed."))
    summary=("### Question, data and headline\n\n"+headline+"\n\n"
             f"Collection called {s['n_accrued_collection']} originals, producing {s['n_eligible_failures']} genuine value failures; {scheduled} pairs were frozen by the pre-outcome ranking. "
             f"Target shortfall is {s['target_shortfall']}; stopping reason: {s['stopping_reason']}. The 96-source audit is excluded from failure accrual and pairing. "
             f"Recovery figures describe the {p['n_pairs']} observed complete pairs. The amended primary decision also checks every binary completion of the unknown scheduled outcomes. Shared templates and failure-count stopping make the inference conditional; a result here does not measure an ordinary production stream or model training.\n\n")
    rules=("### Source rules and material checks\n\nP01 is the signed order; P02 is partial approvals; P03/P04 are dated handling factors and line allocations; P05 is pricing; P06 is the revision register. "
           "Line scope outranks order defaults, then authority, effective timestamp and revision resolve each commercial field independently. Both recorded and effective timestamps must be available by the inclusive October 26 noon cutoff. "
           "Movement identity is logical Event ID: choose the highest recorded-by-cutoff revision before applying occurrence/state tests. A selected VOID does not restore the older row. Timely active reversals remove their referenced selected shipment once. "
           "Returns use the selected original shipment's date, SKU, handling unit and allocation version. Open quantity is approved demand minus allocated shipments plus accepted returns.\n\n"
           "Price tiers use approved demand before movements. Divide gross pack cents by pricing pack units, apply two rebates sequentially, add unit fee and converted pack fee, subtract unit credit, then round once half-up to integer cents. "
           "All answer-relevant facts and joins are visible. All 32 potential pilot sources and every 2,144 potential selected-tier main source were checked before their corresponding calls using full text reconstruction, constructor Decimal, independent Fraction, separately parsed text/SQL/Decimal and separate text/Fraction checks. "
           "Full traces record chosen revisions, exclusions, historical rates/shares and exact price arithmetic. Source IDs and normalized-fact hashes were checked against prior corpora/pilots. This prevents exact recorded overlap, not broad task-program novelty.\n\n"
           "The scope remains clean, active-only high-volume procurement: roughly 110,000–128,000 ordered units and 128/192 logical shipments concentrated on October 18/22/23, with return/correction controls through October 26. "
           "Tools are disabled by the CLI profile. It tests text-only reconciliation rather than an accountant using a calculator/database. Regular control patterns and complete rules are deliberate; OCR, missing contracts, hidden policy, tax, currency conversion and unresolved approval conflicts are outside scope. "
           "Longer histories do not guarantee failures. [EvoEnv](https://arxiv.org/abs/2605.14392) (Shi et al., 2026) motivates executable generators, staged semantic validation and solver-relative calibration; this illustrates data-workflow steps without reproducing its reinforcement-learning training or downstream evaluation.")
    accrual=("### How original failures were accrued\n\n"
             f"The frozen plan began with {cfg['n_initial']} originals and added fixed {cfg['chunk_size']}-source tranches only while eligible original failures remained below {cfg['target_failures']}, capped at {cfg['collection_cap']}. "
             f"Actual called count was {s['n_accrued_collection']}; eligible failures {s['n_eligible_failures']}; selected pairs {scheduled}; observed complete pairs {p['n_pairs']}. "
             f"There are {len(s['uncalled_collection_case_ids'])} uncalled potential collection sources. They are absent from response denominators. No repair outcome affected continuation, stopping or ranking. "
             "Audit calls started after selection froze; intervention calls waited for all originals/audit and source review. Each four-request wave contains both arms for two sources with randomized within-wave order and no result sharing.")
    specs=scale_report_chart_specs(report)
    figures="### Figures and how to read them\n\n"+"\n\n".join(f"![{r['name'].replace('_',' ').replace('.png','')} ]({r['path']})\n\n {r['interpretation']}" for r in specs)
    limitations=("### What the comparison can support\n\nThis measures the prior-answer-plus-feedback package against another attempt on genuine selected failures. The verifier is privileged because it knows the fictional truth, even when its flags omit expected values. "
                 "Another attempt can recover errors without feedback, so only paired disagreements address the package comparison. Shared successes must be deduplicated when counting correction data. "
                 "All-value rejection can hide partial repairs; newly wrong and worsened fields therefore remain visible.\n\n"
                 "A statistically clear conditional difference would concern answer correction, with no model training performed in this study. No held-out post-training accuracy is measured. The same requested provider alias can change during collection; we do not guarantee unchanged provider weights. Alias/profile behavior, one generator, active-only clean tables, stopping on failure count and selected failures limit generalization. "
                 "A small or uncertain difference cannot establish equivalence. The saved plan already shows limited power for five points even at 600 pairs; do not treat an insignificant result or a degenerate bootstrap as proof that the arms are identical.")
    text="\n\n".join([intro, summary, scale_report_workflow(report), scale_report_models_markdown(report), rules, scale_report_pilot_markdown(report), scale_report_power_markdown(report), accrual,
                         scale_report_infrastructure_markdown(report), scale_report_followup_transport_markdown(report), scale_report_missing_markdown(report),
                         scale_report_results_markdown(report), scale_report_error_markdown(report), scale_report_model_improvement_markdown(report), scale_report_family_markdown(report), figures,
                         scale_report_examples_markdown(report), scale_report_prompt_markdown(report), scale_report_coverage_markdown(report), limitations, scale_report_usage_markdown(report)])
    return {"state":"complete","pending_reason": None,"markdown": text,"readme_appendix": text,"headline": headline,
            "summary": {"complete": True,"infrastructure_amended": report.get("infrastructure_amendment") is not None,
                       "selected_tier": report["protocol"]["selected_tier"],"collection": m["original_collection"],"audit": m["audit"],
                       "n_scheduled_pairs": scheduled,"n_observed_pairs": p["n_pairs"],"n_unavailable_pairs": analysis["n_unavailable_pairs"],
                       "n_unavailable_outcomes": analysis["n_unavailable_outcomes"],
                       "n_incomplete_pairs": analysis["n_incomplete_pairs"],
                       "n_wholly_unavailable_pairs": analysis["n_wholly_unavailable_pairs"],
                       "n_completions": analysis["n_completions"],
                       "amended_primary_decision": analysis["amended_primary_decision"],
                       "completion_sensitivity": analysis["completion_sensitivity"],
                       "scheduled_difference_bounds_percentage_points": analysis["scheduled_difference_bounds_percentage_points"],
                       "n_pairs": p["n_pairs"],"paired": p,"target_shortfall": s["target_shortfall"],"fresh_recovered": fresh["value_correct_valid_schema"],
                       "repair_recovered": repair["value_correct_valid_schema"]},"example_case_ids":[e["case_id"] for e in report["examples"]],
            "absent_categories":[SCALE_REPORT_LABELS[k] for k, v in report["categories"].items() if not v],"figures": specs}
