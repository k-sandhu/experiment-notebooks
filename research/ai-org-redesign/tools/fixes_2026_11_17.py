"""One-time mechanical corrections to the organisation files, from organisations/ISSUES.md (2026-11-17).

Safe to run twice. It changes structure and two sourced facts; it does not change headcounts, pay or
volumes that rest on judgment.

Usage:
    python fixes_2026_11_17.py [ROOT]
"""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
orgs = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (root / "organisations").glob("*.json")}
wf_paths = sorted((root / "workflows").glob("*.json"))
workflows = {p: json.loads(p.read_text(encoding="utf-8")) for p in wf_paths}
log = {k: {"inputs_moved": 0, "roles_added": 0, "systems_added": 0, "links_added": 0, "other": []} for k in orgs}


def proc(org, pid):
    return next(p for p in orgs[org]["process_map"] if p["id"] == pid)


def add_object(org, oid, name, description):
    if not any(o["id"] == oid for o in orgs[org]["business_objects"]):
        orgs[org]["business_objects"].append({"id": oid, "name": name, "description": description})
        log[org]["other"].append(f"added business object {oid}")


def add_link(org, src, dst, obj):
    """src produces obj to dst. Either end may be an external party."""
    pids = {p["id"] for p in orgs[org]["process_map"]}
    changed = False
    if src in pids:
        entry = {"to": dst, "object": obj}
        if entry not in proc(org, src)["produces"]:
            proc(org, src)["produces"].append(entry)
            changed = True
    if dst in pids:
        entry = {"from": src, "object": obj}
        target = proc(org, dst)
        if entry not in target["triggered_by"] and entry not in target.get("inputs", []):
            target["triggered_by"].append(entry)
            changed = True
    log[org]["links_added"] += changed


# 1. Standing inputs: a trigger that a workflow gives a share of zero does not start cases.
for path, wf in workflows.items():
    if not wf["org"]:
        continue
    org, entry = wf["org"], proc(wf["org"], wf["process"])
    iface = wf["interfaces"]
    standing = [t for t in iface["triggered_by"] if float(t.get("share", 0)) == 0]
    for t in standing:
        iface["triggered_by"].remove(t)
        item = {"from": t["from"], "object": t["object"]}
        if item not in iface.setdefault("inputs", []):
            iface["inputs"].append(item)
        if item in entry["triggered_by"]:
            entry["triggered_by"].remove(item)
        if item not in entry.setdefault("inputs", []):
            entry["inputs"].append(item)
            log[org]["inputs_moved"] += 1

# 1b. Standing inputs a workflow declares directly, and workflow links the map lacks (second round).
for path, wf in workflows.items():
    if not wf["org"]:
        continue
    org, entry = wf["org"], proc(wf["org"], wf["process"])
    pids = {p["id"] for p in orgs[org]["process_map"]}
    for item in wf["interfaces"].get("inputs", []):
        item = {"from": item["from"], "object": item["object"]}
        if item in entry["triggered_by"]:
            entry["triggered_by"].remove(item)
        if item not in entry.setdefault("inputs", []):
            entry["inputs"].append(item)
            log[org]["inputs_moved"] += 1
        if item["from"] in pids:
            back = {"to": entry["id"], "object": item["object"]}
            if back not in proc(org, item["from"])["produces"]:
                proc(org, item["from"])["produces"].append(back)
    for t in wf["interfaces"]["triggered_by"]:
        item = {"from": t["from"], "object": t["object"]}
        if item not in entry["triggered_by"]:
            entry["triggered_by"].append(item)
            log[org]["links_added"] += 1
            if t["from"] in pids:
                back = {"to": entry["id"], "object": t["object"]}
                if back not in proc(org, t["from"])["produces"]:
                    proc(org, t["from"])["produces"].append(back)
    for t in wf["interfaces"]["produces"]:
        item = {"to": t["to"], "object": t["object"]}
        if item not in entry["produces"]:
            entry["produces"].append(item)
            log[org]["links_added"] += 1
            if t["to"] in pids:
                target = proc(org, t["to"])
                back = {"from": entry["id"], "object": t["object"]}
                if back not in target["triggered_by"] and back not in target.get("inputs", []):
                    target["triggered_by"].append(back)

# 2. Role lists and 3. systems: what the workflows use, the organisation file should list.
for path, wf in workflows.items():
    if not wf["org"]:
        continue
    org, entry = wf["org"], proc(wf["org"], wf["process"])
    org_roles = {r["id"] for r in orgs[org]["roles"]}
    for r in wf["roles"]:
        if r["id"] in org_roles and r["id"] not in entry["roles"]:
            entry["roles"].append(r["id"])
            log[org]["roles_added"] += 1
    systems = {s["id"]: s for s in orgs[org]["systems"]}
    for s in wf["systems"]:
        if s["id"] not in systems:
            new = {"id": s["id"], "name": s["name"], "kind": s["kind"], "used_by": [entry["owner_unit"]]}
            orgs[org]["systems"].append(new)
            systems[s["id"]] = new
            log[org]["systems_added"] += 1
        elif entry["owner_unit"] not in systems[s["id"]].setdefault("used_by", []):
            systems[s["id"]]["used_by"].append(entry["owner_unit"])

# 4. Links the workflow authors found missing.
E, D, P, M = "equipment-finance-co", "diagnostic-lab-services-co", "public-asset-manager", "pension-investment-manager"
add_object(E, "billing_dispute", "Billing dispute", "A charge the customer disputes, raised during a collection contact.")
add_object(E, "closed_month_balances", "Closed month balances",
           "General ledger and sub-ledger balances after the month-end close.")
