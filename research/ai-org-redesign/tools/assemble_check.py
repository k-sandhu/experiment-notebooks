"""Check how the workflow files of each organisation fit together and fit their organisation file.

Usage:
    python assemble_check.py [ROOT]

For each organisation it reports how many mapped processes have a step-by-step workflow, how much of each
role's headcount the workflows claim, roles the workflows use that the process map does not list, and
workflow interfaces that the process map does not have. Writes assembly_check.csv (one row per role).
"""
import csv
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
workflows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "workflows").glob("*.json"))]
rows = []
for org_path in sorted((root / "organisations").glob("*.json")):
    org = json.loads(org_path.read_text(encoding="utf-8"))
    mine = [w for w in workflows if w["org"] == org["id"]]
    procs = {p["id"]: p for p in org["process_map"]}
    roles = {r["id"]: r for r in org["roles"]}
    pri1 = [p for p in procs.values() if p["detail_priority"] == 1]
    done = {w["process"] for w in mine}
    claimed, used_in = {}, {}
    new_roles, missing_roles, missing_links, vol_gaps = set(), 0, 0, []
    labour = 0.0
    for w in mine:
        proc = procs[w["process"]]
        for r in w["roles"]:
            if r.get("layer") == "external_party":
                continue
            claimed[r["id"]] = claimed.get(r["id"], 0) + float(r["fte_on_process"])
            used_in.setdefault(r["id"], []).append(w["process"])
            labour += float(r["fte_on_process"]) * 1560 * float(r["loaded_cost_per_hour"]["mode"])
            if r["id"] not in roles:
                new_roles.add(r["id"])
            elif r["id"] not in proc["roles"]:
                missing_roles += 1
        have_in = {(t["from"], t["object"]) for t in proc["triggered_by"]}
        have_out = {(t["to"], t["object"]) for t in proc["produces"]}
        missing_links += sum((t["from"], t["object"]) not in have_in for t in w["interfaces"]["triggered_by"])
        missing_links += sum((t["to"], t["object"]) not in have_out for t in w["interfaces"]["produces"])
        a, b = float(w["volume"]["cases_per_month"]["mode"]), float(proc["cases_per_month"]["mode"])
        if b and not 0.8 <= a / b <= 1.25:
            vol_gaps.append(f"{w['process']} ({a:g} in the workflow, {b:g} in the map)")
    over = []
    for rid, fte in sorted(claimed.items(), key=lambda kv: -kv[1]):
        head = roles[rid]["headcount"] if rid in roles else None
        share = fte / head if head else None
        rows.append({"org": org["id"], "role": rid, "title": roles[rid]["title"] if rid in roles else "(not in org file)",
                     "headcount": head, "fte_claimed_by_workflows": round(fte, 2),
                     "share_of_headcount": round(share, 2) if share is not None else "",
                     "processes": ";".join(used_in[rid])})
        if share is not None and share > 1.0:
            over.append(f"{roles[rid]['title']} {fte:.1f} of {head:g}")
    total_fte = sum(claimed.values())
    print(f"\n== {org['id']}")
    print(f"  workflows: {len(mine)}; priority 1 processes documented: {len(done & {p['id'] for p in pri1})} of {len(pri1)}; "
          f"all mapped processes documented: {len(done)} of {len(procs)}")
    print(f"  staff time claimed by workflows: {total_fte:.0f} FTE of {org['profile']['employees']:g} employees "
          f"({total_fte / org['profile']['employees']:.0%}); loaded labour cost about "
          f"{labour / 1e6:.1f}M {org['currency']} a year at 1,560 productive hours")
    print(f"  roles claimed beyond their headcount: {len(over)}" + (": " + "; ".join(over[:8]) if over else ""))
    print(f"  roles added by workflows: {len(new_roles)}" + (": " + ", ".join(sorted(new_roles)) if new_roles else ""))
    print(f"  workflow roles missing from the process map's role lists: {missing_roles}")
    print(f"  workflow interfaces missing from the process map: {missing_links}")
    print(f"  volume differs from the map by more than 25%: {len(vol_gaps)}" + (": " + "; ".join(vol_gaps) if vol_gaps else ""))
with open(root / "assembly_check.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"\nwrote {len(rows)} role rows to assembly_check.csv")
