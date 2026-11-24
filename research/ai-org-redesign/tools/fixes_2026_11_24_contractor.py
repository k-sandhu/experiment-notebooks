"""Corrections to the general contractor file from its workflow authors' reports (2026-11-24).

general-contractor-co is modelled on Bird Construction before its 2020 Stuart Olson acquisition. The nine
workflow batches found roles that could not do the documented work at their headcount, volumes that did not
fit the company's size, links that were inputs rather than triggers, and a few links that do not exist in
practice. Bird's 2020 annual information form, which earlier authors could not open, gives the outside check:
about 880 salaried and 1,578 hourly employees at 31 December 2019, on 2019 revenue of $1,376.4 million.

What this script does:
  - Site staff (superintendents, assistant superintendents, field engineers) work 10-hour days and some
    Saturdays in season, as the site coordination author recorded, so they get productive_hours_per_month 180
    instead of the extended_hours default of 140.
  - Foremen follow the crews: 135 crews (75 concrete, 25 finishing, 35 general) each have a working foreman.
    The 45 added foremen come from the crews' own trades, so the hourly workforce is unchanged.
  - Every role whose documented hands-on work exceeds its headcount is resized to cover that work at 97% of
    productive hours. The work is measured by simulating each workflow, as tools/validate.py does.
  - Volumes the workflow authors checked against sources replace the map's estimates; links that were
    triggers become inputs; two links that do not exist in practice are removed or renamed.
  - Employees, unit headcounts and the salaried and hourly demand drivers grow by the headcount added.

Run tools/sync_map_from_workflows.py general-contractor-co first. Safe to run twice.

Usage:
    python fixes_2026_11_24_contractor.py [ROOT]
"""
import json
import math
import random
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools"))
import validate as V  # noqa: E402

ORG = "general-contractor-co"
TODAY = "2026-11-24"
org_path = root / "organisations" / f"{ORG}.json"
org = json.loads(org_path.read_text(encoding="utf-8"))
wf_paths = [p for p in sorted((root / "workflows").glob("*.json"))
            if json.loads(p.read_text(encoding="utf-8")).get("org") == ORG]
workflows = {p: json.loads(p.read_text(encoding="utf-8")) for p in wf_paths}
by_proc = {w["process"]: w for w in workflows.values()}
R = {r["id"]: r for r in org["roles"]}
P = {p["id"]: p for p in org["process_map"]}
RES = {r["id"]: r for r in org["resources"]}
U = {u["id"]: u for u in org["units"]}
log = []

# Headcounts before this script, so a second run adds nothing. Roles the sync added count from zero.
BASE_FILE = Path(__file__).with_suffix(".before.json")  # headcounts before the first run
if BASE_FILE.exists():
    base = json.loads(BASE_FILE.read_text(encoding="utf-8"))
else:
    base = {"roles": {r["id"]: r["headcount"] for r in org["roles"] if r["id"] != "truck-driver"},
            "employees": org["profile"]["employees"],
            "units": {u["id"]: u["headcount"] for u in org["units"]},
            "drivers": {d["id"]: d["per_month"] for d in org["demand_drivers"]}}
    BASE_FILE.write_text(json.dumps(base, indent=1), encoding="utf-8")

HOURLY = {"general-foreman", "foreman", "carpenter", "cement-finisher", "labourer", "equipment-operator",
          "crane-operator", "mechanic", "truck-driver"}


def add_note(ev, text):
    """Append a sentence to an evidence note under one dated tag, once."""
    tag = f"Revised {TODAY}:"
    note = ev.get("note", "")
    if text in note:
        return
    ev["note"] = f"{note} {text}" if tag in note else f"{note} {tag} {text}".strip()


# ---------------------------------------------------------------- 1. Sources and Bird's staffing
SRC = {"id": "src-bird-aif20", "title": "Bird Construction Inc. Annual Information Form 2020",
       "publisher": "Bird Construction Inc.",
       "url": "https://cdn.bird.ca/2025/03/20204424/annual-information-form-2020d55d64d06e724069900aa84fff156498.pdf",
       "year": 2021, "accessed": TODAY,
       "supports": "Section 3.1.8: about 2,041 full-time salaried and 2,465 hourly employees (1,106 unionized) at 31 "
                   "December 2020, after the Stuart Olson acquisition; about 880 salaried and 1,578 hourly (1,211 "
                   "unionized) at 31 December 2019. Section 3.2.7: Bird secures contracts through competitive bids or "
                   "negotiation. Backlog includes work orders under master service agreements."}