add_link(E, "quote-point-of-sale-payments", "price-non-standard-deals", "pricing_request")
add_link(E, "handle-service-requests", "manage-end-of-term", "end_of_term_election")
add_link(E, "handle-service-requests", "collect-early-stage", "delinquent_account")
add_link(E, "close-the-month", "report-to-securitisation-funders", "closed_month_balances")
add_link(E, "collect-early-stage", "bill-customers", "billing_dispute")
add_link(E, "collect-late-stage", "manage-legal-actions-and-insolvencies", "insolvency_notice")

if not any(p["id"] == "olis" for p in orgs[D]["external_parties"]):
    orgs[D]["external_parties"].append({
        "id": "olis", "name": "Ontario Laboratories Information System",
        "description": "The provincial repository that receives laboratory orders and results for Ontario patients."})
    log[D]["other"].append("added external party olis")
add_link(D, "cl-result-reporting", "olis", "lab_report")
add_link(D, "cd-portal-results", "lp-privacy-incident", "privacy_incident")
add_link(D, "fin-provincial-billing", "fin-patient-billing", "billable_order")
add_link(D, "in-tele-interview", "in-order-management", "insurance_order")

add_object(P, "limit_breach_notice", "Limit breach notice",
           "Notice that an investment risk limit was breached, with the cause and the plan to cure it.")
add_link(P, "daily-risk-limit-monitoring", "board", "limit_breach_notice")
add_link(P, "daily-risk-limit-monitoring", "client_pension_plan", "limit_breach_notice")

# 5. Two facts stated in the F2022 annual report (already source src1 of the pension file).
entry = proc(M, "fin-investment-accounting")
old = "Holding subsidiaries add consolidation entries."
if old in entry["description"]:
    entry["description"] = entry["description"].replace(
        old, "Investment holding subsidiaries are not consolidated: the fund is an investment entity under "
             "IFRS 10 and carries them at fair value.")
    log[M]["other"].append("fin-investment-accounting: holding subsidiaries are carried at fair value, not consolidated")
entry = proc(M, "tf-plan-transfers")
if entry["cases_per_month"]["mode"] < 4:
    entry["cases_per_month"] = {"low": 4, "mode": 5, "high": 6}
    entry["description"] = entry["description"].replace("Each month the fund receives", "Each week the fund receives")
    entry["evidence"]["note"] += (" The F2022 annual report (note 18.1) says amounts are transferred to the fund "
                                  "weekly and returned for benefits at least monthly, so about five transfers a month.")
    log[M]["other"].append("tf-plan-transfers: volume raised from 1 to about 5 a month (weekly transfers in, monthly out)")

# 6. Sources the workflow authors opened that the public asset manager's file said could not be read.
have = {s["id"] for s in orgs[P]["sources"]}
wanted = {"mgr_ar20", "mgr_ar21", "mgr_ar22", "osc_mgr_2017"}
for wf in workflows.values():
    if wf["org"] != P:
        continue
    for s in wf["sources"]:
        if s["id"] in wanted and s["id"] not in have:
            orgs[P]["sources"].append(dict(s))
            have.add(s["id"])
            log[P]["other"].append(f"added source {s['id']}")
scale = orgs[P]["profile"]["scale"]
if not any(i["name"].startswith("Costs recovered from clients") for i in scale) and "mgr_ar21" in have:
    scale.append({"name": "Costs recovered from clients, 2021", "value": 216615000, "unit": "CAD",
                  "evidence": {"tier": "A", "sources": ["mgr_ar21"],
                               "note": "Statement of operations, as cited in workflow pam-cost-allocation-billing."}})
    log[P]["other"].append("added scale item: costs recovered from clients, 2021")
fixed = []
for a in orgs[P]["assumptions"]:
    if "annual report PDFs for 2019 to 2022 could not be read" in a and "Later correction" not in a:
        a += (" Later correction: the workflow authors did read the 2020 to 2022 annual reports (sources mgr_ar20, "
              "mgr_ar21, mgr_ar22). Numbers in this file have not yet been re-checked against them"
              + (", apart from the cost recovery figure." if "mgr_ar21" in have else "."))
    if "its order concerning the model manager could not" in a and "Later correction" not in a:
        a += (" Later correction: the workflow authors opened the order of 17 May 2017 (source osc_mgr_2017); it "
              "limits pool units to members who are accredited investors.")
    fixed.append(a)
orgs[P]["assumptions"] = fixed
# The cost figure is cited to the 2021 annual report only. The other added sources are named in the
# assumptions and stay uncited until the file's numbers are re-checked against them.
for item in scale:
    if item["name"].startswith("Costs recovered from clients"):
        item["evidence"]["sources"] = ["mgr_ar21"]

for oid, org in orgs.items():
    (root / "organisations" / f"{oid}.json").write_text(json.dumps(org, indent=2, ensure_ascii=False), encoding="utf-8")
for path, wf in workflows.items():
    if wf["org"]:
        path.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
for oid, entry in log.items():
    print(f"{oid}: {entry['inputs_moved']} standing inputs moved, {entry['roles_added']} role listings added, "
          f"{entry['systems_added']} systems added, {entry['links_added']} links added")
    for line in entry["other"]:
        print(f"    {line}")
