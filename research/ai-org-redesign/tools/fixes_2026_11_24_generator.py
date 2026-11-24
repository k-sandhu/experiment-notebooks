"""Corrections to the power generator file from its workflow authors' reports (2026-11-24).

power-generation-co is an archetype of an Alberta-centred listed generator, built mainly from TransAlta's
filings for its Alberta fleet. The ten workflow batches found volumes counted in project-months or all
trades where the work is counted in projects or hedge trades, converted-unit operator staffing that looks
like coal-era staffing, wind technician work recorded for the lead technician only, and roles, links and
surges that differ from what the workflows record.

What this script does:
  - The three wind workflows predate the step field `people` and record only the lead technician's minutes,
    although technicians climb in pairs and component exchanges use a crew of about four. Their at-turbine
    steps get `people` 2 (or 4 on lift days), so the staffing check counts the whole crew.
  - Converted-unit operators are set from shift coverage: two plant sites, five crews, one shift supervisor per
    site per shift, and the control room and field operators the documented work needs. 112 becomes 75.
  - Every role whose documented hands-on work exceeds its headcount is resized to cover that work at 97% of
    productive hours. The work is measured by simulating each workflow, as tools/validate.py does.
  - Volumes, units of work and surges follow the workflows, which checked them against TransAlta's filings and
    AESO rules; the roles the workflows added get units and reporting lines.
  - Employees and unit headcounts change by the headcount added or removed.

Run tools/sync_map_from_workflows.py power-generation-co first. Safe to run twice.

Usage:
    python fixes_2026_11_24_generator.py [ROOT]
"""
import json
import math
import random
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools"))
import validate as V  # noqa: E402

ORG = "power-generation-co"
TODAY = "2026-11-24"
org_path = root / "organisations" / f"{ORG}.json"
org = json.loads(org_path.read_text(encoding="utf-8"))
wf_paths = [p for p in sorted((root / "workflows").glob("*.json"))
            if json.loads(p.read_text(encoding="utf-8")).get("org") == ORG]
workflows = {p: json.loads(p.read_text(encoding="utf-8")) for p in wf_paths}
by_proc = {w["process"]: w for w in workflows.values()}
R = {r["id"]: r for r in org["roles"]}
P = {p["id"]: p for p in org["process_map"]}
log = []

ADDED_BY_SYNC = {"accounting_manager", "budget_holder", "permit_coordinator", "hydro_scheduler"}
BASE_FILE = Path(__file__).with_suffix(".before.json")  # headcounts before the first run
if BASE_FILE.exists():
    base = json.loads(BASE_FILE.read_text(encoding="utf-8"))
else:
    base = {"roles": {r["id"]: r["headcount"] for r in org["roles"] if r["id"] not in ADDED_BY_SYNC},
            "employees": org["profile"]["employees"],
            "units": {u["id"]: u["headcount"] for u in org["units"]}}
    BASE_FILE.write_text(json.dumps(base, indent=1), encoding="utf-8")


def add_note(ev, text):
    """Append a sentence to an evidence note under one dated tag, once."""
    tag = f"Revised {TODAY}:"
    note = ev.get("note", "")
    if text in note:
        return
    ev["note"] = f"{note} {text}" if tag in note else f"{note} {tag} {text}".strip()


def wf_note(wf, text):
    text = f"Organisation file corrected on {TODAY}: {text}"
    if text not in wf["assumptions"]:
        wf["assumptions"].append(text)


# ---------------------------------------------------------------- 1. Wind crews
CREW = {"wnd-troubleshoot-turbines": ({"s07", "s08", "s09", "s10", "s11", "s12", "s13", "s15", "s19", "s22"}, 2),
        "wnd-scheduled-service": ({"s09", "s10", "s11", "s12", "s13", "s14", "s15", "s16", "s17"}, 2)}
for pid, (ids, n) in CREW.items():
    w = by_proc[pid]
    for s in w["steps"]:
        if s["id"] in ids and s["role"] == "wind_technician":
            s["people"] = n
    wf_note(w, "technicians climb in pairs, so the steps from the drive to the turbine to the drive back now carry "
               "people 2, and the staffing check counts both technicians.")
w = by_proc["wnd-main-component-exchange"]
for s in w["steps"]:
    if s["role"] == "wind_technician":
        s["people"] = 4 if s["id"] in ("s15", "s16", "s17") else 2
wf_note(w, "the lift-day steps now carry people 4 and the inspection and commissioning steps people 2, so the "
           "staffing check counts the crew rather than the lead technician only.")
log.append("wind workflows: crew sizes recorded with people (pairs, and four on lift days)")

