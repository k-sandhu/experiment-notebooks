"""Bring an organisation file's process map into line with its workflow files.

The workflow authors may not edit the organisation file, so a finished set of workflows leaves the map behind:
roles that do the work are missing from a process's role list, links between processes are missing, and
roles or resources the authors needed are only in the workflow, marked "not_in_org_file". This script copies
those facts from the workflows into the organisation file. It changes structure only. Headcounts of the roles
it adds are the FTE the workflows claim, rounded up, and are marked tier C for someone to check.

Safe to run twice.

Usage:
    python sync_map_from_workflows.py ORG_ID [ORG_ID ...] [--root ROOT]
"""
import argparse
import json
import math
from pathlib import Path

DEFAULT_HOURS = {  # available hours a month for a resource the workflows added, by kind (tier C)
    "equipment": {"low": 250, "mode": 350, "high": 450}, "vehicle": {"low": 250, "mode": 350, "high": 450},
    "crew": {"low": 250, "mode": 330, "high": 345}, "facility": {"low": 300, "mode": 500, "high": 730},
    "plant": {"low": 600, "mode": 650, "high": 700}, "bed": {"low": 700, "mode": 720, "high": 730}}

ap = argparse.ArgumentParser()
ap.add_argument("orgs", nargs="+")
ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
args = ap.parse_args()
root = Path(args.root)

for oid in args.orgs:
    org_path = root / "organisations" / f"{oid}.json"
    org = json.loads(org_path.read_text(encoding="utf-8"))
    wf_paths = [p for p in sorted((root / "workflows").glob("*.json"))
                if json.loads(p.read_text(encoding="utf-8")).get("org") == oid]
    workflows = {p: json.loads(p.read_text(encoding="utf-8")) for p in wf_paths}
    procs = {p["id"]: p for p in org["process_map"]}
    units = {u["id"] for u in org["units"]}
    n = {"inputs": 0, "links": 0, "role_listings": 0, "systems": 0, "roles": [], "resources": [], "res_listings": 0}

    def link_out(src, dst, obj):
        """Record that process src sends obj to dst, on both ends when both are processes."""
        added = False
        if src in procs and {"to": dst, "object": obj} not in procs[src]["produces"]:
            procs[src]["produces"].append({"to": dst, "object": obj})
            added = True
        if dst in procs:
            entry = {"from": src, "object": obj}
            if entry not in procs[dst]["triggered_by"] and entry not in procs[dst].get("inputs", []):
                procs[dst]["triggered_by"].append(entry)
                added = True
        return added

    for wf in workflows.values():
        entry = procs[wf["process"]]
        iface = wf["interfaces"]
        # A trigger with a share of zero starts no cases: it is a standing input.
        for t in [t for t in iface["triggered_by"] if float(t.get("share", 0)) == 0]:
            iface["triggered_by"].remove(t)
            item = {"from": t["from"], "object": t["object"]}
            if item not in iface.setdefault("inputs", []):
                iface["inputs"].append(item)
        for item in iface.get("inputs", []):
            item = {"from": item["from"], "object": item["object"]}
            if item in entry["triggered_by"]:
                entry["triggered_by"].remove(item)
            if item not in entry.setdefault("inputs", []):
                entry["inputs"].append(item)
                n["inputs"] += 1
            if item["from"] in procs and {"to": entry["id"], "object": item["object"]} not in procs[item["from"]]["produces"]:
                procs[item["from"]]["produces"].append({"to": entry["id"], "object": item["object"]})
        for t in iface["triggered_by"]:
            # A link that starts cases is a trigger, even where another listing called it a standing input.
            item = {"from": t["from"], "object": t["object"]}
            if item in entry.get("inputs", []):
                entry["inputs"].remove(item)
            n["links"] += link_out(t["from"], entry["id"], t["object"])
        for t in iface["produces"]:
            n["links"] += link_out(entry["id"], t["to"], t["object"])

        # Roles: add the ones the workflow had to invent, then list every employee role on the process.
        org_roles = {r["id"]: r for r in org["roles"]}
        for r in wf["roles"]:
            if r.get("layer") == "external_party":
                continue
            if r["id"] not in org_roles:
                unit = r.get("department") if r.get("department") in units else entry["owner_unit"]
                claimed = sum(float(x["fte_on_process"]) for w in workflows.values() for x in w["roles"]
                              if x["id"] == r["id"])
                new = {"id": r["id"], "title": r["title"], "unit": unit, "layer": r["layer"], "reports_to": None,
                       "headcount": max(1, math.ceil(claimed)), "loaded_cost_per_hour": r["loaded_cost_per_hour"],
                       "occupation_code": r.get("occupation_code"),
                       "evidence": {"tier": "C", "sources": [],
                                    "note": f"Added from workflow {wf['id']}, whose author found the role missing. "
                                            f"Headcount is the {claimed:.2f} FTE the workflows claim, rounded up."}}
                if r.get("shift_pattern"):
                    new["shift_pattern"] = r["shift_pattern"]
                org["roles"].append(new)
                org_roles[r["id"]] = new
                n["roles"].append(r["id"])
            r.pop("not_in_org_file", None)
            if r["id"] not in entry["roles"]:
                entry["roles"].append(r["id"])
                n["role_listings"] += 1

        # Resources the workflow added, and the process's list of resources it ties up.
        org_res = {r["id"]: r for r in org.setdefault("resources", [])}
        for r in wf.get("resources", []):
            if r["id"] not in org_res:
                new = {"id": r["id"], "name": r["name"], "kind": r["kind"], "unit": entry["owner_unit"],
                       "count": r["count"], "available_hours_per_month": dict(DEFAULT_HOURS[r["kind"]]),
                       "evidence": {"tier": "C", "sources": [],
                                    "note": f"Added from workflow {wf['id']}, whose author found it missing. Available "
                                            f"hours are a default for a {r['kind']}, not a measured figure."}}
                if "cost_per_hour" in r:
                    new["cost_per_hour"] = r["cost_per_hour"]
                org["resources"].append(new)
                org_res[r["id"]] = new
                n["resources"].append(r["id"])
            r.pop("not_in_org_file", None)
            if r["id"] not in entry.setdefault("resources", []):
                entry["resources"].append(r["id"])
                n["res_listings"] += 1

        # Systems the workflow uses.
        systems = {s["id"]: s for s in org["systems"]}
        for s in wf["systems"]:
            if s["id"] not in systems:
                systems[s["id"]] = {"id": s["id"], "name": s["name"], "kind": s["kind"], "used_by": [entry["owner_unit"]]}
                org["systems"].append(systems[s["id"]])
                n["systems"] += 1
            elif entry["owner_unit"] not in systems[s["id"]].setdefault("used_by", []):
                systems[s["id"]]["used_by"].append(entry["owner_unit"])

    org_path.write_text(json.dumps(org, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for path, wf in workflows.items():
        path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{oid}: {n['inputs']} standing inputs recorded, {n['links']} links added, {n['role_listings']} role "
          f"listings added, {n['res_listings']} resource listings added, {n['systems']} systems added")
    print(f"    roles added: {', '.join(n['roles']) or 'none'}")
    print(f"    resources added: {', '.join(n['resources']) or 'none'}")
