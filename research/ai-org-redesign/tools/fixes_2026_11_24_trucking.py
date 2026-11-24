"""Corrections to the trucking company file from its workflow authors' reports (2026-11-24).

freight-carrier-co is a composite carrier, not one real company, so most corrections make the file agree with
the work its own workflows record. The nine workflow batches found that several roles could not do the
documented work at their headcount, that owner-operators were counted twice, and that a few volumes and links
were wrong. Old Dominion Freight Line's 2021 annual report gives an outside check on driver and dock staffing
per shipment.

What this script does:
  - Drivers' on-duty hours are nearly all route time, so pickup and delivery drivers and linehaul drivers get
    productive_hours_per_month (195 and 210) instead of the shift-pattern default of 130 or 150.
  - Owner-operators: 310 in truckload, and 70 who pull LTL linehaul, counted as contractor staff in the
    linehaul driver role. 380 in all, as before, none counted as employees.
  - Every role whose documented hands-on work exceeds its headcount is resized to cover that work at 97% of
    productive hours. The work is measured by simulating each workflow, as tools/validate.py does.
  - Volumes, a surge, a demand driver, links, resource counts and the profile follow the reports.
  - Unit headcounts and the employee count are recomputed from the roles, leaving contractor staff out.

Run tools/sync_map_from_workflows.py freight-carrier-co first. Safe to run twice.

Usage:
    python fixes_2026_11_24_trucking.py [ROOT]
"""
import json
import math
import random
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tools"))
import validate as V  # noqa: E402

ORG = "freight-carrier-co"
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
    """Append a dated sentence to an evidence note once."""
    tag = f"Revised {TODAY}:"
    note = ev.get("note", "")
    if tag in note:
        note = note[:note.index(tag)].rstrip()
    ev["note"] = f"{note} {tag} {text}".strip()


# ---------------------------------------------------------------- 1. Sources
SOURCES = [
    {"id": "src-odfl21", "title": "Old Dominion Freight Line, Inc. Form 10-K for the fiscal year ended December 31, 2021",
     "publisher": "Old Dominion Freight Line, Inc. (SEC EDGAR)",
     "url": "https://www.sec.gov/Archives/edgar/data/878927/000156459022006303/odfl-10k_20211231.htm",
     "year": 2022, "accessed": TODAY,
     "supports": "At 31 December 2021 Old Dominion employed 23,663 full-time staff: 5,644 pickup and delivery drivers, "
                 "6,158 linehaul drivers, 5,350 platform (dock) employees and 609 fleet technicians. It handled "
                 "12,880 thousand LTL shipments in 2021."},
    {"id": "src-fw-gri", "title": "LTL: How do general rate increases work?", "publisher": "FreightWaves (Todd Maiden)",
     "url": "https://www.freightwaves.com/news/ltl-how-do-general-rate-increases-work", "year": 2022,
     "accessed": TODAY,
     "supports": "General rate increases are announced in Q3 or Q4 and take effect in Q1; only about 20% to 25% of "
                 "LTL carriers' business is subject to them, the rest being under contract or individual pricing."},
]
have = {s["id"] for s in org["sources"]}
for s in SOURCES:
    if s["id"] not in have:
        org["sources"].append(s)

# ---------------------------------------------------------------- 2. Drivers and owner-operators
SHIPMENTS_PER_YEAR = 1_800_000
odfl_pd = round(5644 / 12.88 * SHIPMENTS_PER_YEAR / 1e6)
odfl_dock = round(5350 / 12.88 * SHIPMENTS_PER_YEAR / 1e6)

