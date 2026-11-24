"""Validate organisation and workflow files (format version 0.3; 0.2 files are accepted).

Usage:
    python validate.py FILE.json [FILE.json ...] [--min-steps N] [--min-processes N] [--org-dir DIR] [--index OUT.csv]

A file with a "process_map" is checked as an organisation file, any other as a workflow file.
Exit code 1 if any file has errors. Warnings do not fail a file.
"""
import argparse
import csv
import json
import random
import statistics
import sys
from pathlib import Path

LAYERS = {"individual_contributor", "senior_specialist", "supervisor", "manager", "director", "executive",
          "external_party"}
CADENCES = {"per_case", "daily", "weekly", "monthly", "quarterly", "annual", "ad_hoc"}
KINDS = {"intake", "data_entry", "lookup", "validation", "analysis", "judgment", "drafting", "review", "approval",
         "communication", "coordination", "physical", "travel", "system_auto", "external_wait"}
WAIT_CAUSES = {"none", "queue", "batch", "external_party", "calendar", "approval_availability", "transit",
               "weather", "resource_availability", "site_access"}
CONTROL_TYPES = {"segregation_of_duties", "regulatory", "licensed_signoff", "policy", "audit_requirement",
                 "accreditation", "safety"}
RESOURCE_KINDS = {"equipment", "vehicle", "crew", "facility", "plant", "bed"}
SHIFT_PATTERNS = {"office_hours", "extended_hours", "shift_24x7", "field_rotation", "on_call"}
SCHEMA_VERSIONS = {"0.2", "0.3"}
# productive hands-on hours a month per full-time person, used by the staffing check
PRODUCTIVE_HOURS = {"office_hours": 130, "extended_hours": 140, "on_call": 130, "shift_24x7": 150,
                    "field_rotation": 200}
REMOVABILITY = {"fixed_by_law", "needs_policy_change", "discretionary"}
SYSTEM_KINDS = {"system_of_record", "workflow", "communication", "document_store", "analytics", "spreadsheet",
                "external_portal", "instrument", "other"}
UNIT_KINDS = {"division", "department", "team", "shared_service", "site_network"}
CATEGORIES = {"core", "support", "management"}
CURRENCIES = {"CAD", "USD"}
ORG_FIELDS = ["schema_version", "id", "name", "modelled_on", "sector", "summary", "currency", "profile", "units",
              "roles", "systems", "business_objects", "external_parties", "demand_drivers", "process_map", "sources",
              "assumptions", "author"]
PROCESS_FIELDS = ["id", "name", "owner_unit", "category", "description", "unit_of_work", "cadence", "cases_per_month",
                  "driver", "triggered_by", "produces", "roles", "detail_priority", "evidence"]
WF_FIELDS = ["schema_version", "id", "name", "org", "process", "sector", "function", "summary", "baseline",
             "currency", "unit_of_work", "trigger", "end_state", "cadence", "volume", "interfaces", "roles", "systems",
             "steps", "exceptions", "benchmarks", "pain_points", "sources", "assumptions", "author"]
STEP_FIELDS = ["id", "name", "description", "role", "kind", "inputs", "outputs", "systems", "touch_min",
               "wait_before_min", "wait_cause", "error", "control", "desk_work_share", "experience_needed", "next",
               "evidence"]
N_CASES = 5000
MAX_VISITS = 400


def tri_ok(obj):
    try:
        lo, mo, hi = float(obj["low"]), float(obj["mode"]), float(obj["high"])
    except (KeyError, TypeError, ValueError):
        return False
    return 0 <= lo <= mo <= hi


def sample(obj, rng):
    lo, mo, hi = float(obj["low"]), float(obj["mode"]), float(obj["high"])
    return lo if hi == lo else rng.triangular(lo, hi, mo)


def check_sources(doc, errors):
    ids = set()
    for src in doc.get("sources", []):
        for field in ["id", "title", "publisher", "url", "year", "accessed", "supports"]:
            if field not in src:
                errors.append(f"source {src.get('id', '?')}: missing '{field}'")
        if src.get("id") in ids:
            errors.append(f"duplicate source id '{src.get('id')}'")
        ids.add(src.get("id"))
        url = str(src.get("url", ""))
        if url and not url.startswith("http"):  # an empty url means the link is withheld
            errors.append(f"source {src.get('id')}: url must start with http, or be empty when withheld")
    return ids


def check_evidence(ev, where, source_ids, errors, cited):
    if not isinstance(ev, dict) or ev.get("tier") not in {"A", "B", "C"}:
        errors.append(f"{where}: evidence.tier must be A, B or C")
        return None
    refs = ev.get("sources", [])
    cited.update(refs)
    for ref in refs:
        if ref not in source_ids:
            errors.append(f"{where}: evidence cites unknown source '{ref}'")
    if ev["tier"] in {"A", "B"} and not refs:
        errors.append(f"{where}: tier {ev['tier']} needs at least one source")
    if ev["tier"] == "C" and not str(ev.get("note", "")).strip():
        errors.append(f"{where}: tier C needs a note saying what the estimate rests on")
    return ev["tier"]