if SRC["id"] not in {s["id"] for s in org["sources"]}:
    org["sources"].append(SRC)
scale = {s["name"]: s for s in org["profile"]["scale"]}
for name, value in [("Bird Construction salaried employees at 31 December 2019", 880),
                    ("Bird Construction hourly employees at 31 December 2019", 1578)]:
    if name not in scale:
        org["profile"]["scale"].append({"name": name, "value": value, "unit": "people",
                                        "evidence": {"tier": "A", "sources": ["src-bird-aif20"], "note": ""}})

# ---------------------------------------------------------------- 2. Site staff hours, foremen and crews
SITE = ["superintendent", "asst-super", "field-engineer"]
for rid in SITE:
    R[rid]["productive_hours_per_month"] = 180
    add_note(R[rid]["evidence"],
             "Site staff work 10-hour days and some Saturdays in the construction season (about 190 hours a month, "
             "as gc-ops-site-coordination records) and shorter winter weeks, so they are sized at 180 productive "
             "hours a month rather than the extended_hours default of 140.")

if R["foreman"]["headcount"] < 135:
    moved = {"carpenter": 25, "labourer": 12, "cement-finisher": 8}
    for rid, n in moved.items():
        R[rid]["headcount"] -= n
        add_note(R[rid]["evidence"], f"{n} moved to foreman, so that each of the 135 crews has a working foreman "
                                     "drawn from its own trade; the hourly workforce is unchanged.")
    old = R["foreman"]["headcount"]
    R["foreman"]["headcount"] = 135
    add_note(R["foreman"]["evidence"],
             f"headcount {old} raised to 135, one working foreman for each crew in the resources (75 concrete, 25 "
             "finishing, 35 general), as the gc-09 workflow author found. The 45 come from the crews' carpenters (25), "
             "labourers (12) and cement finishers (8).")
log.append("site staff at 180 productive hours; foremen 90 -> 135 from the crews' own trades")

td = R["truck-driver"]
td["reports_to"] = "equipment-manager"
if "Added from gc-spe-equipment-dispatch" not in td["evidence"]["note"]:
    td["evidence"]["note"] = ("Added from gc-spe-equipment-dispatch, whose author found no role for the 14 boom "
                              "and flatbed trucks the resources list. Hourly union driver; headcount follows the "
                              "documented deliveries.")

# ---------------------------------------------------------------- 3. Volumes the workflows checked
VOL = ["ops-rfi", "legal-lien-adjudication", "fin-holdback-release", "scm-subcontractor-prequal",
       "bd-p3-pursuit", "bd-preconstruction-services"]
for pid in VOL:
    w = by_proc[pid]
    P[pid]["cases_per_month"] = dict(w["volume"]["cases_per_month"])
    ev = w["volume"].get("evidence") or {}
    P[pid]["evidence"] = {"tier": ev.get("tier", "C"), "sources": list(ev.get("sources", [])),
                          "note": f"Volume from {w['id']} ({TODAY}): {ev.get('note', '')}".strip()}
    for s in P[pid]["evidence"]["sources"]:
        if s not in {x["id"] for x in org["sources"]}:
            org["sources"].append(dict(next(x for x in w["sources"] if x["id"] == s)))
P["bd-p3-pursuit"]["unit_of_work"] = "one P3 pursuit, from screening the opportunity to financial close or loss"
P["bd-p3-pursuit"]["cadence"] = "per_case"
P["bd-preconstruction-services"]["unit_of_work"] = ("one preconstruction engagement, from the signed preconstruction "
                                                    "agreement to an agreed construction price")
P["bd-preconstruction-services"]["cadence"] = "per_case"
log.append("volumes from workflows: RFIs 2,200, liens and adjudications 5, holdback releases 16, prequalifications "
           "110, P3 pursuits 0.2 and preconstruction engagements 1.3 started a month")

# ---------------------------------------------------------------- 4. Links and descriptions
ca = P["bd-contract-award"]
bond = [t for t in ca["triggered_by"] if t["from"] == "fin-surety-bonding"]
for t in bond:
    ca["triggered_by"].remove(t)
    if not any(i["from"] == t["from"] and i["object"] == t["object"] for i in ca.setdefault("inputs", [])):
        ca["inputs"].append(t)