R["pd-driver"]["productive_hours_per_month"] = 195
R["pd-driver"]["evidence"]["tier"] = "B"
R["pd-driver"]["evidence"]["sources"] = sorted(set(R["pd-driver"]["evidence"]["sources"]) | {"src-odfl21", "src-hos"})
R["linehaul-driver"]["productive_hours_per_month"] = 210
R["linehaul-driver"]["title"] = "Linehaul driver"
R["linehaul-driver"]["contractor_headcount"] = 70
R["linehaul-driver"]["evidence"]["sources"] = sorted(set(R["linehaul-driver"]["evidence"]["sources"]) | {"src-odfl21"})
R["owner-operator"]["headcount"] = 310
R["owner-operator"]["contractor_headcount"] = 310
R["owner-operator"]["title"] = "Owner-operator, truckload (contracted, not an employee)"
add_note(R["owner-operator"]["evidence"],
         "310 owner-operators haul truckload freight. Another 70 pull LTL linehaul (about a fifth of linehaul trips, "
         "as frt-ltl-linehaul-dispatch records) and are counted as contractor staff in linehaul-driver, so the "
         "carrier has 380 in all. Previously all 380 were here while the linehaul workflow also used them.")
add_note(RES["oo-tractor"]["evidence"],
         "About 70 of these pull LTL linehaul and 310 haul truckload freight.")
RES["oo-tractor"]["evidence"]["note"] = RES["oo-tractor"]["evidence"]["note"].replace("about 90 of these", "about 70 of these")
log.append("drivers: productive hours set for P&D (195) and linehaul (210); owner-operators split 310 truckload, 70 linehaul")

DRIVER_ROLES = ["pd-driver", "linehaul-driver", "tl-driver-longhaul", "tl-driver-regional"]

# ---------------------------------------------------------------- 4. Volumes, surge and descriptions
qp = P["sls-pricing-quotes"]
qp["surge"]["volume_multiplier"] = {"low": 1.2, "mode": 1.4, "high": 1.8}
qp["surge"]["cause"] = ("General rate increase and contract renewal season (shippers re-tender and ask for new quotes "
                        "after the rate increase notice)")
qp["surge"]["evidence"] = {"tier": "B", "sources": ["src-fw-gri"],
                           "note": "Only 20% to 25% of LTL revenue is subject to the general rate increase, which is "
                                   "applied to the tariff without new quotes, so the season adds less quoting work than "
                                   "the earlier 2 to 4 times; the multiplier is the workflow author's estimate."}

oo = P["tl-oo-contracting"]
oo["cases_per_month"] = {"low": 35, "mode": 50, "high": 70}
if "renewals" not in oo["description"] or "declined" not in oo["description"]:
    oo["description"] = ("The owner-operator coordinator reviews applications, checks the tractor's inspection and "
                         "insurance, signs the lease agreement and plates the unit. A case is any contract event: a new "
                         "lease, a renewal, a tractor change, a termination or a declined application. Pay terms, fuel "
                         "surcharge pass-through and chargebacks are frequent sources of disputes.")

ai = P["mnt-annual-inspection"]
if "SAAQ" not in ai["description"]:
    ai["description"] += (" Quebec-plated units are maintained under the SAAQ preventive maintenance program, which "
                          "replaces the separate annual inspection with scheduled maintenance checks.")
log.append("processes: pricing-quote surge 1.2 to 1.8, owner-operator contracting 50 a month, Quebec inspection rule")

# Links the workflows moved: daily inspection reports and timecards come from the driver-day, not each stop.
# frt-ltl-pickup-execution and frt-ltl-delivery-execution moved them to ltl-pd-dispatch; the workflows that
# receive them still name the per-stop processes, so their triggers move too, with the shares added together.
PER_STOP = ("ltl-pickup-execution", "ltl-delivery-execution")
for pid in PER_STOP:
    wf = by_proc.get(pid)
    gone = [t for t in wf["interfaces"]["produces"] if t["object"] in ("dvir", "driver_timecard")] if wf else []
    for t in gone:
        wf["interfaces"]["produces"].remove(t)
    if gone:
        note = (f"Organisation file corrected on {TODAY}: dvir and driver_timecard are produced once per driver-day by "
                "ltl-pd-dispatch, not by each stop, so they are no longer outputs of this workflow.")
        if note not in wf["assumptions"]:
            wf["assumptions"].append(note)