def check_surge(surge, where, source_ids, errors, cited, tiers):
    """Optional surge: bursts of extra work (a storm, a spring break-up, a flu season)."""
    if surge is None:
        return
    if not isinstance(surge, dict) or not str(surge.get("cause", "")).strip():
        errors.append(f"{where}: surge needs a 'cause'")
        return
    for field in ["events_per_year", "duration_days", "volume_multiplier"]:
        if not tri_ok(surge.get(field)):
            errors.append(f"{where}: surge.{field} needs low <= mode <= high")
    tiers.append(check_evidence(surge.get("evidence"), f"{where} surge", source_ids, errors, cited))


def check_shift(item, where, errors):
    if "shift_pattern" in item and item["shift_pattern"] not in SHIFT_PATTERNS:
        errors.append(f"{where}: shift_pattern '{item['shift_pattern']}' not allowed")
    if "productive_hours_per_month" in item:
        h = item["productive_hours_per_month"]
        if not isinstance(h, (int, float)) or not 60 <= h <= 300:
            errors.append(f"{where}: productive_hours_per_month must be a number from 60 to 300")


def unique_ids(items, label, errors):
    seen = set()
    for item in items:
        iid = item.get("id")
        if not iid:
            errors.append(f"{label}: an entry has no id")
        elif iid in seen:
            errors.append(f"duplicate {label} id '{iid}'")
        seen.add(iid)
    return seen


