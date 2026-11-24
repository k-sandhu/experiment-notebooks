"""Corrections to the hospital file from its workflow authors' reports (2026-11-24).

community-hospital-corp is modelled on Halton Healthcare's public figures for 2018/19 to 2021/22. Its employee
count is an average of the reported staff counts plus the medical staff, so it is kept as the anchor: roles grow
within their units' unassigned headcount, and a unit grows only when its listed roles exceed it.

What this script does:
  - Surgeries: the reported 45,256 surgeries a year include endoscopies, which the map also counts in
    sx-endoscopy (1,300 a month). Operating room cases become surgeries less endoscopies, about 2,450 a month,
    and elective bookings and add-on cases follow. This is most of the operating room shortfall the
    workflow author found.
  - ICU nurses are set from bedside coverage (30 beds at one nurse to one or two patients, around the clock),
    about 97 FTE, which is about 140 people at the part-time share the role headcounts assume.
  - Charge nurses on the medicine units come out of the medicine RN headcount; the other roles the workflows
    added get units and reporting lines.
  - Every role whose documented hands-on work exceeds its headcount is resized to cover that work at 97% of
    productive hours. Headcounts here are people, many part-time, so this is a floor.
  - Volumes the workflow authors checked against CIHI and the Auditor General replace the map's estimates, and
    a few links become inputs or are removed.

Run tools/sync_map_from_workflows.py community-hospital-corp first. Safe to run twice.

Usage:
    python fixes_2026_11_24_hospital.py [ROOT]
"""
import json
import math
import random
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools"))
import validate as V  # noqa: E402

ORG = "community-hospital-corp"
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
log = []

ADDED_BY_SYNC = {"patient_care_coordinator", "rehab_assistant", "dialysis_assistant", "icu_charge_nurse",
                 "med_charge_nurse", "ipac_physician", "hearing_screener"}
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


def set_volume(pid, vol, note):
    P[pid]["cases_per_month"] = dict(vol)
    add_note(P[pid]["evidence"], note)
    if pid in by_proc:
        w = by_proc[pid]
        ratio = vol["mode"] / float(w["volume"]["cases_per_month"]["mode"])
        if ratio != 1:  # stated FTE scale with the volume
            for r in w["roles"]:
                r["fte_on_process"] = round(float(r["fte_on_process"]) * ratio, 2)
        w["volume"]["cases_per_month"] = dict(vol)
        wf_note(w, note + " Stated FTE on this process were scaled to the new volume.")


# ---------------------------------------------------------------- 1. Operating room cases
OR_CASES = {"low": 2200, "mode": 2450, "high": 2600}
set_volume("sx-perioperative-case", OR_CASES,
           "operating room cases are the reported surgeries less endoscopies (about 1,300 a month, counted in "
           "sx-endoscopy and done in the endoscopy rooms), about 2,450 a month. Previously all 3,700 reported "
           "surgeries went through the operating rooms, which needed about twice the room hours the 17 rooms have.")
set_volume("sx-surgical-booking", {"low": 1900, "mode": 2150, "high": 2300},
           "elective bookings are about 87% of operating room cases (the Auditor General gives 13% emergencies), "
           "about 2,150 a month, now that endoscopies are counted only in sx-endoscopy.")
set_volume("sx-emergency-surgery", {"low": 290, "mode": 320, "high": 340},
           "add-on cases are about 13% of operating room cases (Auditor General of Ontario), about 320 a month.")
P["sx-perioperative-case"]["description"] = P["sx-perioperative-case"]["description"].rstrip()
if "run through sx-endoscopy" not in P["sx-perioperative-case"]["description"]:
    P["sx-perioperative-case"]["description"] += (" Cases are operating room surgeries; endoscopies, which the "
                                                  "annual reports include in surgeries, run through sx-endoscopy.")
add_note(P["sx-endoscopy"]["evidence"], "the reported surgeries include these procedures, so they are no longer "
                                        "also counted as operating room cases.")
add_note(RES["operating_rooms"]["evidence"],
         "2,450 operating room cases a month at about 1.5 room-hours each need about 3,700 room-hours against about "
         "2,800 in 17 rooms at 165 hours; the gap is about a quarter and is open. Short procedures in procedure "
         "rooms and after-hours use of the emergency room may account for it.")