if "negotiated" not in ca["description"]:
    ca["description"] += (" About half of the 10 awards a month come from the bid and proposal processes (about 3 from "
                          "stipulated bids at a 1-in-7 hit rate and about 2 from CM and design-build proposals); the "
                          "rest are negotiated work for repeat clients, contract extensions and work orders under "
                          "master service agreements, which skip formal bidding.")
    add_note(ca["evidence"], "The gc-01 author found that the bid processes yield about 5 awards a month, not 10. "
                             "Bird secures work through bids or negotiation and books master service agreement work "
                             "orders (src-bird-aif20), so the remainder is recorded as negotiated work.")
    ca["evidence"]["sources"] = sorted(set(ca["evidence"]["sources"]) | {"src-bird-aif20"})

cr = P["spe-crane-operations"]
cr["produces"] = [t for t in cr["produces"] if not (t["to"] == "ministry-labour" and t["object"] == "lift_plan")]

APP = "substantial_performance_application"
if APP not in {b["id"] for b in org["business_objects"]}:
    org["business_objects"].append({"id": APP, "name": "Application for substantial performance",
                                    "description": "The contractor's application to the payment certifier, with "
                                                   "the deficiency status and cost to complete, asking for the "
                                                   "certificate of substantial performance."})
for t in P["ops-deficiency-closeout"]["produces"]:
    if t["to"] == "consultant" and t["object"] == "substantial_performance_cert":
        t["object"] = APP
w = by_proc["ops-deficiency-closeout"]
for t in w["interfaces"]["produces"]:
    if t["to"] == "consultant" and t["object"] == "substantial_performance_cert":
        t["object"] = APP
note = (f"Organisation file corrected on {TODAY}: the contractor sends the consultant an application for substantial "
        "performance; the consultant issues the certificate, so the output to consultant is now "
        "substantial_performance_application.")
if note not in w["assumptions"]:
    w["assumptions"].append(note)

sp = P["fin-sub-invoice-payment"]
sp["description"] = sp["description"].replace(
    "payment goes out within 7 days of receiving the owner's payment.",
    "payment goes out within 7 days of receiving the owner's payment on Ontario contracts procured after 1 October "
    "2019; older contracts and most work in other provinces pay when the owner pays.")
log.append("links: surety bond is an input to contract award; lift plan to the Ministry of Labour removed; "
           "substantial performance application to consultant")

# ---------------------------------------------------------------- 5. Resize roles to the documented work


def measure_load():
    """Hands-on hours a month per role and per process, from simulating every workflow (seeded)."""
    load, parts = {}, {}
    for wf in workflows.values():
        by = {s["id"]: s for s in wf["steps"]}
        rng, n_cases, tot = random.Random(20261124), 2000, {}
        for _ in range(n_cases):
            cur, n = wf["steps"][0]["id"], 0
            while cur != "END" and n < 200:
                s = by[cur]
                tot[s["role"]] = tot.get(s["role"], 0.0) + V.sample(s["touch_min"], rng) * float(s.get("people", 1))
                draw, acc, chosen = rng.random(), 0.0, s["next"][-1]
                for e in s["next"]:
                    acc += float(e["prob"])
                    if draw <= acc:
                        chosen = e
                        break
                cur, n = chosen["to"], n + 1
        vol = float(wf["volume"]["cases_per_month"]["mode"])
        for role, minutes in tot.items():
            h = minutes / n_cases / 60 * vol
            load[role] = load.get(role, 0.0) + h
            parts.setdefault(role, []).append((wf["process"], h))
    return load, parts


TARGET = 0.97
resized = []
load, parts = measure_load()
for rid, hours in sorted(load.items()):
    role = R.get(rid)
    if role is None or role.get("layer") == "external_party":
        continue
    cap = role.get("productive_hours_per_month") or V.PRODUCTIVE_HOURS[role.get("shift_pattern", "office_hours")]
    fte = hours / cap
    need = math.ceil(fte / TARGET)
    if need <= role["headcount"]:
        continue  # covered, including by an earlier run of this script
    top = ", ".join(f"{p} {h:,.0f}" for p, h in sorted(parts[rid], key=lambda x: -x[1])[:3])
    old = role["headcount"]
    text = (f"headcount {old} raised to {need} to cover the hands-on work the workflows record: about {hours:,.0f} "
            f"hours a month (largest: {top}), which is {fte:.1f} FTE at {cap} productive hours a month, sized to "
            f"{TARGET:.0%} load. Work in processes without a workflow is not counted.")
    if rid == "superintendent":
        text += (" Daily site coordination counts every active project-day at an average of about 4.7 superintendent "
                 "hours, across large and small projects.")
    role["headcount"] = need
    add_note(role["evidence"], text)
    resized.append(f"{rid} {old}->{need}")