def validate_org(org, path, min_processes):
    errors, warnings, cited, tiers = [], [], set(), []
    for field in ORG_FIELDS:
        if field not in org:
            errors.append(f"missing top-level field '{field}'")
    if errors:
        return errors, warnings, None
    if org["id"] != path.stem:
        errors.append(f"id '{org['id']}' does not match file name '{path.stem}'")
    if str(org["schema_version"]) not in SCHEMA_VERSIONS:
        errors.append(f"schema_version must be one of {sorted(SCHEMA_VERSIONS)}")
    if org["currency"] not in CURRENCIES:
        errors.append("currency must be CAD or USD")
    if len(str(org["summary"]).split()) < 70:
        warnings.append("summary is under 70 words")
    source_ids = check_sources(org, errors)
    profile = org["profile"]
    employees = profile.get("employees")
    if not isinstance(employees, (int, float)):
        errors.append("profile.employees must be a number")
        employees = 0
    for item in profile.get("scale", []):
        tiers.append(check_evidence(item.get("evidence"), f"scale '{item.get('name')}'", source_ids, errors, cited))

    unit_ids = unique_ids(org["units"], "unit", errors)
    children = {}
    for unit in org["units"]:
        uid = unit.get("id")
        if unit.get("parent") is not None and unit.get("parent") not in unit_ids:
            errors.append(f"unit {uid}: unknown parent '{unit.get('parent')}'")
        children.setdefault(unit.get("parent"), []).append(uid)
        if unit.get("kind") not in UNIT_KINDS:
            errors.append(f"unit {uid}: kind '{unit.get('kind')}' not allowed")
        if not isinstance(unit.get("headcount"), (int, float)):
            errors.append(f"unit {uid}: headcount must be a number")
        tiers.append(check_evidence(unit.get("evidence"), f"unit {uid}", source_ids, errors, cited))

    role_ids = unique_ids(org["roles"], "role", errors)
    for role in org["roles"]:
        rid = role.get("id")
        if role.get("unit") not in unit_ids:
            errors.append(f"role {rid}: unknown unit '{role.get('unit')}'")
        if role.get("layer") not in LAYERS:
            errors.append(f"role {rid}: layer '{role.get('layer')}' not allowed")
        if role.get("reports_to") is not None and role.get("reports_to") not in role_ids:
            errors.append(f"role {rid}: unknown reports_to '{role.get('reports_to')}'")
        if not tri_ok(role.get("loaded_cost_per_hour")):
            errors.append(f"role {rid}: loaded_cost_per_hour needs low <= mode <= high")
        if not isinstance(role.get("headcount"), (int, float)):
            errors.append(f"role {rid}: headcount must be a number")
        elif "contractor_headcount" in role:
            ch = role["contractor_headcount"]
            if not isinstance(ch, (int, float)) or not 0 <= ch <= role["headcount"]:
                errors.append(f"role {rid}: contractor_headcount must be a number from 0 to headcount")
        check_shift(role, f"role {rid}", errors)
        tiers.append(check_evidence(role.get("evidence"), f"role {rid}", source_ids, errors, cited))

    resource_ids = unique_ids(org.get("resources", []), "resource", errors)
    for res in org.get("resources", []):
        where = f"resource {res.get('id')}"
        if res.get("kind") not in RESOURCE_KINDS:
            errors.append(f"{where}: kind '{res.get('kind')}' not allowed")
        if res.get("unit") not in unit_ids:
            errors.append(f"{where}: unknown unit '{res.get('unit')}'")
        if not isinstance(res.get("count"), (int, float)) or res.get("count") <= 0:
            errors.append(f"{where}: count must be a positive number")
        if not tri_ok(res.get("available_hours_per_month")):
            errors.append(f"{where}: available_hours_per_month needs low <= mode <= high")
        if "cost_per_hour" in res and not tri_ok(res["cost_per_hour"]):
            errors.append(f"{where}: cost_per_hour needs low <= mode <= high")
        tiers.append(check_evidence(res.get("evidence"), where, source_ids, errors, cited))

    unique_ids(org["systems"], "system", errors)
    for system in org["systems"]:
        if system.get("kind") not in SYSTEM_KINDS:
            errors.append(f"system {system.get('id')}: kind '{system.get('kind')}' not allowed")
        for ref in system.get("used_by", []):
            if ref not in unit_ids:
                errors.append(f"system {system.get('id')}: used_by unknown unit '{ref}'")
    object_ids = unique_ids(org["business_objects"], "business object", errors)
    party_ids = unique_ids(org["external_parties"], "external party", errors)
    driver_ids = unique_ids(org["demand_drivers"], "demand driver", errors)
    for driver in org["demand_drivers"]:
        if not tri_ok(driver.get("per_month")):
            errors.append(f"demand driver {driver.get('id')}: per_month needs low <= mode <= high")
        tiers.append(check_evidence(driver.get("evidence"), f"demand driver {driver.get('id')}", source_ids, errors, cited))

    process_ids = unique_ids(org["process_map"], "process", errors)
    if process_ids & party_ids:
        errors.append(f"ids used for both a process and an external party: {sorted(process_ids & party_ids)}")
    if len(org["process_map"]) < min_processes:
        errors.append(f"{len(org['process_map'])} processes; at least {min_processes} expected")
    linked, used_roles = set(), set()
    for proc in org["process_map"]:
        pid = proc.get("id")
        missing = [f for f in PROCESS_FIELDS if f not in proc]
        if missing:
            errors.append(f"process {pid}: missing {missing}")
            continue
        if proc["owner_unit"] not in unit_ids:
            errors.append(f"process {pid}: unknown owner_unit '{proc['owner_unit']}'")
        if proc["category"] not in CATEGORIES:
            errors.append(f"process {pid}: category '{proc['category']}' not allowed")
        if proc["cadence"] not in CADENCES:
            errors.append(f"process {pid}: cadence '{proc['cadence']}' not allowed")
        if not tri_ok(proc["cases_per_month"]):
            errors.append(f"process {pid}: cases_per_month needs low <= mode <= high")
        if proc["driver"] is not None and proc["driver"] not in driver_ids:
            errors.append(f"process {pid}: unknown driver '{proc['driver']}'")
        if proc["detail_priority"] not in {1, 2, 3}:
            errors.append(f"process {pid}: detail_priority must be 1, 2 or 3")
        if len(str(proc["description"]).split()) < 25:
            warnings.append(f"process {pid}: description under 25 words")
        for ref in proc["roles"]:
            used_roles.add(ref)
            if ref not in role_ids:
                errors.append(f"process {pid}: unknown role '{ref}'")
        if not proc["roles"]:
            warnings.append(f"process {pid}: no roles listed")
        for ref in proc.get("resources", []):
            if ref not in resource_ids:
                errors.append(f"process {pid}: unknown resource '{ref}'")
        check_surge(proc.get("surge"), f"process {pid}", source_ids, errors, cited, tiers)
        for key, end in [("triggered_by", "from"), ("produces", "to"), ("inputs", "from")]:
            for link in proc.get(key, []):
                other = link.get(end)
                if other not in process_ids and other not in party_ids:
                    errors.append(f"process {pid}: {key} refers to unknown process or party '{other}'")
                if link.get("object") not in object_ids:
                    errors.append(f"process {pid}: {key} refers to unknown business object '{link.get('object')}'")
                if other in process_ids:
                    linked.update([pid, other])
                elif other in party_ids:
                    linked.add(pid)
        if not proc["triggered_by"] and not proc["produces"]:
            warnings.append(f"process {pid}: links to no other process or outside party")
        tiers.append(check_evidence(proc["evidence"], f"process {pid}", source_ids, errors, cited))
    if errors:
        return errors, warnings, None

    # one-directional links: A says it produces to B but B does not list A in triggered_by
    by_id = {p["id"]: p for p in org["process_map"]}
    for proc in org["process_map"]:
        for link in proc["produces"]:
            other = by_id.get(link["to"])
            received = other["triggered_by"] + other.get("inputs", []) if other else []
            if other and not any(t["from"] == proc["id"] and t["object"] == link["object"] for t in received):
                warnings.append(f"process {proc['id']} produces '{link['object']}' to {other['id']}, "
                                f"which does not list it in triggered_by or inputs")
        for link in proc["triggered_by"] + proc.get("inputs", []):
            other = by_id.get(link["from"])
            if other and not any(t["to"] == proc["id"] and t["object"] == link["object"] for t in other["produces"]):
                warnings.append(f"process {proc['id']} receives '{link['object']}' from {other['id']}, "
                                f"which does not list it in produces")

    parent = {u["id"]: u["parent"] for u in org["units"]}

    def top(uid):
        while parent.get(uid) is not None:
            uid = parent[uid]
        return uid

    top_units = [u for u in org["units"] if u["parent"] is None]
    top_total = sum(u["headcount"] for u in top_units)
    if employees and not 0.9 <= top_total / employees <= 1.1:
        warnings.append(f"top-level unit headcounts sum to {top_total:g}, employees is {employees:g}")
    for unit in org["units"]:
        kids = children.get(unit["id"], [])
        if kids:
            kid_total = sum(u["headcount"] for u in org["units"] if u["id"] in kids)
            if kid_total > unit["headcount"] * 1.05:
                warnings.append(f"unit {unit['id']}: children headcount {kid_total:g} exceeds its own {unit['headcount']:g}")
    # Contractor staff work in a role but are not employees, so they count toward capacity only.
    role_total = sum(r["headcount"] - r.get("contractor_headcount", 0) for r in org["roles"])
    if employees and not 0.6 <= role_total / employees <= 1.1:
        warnings.append(f"role headcounts sum to {role_total:g}, employees is {employees:g}")
    for rid in sorted(role_ids - used_roles):
        warnings.append(f"role '{rid}' takes part in no process")
    owners = {p["owner_unit"] for p in org["process_map"]}
    names = {u["id"]: u["name"] for u in org["units"]}
    by_top, by_cat, by_pri = {}, {}, {}
    for proc in org["process_map"]:
        by_top[names[top(proc["owner_unit"])]] = by_top.get(names[top(proc["owner_unit"])], 0) + 1
        by_cat[proc["category"]] = by_cat.get(proc["category"], 0) + 1
        by_pri[proc["detail_priority"]] = by_pri.get(proc["detail_priority"], 0) + 1
    for unit in top_units:
        if names[unit["id"]] not in by_top:
            warnings.append(f"top-level unit '{unit['name']}' owns no process")
    for unused in sorted(source_ids - cited):
        warnings.append(f"source '{unused}' is never cited")
    stats = {"id": org["id"], "employees": employees, "units": len(org["units"]), "roles": len(org["roles"]),
             "resources": len(resource_ids), "systems": len(org["systems"]), "business_objects": len(object_ids), "external_parties": len(party_ids),
             "processes": len(process_ids), "units_owning_a_process": len(owners), "sources": len(source_ids),
             "by_top_unit": by_top, "by_category": by_cat, "by_priority": by_pri,
             "tiers": {t: tiers.count(t) for t in "ABC"}}
    return errors, warnings, stats


