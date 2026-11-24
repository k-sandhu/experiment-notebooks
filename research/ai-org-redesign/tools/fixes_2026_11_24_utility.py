"""Corrections to the electricity distributor file from its workflow authors' reports (2026-11-24).

electric-distribution-utility is a composite modelled mainly on Hydro Ottawa Limited in 2019-2022. The ten
workflow batches found that locates are done by contractors in practice, that several volumes and surges
differ from the evidence, and that many roles cannot do the documented work at their headcount.

What this script does:
  - Locates: the 38 contract locators the locate workflow needs are recorded as contractor staff, not employees.
  - Volumes and surges the workflows set with evidence replace the map's estimates (cable faults, inspections,
    vegetation, major events and others).
  - Every role whose documented hands-on work exceeds its headcount is resized to cover that work at 97% of
    productive hours, the same method as the other company files. The work is measured by simulating each
    workflow, as tools/validate.py does.
  - Unit headcounts and employees are recomputed from the roles, leaving contractor staff out. Hydro Ottawa
    reported 581 FTE for 2020; the gap between that and the resized total is recorded as the main open item.

Run tools/sync_map_from_workflows.py electric-distribution-utility first. Safe to run twice.

Usage:
    python fixes_2026_11_24_utility.py [ROOT]
"""
import json
import math
import random
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools"))
import validate as V  # noqa: E402

ORG = "electric-distribution-utility"
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


# ---------------------------------------------------------------- 1. Contract locators
cl = R["contract-locator"]
cl["contractor_headcount"] = cl["headcount"]
cl["reports_to"] = "field-services-supervisor"
if not cl["evidence"]["note"].startswith("Added from edu-ops-locates. Contract"):
    cl["evidence"]["note"] = (
        "Added from edu-ops-locates. Contract locate service providers mark most of about 7,500 locate requests a "
        "month; the workflow author found a later Hydro Ottawa rate filing excerpt saying external vendors did the "
        "locates at about $3.1 million a year. They are contractor staff, not employees; in-house cable locators "
        "keep complex and urgent jobs.")
add_note(P["ops-locates"]["evidence"], "most locates are marked by contract locators (contract-locator, contractor "
                                       "staff); in-house locators handle complex and urgent jobs.")
log.append(f"locates: {cl['headcount']} contract locators recorded as contractor staff")

# ---------------------------------------------------------------- 2. Volumes and surges from the workflows
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

# ---------------------------------------------------------------- 3. Descriptions and facts
cp = P["corp-public-safety-compliance"]
cp["description"] = cp["description"].replace(
    "report serious electrical incidents to the Electrical Safety Authority, which audits compliance each year.",
    "report serious electrical incidents to the Electrical Safety Authority. Each year the utility hires an "
    "ESA-approved auditor, ESA reviews the auditor's report, and a professional engineer, director or officer "
    "signs the Declaration of Compliance.")
me = P["ops-major-event-response"]
if "Hydro One" not in me["description"]:
    me["description"] += (" In 2019 to 2022 there were nine major events: five were losses of supply from Hydro One, "
                          "three opened the incident command centre, and only the May 2022 derecho used mutual aid.")
sc = {s["name"]: s for s in org["profile"]["scale"]}
w = by_proc["ops-station-maintenance"]
copy_sources(["ho_stations2021"], w)
add_note(sc["Substations"]["evidence"], "Hydro Ottawa's 2021 blog post on its stations (ho_stations2021) gives 92.")
if "ho_stations2021" not in sc["Substations"]["evidence"]["sources"]:
    sc["Substations"]["evidence"]["sources"].append("ho_stations2021")
add_note(P["fin-rate-application"]["evidence"],
         "the OEB backgrounder gives a proposed 2021 base revenue requirement of $203.9 million; the description's "
         "$216.6 million may be the service revenue requirement, as the edu-09 workflow author noted.")
log.append("descriptions: ESA audit by an approved auditor; major events mostly Hydro One supply losses")

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
    if rid == "meter-technician":
        text += (" Seal-expiry exchange campaigns may be partly contracted out, as Hydro One does; if so, part of "
                 "this work belongs to contractor staff.")
    if rid in ("billing-analyst", "field-service-rep"):
        text += " Part of the work rests on unsourced volumes (billing exceptions, field service orders)."
    if rid in ("contract-locator",):
        role["contractor_headcount"] = need
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
log.append(f"employees recomputed from roles: {employees} (contract locators excluded)")

asm = org["assumptions"]
for i, a in enumerate(asm):
    if a.startswith("Corporate functions (HR, IT, finance"):
        asm[i] = ("Corporate functions (HR, IT, finance, legal, communications, fleet and facilities) are shown inside "
                  "the distribution company. Hydro Ottawa reported 581 FTE for 2020 (668 in the holding company). "
                  f"Role headcounts were about 570 until {TODAY}, when roles were raised to the work the workflows "
                  f"record, giving {employees} employees, about {employees / 581 - 1:.0%} above the reported FTE. Either "
                  "some workflow volumes and step times are high, or more work is contracted out than the file shows; "
                  "locates are already shown as contracted.")
log.append(f"gap to Hydro Ottawa's 581 FTE: {employees - 581:+d}")

# ---------------------------------------------------------------- 6. Workflows: role titles
for wf in workflows.values():
    for r in wf["roles"]:
        if r["id"] in R:
            r["title"] = R[r["id"]]["title"]

org_path.write_text(json.dumps(org, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for path, wf in workflows.items():
    path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\n".join(log))