log.append("roles resized: " + "; ".join(resized))

# ---------------------------------------------------------------- 6. Units, employees and demand drivers
delta = {r["id"]: r["headcount"] - base["roles"].get(r["id"], 0) for r in org["roles"]}
REGIONS = ["ops-on", "ops-west", "ops-atl"]
reg_base = {u: base["units"][u] for u in REGIONS}
unit_add = {}
for rid, d in delta.items():
    if not d:
        continue
    uid = R[rid]["unit"]
    if uid == "ops":  # project staff are listed at division level and work in the regions
        share = sum(reg_base.values())
        for i, reg in enumerate(REGIONS):
            unit_add[reg] = unit_add.get(reg, 0) + d * reg_base[reg] / share
    else:
        unit_add[uid] = unit_add.get(uid, 0) + d
own_add = {u: round(v) for u, v in unit_add.items()}
kids = {}
for u in org["units"]:
    if u["parent"]:
        kids.setdefault(u["parent"], []).append(u["id"])


def added(uid):
    return own_add.get(uid, 0) + sum(added(k) for k in kids.get(uid, []))


for u in org["units"]:
    u["headcount"] = base["units"][u["id"]] + added(u["id"])
employees = base["employees"] + sum(added(u["id"]) for u in org["units"] if not u["parent"])
org["profile"]["employees"] = employees
sal = sum(d for rid, d in delta.items() if rid not in HOURLY)
hrly = sum(d for rid, d in delta.items() if rid in HOURLY)
dd = {d["id"]: d for d in org["demand_drivers"]}
for did, add in [("salaried-staff", sal), ("field-workforce", hrly)]:
    b = base["drivers"][did]
    dd[did]["per_month"] = {k: b[k] + add for k in ("low", "mode", "high")}
add_note(dd["salaried-staff"]["evidence"], f"raised by {sal} for the salaried roles resized to their documented work.")
log.append(f"employees {base['employees']} -> {employees} ({sal:+d} salaried, {hrly:+d} hourly)")

asm = org["assumptions"]
for i, a in enumerate(asm):
    if a.startswith("Bird's annual information forms and annual reports"):
        asm[i] = ("Bird's 2020 annual information form (src-bird-aif20) gives its staffing: about 880 salaried and "
                  "1,578 hourly employees at 31 December 2019, on 2019 revenue of $1,376.4 million. Office lists and "
                  "self-perform shares remain tier C estimates.")
    if a.startswith("Employees = about"):
        asm[i] = (f"Employees = about {1470 + sal:,} salaried staff plus about {1330 + hrly:,} hourly union trades on "
                  "average; hourly headcount swings from about 1,050 in winter to 1,700 in summer. Headcounts were "
                  f"first set at 2,800 and raised on {TODAY} to {employees:,} to cover the work the workflows record. "
                  "Bird's total at the end of 2019 (2,458 for $1.38 billion of revenue) scales to about 2,680 at this "
                  "company's $1.5 billion, but Bird's split was about 36% salaried, against about half here.")
SITE_ASM = ("Superintendents, assistant superintendents and field engineers are sized at 180 productive hours a month "
            "(productive_hours_per_month): their paid time is nearly all on site, with 10-hour days and some Saturdays "
            "in season.")
if SITE_ASM not in asm:
    asm.append(SITE_ASM)

# ---------------------------------------------------------------- 7. Workflows: role titles and productive hours
for wf in workflows.values():
    for r in wf["roles"]:
        if r["id"] in R:
            r["title"] = R[r["id"]]["title"]
            if "productive_hours_per_month" in R[r["id"]]:
                r["productive_hours_per_month"] = R[r["id"]]["productive_hours_per_month"]

org_path.write_text(json.dumps(org, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for path, wf in workflows.items():
    path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\n".join(log))