def validate_workflow(wf, path, min_steps, org_dir):
    errors, warnings, cited, tiers = [], [], set(), []
    for field in WF_FIELDS:
        if field not in wf:
            errors.append(f"missing top-level field '{field}'")
    if errors:
        return errors, warnings, None
    if wf["id"] != path.stem:
        errors.append(f"id '{wf['id']}' does not match file name '{path.stem}'")
    if str(wf["schema_version"]) not in SCHEMA_VERSIONS:
        errors.append(f"schema_version must be one of {sorted(SCHEMA_VERSIONS)}")
    if wf["currency"] not in CURRENCIES:
        errors.append("currency must be CAD or USD")
    if wf["cadence"] not in CADENCES:
        errors.append(f"cadence '{wf['cadence']}' not allowed")
    if len(str(wf["summary"]).split()) < 40:
        warnings.append("summary is under 40 words")
    source_ids = check_sources(wf, errors)

    org = None
    if wf["org"] is not None:
        org_path = org_dir / f"{wf['org']}.json"
        if not org_path.exists():
            errors.append(f"org '{wf['org']}' not found at {org_path}")
        else:
            org = json.loads(org_path.read_text(encoding="utf-8"))
    org_roles = {r["id"] for r in org["roles"]} if org else set()
    org_procs = {p["id"] for p in org["process_map"]} if org else set()
    org_parties = {p["id"] for p in org["external_parties"]} if org else set()
    org_objects = {o["id"] for o in org["business_objects"]} if org else set()
    org_resources = {r["id"] for r in org.get("resources", [])} if org else set()
    if org and wf["process"] not in org_procs:
        errors.append(f"process '{wf['process']}' is not in the process map of {wf['org']}")

    role_ids = unique_ids(wf["roles"], "role", errors)
    for role in wf["roles"]:
        rid = role.get("id")
        if role.get("layer") not in LAYERS:
            errors.append(f"role {rid}: layer '{role.get('layer')}' not allowed")
        if not tri_ok(role.get("loaded_cost_per_hour")):
            errors.append(f"role {rid}: loaded_cost_per_hour needs low <= mode <= high")
        if not isinstance(role.get("fte_on_process"), (int, float)):
            errors.append(f"role {rid}: fte_on_process must be a number")
        if org and rid not in org_roles and not role.get("not_in_org_file"):
            errors.append(f"role {rid}: not in the organisation file (use its role ids, or set not_in_org_file)")
        check_shift(role, f"role {rid}", errors)
        tiers.append(check_evidence(role.get("evidence"), f"role {rid}", source_ids, errors, cited))

    system_ids = unique_ids(wf["systems"], "system", errors)
    for system in wf["systems"]:
        if system.get("kind") not in SYSTEM_KINDS:
            errors.append(f"system {system.get('id')}: kind '{system.get('kind')}' not allowed")

    resource_ids = unique_ids(wf.get("resources", []), "resource", errors)
    for res in wf.get("resources", []):
        where = f"resource {res.get('id')}"
        if res.get("kind") not in RESOURCE_KINDS:
            errors.append(f"{where}: kind '{res.get('kind')}' not allowed")
        if "cost_per_hour" in res and not tri_ok(res["cost_per_hour"]):
            errors.append(f"{where}: cost_per_hour needs low <= mode <= high")
        if org and res.get("id") not in org_resources and not res.get("not_in_org_file"):
            errors.append(f"{where}: not in the organisation file (use its resource ids, or set not_in_org_file)")

    if not tri_ok(wf["volume"].get("cases_per_month")):
        errors.append("volume.cases_per_month needs low <= mode <= high")
    tiers.append(check_evidence(wf["volume"].get("evidence"), "volume", source_ids, errors, cited))
    check_surge(wf["volume"].get("surge"), "volume", source_ids, errors, cited, tiers)

    steps = wf["steps"]
    if len(steps) < min_steps:
        errors.append(f"{len(steps)} steps; at least {min_steps} expected")
    step_ids = [s.get("id") for s in steps]
    if len(set(step_ids)) != len(step_ids):
        errors.append("duplicate step ids")
    by_id = {s.get("id"): s for s in steps}
    end_labels = set()

    for step in steps:
        sid = step.get("id")
        missing = [f for f in STEP_FIELDS if f not in step]
        if missing:
            errors.append(f"step {sid}: missing {missing}")
            continue
        if step["role"] not in role_ids | {"system", "external"}:
            errors.append(f"step {sid}: unknown role '{step['role']}'")
        if step["kind"] not in KINDS:
            errors.append(f"step {sid}: kind '{step['kind']}' not allowed")
        if step["wait_cause"] not in WAIT_CAUSES:
            errors.append(f"step {sid}: wait_cause '{step['wait_cause']}' not allowed")
        for field in ["touch_min", "wait_before_min"]:
            if not tri_ok(step[field]):
                errors.append(f"step {sid}: {field} needs 0 <= low <= mode <= high")
        for ref in step["systems"]:
            if ref not in system_ids:
                errors.append(f"step {sid}: unknown system '{ref}'")
        for ref in step.get("concurrent_with", []):
            if ref not in by_id:
                errors.append(f"step {sid}: concurrent_with unknown step '{ref}'")
        if "people" in step and (not isinstance(step["people"], (int, float)) or step["people"] < 1):
            errors.append(f"step {sid}: people must be a number of at least 1")
        for use in step.get("resources", []):
            if not isinstance(use, dict) or use.get("id") not in resource_ids:
                errors.append(f"step {sid}: resources entry must name a workflow resource id")
            elif not tri_ok(use.get("occupied_min")):
                errors.append(f"step {sid}: resource {use['id']} occupied_min needs low <= mode <= high")
        if len(str(step["description"]).split()) < 20:
            warnings.append(f"step {sid}: description under 20 words")
        try:
            if not 0 <= float(step["desk_work_share"]) <= 1:
                raise ValueError
        except (TypeError, ValueError):
            errors.append(f"step {sid}: desk_work_share must be between 0 and 1")
        if step["experience_needed"] not in {"low", "medium", "high"}:
            errors.append(f"step {sid}: experience_needed must be low, medium or high")
        err = step["error"]
        try:
            ok = isinstance(err, dict) and 0 <= float(err.get("introduces_defect_prob", -1)) <= 1
        except (TypeError, ValueError):
            ok = False
        if not ok:
            errors.append(f"step {sid}: error.introduces_defect_prob must be between 0 and 1")
        else:
            caught = err.get("typically_caught_at")
            if caught not in {None, "downstream"} and caught not in by_id:
                errors.append(f"step {sid}: error.typically_caught_at '{caught}' is not a step")
        control = step["control"]
        if control is not None:
            if control.get("type") not in CONTROL_TYPES:
                errors.append(f"step {sid}: control.type '{control.get('type')}' not allowed")
            if control.get("removability") not in REMOVABILITY:
                errors.append(f"step {sid}: control.removability '{control.get('removability')}' not allowed")
            if not str(control.get("basis", "")).strip():
                errors.append(f"step {sid}: control.basis must name the rule")
        nxt = step["next"]
        if not nxt:
            errors.append(f"step {sid}: next is empty (use to: END for a final step)")
        total = 0.0
        for edge in nxt:
            total += float(edge.get("prob", 0))
            if edge.get("to") != "END" and edge.get("to") not in by_id:
                errors.append(f"step {sid}: next points to unknown step '{edge.get('to')}'")
            if edge.get("to") == "END":
                if not edge.get("outcome"):
                    errors.append(f"step {sid}: an END edge needs an outcome label")
                end_labels.add(edge.get("outcome"))
        if nxt and abs(total - 1.0) > 0.011:
            errors.append(f"step {sid}: next probabilities sum to {total:.3f}, not 1")
        tiers.append(check_evidence(step["evidence"], f"step {sid}", source_ids, errors, cited))

    iface = wf["interfaces"]
    if not isinstance(iface, dict) or "triggered_by" not in iface or "produces" not in iface:
        errors.append("interfaces needs triggered_by and produces lists")
    else:
        if not iface["triggered_by"]:
            errors.append("interfaces.triggered_by is empty")
        share = sum(float(t.get("share", 0)) for t in iface["triggered_by"])
        if iface["triggered_by"] and abs(share - 1.0) > 0.011:
            errors.append(f"interfaces.triggered_by shares sum to {share:.3f}, not 1")
        if not iface["produces"]:
            warnings.append("interfaces.produces is empty")
        for key, end in [("triggered_by", "from"), ("produces", "to"), ("inputs", "from")]:
            for link in iface.get(key, []):
                if not link.get(end) or not link.get("object"):
                    errors.append(f"interfaces.{key}: each entry needs '{end}' and 'object'")
                elif org:
                    if link[end] not in org_procs | org_parties:
                        errors.append(f"interfaces.{key}: '{link[end]}' is not a process or external party of {wf['org']}")
                    if link["object"] not in org_objects:
                        errors.append(f"interfaces.{key}: '{link['object']}' is not a business object of {wf['org']}")
        for link in iface["produces"]:
            if link.get("outcome") != "any" and link.get("outcome") not in end_labels:
                errors.append(f"interfaces.produces: outcome '{link.get('outcome')}' is not an END outcome or 'any'")

    for exc in wf["exceptions"]:
        for ref in exc.get("path", []):
            if ref not in by_id:
                errors.append(f"exception '{exc.get('name')}': unknown step '{ref}'")
    for pain in wf["pain_points"]:
        for ref in pain.get("steps", []):
            if ref not in by_id:
                errors.append(f"pain point: unknown step '{ref}'")
        tiers.append(check_evidence(pain.get("evidence"), "pain point", source_ids, errors, cited))
    for bench in wf["benchmarks"]:
        tiers.append(check_evidence(bench.get("evidence"), f"benchmark {bench.get('metric')}", source_ids, errors, cited))
    for unused in sorted(source_ids - cited):
        warnings.append(f"source '{unused}' is never cited")
    if errors:
        return errors, warnings, None

    reach, stack = set(), [steps[0]["id"]]
    while stack:
        cur = stack.pop()
        if cur in reach or cur == "END":
            continue
        reach.add(cur)
        stack.extend(e["to"] for e in by_id[cur]["next"])
    for sid in step_ids:
        if sid not in reach:
            errors.append(f"step {sid}: not reachable from the first step")
    can_end = {sid for sid in step_ids if any(e["to"] == "END" for e in by_id[sid]["next"])}
    changed = True
    while changed:
        changed = False
        for sid in step_ids:
            if sid not in can_end and any(e["to"] in can_end for e in by_id[sid]["next"]):
                can_end.add(sid)
                changed = True
    for sid in step_ids:
        if sid not in can_end:
            errors.append(f"step {sid}: no path to END")
    if errors:
        return errors, warnings, None

    rng = random.Random(20261117)
    cost = {r["id"]: float(r["loaded_cost_per_hour"]["mode"]) for r in wf["roles"]}
    res_cost = {r["id"]: float(r["cost_per_hour"]["mode"]) for r in wf.get("resources", []) if "cost_per_hour" in r}
    cycle, touch, handoffs, visits, money, outcomes, truncated, reworked = [], [], [], [], [], {}, 0, 0
    res_hours, res_money = [], []
    role_touch = {}  # minutes per role summed over all simulated cases
    for _ in range(N_CASES):
        cur, last_role, t_cycle, t_touch, n_hand, n_vis, spend = steps[0]["id"], None, 0.0, 0.0, 0, 0, 0.0
        r_hours, r_spend = 0.0, 0.0
        seen, repeat = set(), False
        prev, block = None, 0.0  # block: elapsed length of the current run of overlapping steps
        while cur != "END" and n_vis < MAX_VISITS:
            step = by_id[cur]
            repeat = repeat or cur in seen
            seen.add(cur)
            work = sample(step["touch_min"], rng)
            people = float(step.get("people", 1))
            t_touch += work * people
            role_touch[step["role"]] = role_touch.get(step["role"], 0.0) + work * people
            wait = sample(step["wait_before_min"], rng)
            if prev is not None and (prev in step.get("concurrent_with", []) or cur in by_id[prev].get("concurrent_with", [])):
                # runs alongside the step before it: only the part that outlasts the block adds elapsed time
                t_cycle += wait + max(0.0, work - block)
                block = max(block, work)
            else:
                t_cycle += wait + work
                block = work
            prev = cur
            spend += work * people / 60 * cost.get(step["role"], 0.0)
            for use in step.get("resources", []):
                held = sample(use["occupied_min"], rng) / 60
                r_hours += held
                r_spend += held * res_cost.get(use["id"], 0.0)
            if last_role is not None and step["role"] != last_role:
                n_hand += 1
            last_role = step["role"]
            n_vis += 1
            draw, acc, chosen = rng.random(), 0.0, step["next"][-1]
            for edge in step["next"]:
                acc += float(edge["prob"])
                if draw <= acc:
                    chosen = edge
                    break
            if chosen["to"] == "END":
                outcomes[chosen["outcome"]] = outcomes.get(chosen["outcome"], 0) + 1
            cur = chosen["to"]
        if cur != "END":
            truncated += 1
        reworked += repeat
        cycle.append(t_cycle / 1440)
        touch.append(t_touch / 60)
        handoffs.append(n_hand)
        visits.append(n_vis)
        money.append(spend)
        res_hours.append(r_hours)
        res_money.append(r_spend)
    if truncated:
        warnings.append(f"{truncated} of {N_CASES} simulated cases did not finish in {MAX_VISITS} step visits")

    def pct(values, q):
        return sorted(values)[int(q * (len(values) - 1))]

    tier_counts = {t: tiers.count(t) for t in "ABC"}
    stats = {
        "id": wf["id"], "name": wf["name"], "org": wf["org"] or "", "process": wf["process"] or "",
        "sector": wf["sector"], "function": wf["function"], "currency": wf["currency"],
        "cases_per_month": wf["volume"]["cases_per_month"]["mode"],
        "steps": len(steps), "roles": len(wf["roles"]), "sources": len(wf["sources"]),
        "controls": sum(1 for s in steps if s["control"]),
        "tier_A": tier_counts["A"], "tier_B": tier_counts["B"], "tier_C": tier_counts["C"],
        "sim_cycle_days_p50": round(pct(cycle, 0.5), 2), "sim_cycle_days_p90": round(pct(cycle, 0.9), 2),
        "sim_touch_hours_p50": round(pct(touch, 0.5), 2), "sim_touch_hours_p90": round(pct(touch, 0.9), 2),
        "sim_touch_share_of_cycle": round(statistics.mean(touch) / 24 / max(statistics.mean(cycle), 1e-9), 4),
        "sim_handoffs_p50": pct(handoffs, 0.5), "sim_step_visits_mean": round(statistics.mean(visits), 1),
        "sim_labour_cost_mean": round(statistics.mean(money), 2),
        "sim_rework_share": round(reworked / N_CASES, 3),
        "sim_resource_hours_mean": round(statistics.mean(res_hours), 2),
        "sim_resource_cost_mean": round(statistics.mean(res_money), 2),
        "outcomes": {k: round(v / N_CASES, 3) for k, v in sorted(outcomes.items(), key=lambda kv: -kv[1])},
    }
    fte = sum(float(r["fte_on_process"]) for r in wf["roles"] if r.get("layer") != "external_party")
    stats["fte_stated"] = round(fte, 1)
    # implied FTE: each internal role's hands-on hours a month divided by the productive hours its shift pattern gives
    implied = 0.0
    for r in wf["roles"]:
        if r.get("layer") == "external_party":
            continue
        hours = r.get("productive_hours_per_month") or PRODUCTIVE_HOURS.get(r.get("shift_pattern", "office_hours"), 130)
        implied += role_touch.get(r["id"], 0.0) / N_CASES / 60 * stats["cases_per_month"] / hours
    stats["fte_implied_by_touch_time"] = round(implied, 1)
    if fte > 0 and stats["fte_implied_by_touch_time"] > 0:
        ratio = fte / stats["fte_implied_by_touch_time"]
        if not 0.5 <= ratio <= 4:
            warnings.append(f"roles state {fte:g} FTE on this process, but hands-on time times monthly volume implies "
                            f"about {stats['fte_implied_by_touch_time']:g} FTE (productive hours a month by shift "
                            f"pattern: {PRODUCTIVE_HOURS})")
    for bench in wf["benchmarks"]:
        value = bench.get("value")
        if bench.get("metric") == "cycle_time_days" and isinstance(value, dict) and value.get("p50"):
            stats["bench_cycle_days_p50"] = value["p50"]
            ratio = stats["sim_cycle_days_p50"] / float(value["p50"])
            if not 0.5 <= ratio <= 2.0:
                warnings.append(f"simulated median cycle time {stats['sim_cycle_days_p50']} days is "
                                f"{ratio:.1f}x the benchmark p50 of {value['p50']} days")
    return errors, warnings, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--min-steps", type=int, default=12)
    parser.add_argument("--min-processes", type=int, default=30)
    parser.add_argument("--org-dir", default=str(Path(__file__).resolve().parent.parent / "organisations"))
    parser.add_argument("--index", help="write one row per valid workflow to this CSV")
    args = parser.parse_args()

    rows, valid, failed = [], 0, 0
    for name in args.files:
        path = Path(name)
        print(f"\n== {path.name}")
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ERROR cannot read as JSON: {exc}")
            failed += 1
            continue
        is_org = "process_map" in doc
        if is_org:
            errors, warnings, stats = validate_org(doc, path, args.min_processes)
        else:
            errors, warnings, stats = validate_workflow(doc, path, args.min_steps, Path(args.org_dir))
        for msg in errors:
            print(f"  ERROR {msg}")
        for msg in warnings:
            print(f"  warning {msg}")
        if errors:
            failed += 1
            continue
        valid += 1
        if is_org:
            print(f"  ok: {stats['employees']:g} employees, {stats['units']} units, {stats['roles']} roles, {stats['resources']} resources, "
                  f"{stats['systems']} systems, {stats['business_objects']} business objects, "
                  f"{stats['external_parties']} outside parties, {stats['sources']} sources")
            print(f"  {stats['processes']} processes; by category {stats['by_category']}; "
                  f"by detail priority {stats['by_priority']}")
            print(f"  processes by top-level unit: {stats['by_top_unit']}")
            print(f"  evidence tiers A/B/C {stats['tiers']['A']}/{stats['tiers']['B']}/{stats['tiers']['C']}")
            continue
        rows.append(stats)
        cur = stats["currency"]
        print(f"  ok: {stats['steps']} steps, {stats['roles']} roles, {stats['controls']} controls, "
              f"{stats['sources']} sources, evidence tiers A/B/C {stats['tier_A']}/{stats['tier_B']}/{stats['tier_C']}")
        print(f"  simulated cycle time: median {stats['sim_cycle_days_p50']} days, p90 {stats['sim_cycle_days_p90']} "
              f"(benchmark p50: {stats.get('bench_cycle_days_p50', 'none')})")
        print(f"  simulated hands-on time: median {stats['sim_touch_hours_p50']} h, p90 {stats['sim_touch_hours_p90']} h "
              f"({stats['sim_touch_share_of_cycle']:.1%} of elapsed time)")
        print(f"  handoffs (median) {stats['sim_handoffs_p50']}, step visits (mean) {stats['sim_step_visits_mean']}, "
              f"cases with rework {stats['sim_rework_share']:.1%}, labour cost per case {stats['sim_labour_cost_mean']} {cur}")
        if stats["sim_resource_hours_mean"]:
            print(f"  equipment, vehicles and crews held per case: {stats['sim_resource_hours_mean']} h, "
                  f"costing {stats['sim_resource_cost_mean']} {cur}")
        print(f"  staffing: roles state {stats['fte_stated']} FTE; hands-on time x volume implies "
              f"{stats['fte_implied_by_touch_time']} FTE")
        print(f"  outcomes: {stats['outcomes']}")
    if args.index and rows:
        fields = list(dict.fromkeys([k for k in rows[0] if k != "outcomes"] + ["bench_cycle_days_p50", "outcomes"]))
        with open(args.index, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                row = dict(row)
                row["outcomes"] = json.dumps(row["outcomes"])
                writer.writerow(row)
        print(f"\nwrote {len(rows)} rows to {args.index}")
    print(f"\n{valid} valid, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