# ---------------------------------------------------------------- 2. Converted-unit operators
SHIFT = {"shift_supervisor_gas": 10, "control_room_operator_gas": 25, "field_operator_gas": 40}
for rid, n in SHIFT.items():
    old = R[rid]["headcount"]
    if old != n and f"set to {n} from shift coverage" not in R[rid]["evidence"]["note"]:
        R[rid]["headcount"] = n
        add_note(R[rid]["evidence"],
                 f"headcount {old} set to {n} from shift coverage. The three converted units sit at two plant sites "
                 "staffed by five rotating crews; each site has one shift supervisor per shift, and the control room "
                 "and field operators cover the work the gas operation, permit and maintenance workflows record "
                 "(about 23 and 38 FTE at 150 productive hours). The earlier 112 operators matched coal-era "
                 "staffing with coal handling, as the gen-04 workflow author found; gas firing needs about 6 to 8 "
                 "people per site per shift.")
log.append("converted-unit operators 112 -> 75 (10 shift supervisors, 25 control room, 40 field)")

# ---------------------------------------------------------------- 3. Roles the workflows added; other role facts
R["permit_coordinator"].update({"unit": "gas-wabamun", "reports_to": "plant_manager_gas"})
post = next(x for x in by_proc["gas-issue-work-permits"]["sources"] if x["id"] == "ta_permit_post")
if post["id"] not in {x["id"] for x in org["sources"]}:
    org["sources"].append(dict(post))
R["permit_coordinator"]["evidence"]["tier"] = "B"
R["permit_coordinator"]["evidence"]["sources"] = ["ta_permit_post"]
if not R["permit_coordinator"]["evidence"]["note"].startswith("Added from gen-gas-issue-work-permits. TransAlta"):
    R["permit_coordinator"]["evidence"]["note"] = (
        "Added from gen-gas-issue-work-permits. TransAlta's careers site lists a permit coordinator position at "
        "Wabamun; day-shift power engineers who prepare isolations and permits for planned work.")
R["hydro_scheduler"].update({"unit": "hyd-control", "reports_to": "hydro_area_manager"})
if not R["hydro_scheduler"]["evidence"]["note"].startswith("Added from gen-hyd-plan-water-schedule;"):
    R["hydro_scheduler"]["evidence"]["note"] = (
        "Added from gen-hyd-plan-water-schedule; TransAlta's control centre postings name a Hydro Scheduling function. "
        "One engineer sets the weekly water schedule and storage targets.")
R["accounting_manager"]["reports_to"] = "controller"
R["budget_holder"]["reports_to"] = "controller"
if not R["budget_holder"]["evidence"]["note"].startswith("Added from gen-fin-pay-suppliers as a stand-in"):
    R["budget_holder"]["evidence"]["note"] = (
        "Added from gen-fin-pay-suppliers as a stand-in for the managers across the company who approve invoices "
        "under delegated signing authority; the headcount is the time they spend on it, counted as if one role.")
for rid in ("accountant", "ap_clerk"):
    R[rid]["reports_to"] = "accounting_manager"
R["internal_auditor"]["reports_to"] = "exec_officer"
add_note(R["internal_auditor"]["evidence"],
         "reports to the chief financial officer for administration and to the board's audit committee for its "
         "work, not to the controller whose accounts it audits.")
add_note(R["accountant"]["evidence"], "accountants and AP clerks now report to two accounting managers, not "
                                      "straight to the controller.")
R["hydro_tech"]["shift_pattern"] = "on_call"
add_note(R["hydro_tech"]["evidence"], "shift pattern on_call: day work with after-hours call-out, as "
                                      "gen-hyd-operate-plants records.")
log.append("roles: permit coordinator, hydro scheduler, accounting managers placed; internal audit reports to the "
           "CFO; hydro technicians on call")

# ---------------------------------------------------------------- 4. Volumes, units of work and surges
VOL = ["eng-execute-major-outage", "eng-plan-major-outages", "eng-manage-capital-projects", "etr-convert-coal-units",
       "gas-issue-work-permits", "gas-routine-maintenance", "hse-report-emissions-tier", "mkt-execute-hedges",
       "mkt-offer-ancillary", "hse-manage-incidents"]
have_src = lambda: {x["id"] for x in org["sources"]}  # noqa: E731
for pid in VOL:
    w = by_proc[pid]
    P[pid]["cases_per_month"] = dict(w["volume"]["cases_per_month"])
    if w.get("unit_of_work"):
        P[pid]["unit_of_work"] = w["unit_of_work"]
    ev = w["volume"].get("evidence") or {}
    kept = [x for x in P[pid]["evidence"].get("sources", []) if x not in ev.get("sources", [])]
    P[pid]["evidence"] = {"tier": ev.get("tier", "C"), "sources": list(ev.get("sources", [])) + kept,
                          "note": f"Volume from {w['id']} ({TODAY}): {ev.get('note', '')}".strip()}
    for s in P[pid]["evidence"]["sources"]:
        if s not in have_src():
            org["sources"].append(dict(next(x for x in w["sources"] if x["id"] == s)))
for pid in ("eng-manage-capital-projects", "etr-convert-coal-units"):
    P[pid]["cadence"] = "per_case"
for pid in ("eng-execute-major-outage", "eng-plan-major-outages", "mkt-execute-hedges"):
    P[pid]["driver"] = None  # the drivers count all outages reported to the AESO and all trades on the desk