log.append("surgeries: operating room cases 3,700 -> 2,450 (endoscopies no longer counted twice); bookings 2,150; "
           "add-ons 320")

# ---------------------------------------------------------------- 2. Volumes the workflows checked
for pid in ("ed-ambulance-offload", "ed-discharge-home", "ed-admission-boarding", "cs-discharge-planning"):
    w = by_proc[pid]
    P[pid]["cases_per_month"] = dict(w["volume"]["cases_per_month"])
    ev = w["volume"].get("evidence") or {}
    kept = [x for x in P[pid]["evidence"].get("sources", []) if x not in ev.get("sources", [])]
    P[pid]["evidence"] = {"tier": ev.get("tier", "C"), "sources": list(ev.get("sources", [])) + kept,
                          "note": f"Volume from {w['id']} ({TODAY}): {ev.get('note', '')}".strip()}
    for s in P[pid]["evidence"]["sources"]:
        if s not in {x["id"] for x in org["sources"]}:
            org["sources"].append(dict(next(x for x in w["sources"] if x["id"] == s)))
P["cs-discharge-planning"]["unit_of_work"] = by_proc["cs-discharge-planning"]["unit_of_work"]
log.append("volumes from workflows: ambulance arrivals 2,600, ED discharges home 10,300, admissions from the ED "
           "1,400, discharge planning 1,700 (medicine, surgery and complex care)")

# ---------------------------------------------------------------- 3. Links
for pid in ("dx-imaging-exam", "sx-perioperative-case"):  # a hand-off during the case, not its start
    p = P[pid]
    for t in [t for t in p["triggered_by"] if t["from"] == "fs-patient-portering" and t["object"] == "transported_patient"]:
        p["triggered_by"].remove(t)
        if not any(i["from"] == t["from"] and i["object"] == t["object"] for i in p.setdefault("inputs", [])):
            p["inputs"].append(t)
hd = P["med-hemodialysis"]
hd["produces"] = [t for t in hd["produces"] if not (t["to"] == "dx-lab-specimen-collection" and t["object"] == "lab_order")]
lc = P["dx-lab-specimen-collection"]
lc["triggered_by"] = [t for t in lc["triggered_by"] if not (t["from"] == "med-hemodialysis" and t["object"] == "lab_order")]
lw = by_proc["dx-lab-specimen-collection"]
trig = lw["interfaces"]["triggered_by"]
gone = [t for t in trig if t["from"] == "med-hemodialysis" and t["object"] == "lab_order"]
if gone:
    rest = [t for t in trig if t not in gone]
    total = sum(float(t["share"]) for t in rest)
    for t in rest:
        t["share"] = round(float(t["share"]) / total, 4)
    rest[0]["share"] = round(rest[0]["share"] + 1 - sum(t["share"] for t in rest), 4)
    lw["interfaces"]["triggered_by"] = rest
    wf_note(lw, "dialysis nurses draw the monthly blood work themselves and send specimens straight to the "
                "laboratory (hosp-med-hemodialysis), so med-hemodialysis no longer triggers collection; its 4% share "
                "is spread over the other sources.")
log.append("links: portered patients are an input to imaging and surgery; dialysis sends specimens to the lab, not "
           "orders to the collection service")

# ---------------------------------------------------------------- 4. Roles the workflows added; ICU nurses
PLACE = {"med_charge_nurse": ("med_inpatient", "med_manager"), "icu_charge_nurse": ("icu", "med_manager"),
         "rehab_assistant": ("allied_health", "allied_manager"),
         "patient_care_coordinator": ("patient_flow", "patient_flow_manager"),
         "dialysis_assistant": ("renal", "med_manager"), "hearing_screener": ("maternity", "wc_manager"),
         "ipac_physician": ("medical_staff", "dept_chief")}
for rid, (unit, boss) in PLACE.items():
    R[rid]["unit"], R[rid]["reports_to"] = unit, boss
