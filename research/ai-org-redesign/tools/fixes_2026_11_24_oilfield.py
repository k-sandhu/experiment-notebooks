"""Corrections to the oilfield services file from its workflow authors' reports (2026-11-24).

oilfield-services-co is a composite modelled mainly on Trican Well Service in 2019-2022, with STEP Energy
Services' Canadian segment for workforce and coiled tubing activity. The nine workflow batches found cementing
equipment and crews short of the stated job volume, field tickets undercounted, and roles, links and surges
that differ from what the workflows record. Trican's 2023 annual information form gives an outside check:
1,124 full and part time employees at 31 December 2022.

What this script does:
  - Cementing crews and bulk truck drivers work long on-call days in which nearly all paid time is travel and
    job time, so they get productive_hours_per_month 180 instead of the on_call default of 130.
  - Cementing units and bulk cement trucks are on call around the clock; their available hours rise to fit the
    job volume (about 14 to 15 unit-hours a job and two truck trips of about 11 hours).
  - Volumes and surges the workflows set replace the map's estimates (field tickets, job calls, mobilizations).
  - Every role whose documented hands-on work exceeds its headcount is resized to cover that work at 97% of
    productive hours, the same method as the other company files.
  - Unit headcounts and employees are recomputed from the roles. The gap to Trican's reported employees is
    recorded as an open item.

Run tools/sync_map_from_workflows.py oilfield-services-co first. Safe to run twice.

Usage:
    python fixes_2026_11_24_oilfield.py [ROOT]
"""
import json
import math
import random
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools"))
import validate as V  # noqa: E402

ORG = "oilfield-services-co"
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


def add_note(ev, text):
    """Append a sentence to an evidence note under one dated tag, once."""
    tag = f"Revised {TODAY}:"
    note = ev.get("note", "")
    if text in note:
        return
    ev["note"] = f"{note} {text}" if tag in note else f"{note} {tag} {text}".strip()


def have_src():
    return {x["id"] for x in org["sources"]}


def copy_sources(ids, wf):
    for s in ids:
        if s not in have_src():
            org["sources"].append(dict(next(x for x in wf["sources"] if x["id"] == s)))


# ---------------------------------------------------------------- 1. Outside check
SRC = {"id": "src-trican-aif23", "title": "Trican Well Service Ltd. Annual Information Form for the year ended "
                                          "December 31, 2023",
       "publisher": "Trican Well Service Ltd.",
       "url": "https://tricanwellservice.com/app/uploads/2024/02/2023-Trican-AIF.pdf", "year": 2024,
       "accessed": TODAY,
       "supports": "As at December 31, 2023, Trican had 1,195 full and part time employees (2022: 1,124)."}
if SRC["id"] not in have_src():
    org["sources"].append(SRC)
sc = {s["name"]: s for s in org["profile"]["scale"]}
if "Trican employees at 31 December 2022" not in sc:
    org["profile"]["scale"].append({"name": "Trican employees at 31 December 2022", "value": 1124,
                                    "unit": "full and part time employees",
                                    "evidence": {"tier": "A", "sources": ["src-trican-aif23"], "note": ""}})

# ---------------------------------------------------------------- 2. Cementing crews and equipment
CEM = ["cem-operator", "cem-supervisor", "bulk-truck-driver"]
for rid in CEM:
    R[rid]["productive_hours_per_month"] = 180
    add_note(R[rid]["evidence"],
             "sized at 180 productive hours a month: cementing crews and bulk drivers are on call around the clock "
             "and work long job days in which nearly all paid time is travel, rig-up, pumping and rig-down, so the "
             "on_call default of 130 understates their capacity.")
cu = RES["cementing-unit"]
cu["available_hours_per_month"] = {"low": 300, "mode": 400, "high": 480}
add_note(cu["evidence"], "available hours raised to about 400 a month: units are on call around the clock and each "
                         "job ties a unit up for about 14 to 15 hours with travel and waiting, so 400 jobs a month on "
                         "16 to 17 units need about 350 to 450 hours each, as the ofs-04 workflow author found.")
bt = RES["bulk-cement-truck"]
bt["available_hours_per_month"] = {"low": 200, "mode": 240, "high": 300}
add_note(bt["evidence"], "available hours raised to about 240 a month for on-call operation: two trucks of about 11 "
                         "hours each per job, 400 jobs a month, need about 8,800 truck-hours, which 45 trucks at the "
                         "earlier 190 hours could not supply.")
log.append("cementing: crews and bulk drivers at 180 productive hours; units 400 and bulk trucks 240 available hours")