for wf in workflows.values():
    trig = wf["interfaces"]["triggered_by"]
    for obj in ("dvir", "driver_timecard"):
        old = [t for t in trig if t["from"] in PER_STOP and t["object"] == obj]
        if not old:
            continue
        share = round(sum(float(t.get("share", 0)) for t in old), 4)
        keep = next((t for t in trig if t["from"] == "ltl-pd-dispatch" and t["object"] == obj), None)
        for t in old:
            trig.remove(t)
        if keep:
            keep["share"] = round(float(keep.get("share", 0)) + share, 4)
        else:
            trig.append({"from": "ltl-pd-dispatch", "object": obj, "share": share})
        note = (f"Organisation file corrected on {TODAY}: {obj} now comes from ltl-pd-dispatch, once per driver-day, "
                "as the pickup and delivery workflows record; it previously came from each pickup and delivery stop.")
        if note not in wf["assumptions"]:
            wf["assumptions"].append(note)
moved = 0
for src in ["ltl-pickup-execution", "ltl-delivery-execution"]:
    wf_out = {(t["to"], t["object"]) for t in by_proc[src]["interfaces"]["produces"]} if src in by_proc else set()
    for link in list(P[src]["produces"]):
        if link["object"] in ("dvir", "driver_timecard") and (link["to"], link["object"]) not in wf_out:
            P[src]["produces"].remove(link)
            moved += 1
            dst = P.get(link["to"])
            if dst:
                for key in ("triggered_by", "inputs"):
                    dst[key] = [t for t in dst.get(key, []) if not (t["from"] == src and t["object"] == link["object"])]
log.append(f"links: {moved} daily inspection and timecard links removed from per-stop processes")

# Triggers the workflow authors found are steps inside a case, not starts of one.
for pid, src, obj in [("mnt-parts-inventory", "parts-supplier", "parts_delivery"),
                      ("tl-customs-emanifest", "customs-broker", "customs_release")]:
    P[pid]["triggered_by"] = [t for t in P[pid]["triggered_by"] if not (t["from"] == src and t["object"] == obj)]

# Surges and volumes the workflows set with evidence the map lacks.
for pid in ["fin-rating-invoicing", "saf-driver-onboarding", "saf-driver-recruiting", "tl-load-planning"]:
    if pid in by_proc and by_proc[pid]["volume"].get("surge") and not P[pid].get("surge"):
        P[pid]["surge"] = json.loads(json.dumps(by_proc[pid]["volume"]["surge"]))
        for s in P[pid]["surge"]["evidence"].get("sources", []):
            if s not in {x["id"] for x in org["sources"]}:
                src_doc = next(x for x in by_proc[pid]["sources"] if x["id"] == s)
                org["sources"].append(dict(src_doc))
P["mnt-preventive-maintenance"]["cases_per_month"] = {"low": 950, "mode": 1200, "high": 1600}
log.append("map: 2 mid-case triggers removed, 4 surges and the preventive maintenance volume taken from workflows")

# ---------------------------------------------------------------- 5. Roles the workflows added
if "road-call-coordinator" in R:
    rc = R["road-call-coordinator"]
    rc["headcount"] = 5
    rc["shift_pattern"] = "shift_24x7"
    rc["unit"] = "mnt"
    rc["reports_to"] = "shop-manager"
    rc["evidence"]["note"] = ("Added from frt-mnt-roadside-breakdown, whose author found no role for the breakdown "
                              "desk the process names. Five people keep one desk open around the clock; road calls "
                              "take about 2.6 FTE of their time, and they also arrange towing and replacement units. "
                              "Author's estimate.")

# ---------------------------------------------------------------- 6. Driver pay volume and demand driver


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


# ---------------------------------------------------------------- 7. Resize roles to the documented work
TARGET = 0.97
resized = []