if R["med_rn"]["headcount"] == base["roles"]["med_rn"]:
    R["med_rn"]["headcount"] -= R["med_charge_nurse"]["headcount"]
    add_note(R["med_rn"]["evidence"], f"{R['med_charge_nurse']['headcount']} moved to med_charge_nurse: charge "
                                      "nurses are experienced RNs assigned to run a unit's shift.")
if R["consultant_specialist"]["headcount"] == base["roles"]["consultant_specialist"]:
    R["consultant_specialist"]["headcount"] -= 1
    add_note(R["consultant_specialist"]["evidence"], "one moved to ipac_physician, the infection control physician "
                                                     "lead, who is a credentialed specialist.")
add_note(R["ipac_practitioner"]["evidence"],
         "12 is above the published Ontario average of about 1 per 90 beds (about 7 here) and reflects the COVID-19 "
         "years in the reference period, as the hosp-06 workflow author found.")

if R["icu_rn"]["headcount"] < 140:
    old = R["icu_rn"]["headcount"]
    R["icu_rn"]["headcount"] = 140
    add_note(R["icu_rn"]["evidence"],
             f"headcount {old} raised to 140 from bedside coverage: 30 ICU beds at one nurse to one or two "
             "patients need about 20 nurses on duty around the clock, about 97 FTE at 150 productive hours, which "
             "is about 140 people at the part-time share the medicine units' headcounts imply (430 RNs for 300 "
             "beds). The workflows record only hands-on tasks, not continuous presence at the bedside, as the "
             "hosp-03 workflow author found.")
log.append("ICU nurses 110 -> 140 from bedside coverage; medicine charge nurses taken from medicine RNs")

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
    add_note(role["evidence"],
             f"headcount {old} raised to {need} to cover the hands-on work the workflows record: about {hours:,.0f} "
             f"hours a month (largest: {top}), which is {fte:.1f} FTE at {cap} productive hours a month, sized to "
             f"{TARGET:.0%} load. Headcounts are people and some work part-time, so this is a floor; work in "
             "processes without a workflow is not counted.")
    role["headcount"] = need
    resized.append(f"{rid} {old}->{need}")
log.append("roles resized: " + "; ".join(resized))

# ---------------------------------------------------------------- 6. Units and employees
# The employee count is a sourced average, so roles first use their units' unassigned headcount; a unit grows only
# when the roles listed in it (and its child units) exceed it.
in_unit = {}
for r in org["roles"]:
    in_unit[r["unit"]] = in_unit.get(r["unit"], 0) + r["headcount"] - r.get("contractor_headcount", 0)
kids = {}
for u in org["units"]:
    if u["parent"]:
        kids.setdefault(u["parent"], []).append(u["id"])


def subtree_roles(uid):
    return in_unit.get(uid, 0) + sum(subtree_roles(k) for k in kids.get(uid, []))


def size(uid):
    # Child units can be a split by site of roles listed at the parent (emergency), so the parent holds the larger
    # of its own figure, the roles listed anywhere under it, and the sum of its children.
    return max(base["units"][uid], subtree_roles(uid), sum(size(k) for k in kids.get(uid, [])))


grown = []
for u in org["units"]:
    u["headcount"] = size(u["id"])
    if u["headcount"] != base["units"][u["id"]]:
        grown.append(f"{u['id']} {base['units'][u['id']]}->{u['headcount']}")
employees = sum(u["headcount"] for u in org["units"] if not u["parent"])
org["profile"]["employees"] = employees
log.append(f"employees {base['employees']} -> {employees}; units grown: {', '.join(grown) or 'none'}")

asm = org["assumptions"]
NOTE = (f"Revised {TODAY}: role headcounts were raised where the workflows record more work than the role could "
        "do, and roles first fill their units' unassigned headcount, so the employee total moves only where a unit's "
        "listed roles exceed it. Operating room cases exclude endoscopies, which the annual reports count as "
        "surgeries and the map counts in sx-endoscopy.")
if NOTE not in asm:
    asm.append(NOTE)

# ---------------------------------------------------------------- 7. Workflows: role titles
for wf in workflows.values():
    for r in wf["roles"]:
        if r["id"] in R:
            r["title"] = R[r["id"]]["title"]

org_path.write_text(json.dumps(org, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for path, wf in workflows.items():
    path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\n".join(log))