# ---------------------------------------------------------------- 3. Volumes, surges, links and owners
changed_vol, changed_surge = [], []
for pid, w in sorted(by_proc.items()):
    wv = w["volume"]["cases_per_month"]
    if P[pid]["cases_per_month"] != wv:
        P[pid]["cases_per_month"] = dict(wv)
        ev = w["volume"].get("evidence") or {}
        kept = [x for x in P[pid]["evidence"].get("sources", []) if x not in ev.get("sources", [])]
        P[pid]["evidence"] = {"tier": ev.get("tier", "C"), "sources": list(ev.get("sources", [])) + kept,
                              "note": f"Volume from {w['id']} ({TODAY}): {ev.get('note', '')}".strip()}
        copy_sources(ev.get("sources", []), w)
        changed_vol.append(f"{pid} {wv['mode']:g}")
    if w.get("unit_of_work") and P[pid]["unit_of_work"] != w["unit_of_work"]:
        P[pid]["unit_of_work"] = w["unit_of_work"]
    ws = w["volume"].get("surge")
    if ws and P[pid].get("surge", {}).get("volume_multiplier") != ws["volume_multiplier"]:
        P[pid]["surge"] = json.loads(json.dumps(ws))
        copy_sources(ws.get("evidence", {}).get("sources", []), w)
        changed_surge.append(pid)
log.append("volumes from workflows: " + ", ".join(changed_vol))
log.append(f"surges from workflows: {len(changed_surge)} processes")

ft = P["fo-dist-field-ticket-preparation"]  # the signed ticket is what the process produces, not what starts it
ft["triggered_by"] = [t for t in ft["triggered_by"] if not (t["from"] == "customer-wellsite-supervisor"
                                                             and t["object"] == "signed_field_ticket")]
P["hs-incident-reporting-and-investigation"]["driver"] = "field-headcount"
P["hs-pre-job-hazard-assessment"]["owner_unit"] = "fo"
add_note(P["hs-pre-job-hazard-assessment"]["evidence"],
         "owned by field operations: service-line supervisors lead the hazard assessments, with HSE advisors in "
         "support, as the ofs-05 workflow author found.")
log.append("links: signed field ticket is an output, not a trigger; incidents driven by field headcount; hazard "
           "assessments owned by field operations")

# ---------------------------------------------------------------- 4. Resize roles to the documented work


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
    if rid == "design-engineer":
        text += " About 7 of them design cement slurries; the file has no separate cement engineer role."
    add_note(role["evidence"], text)
    role["headcount"] = need
    resized.append(f"{rid} {old}->{need}")
log.append("roles resized: " + "; ".join(resized))

# ---------------------------------------------------------------- 5. Units, employees and profile
emp = {r["id"]: r["headcount"] - r.get("contractor_headcount", 0) for r in org["roles"]}
own = {}
for r in org["roles"]:
    own[r["unit"]] = own.get(r["unit"], 0) + emp[r["id"]]
kids = {}
for u in org["units"]:
    if u["parent"]:
        kids.setdefault(u["parent"], []).append(u["id"])


def total(uid):
    return own.get(uid, 0) + sum(total(k) for k in kids.get(uid, []))


for u in org["units"]:
    u["headcount"] = total(u["id"])
employees = sum(emp.values())
org["profile"]["employees"] = employees
sc["Employees"]["value"] = employees
add_note(sc["Employees"]["evidence"],
         f"recomputed from the roles after they were raised to the work the workflows record: {employees}. Trican "
         "reported 1,124 full and part time employees at the end of 2022 (src-trican-aif23), so this file is about "
         f"{employees / 1124 - 1:.0%} above the company it is modelled on.")
dd = {d["id"]: d for d in org["demand_drivers"]}
field = sum(emp[r["id"]] for r in org["roles"] if r["unit"].startswith("fo"))
dd["field-headcount"]["per_month"] = {"low": round(field * 0.9), "mode": field, "high": round(field * 1.05)}

asm = org["assumptions"]
for i, a in enumerate(asm):
    if a.startswith("Headcount (1,350) is a tier C estimate"):
        asm[i] = (f"Headcount was first set at 1,350 (tier C) and revised on {TODAY} to {employees:,} to cover the work "
                  "the workflows record. Trican reported 1,124 full and part time employees at the end of 2022 "
                  "(src-trican-aif23), so the file sits above the company it is modelled on; crew sizes, contracted "
                  "trucking or workflow step times may explain the gap. Role headcounts are sized from crew counts at "
                  "three rotating shift crews per 24-hour frac or coiled tubing crew.")
log.append(f"employees recomputed from roles: {employees} (field operations {field}); Trican 2022: 1,124")

# ---------------------------------------------------------------- 6. Workflows: role titles and productive hours
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