def resize(only=None, skip=()):
    """Raise each role whose documented hands-on work exceeds its headcount, at TARGET load."""
    load, parts = measure_load()
    for rid, hours in sorted(load.items()):
        role = R.get(rid)
        if role is None or role.get("layer") == "external_party" or rid in skip or (only and rid not in only):
            continue
        cap = role.get("productive_hours_per_month") or V.PRODUCTIVE_HOURS[role.get("shift_pattern", "office_hours")]
        fte = hours / cap
        need = math.ceil(fte / TARGET)
        if rid == "linehaul-driver":  # the hours include the owner-operators' trips; headcount counts them too
            need = max(need, role["headcount"])
        if need <= role["headcount"] or f"Revised {TODAY}" in role["evidence"].get("note", ""):
            continue  # covered, or already resized by an earlier run
        top = ", ".join(f"{p} {h:,.0f}" for p, h in sorted(parts[rid], key=lambda x: -x[1])[:3])
        old = role["headcount"]
        text = (f"headcount {old} raised to {need} to cover the hands-on work the workflows record: about {hours:,.0f} "
                f"hours a month (largest: {top}), which is {fte:.1f} FTE at {cap} productive hours a month, sized to "
                f"{TARGET:.0%} load. Work in processes without a workflow is not counted.")
        if rid == "pd-driver":
            text += (f" Old Dominion had 5,644 P&D drivers for 12.88 million LTL shipments in 2021; at this carrier's 1.8 "
                     f"million that ratio gives about {odfl_pd}. 195 on-duty hours is about 9.5 hours on 21 days less "
                     "absence, inside the 14-hour daily on-duty limit. Shipper waiting at pickups is recorded as wait, "
                     "not hands-on time, so the work is a floor.")
        if rid == "linehaul-driver":
            text += (" 70 of them are owner-operators under contract, who run about a fifth of trips. 210 on-duty hours "
                     "fits the 70-hour weekly cycle. Old Dominion's ratio (6,158 linehaul drivers for 12.88 million "
                     "shipments) is not used because its US hauls are much longer.")
        if rid in ("terminal-dock-worker", "hub-dock-worker"):
            text += (f" Old Dominion had 5,350 platform staff for 12.88 million shipments in 2021, about {odfl_dock} at "
                     "this carrier's volume, against hub and terminal dock workers combined.")
        role["headcount"] = need
        add_note(role["evidence"], text)
        resized.append(f"{rid} {old}->{need}")


# Drivers first: their work does not depend on other headcounts, and driver pay volume depends on them.
resize(only=set(DRIVER_ROLES))
company_drivers = sum(R[r]["headcount"] - R[r].get("contractor_headcount", 0) for r in DRIVER_ROLES)

# Pay records: company drivers paid every two weeks.
records = round(company_drivers * 26 / 12 / 50) * 50
dp = P["fin-driver-pay"]
dp["cases_per_month"] = {"low": round(records * 0.9 / 50) * 50, "mode": records, "high": round(records * 1.1 / 50) * 50}
dp["driver"] = "company-drivers"
dd = {d["id"]: d for d in org["demand_drivers"]}
cd = {"id": "company-drivers", "name": "Company drivers on payroll",
      "per_month": {"low": round(company_drivers * 0.95), "mode": company_drivers, "high": round(company_drivers * 1.05)}, "unit": "drivers",
      "evidence": {"tier": "C", "sources": [],
                   "note": "Sum of employed pickup and delivery, linehaul and truckload drivers in roles, owner-operators "
                           "excluded."}}
if "company-drivers" in dd:
    dd["company-drivers"].update(cd)
else:
    org["demand_drivers"].append(cd)
wf = by_proc.get("fin-driver-pay")
if wf:
    wf["volume"]["cases_per_month"] = dict(dp["cases_per_month"])
    note = (f"Organisation file corrected on {TODAY}: driver pay records now follow the {company_drivers} employed "
            f"drivers paid every two weeks, about {records} a month (previously 2,650, which fitted about 1,210 drivers).")
    wf["assumptions"] = [a for a in wf["assumptions"] if "driver pay records now follow" not in a] + [note]
log.append(f"driver pay: {records} records a month for {company_drivers} company drivers paid every two weeks")

resize(skip=set(DRIVER_ROLES))
log.append("roles resized: " + "; ".join(resized))