for pid, w in by_proc.items():
    ws = w["volume"].get("surge")
    if ws and P[pid].get("surge", {}).get("volume_multiplier") != ws["volume_multiplier"]:
        P[pid]["surge"] = json.loads(json.dumps(ws))
        for s in ws.get("evidence", {}).get("sources", []):
            if s not in have_src():
                org["sources"].append(dict(next(x for x in w["sources"] if x["id"] == s)))
log.append("volumes from workflows: major outages 0.8 a month, capital projects 4 started, conversions 0.07, "
           "work orders 1,400, permits 1,250, hedge trades 120, reserve sessions 21, emissions reports 1.8; "
           "surges taken from the workflows")

# Links the workflow authors found wrong.
go = P["gas-operate-units"]
go["produces"] = [t for t in go["produces"] if not (t["to"] == "hr-recruit-hire" and t["object"] == "job_requisition")]
hr = P["hr-recruit-hire"]
hr["triggered_by"] = [t for t in hr["triggered_by"] if not (t["from"] == "gas-operate-units"
                                                             and t["object"] == "job_requisition")]

sc = {s["name"]: s for s in org["profile"]["scale"]}
add_note(sc["Alberta wind facilities"]["evidence"],
         "630 MW is the fleet after Windrise (206 MW) entered service in November 2021; for most of 2019 to 2021 "
         "the fleet was about 420 MW net, as the gen-06 workflow author found.")

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
        continue
    top = ", ".join(f"{p} {h:,.0f}" for p, h in sorted(parts[rid], key=lambda x: -x[1])[:3])
    old = role["headcount"]
    text = (f"headcount {old} raised to {need} to cover the hands-on work the workflows record: about {hours:,.0f} "
            f"hours a month (largest: {top}), which is {fte:.1f} FTE at {cap} productive hours a month, sized to "
            f"{TARGET:.0%} load. Work in processes without a workflow is not counted.")
    if rid == "maintenance_planner":
        text += (" The gen-05 author notes that one planner per five crafts is far above the 1:20 to 1:30 that "
                 "maintenance planning texts recommend; the workflow's planning steps are what need checking.")
    role["headcount"] = need
    add_note(role["evidence"], text)
    resized.append(f"{rid} {old}->{need}")
log.append("roles resized: " + "; ".join(resized))

# ---------------------------------------------------------------- 6. Units and employees
delta = {r["id"]: r["headcount"] - base["roles"].get(r["id"], 0) for r in org["roles"]}
unit_add = {}
for rid, d in delta.items():
    if d:
        unit_add[R[rid]["unit"]] = unit_add.get(R[rid]["unit"], 0) + d
in_unit = {}
for r in org["roles"]:
    in_unit[r["unit"]] = in_unit.get(r["unit"], 0) + r["headcount"] - r.get("contractor_headcount", 0)
kids = {}
for u in org["units"]:
    if u["parent"]:
        kids.setdefault(u["parent"], []).append(u["id"])


def added(uid):
    return unit_add.get(uid, 0) + sum(added(k) for k in kids.get(uid, []))


for u in org["units"]:  # a leaf unit holds at least its listed roles (wnd-roc listed 11 people in a unit of 10)
    if not kids.get(u["id"]):
        short = in_unit.get(u["id"], 0) - (base["units"][u["id"]] + unit_add.get(u["id"], 0))
        if short > 0:
            unit_add[u["id"]] = unit_add.get(u["id"], 0) + short
for u in org["units"]:
    u["headcount"] = base["units"][u["id"]] + added(u["id"])
employees = base["employees"] + sum(added(u["id"]) for u in org["units"] if not u["parent"])
org["profile"]["employees"] = employees
dd = {d["id"]: d for d in org["demand_drivers"]}
dd["dd_headcount"]["per_month"] = {"low": round(employees * 0.97), "mode": employees, "high": round(employees * 1.03)}
log.append(f"employees {base['employees']} -> {employees}")

asm = org["assumptions"]
for i, a in enumerate(asm):
    if a.startswith("Employees are set at 1,300"):
        asm[i] = (f"Employees were set at 1,300 for 2020-2021 and revised on {TODAY} to {employees:,}: TransAlta "
                  "reported 1,282 at the end of 2021 for the whole company; this archetype drops non-Alberta staff "
                  "but keeps the Highvale mine workforce of the wind-down years, which roughly offset each other. "
                  "The revision sets converted-unit operators from shift coverage and raises roles to the work "
                  "the workflows record. Unit and role headcounts are tier C estimates.")

# ---------------------------------------------------------------- 7. Workflows: role titles and shift patterns
for wf in workflows.values():
    for r in wf["roles"]:
        if r["id"] in R:
            r["title"] = R[r["id"]]["title"]
            if "shift_pattern" in R[r["id"]] and "shift_pattern" in r:
                r["shift_pattern"] = R[r["id"]]["shift_pattern"]

org_path.write_text(json.dumps(org, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for path, wf in workflows.items():
    path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\n".join(log))
