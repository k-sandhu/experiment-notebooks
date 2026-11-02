"""Four actual completed v5 pilot examples. Never reads main/intervention data."""
from collections import Counter
from pathlib import Path
import argparse
import copy
import gzip
import hashlib
import json

AUTHORING=Path(__file__).resolve().parent
_ARCHIVED_PILOT_ROOT=AUTHORING.parent/"pilot"
_ARCHIVED_LAYOUT=_ARCHIVED_PILOT_ROOT.is_dir()
DEFAULT_PILOT_ROOT=(_ARCHIVED_PILOT_ROOT if _ARCHIVED_LAYOUT else
                    AUTHORING.parent/"experiment_notebooks"/"notebooks"/"23-synthetic-data-curation"/"data"/"scale_v5"/"pilot")
DEFAULT_OUTPUT_PATH=(AUTHORING.parent/"pilot_examples.json" if _ARCHIVED_LAYOUT else AUTHORING/"scale_pilot_examples.json")


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))


def read_json(path):
    path=Path(path)
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",encoding="utf-8-sig") as stream:return json.load(stream)


def read_rows(path):
    path=Path(path)
    if not path.exists():path=path.with_name(path.name+".gz")
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",encoding="utf-8-sig") as stream:return [json.loads(line) for line in stream if line.strip()]


def table_lines(document,source_id):
    lines=document.splitlines();start=lines.index("BEGIN TABLE "+source_id);end=lines.index("END TABLE "+source_id)
    return lines[start+1],[line for line in lines[start+2:end] if line]


def selected_record(record,trace_event):
    choices=[r for r in record["ledger"] if r["event_id"]==trace_event["event_id"] and
             r["row_revision"]==trace_event["selected_revision"] and r["recorded_at"]<=record["cutoff"]]
    distinct={canonical(r):r for r in choices}
    if len(distinct)!=1:raise ValueError("Nonunique selected visible row")
    return next(iter(distinct.values()))


def literal_excerpts(case,trace):
    record=case["source_record"];by_id={e["event_id"]:e for e in trace["events"]}
    selected=[]
    shipment=next((e for e in trace["events"] if e["reason"]=="shipment" and e["net_dispatched_units"]),None)
    returned=next((e for e in trace["events"] if e["reason"]=="accepted_return" and e["net_dispatched_units"]),None)
    removed=next((e for e in trace["events"] if e["reason"]=="reversed_shipment"),None)
    for event in (shipment,returned,by_id[returned["reference"]] if returned else None,removed):
        if event and event["event_id"] not in {e["event_id"] for e in selected}:selected.append(event)
    if removed:
        control=next((e for e in trace["events"] if e["reason"]=="reversal_control" and e["reference"]==removed["event_id"]),None)
        if control:selected.append(control)
    rate_keys=set();allocation_keys=set()
    for event in selected:
        if "uom_effective_from" not in event:continue
        ship=by_id[event["reference"]] if event["kind"]=="RETURN" else event
        physical=selected_record(record,ship)
        rate_keys.add((physical["sku"],physical["uom"],event["uom_effective_from"]))
        allocation_keys.add((physical["allocation"],event["allocation_effective_from"]))
    current_approvals={v["approval"] for v in trace["term_winners"].values()}
    current_approvals.update({"AP-04","AP-05","AP-06"})
    chosen_rows={e["event_id"]:canonical(selected_record(record,e)) for e in selected}
    excerpts={}
    for source in ("P01","P02","P03","P04","P05","P06"):
        columns,rows=table_lines(case["document"],source);kept=[]
        for line in rows:
            cells=[v.strip() for v in line.split(" | ")]
            use=(source=="P01" and cells[0] in {record["target_line_id"],"L07"}) or (
                source=="P02" and cells[0] in current_approvals) or (
                source=="P03" and tuple(cells[:3]) in rate_keys) or (
                source=="P04" and tuple(cells[:2]) in allocation_keys) or (
                source=="P05" and cells[0]==trace["price"]["plan"] and cells[2]==str(trace["price"]["tier_minimum"]))
            if source=="P06" and cells[0] in chosen_rows:
                event=by_id[cells[0]]
                use=cells[1]==str(event["selected_revision"]) and cells[10]<=record["cutoff"]
            if use:kept.append(line)
        unique=list(dict.fromkeys(kept))
        if not unique:raise ValueError("Empty required source excerpt: "+source)
        excerpts[source]={"column_header":columns,"literal_rows":unique}
    header=case["document"].splitlines()
    excerpts["P01"]["literal_packet_headers"]=[line for line in header if line.startswith(("Case-ID:","Target-","Issued-UTC:","Cutoff-UTC:","Default-"))]
    p01=header.index("[P01] Signed purchase order")
    excerpts["P01"]["literal_memo"]=header[p01+1]
    return excerpts,selected