# Fleet that follows the drivers
RES["pd-truck"]["count"] = math.ceil(R["pd-driver"]["headcount"] * 1.05 / 10) * 10
add_note(RES["pd-truck"]["evidence"], f"count follows {R['pd-driver']['headcount']} P&D drivers plus about 5% spares.")

# ---------------------------------------------------------------- 8. Units, employees and profile
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
dd = {d["id"]: d for d in org["demand_drivers"]}
dd["employees"]["per_month"] = {"low": round(employees * 0.95), "mode": employees, "high": round(employees * 1.05)}

units_of = {"linehaul-tractor", "tl-tractor", "pd-truck"}
power = sum(RES[r]["count"] for r in units_of)
trailers = sum(RES[r]["count"] for r in ("ltl-trailer", "tl-dry-van", "tl-reefer", "flatdeck"))
scale = {s["name"]: s for s in org["profile"]["scale"]}
scale["Company power units"]["value"] = power
dd["fleet-units"]["per_month"] = {"low": power + trailers - 150, "mode": power + trailers, "high": power + trailers + 150}
rev = scale["Annual revenue including fuel surcharge (2021)"]["evidence"]
rev["note"] = rev["note"].replace("about 60% LTL, 34% truckload, 6% brokerage",
                                  "about 60% LTL, 37% truckload, 3% brokerage (600 brokered loads a month at about "
                                  "CAD 2,500 each, as frt-tl-brokerage records)")

org["summary"] = (
    f"This is a Canadian trucking company of about {round(employees, -2):,} employees that moves freight for "
    "manufacturers, distributors and retailers. Its largest business is less-than-truckload (LTL) freight: it "
    "collects many small shipments from shippers with city trucks, sorts them overnight through 38 terminals and "
    "five hub cross-docks in Ontario, Quebec and western Canada, and delivers them to consignees, usually in one to "
    "four days. Company drivers and about 70 contracted owner-operators pull the linehaul trailers between "
    "terminals. A truckload division hauls full trailer loads within Canada and to and from the United States, "
    "using about 430 company drivers, 310 contracted owner-operators and brokered carriers when its own fleet is "
    "full. Customers pay per shipment or per load at negotiated rates, plus a weekly fuel surcharge and charges "
    "for extras such as detention, appointments and liftgates. The company runs its own maintenance shops, "
    "recruits and trains its drivers, and must follow federal and provincial rules on hours of service, electronic "
    "logging, vehicle inspection, dangerous goods and customs reporting. Head-office departments handle sales and "
    "pricing, customer service and claims, billing and settlements, safety, HR and IT, and the company reports to "
    "a TSX-listed transportation group that owns it.")
log.append(f"employees recomputed from roles: {employees} (owner-operators excluded); power units {power}")

# ---------------------------------------------------------------- 9. Assumptions
asm = org["assumptions"]
for i, a in enumerate(asm):
    if a.startswith("The company is a composite"):
        asm[i] = ("The company is a composite, not a real carrier. Scale and structure are drawn from Mullen Group's "
                  "LTL segment (including Gardewine) and TFI International's Canadian operations, at about CAD 650 "
                  f"million of revenue in 2021. Headcounts were first set at about 3,000 and revised on {TODAY} to "
                  f"{employees:,} to cover the work the workflows record; Old Dominion's driver and dock staff per "
                  "shipment are the outside check.")
    if a.startswith("Employees exclude about 380 owner-operators"):
        asm[i] = ("Employees exclude 380 owner-operators, who are contractors: 310 in truckload (role owner-operator, "
                  "layer external_party) and 70 who pull LTL linehaul, counted in linehaul-driver as "
                  "contractor_headcount. Neither group is in the employee count.")
DRV = ("Drivers' on-duty hours are nearly all route time, so pickup and delivery drivers are sized at 195 productive "
       "hours a month and linehaul drivers at 210 (productive_hours_per_month), not the 130 or 150 the shift-pattern "
       "defaults give office and shift staff.")
if DRV not in asm:
    asm.append(DRV)

# ---------------------------------------------------------------- 10. Workflows: role titles and productive hours
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
