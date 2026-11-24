"""Build pages/process-explorer.html: one page that draws every workflow and each organisation's process map.

Usage:
    python build_explorer.py [ROOT]

Reads organisations/*.json, workflows/*.json and workflows_index.csv (run validate.py --index first).
"""
import csv
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
index = {}
if (root / "workflows_index.csv").exists():
    with open(root / "workflows_index.csv", encoding="utf-8") as handle:
        index = {r["id"]: r for r in csv.DictReader(handle)}

LABELS = {"equipment-finance-co": "Equipment leasing and finance company",
          "diagnostic-lab-services-co": "Laboratory and health services company",
          "pension-investment-manager": "Pension investment manager",
          "public-asset-manager": "Public-sector asset manager",
          "oilfield-services-co": "Oil field services company",
          "electric-distribution-utility": "Electricity distribution utility",
          "power-generation-co": "Power generation company",
          "mining-operator-co": "Gold mining company",
          "general-contractor-co": "General contractor",
          "freight-carrier-co": "Trucking company",
          "community-hospital-corp": "Community hospital"}


def flt(row, key):
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return None


wfs, by_org = {}, {}
for path in sorted((root / "workflows").glob("*.json")):
    w = json.loads(path.read_text(encoding="utf-8"))
    row = index.get(w["id"], {})
    wfs[w["id"]] = {
        "id": w["id"], "name": w["name"], "org": w["org"], "process": w["process"], "summary": w["summary"],
        "sector": w["sector"], "currency": w["currency"], "cases": w["volume"]["cases_per_month"]["mode"],
        "roles": {r["id"]: r["title"] for r in w["roles"]},
        "stats": {"cycle50": flt(row, "sim_cycle_days_p50"), "touch50": flt(row, "sim_touch_hours_p50"),
                  "share": flt(row, "sim_touch_share_of_cycle"), "handoffs": flt(row, "sim_handoffs_p50"),
                  "rework": flt(row, "sim_rework_share"), "cost": flt(row, "sim_labour_cost_mean")} if row else None,
        "steps": [{"id": s["id"], "name": s["name"], "desc": s["description"], "role": s["role"], "kind": s["kind"],
                   "touch": [s["touch_min"]["low"], s["touch_min"]["mode"], s["touch_min"]["high"]],
                   "wait": [s["wait_before_min"]["low"], s["wait_before_min"]["mode"], s["wait_before_min"]["high"]],
                   "cause": s["wait_cause"],
                   "control": [s["control"]["type"], s["control"]["basis"], s["control"]["removability"]] if s["control"] else None,
                   "tier": s["evidence"]["tier"],
                   "next": [[e["to"], float(e["prob"]), e.get("outcome", "")] for e in s["next"]]} for s in w["steps"]],
    }
    by_org.setdefault(w["org"] or "general", []).append(w)

orgs = []
for path in sorted((root / "organisations").glob("*.json")):
    o = json.loads(path.read_text(encoding="utf-8"))
    units = {u["id"]: u for u in o["units"]}

    def top(uid):
        while units[uid]["parent"] is not None:
            uid = units[uid]["parent"]
        return uid

    documented = {w["process"]: w["id"] for w in by_org.get(o["id"], [])}
    orgs.append({"id": o["id"], "label": LABELS.get(o["id"], o["name"]),
                 "units": [{"id": u["id"], "name": u["name"]} for u in o["units"] if u["parent"] is None],
                 "processes": [{"id": p["id"], "name": p["name"], "unit": top(p["owner_unit"]),
                                "vol": p["cases_per_month"]["mode"], "wf": documented.get(p["id"])}
                               for p in sorted(o["process_map"], key=lambda p: (p["detail_priority"], p["name"]))]})
order = ["diagnostic-lab-services-co", "equipment-finance-co", "pension-investment-manager", "public-asset-manager",
         "oilfield-services-co", "electric-distribution-utility", "power-generation-co", "mining-operator-co",
         "general-contractor-co", "freight-carrier-co", "community-hospital-corp"]
orgs.sort(key=lambda o: order.index(o["id"]) if o["id"] in order else 99)
general = by_org.get("general", [])
sectors = sorted({w["sector"] for w in general})
orgs.append({"id": "general", "label": "General processes, not tied to one organisation",
             "units": [{"id": s, "name": s[:1].upper() + s[1:]} for s in sectors],
             "processes": [{"id": w["id"], "name": w["name"], "unit": w["sector"],
                            "vol": w["volume"]["cases_per_month"]["mode"], "wf": w["id"]} for w in general]})

start = "dls-cl-psc-collection" if "dls-cl-psc-collection" in wfs else next(iter(wfs))
data = json.dumps({"orgs": orgs, "wfs": wfs, "start": start}, ensure_ascii=False, separators=(",", ":"))
data = data.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
template = (root / "tools" / "explorer_template.html").read_text(encoding="utf-8")
out = root / "pages" / "process-explorer.html"
out.write_text(template.replace("/*DATA*/", data), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB): {len(wfs)} workflows, {len(orgs)} organisations")