def build(pilot_root=DEFAULT_PILOT_ROOT,write=False,output_path=None):
    pilot_root=Path(pilot_root).resolve()
    if pilot_root.name!="pilot" or pilot_root.parent.name!="scale_v5":
        raise ValueError("Expected the completed scale_v5/pilot directory")
    snapshot=pilot_root.parent/"source_snapshot"
    namespace={"__name__":"pilot_example_audit","__file__":str(snapshot/"scale_fixtures.py")}
    exec(compile((snapshot/"scale_fixtures.py").read_text(encoding="utf-8-sig"),"scale_fixtures.py","exec"),namespace)
    namespace["scale_load_cores"](core_dir=snapshot)
    ladder=read_json(pilot_root/"ladder.json")
    tier_dir=pilot_root/"tier_192";metrics=read_json(tier_dir/"metrics.json");manifest=read_json(tier_dir/"manifest.json")
    rows=read_rows(tier_dir/"candidates.jsonl")
    if hashlib.sha256(canonical(rows).encode()).hexdigest()!=manifest["candidate_hash"]:
        raise ValueError("Frozen pilot candidate hash mismatch")
    source_path=pilot_root/"sources"/"tier_192.jsonl.gz"
    source_manifest=read_json(source_path.with_name(source_path.name+".manifest.json"))
    cases={c["case_id"]:c for c in namespace["scale_iter_corpus"](source_path,source_manifest)}
    if len(rows)!=16 or metrics["value_correct_valid_schema"]!=5 or metrics["value_failure_cases"]!=11:
        raise ValueError("This report is for the frozen completed 16-case, 192-shipment pilot")
    correct=[r for r in rows if r["verification"]["accepted"]]
    failures=[r for r in rows if r["verification"]["valid_schema"] and not r["verification"]["exact_fields"]]
    if any(r["transport_error"] or not r["verification"]["valid_schema"] or not all(r["verification"]["evidence_correct"].values()) for r in rows):
        raise ValueError("Unexpected pilot transport/schema/evidence failure")
    absolute=lambda r:abs(r["response"]["answer"]["quantity_units"]-cases[r["case_id"]]["gold"]["quantity_units"])
    ordinary=min(correct,key=lambda r:r["case_id"])
    small=min(failures,key=lambda r:(absolute(r),r["case_id"]))
    large=min(failures,key=lambda r:(-absolute(r),r["case_id"]))
    used={r["case_id"] for r in (ordinary,small,large)};used_variants={r["family"] for r in (ordinary,small,large)}
    extra_pool=[r for r in failures if r["case_id"] not in used and r["family"] not in used_variants]
    if not extra_pool:extra_pool=[r for r in rows if r["case_id"] not in used]
    extra=min(extra_pool,key=lambda r:(-absolute(r),r["case_id"]))
    choices=[("ordinary_success",ordinary),("small_quantity_error",small),("largest_quantity_error",large),("different_variant",extra)]
    examples=[]
    for category,row in choices:
        case=cases[row["case_id"]];audit=namespace["scale_audit_case"](case,include_traces=True)
        trace=audit["fixture_trace"];verification=namespace["scale_validate_answer"](case,row["response"])
        if verification!=row["verification"]:raise ValueError("Saved checker result changed")
        path=tier_dir/"cache"/(row["request_key"]+".json.gz");raw=read_json(path);request=raw["request"]
        if raw["key"]!=row["request_key"] or hashlib.sha256(canonical(request).encode()).hexdigest()!=row["request_key"]:
            raise ValueError("Original pilot request key mismatch")
        attempt=raw["attempts"][-1]
        if attempt.get("pending") or attempt.get("error"):raise ValueError("Selected pilot response is incomplete/unusable")
        result=json.loads(attempt["final_assistant_response"])
        if result!={"results":[row["response"]]}:raise ValueError("Raw final response differs from observed pilot answer")
        if request["case_inputs"]!=[namespace["scale_model_input"](case)]:raise ValueError("Cached original source/instructions differ")
        expected=case["gold"];observed=row["response"]["answer"];delta=observed["quantity_units"]-expected["quantity_units"]
        wrong=[f for f in namespace["SCALE_FIELDS"] if not verification["field_correct"][f]]
        if wrong and wrong!=["quantity_units"]:raise ValueError("Unexpected nonquantity wrong value")
        excerpts,events=literal_excerpts(case,trace)
        positive=sum(max(e["net_dispatched_units"],0) for e in trace["events"])
        returns=-sum(min(e["net_dispatched_units"],0) for e in trace["events"])
        variant=[r for r in rows if r["family"]==row["family"]]
        matched=[r for r in failures if absolute(r)==abs(delta)]
        reasons={"ordinary_success":"First stable case ID among the five fully accepted pilot answers.",
                 "small_quantity_error":"Smallest absolute wrong quantity among eleven genuine failures; stable ID breaks ties.",
                 "largest_quantity_error":"Largest absolute wrong quantity among eleven genuine failures; stable ID breaks ties.",
                 "different_variant":"Largest absolute error in a variant absent from the first three examples; stable ID breaks ties."}
        explanation=("Accepted: valid schema, all seven exact typed values and sufficient evidence for every field." if not wrong else
                     f"Rejected for the quantity value: expected {expected['quantity_units']:,}, observed {observed['quantity_units']:,}, delta {delta:+,} individual units. The other six values, including unit price, are correct; schema and all evidence checks pass. This is an actual value failure beyond citations.")
        examples.append({"showcase_id":"v5-pilot192-"+category,"case_id":row["case_id"],"family":row["family"],
          "selection_category":category,"selection_reason":reasons[category],
          "category_prevalence":{"all_value_correct":len(correct),"value_failures":len(failures),"pilot_cases":len(rows),
                                 "same_absolute_quantity_error_count_among_failures":len(matched),"absolute_error_units":abs(delta)},
          "variant_prevalence":{"variant_cases":len(variant),"variant_value_failures":sum(not r['verification']['exact_fields'] for r in variant)},
          "literal_input_excerpts":excerpts,"expected_all_seven":expected,"observed_all_seven":observed,
          "observed_evidence":row["response"]["evidence"],"signed_quantity_error_units":delta,
          "relative_quantity_error_percent":100*abs(delta)/expected["quantity_units"],"scoring_explanation":explanation,
          "verification":{"valid_schema":verification["valid_schema"],"field_correct":verification["field_correct"],
                          "evidence_correct":verification["evidence_correct"],"exact_fields":verification["exact_fields"],
                          "accepted":verification["accepted"],"reasons":verification["reasons"]},
          "calculation_trace":{"ordered_units":trace["ordered_units"],"ordered_term_winner":trace["term_winners"]["ordered_units"],
             "allocated_positive_shipments_units":positive,"accepted_returns_units":returns,"net_dispatched_units":trace["net_dispatched_units"],
             "open_units":trace["open_units"],"balance_equation":f"{trace['ordered_units']:,} - ({positive:,} - {returns:,}) = {trace['open_units']:,}",
             "selected_logical_event_count":len(trace["events"]),"event_reason_counts":dict(Counter(e["reason"] for e in trace["events"])),
             "illustrative_selected_events":events,"price_exact_then_final_half_up":trace["price"],
             "full_trace_sha256":hashlib.sha256(canonical(trace).encode()).hexdigest()},
          "source_audit":{"all_full_visible_text_checks_passed":True,"source_record_reconstructed":audit["source_record_reconstructed"],
              "fraction_and_decimal_agree":audit["fraction_and_decimal_agree"],"evidence_needs_match":audit["evidence_needs_match"],
              "independent_fraction_trace_sha256":audit["independent_fraction_trace_hash"],"document_words":audit["document_words"]},
          "provenance":{"source_corpus":"data/scale_v5/pilot/sources/tier_192.jsonl.gz","source_content_sha256":case["content_hash"],
             "semantic_hash":case["semantic_hash"],"original_request_key":row["request_key"],
             "request_cache":"data/scale_v5/pilot/tier_192/cache/"+row["request_key"]+".json.gz",
             "request_cache_gzip_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
             "requested_model":request["model"],"reasoning_effort":request["reasoning_effort"],"protocol":request["protocol"]}})
    output={"scope":"Completed v5 pilot only; calibration examples, excluded from main paired inference. No main or intervention artifacts were opened.",
            "tier_base_shipments":192,"pilot_counts":{"called":16,"all_value_correct":5,"fully_accepted":5,"genuine_quantity_failures":11,
              "schema_failures":0,"citation_only_failures":0,"transport_failures":0,"unit_price_correct":16},
            "ladder":{"tier128_value_failures":next(b['value_failure_cases'] for b in ladder['tiers'] if b['tier']==128),
                      "tier192_value_failures":11,"selected_tier":ladder["selected_tier"],"threshold_met":ladder["threshold_met"]},
            "selection_note":"Four purposeful illustrations, not four independent estimates or a representative failure sample. All responses are actual saved CLI outputs.",
            "truth_methods":"Byte-frozen full text parser/record checks, constructor Decimal, core Fraction, independent text+SQL+Decimal and separate text+Fraction audits.",
            "core_sha256":namespace["SCALE_CORE_SHA256"],"examples":examples,
            "limits":"Excerpts are literal but incomplete; full 192-shipment packets determine truth. Event contributions and price traces explain the verifier, not the model's private reasoning. No numeric match is asserted as a cause. The same requested alias is not an immutable provider-weight snapshot."}
    if write:
        target=Path(output_path) if output_path else DEFAULT_OUTPUT_PATH
        target.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
    return output


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Reproduce four audited examples from the completed v5 pilot only.")
    parser.add_argument("--pilot-root",type=Path,default=DEFAULT_PILOT_ROOT,help="Completed data/scale_v5/pilot directory")
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT_PATH,help="JSON destination when --write is supplied")
    parser.add_argument("--write",action="store_true",help="Save the reproduced JSON; otherwise print a summary only")
    args=parser.parse_args()
    report=build(pilot_root=args.pilot_root,write=args.write,output_path=args.output)
    for item in report["examples"]:
        print(item["selection_category"],item["case_id"],"expected",item["expected_all_seven"]["quantity_units"],
              "observed",item["observed_all_seven"]["quantity_units"],"delta",item["signed_quantity_error_units"],
              "price",item["expected_all_seven"]["unit_price_cents"],"accepted",item["verification"]["accepted"])
