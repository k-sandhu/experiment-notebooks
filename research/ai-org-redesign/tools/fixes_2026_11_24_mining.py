"""Corrections to the gold mining company file from the reference mine's own technical reports (2026-11-24).

The workflow authors for mining-operator-co read the Eagle River technical reports (SRK 2022 and Wesdome
2016) and found the organisation file wrong on the mill flowsheet, the mill's location, hoisting, tailings,
the assay lab, the mobile fleet and the underground labour force. Each fact below was checked against the
report text before it was written here. Run tools/sync_map_from_workflows.py mining-operator-co first.

Ids that named the wrong technology are renamed in the organisation file and in every workflow:
    process   mill-elution-refining -> mill-gold-room-refining (workflow file and id follow)
    object    loaded_carbon         -> gold_concentrate
    object    tailings_slurry       -> filtered_tailings
    resource  elution-circuit       -> refinery

Safe to run twice.

Usage:
    python fixes_2026_11_24_mining.py [ROOT]
"""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
ORG = "mining-operator-co"
org_path = root / "organisations" / f"{ORG}.json"
org = json.loads(org_path.read_text(encoding="utf-8"))
wf_paths = [p for p in sorted((root / "workflows").glob("*.json"))
            if json.loads(p.read_text(encoding="utf-8")).get("org") == ORG]
workflows = {p: json.loads(p.read_text(encoding="utf-8")) for p in wf_paths}
log = []
TODAY = "2026-11-24"

# ---------------------------------------------------------------- 1. Renames (exact id values only, not prose)
RENAME = {"mill-elution-refining": "mill-gold-room-refining", "mine-mill-elution-refining": "mine-mill-gold-room-refining",
          "loaded_carbon": "gold_concentrate", "tailings_slurry": "filtered_tailings", "elution-circuit": "refinery"}


def rename(x):
    if isinstance(x, dict):
        return {k: rename(v) for k, v in x.items()}
    if isinstance(x, list):
        return [rename(v) for v in x]
    if isinstance(x, str) and x in RENAME:
        return RENAME[x]
    return x


touched = {p for p, w in workflows.items()
           if any(k in json.dumps(w) for k in list(RENAME) + ["not in the organisation file", "not in the organization "
                                                                "file", "not_in_org_file", "does not match"])}
org = rename(org)
for path in list(workflows):
    workflows[path] = rename(workflows[path])
# The org file had both elution-circuit and (from the sync) refinery; keep one refinery entry.
seen, kept = set(), []
for r in org["resources"]:
    if r["id"] not in seen:
        kept.append(r)
        seen.add(r["id"])
org["resources"] = kept
for proc in org["process_map"]:
    if "resources" in proc:
        proc["resources"] = list(dict.fromkeys(proc["resources"]))
for wf in workflows.values():
    seen, kept = set(), []
    for r in wf.get("resources", []):
        if r["id"] not in seen:
            kept.append(r)
            seen.add(r["id"])
    if "resources" in wf:
        wf["resources"] = kept

P = {p["id"]: p for p in org["process_map"]}
R = {r["id"]: r for r in org["roles"]}
RES = {r["id"]: r for r in org["resources"]}
U = {u["id"]: u for u in org["units"]}
OBJ = {b["id"]: b for b in org["business_objects"]}
EXT = {e["id"]: e for e in org["external_parties"]}

# ---------------------------------------------------------------- 2. Sources (opened by the workflow authors and re-read here)
NEW_SOURCES = [
    {"id": "er2022", "title": "Independent Technical Report for the Eagle River Gold Mining Complex, Canada (NI 43-101), "
                              "22 April 2022",
     "publisher": "SRK Consulting (Canada) Inc. for Wesdome Gold Mines Ltd.",
     "url": "https://s203.q4cdn.com/643390454/files/doc_downloads/2022/11/ERtechnicalReport.pdf", "year": 2022,
     "accessed": TODAY,
     "supports": "Section 16.4: ramp access through a portal; shaft hoists ore from the loading pocket below the 460 m "
                 "level to a skip dump at the 70 m level; cage limited to 6 people; underground trucks haul ore out the "
                 "portal to a surface pad and surface trucks haul it 16.6 km to the mill; hoist realistic maximum 16 hours "
                 "a day; loading pocket not automated. Table 16-9: mobile fleet (owner and contractor). Table 16-10: "
                 "underground labour force, 111 owner and 36 contractor. Section 17: mill flowsheet with gravity, leach, "
                 "Merrill-Crowe precipitation in sock presses (socks changed every two weeks), tailings filtration for "
                 "dry stacking, refinery smelting table and precipitation concentrate; 2021-2022 average throughput "
                 "779 t/d, maximum 1,027 t/d; availability 93.3% planned and 86% in 2021 after an August shutdown. "
                 "Section 18: 100-person camp at the mine and a smaller camp at the mill. Section 20: tailings filtered "
                 "and trucked to the tailings area since 2007; reclaim pond, Mishi pit storage, treatment plant, "
                 "polishing pond. Section 11: production samples assayed at the company's uncertified assay office in "
                 "Wawa, delivered daily by company shuttle."},
    {"id": "er2016", "title": "Technical Report for the Eagle River Mining Complex including the Eagle River Gold Mine, the "
                              "Mishi Gold Mine and related infrastructure (NI 43-101), 17 March 2016",
     "publisher": "Wesdome Gold Mines Ltd. (G. Mannard, P. Ng)",
     "url": "https://minedocs.com/12/EagleRiver_TechnicalReport_03172016.pdf", "year": 2016, "accessed": TODAY,
     "supports": "Merrill-Crowe solution mill; dore bars shipped to the Royal Canadian Mint in Ottawa for refining; mill "
                 "runs 24 hours a day, seven days a week, two crews on 12-hour shifts on a seven days in, seven days out "
                 "rotation; assay office in Wawa with shift supervisors and an Assay Lab Superintendent; Wawa to the "
                 "mine about 1.5 hours by road."},
    {"id": "wdofs2021", "title": "Wesdome Gold Mines Ltd. consolidated financial statements for the years ended December "
                                 "31, 2021 and 2020",
     "publisher": "Wesdome Gold Mines Ltd.",
     "url": "https://s203.q4cdn.com/643390454/files/doc_financials/2021/q4/Wesdome-Q4-2021-Financial-Statements.pdf",
     "year": 2022, "accessed": TODAY,
     "supports": "No gold price hedges or forward foreign exchange contracts in 2020 or 2021; gold sold exclusively to "
                 "financial institutions (as read by the author of workflow mine-corp-gold-sales)."},
]
have = {s["id"] for s in org["sources"]}
for s in NEW_SOURCES:
    if s["id"] not in have:
        org["sources"].append(s)
        log.append(f"added source {s['id']}")


def ev(tier, sources, note):
    return {"tier": tier, "sources": sources, "note": note}


# ---------------------------------------------------------------- 3. Summary and profile
org["summary"] = (
    "The company mines gold ore underground at one mine in northern Ontario, about 1.5 hours by road from the nearest "
    "town, and turns it into doré bars at its own mill 16.6 km by road from the mine portal. Ore is hoisted up a "
    "shaft to a dump near the top of the mine, trucked out the ramp to a surface pad and hauled to the mill by surface "
    "trucks. A small satellite open pit, mined by a contractor, added ore until 2020. The mine produces about 90,000 to "
    "120,000 ounces of gold a year from roughly 600 to 800 tonnes of high-grade ore a day. The mill recovers gold by "
    "gravity concentration and cyanide leaching with zinc precipitation (the Merrill-Crowe process), filters its "
    "tailings and stacks them dry. The doré is trucked by a secure carrier to the Royal Canadian Mint and the "
    "refined gold is sold at spot to financial institutions, the company's only revenue, about C$165-290 million a "
    "year. About 250 company employees work at the site, underground crews on long rotations and mill crews on 12-hour "
    "shifts seven days on and seven off, living in camps while on shift; a mining contractor supplies about 36 more "
    "people underground. Production samples go by daily shuttle to the company's assay office in town. A head office "
    "of about 18 people in Toronto handles finance, gold sales, disclosure, legal and investor relations for the listed "
    "company. The site is organised into mine operations, technical services (engineering and geology), processing "
    "with the assay office, maintenance, health, safety and environment, and site administration under a general "
    "manager who reports to the chief operating officer. An exploration team drills near the mine and on a property in "
    "Quebec that is on care and maintenance. The mine is regulated by Ontario labour, mining and environment "
    "ministries, federal effluent rules and securities regulators.")
if "Eagle River technical reports" not in org["modelled_on"]:
    org["modelled_on"] += (". Mine, mill, fleet and underground labour corrected on 2026-11-24 from the Eagle River "
                           "technical reports (SRK 2022, Wesdome 2016)")
for item in org["profile"]["scale"]:
    if item["name"] == "Mill capacity":
        item.update({"name": "Mill throughput, maximum day 2021-2022", "value": 1027, "unit": "tonnes per day",
                     "evidence": ev("A", ["er2022"], "Table 17-1. The 2021-2022 average was 779 t/d.")})
names = {i["name"] for i in org["profile"]["scale"]}
for item in [
    {"name": "Mill throughput, average 2021-2022", "value": 779, "unit": "tonnes per day",
     "evidence": ev("A", ["er2022"], "Table 17-1.")},
    {"name": "Mill availability 2021", "value": 86, "unit": "percent",
     "evidence": ev("A", ["er2022"], "Planned 93.3%; a planned shutdown in August 2021 replaced the cone crusher and trash "
                                     "screen and inspected the secondary ball mill.")},
    {"name": "Underground labour force 2022", "value": 147, "unit": "people (111 company, 36 contractor)",
     "evidence": ev("A", ["er2022"], "Table 16-10.")}]:
    if item["name"] not in names:
        org["profile"]["scale"].append(item)

# ---------------------------------------------------------------- 4. Roles: underground labour from Table 16-10
T1610 = "Table 16-10 of the 2022 technical report (company and contractor underground labour)."
role_fix = {
    "ug-shift-supervisor": dict(headcount=8, contractor_headcount=3, evidence=ev(
        "A", ["er2022"], T1610 + " Mine supervision is 8 company and 3 contractor; the company's 8 are the "
        "superintendent, two captains and five shift supervisors.")),
    "dev-miner": dict(headcount=24, contractor_headcount=16, evidence=ev(
        "B", ["er2022"], T1610 + " Development crews are 16 company and 24 contractor miners, 40 in all, with no "
        "separate line for production or bolting. The split of the 40 across development, production and bolting "
        "roles is the editor's estimate from the fleet each side owns (Table 16-9).")),
    "prod-miner": dict(headcount=10, contractor_headcount=6, evidence=ev(
        "B", ["er2022"], "Part of the 40 development and production miners in Table 16-10; split is the editor's "
        "estimate. The company owns 4 of 5 production drills and 2 of 5 blockholers.")),
    "bolter-operator": dict(headcount=6, contractor_headcount=2, evidence=ev(
        "C", ["er2022"], "Part of the 40 miners in Table 16-10. Table 16-9 lists no mechanised bolter, so bolting is "
        "probably done from jumbos and scissor lifts with jacklegs; the mining method is in transition to mechanised "
        "access (section 25).")),
    "lhd-operator": dict(headcount=8, evidence=ev("A", ["er2022"], T1610 + " Previously 20.")),
    "ug-truck-driver": dict(headcount=24, evidence=ev(
        "A", ["er2022"], T1610 + " Previously 12. Twenty-four operators for five 30-tonne trucks; the report does not "
        "say whether they also drive the surface ore haul to the mill.")),
    "ug-services-worker": dict(headcount=21, contractor_headcount=5,
                               title="Underground services and construction miner", evidence=ev(
        "A", ["er2022"], T1610 + " Service miners 8 company and 2 contractor; construction miners 8 company and 3 "
        "contractor.")),
    "hd-mechanic": dict(headcount=16, contractor_headcount=4, evidence=ev(
        "A", ["er2022"], T1610 + " Mine maintenance 12 company and 4 contractor. Previously 22.")),
    "electrician": dict(headcount=12, evidence=ev(
        "B", ["er2022"], "Table 16-10 lists 8 mine electricians; 4 for the mill and surface are the editor's estimate.")),
    "geo-technician": dict(headcount=4, evidence=ev(
        "A", ["er2022"], T1610 + " Mine geology is 10 people: the chief geologist, 5 geologists and 4 technicians.")),
    "geotech-engineer": dict(headcount=2, evidence=ev(
        "C", [], "One engineer on rotation covers only the days on site; the ground control work in workflow "
                 "mine-ts-geotech needs about 1.8 FTE, so a second engineer or technologist on the opposite rotation "
                 "is assumed.")),
    "assay-technician": dict(headcount=11, shift_pattern="extended_hours", evidence=ev(
        "C", ["er2016", "er2022"], "The assay office is in Wawa and staff commute daily, so not on a site rotation. "
        "Eleven technicians is the hands-on time in workflow mine-mill-assay-lab for about 300 furnace batches of 28 "
        "positions a month.")),
    "assay-supervisor": dict(headcount=2, shift_pattern="extended_hours",
                             title="Assay lab superintendent or shift supervisor", evidence=ev(
        "B", ["er2016", "er2022"], "The reports name an Assay Lab Superintendent and shift supervisors; the count of "
        "two is the editor's estimate.")),
    "sample-driver": dict(shift_pattern="extended_hours", evidence=ev(
        "A", ["er2022"], "Section 11: a company shuttle takes samples to the laboratory in Wawa daily. One driver is "
        "the editor's estimate.")),
    "loading-pocket-operator": dict(unit="mine-shaft", reports_to="ug-shift-supervisor", evidence=ev(
        "B", ["er2022"], "Section 16.4: the loading pocket has not been automated, so it is run by hand; one operator "
        "per crew is the editor's estimate.")),
}
notes = {
    "mill-operator": "Four operators per crew covering grinding, leach, Merrill-Crowe and tailings filtration. The mill "
                     "runs around the clock with two crews on 12-hour shifts on seven days in, seven days out (er2016); "
                     "wage about C$32-36/h in 2019-2022, loaded 1.35.",
    "hoist-operator": "Reg. 854 s. 9(3) limits anyone to 8 hours at the hoist controls in 24 hours, so each 12-hour "
                      "shift needs a relief operator; six covers four crews.",
}
# The original notes also gave the pay basis; keep it beside the new headcount evidence.
PAY = {
    "dev-miner": ("Job Bank 2024-25 Ontario median C$40/h deflated about 10% to 2019-2022, plus underground bonus, "
                  "loaded 1.35.", ["src8"]),
    "prod-miner": ("Same wage basis as development miners.", ["src8"]),
    "bolter-operator": ("Same occupation group as development miners; slightly lower bonus.", ["src8"]),
    "lhd-operator": ("Same occupation group as development miners.", ["src8"]),
    "ug-truck-driver": ("Mine service worker rates in northern Ontario, loaded 1.35.", []),
    "hd-mechanic": ("Licensed 310T mechanic wage about C$38-42/h in 2019-2022, loaded 1.35.", []),
    "electrician": ("Licensed 442A electrician wage, loaded 1.35.", []),
    "hoist-operator": ("Certified hoistman rates in northern Ontario, loaded 1.35.", []),
}
for rid, change in role_fix.items():
    role = R[rid]
    for k, v in change.items():
        if role.get(k) != v:
            role[k] = v
for rid, note in notes.items():
    R[rid]["evidence"]["note"] = note
for rid, (pay, srcs) in PAY.items():
    e = R[rid]["evidence"]
    if "Pay:" not in e["note"]:
        e["note"] += " Pay: " + pay
        e["sources"] = list(dict.fromkeys(e["sources"] + srcs))
for rid in ["mill-operator", "mill-shift-supervisor", "crusher-operator"]:
    R[rid]["shift_pattern"] = "shift_24x7"
log.append("roles: underground headcounts set from Table 16-10 of the 2022 report, contractor staff recorded")

# ---------------------------------------------------------------- 5. Resources
res_fix = {
    "jumbo": dict(count=4, evidence=ev("A", ["er2022"], "Table 16-9: 3 company and 1 contractor two-boom jumbos.")),
    "lhd": dict(count=19, name="Underground loaders (2 to 6 yard scooptrams)", evidence=ev(
        "A", ["er2022"], "Table 16-9: six 6-yd, two 4-yd, three 3.5-yd and eight 2-yd loaders; 17 company and 2 "
        "contractor.")),
    "ug-truck": dict(count=5, name="Underground haul truck (30 t)", evidence=ev(
        "A", ["er2022"], "Table 16-9: 3 company and 2 contractor 30-tonne trucks.")),
    "longhole-drill": dict(count=5, evidence=ev(
        "A", ["er2022"], "Table 16-9: 4 company and 1 contractor production drills; there are also 5 blockholers.")),
    "bolter": dict(evidence=ev("C", ["er2022"], "Table 16-9 lists no mechanised bolter. Kept at 3 because the ground "
                                                 "support workflow models a bolting unit; check before use.")),
    "ug-utility": dict(count=34, name="Underground utility fleet (scissor lifts and light vehicles)", evidence=ev(
        "A", ["er2022"], "Table 16-9: 4 scissor lifts and 30 light vehicles, company and contractor.")),
    "shaft-hoist": dict(name="Production shaft hoist, skip and cage (loading pocket below 460 m level to dump at 70 m "
                             "level)",
                        available_hours_per_month={"low": 400, "mode": 450, "high": 486}, evidence=ev(
        "A", ["er2022"], "Section 16.4: double-drum hoist, 4-tonne skip, cage for 6 people; realistic maximum 16 "
        "operating hours a day.")),
    "mill-plant": dict(name="Crushing-to-precipitation mill (grinding, gravity, leach, Merrill-Crowe, tailings filters)",
                       available_hours_per_month={"low": 584, "mode": 628, "high": 681}, evidence=ev(
        "A", ["er2022"], "Availability 93.3% planned and 86% in 2021 (Table 17-1); the low end is the 80% reported for "
        "2020 in workflow mine-mill-grind-leach. Running cost per hour is the original author's estimate and looks "
        "high to the workflow author.")),
    "refinery": dict(name="Refinery (sock burner oven and propane furnace in a secure room)", kind="facility",
                     unit="mill-ops", count=1, available_hours_per_month={"low": 80, "mode": 120, "high": 200},
                     evidence=ev("A", ["er2022"], "Section 17.3.7. Hours in use a month are the editor's estimate for "
                                                  "4 to 8 smelt batches.")),
    "assay-lab": dict(name="Company assay office in Wawa (preparation, fire assay, AA; not accredited)", evidence=ev(
        "A", ["er2022", "er2016"], "Section 11: the mine assay office is in Wawa and is not a certified laboratory.")),
    "tailings-facility": dict(name="Tailings management area (filtered tailings, reclaim pond, polishing pond)",
                              evidence=ev("A", ["er2022"], "Section 20.3: filtered tailings trucked to the tailings area "
                                                           "since 2007.")),
    "camp": dict(name="Camps (100-person camp at the mine and a smaller camp at the mill)", count=2, evidence=ev(
        "A", ["er2022"], "Section 18.")),
    "surface-drill": dict(available_hours_per_month={"low": 450, "mode": 600, "high": 680}, evidence=ev(
        "C", ["src1"], "Contract rigs drilling around the clock. At 450 hours a month three rigs could drill only about "
        "7 holes a month against the 15 in the process map, so hours are raised; 54,000 m at the mine in 2021 guidance "
        "(src1).")),
}
for rid, change in res_fix.items():
    if rid not in RES:
        continue
    RES[rid].update(change)
if "ore-haul-truck" not in RES:
    org["resources"].append({"id": "ore-haul-truck", "name": "Surface ore haul trucks (mine portal pad to mill, 16.6 km)",
                             "kind": "vehicle", "unit": "mine", "count": 3,
                             "available_hours_per_month": {"low": 300, "mode": 400, "high": 500},
                             "evidence": ev("C", ["er2022"], "Section 16.4 describes the haul; the report does not say "
                                                             "how many trucks or whether they are company or "
                                                             "contractor. Three is the editor's estimate for about 22 "
                                                             "loads a day.")})
log.append("resources: fleet from Table 16-9, hoist hours, mill availability, refinery replaces the elution circuit")

# ---------------------------------------------------------------- 6. Units
U["mill"]["purpose"] = ("Crushing, grinding, gravity concentration, cyanide leaching with Merrill-Crowe zinc precipitation, "
                        "refining to doré, tailings filtration and water, and the assay office in Wawa.")
U["mill"]["evidence"] = ev("A", ["er2022", "er2016"], "Flowsheet from section 17 of the 2022 report; staffing is the "
                                                      "original author's estimate.")
U["mill-ops"]["evidence"] = ev("B", ["er2016"], "Mill crews work 12-hour shifts on seven days in, seven days out; crew "
                                                "sizes are the original author's estimate.")
U["mill-lab"].update({"name": "Assay office (Wawa)",
                      "purpose": "Fire assay of grade control, mill process and some definition samples at the company "
                                 "assay office in Wawa, 1.5 hours by road from the mine.",
                      "evidence": ev("A", ["er2022", "er2016"], "Uncertified company lab in Wawa; samples arrive by daily "
                                                                "shuttle. It also assays production samples for a "
                                                                "neighbouring mine (workflow mine-mill-assay-lab).")})
U["mine-ug"]["purpose"] = ("Company and contractor crews on rotation that drill, blast, support, muck and haul development "
                           "headings and stopes reached by ramp and by raises.")
U["mine-ug"]["evidence"] = ev("A", ["er2022"], "Table 16-10; rotation length is the original author's estimate.")

# ---------------------------------------------------------------- 7. Objects and outside parties
OBJ["gold_concentrate"].update({"name": "Gold precipitate and gravity concentrate",
                                "description": "Press socks holding zinc-gold precipitate from the Merrill-Crowe circuit, "
                                               "and shaking table concentrate from the gravity circuit, sent to the "
                                               "refinery for smelting."})
OBJ["filtered_tailings"].update({"name": "Filtered tailings",
                                 "description": "Detoxified tailings dewatered on drum filters and conveyed or trucked to "
                                                "the tailings area for dry stacking."})
OBJ["process_samples"]["description"] = "Shift composite samples of feed, leach, solution and tailings."
OBJ["gold_sale"]["description"] = "A spot sale of refined ounces to a financial institution."
OBJ["reagent_delivery"]["description"] = ("Sodium cyanide, zinc dust, lead nitrate, lime, flocculant, diatomaceous earth "
                                          "and hydrogen peroxide delivered to site.")
OBJ["treasury_report"]["description"] = "Cash, liquidity and credit facility covenant position."
EXT["refinery"].update({"name": "Royal Canadian Mint (refinery)",
                        "description": "Refines doré into good-delivery gold and credits ounces to the company's "
                                       "metal account; named as the refiner in the 2016 technical report."})
EXT["bullion-bank"].update({"name": "Gold buyers (financial institutions)",
                            "description": "Financial institutions that buy refined gold at spot and hold metal accounts. "
                                           "The company had no gold forward contracts in 2020 or 2021."})
EXT["mining-contractor"].update({"name": "Mining contractor",
                                 "description": "Mined the satellite pit with its own fleet under a unit-rate contract, and "
                                                "supplies underground crews and equipment: 36 people in 2022, most of "
                                                "them development miners."})
EXT["reagent-supplier"]["description"] = "Supplies sodium cyanide, zinc dust, lime and other mill reagents."

# ---------------------------------------------------------------- 8. Processes
def set_proc(pid, **kw):
    for k, v in kw.items():
        P[pid][k] = v


set_proc("mine-hoisting",
         description="Hoist operators skip ore from the loading pocket below the 460 m level to a dump at the 70 m "
                     "level, where underground trucks load at a chute and haul it out the ramp to the surface ore pad. "
                     "A loading pocket operator runs the pocket by hand, and the cage carries up to six people and "
                     "materials, though most people travel by ramp. A hoist breakdown stops ore delivery, so the hoist "
                     "is checked before every shift and can run at most about 16 hours a day.",
         evidence=ev("A", ["er2022"], "Section 16.4."))
set_proc("mill-crushing",
         description="Surface trucks bring ore 16.6 km from the mine portal pad to the mill stockpile, and crusher "
                     "operators feed it through the jaw and cone crushers and screens to the fine ore bin, removing "
                     "tramp steel and clearing chokes. Crusher breakdowns are the most common cause of lost milling time.",
         evidence=ev("A", ["src1", "er2022"], "Two-stage crushing; six days of milling lost to cone crusher downtime in "
                                              "December 2020 (src1); cone crusher replaced in the August 2021 shutdown "
                                              "(er2022)."))
set_proc("mill-grind-leach", name="Grinding, gravity, leaching and Merrill-Crowe precipitation",
         description="Control room operators run the ball mills, the gravity concentrator and shaking table, the "
                     "cyanide leach tanks, the drum filters that recover the gold-bearing solution and the Merrill-Crowe "
                     "circuit, where zinc dust precipitates gold that is caught in sock presses. They adjust grind, "
                     "density, cyanide and pH against shift samples around the clock. Gravity recovers about 43% of the "
                     "gold and precipitation most of the rest, 97% overall. Feed changes, power dips and pump failures "
                     "upset recovery.",
         evidence=ev("A", ["er2022", "src1"], "Section 17 and Table 17-1; 97.7% recovery on underground ore in 2020 "
                                              "(src1)."))
set_proc("mill-gold-room-refining", name="Refining precipitate and gravity concentrate to doré",
         description="Every two weeks the loaded press socks are taken out and burned in the sock oven, and about weekly "
                     "the shaking table concentrate is collected. Gold room operators mix each concentrate with fluxes, "
                     "smelt it in the furnace and pour doré bars of 80 to 94% gold under two-person rule and camera "
                     "coverage. Each bar is weighed, sampled and recorded before going to the vault.",
         unit_of_work="one smelt and pour batch (precipitate or table concentrate)",
         cases_per_month={"low": 4, "mode": 6, "high": 8},
         evidence=ev("A", ["er2022"], "Sections 17.3.5 and 17.3.7; batch count is the workflow author's estimate from "
                                      "the two-weekly sock change and weekly table cleanup."))
set_proc("mill-tailings",
         description="Leached slurry is washed and dewatered on drum filters in the tailings building, and the filter "
                     "cake is conveyed and trucked to the tailings area, where a dozer spreads it along the dam crest. "
                     "Technicians read pond levels and piezometers, and the engineer of record inspects the dams yearly. "
                     "Spring melt and heavy rain raise pond levels and inspection frequency.",
         evidence=ev("A", ["er2022"], "Sections 17.3.6 and 20.3: filtered tailings deposited by haul trucks since 2007."))
set_proc("mill-water-treatment",
         description="Runoff from the tailings area collects in the reclaim pond, which supplies the mill. Operators "
                     "add hydrogen peroxide to destroy cyanide, send excess water through the treatment plant (hydroxide, "
                     "flocculant and geotube filtration) to the polishing pond, and in high-flow periods pump it to the "
                     "mined-out Mishi pit for storage. Treated water leaves the polishing pond at controlled rates "
                     "through most of the year. Freshet volumes and tighter limits from January 2021 strain the system.",
         evidence=ev("A", ["er2022"], "Sections 17.3.8 and 20.3.3."))
set_proc("mill-assay-lab", name="Assay office (Wawa)",
         description="A company shuttle brings face, muck, process and some definition samples 1.5 hours by road to the "
                     "assay office in Wawa every day. Technicians dry, crush and pulverise them, fire assay them in "
                     "furnace batches of 28 positions with gravimetric or AA finish, insert standards and blanks, and "
                     "email results to geology and the mill. The office is not accredited and also assays a neighbouring "
                     "mine's production samples. Backlogs delay grade decisions underground.",
         unit_of_work="one furnace batch of 28 positions",
         cases_per_month={"low": 200, "mode": 300, "high": 420},
         evidence=ev("A", ["er2022", "er2016"], "Section 11 of both reports; batch count is the workflow author's "
                                                "estimate from sample volumes."))
set_proc("mill-dore-shipment", name="Doré shipment to refinery",
         description="The mill superintendent and security prepare a shipment, seal the bars, hand them to the armed "
                     "carrier against signed manifests and send the shipment advice to finance and the Royal Canadian "
                     "Mint. The site controller records the doré in transit. Weather and carrier schedules set the "
                     "timing.",
         evidence=ev("B", ["er2016"], "The 2016 report names the Royal Canadian Mint; two to four shipments a month is "
                                      "the original author's estimate."))
set_proc("corp-gold-sales",
         description="When the refinery credits ounces to the metal account, the treasury manager sells them at spot to "
                     "a financial institution, checks the refinery outturn against the shipment, and the corporate "
                     "controller matches the trade before it is recorded. The company had no gold forward contracts in "
                     "2020 or 2021. Timing and price decisions are approved by the CFO.",
         evidence=ev("A", ["src1", "wdofs2021"], "91,229 oz sold in 2020 for C$215.3M (src1); spot sales to financial "
                                                 "institutions only (wdofs2021)."))
set_proc("ts-grade-control", unit_of_work="one face mapped and sampled",
         cases_per_month={"low": 40, "mode": 65, "high": 100},
         description="After each round in an ore heading a geologist maps the face, takes chip samples, marks ore and "
                     "waste limits and updates the grade control model when assays return; miners take a muck "
                     "sample from each truck they load. Waste development is not sampled. Assay turnaround and inconsistent sampling decide how "
                     "much waste is sent to the mill.",
         evidence=ev("B", ["er2022"], "Section 11.1: chip samples on ore faces and muck samples taken by miners during "
                                      "loading. The count of 40 to 100 faces a month (one per 3 to 4 m round in ore) "
                                      "is the workflow author's estimate. Previously 130."))
set_proc("hse-env-monitoring", cases_per_month={"low": 8, "mode": 9, "high": 13},
         unit_of_work="one weekly effluent sampling event at one final discharge point",
         description="Technicians sample the mill polishing pond discharge and the mine settling pond discharge to Lake "
                     "C7 weekly and send monthly toxicity samples to an accredited lab; the coordinator checks results "
                     "against federal and provincial limits and files quarterly and annual reports. Mill effluent leaves "
                     "at controlled rates through most of the year. A failed toxicity test raises sampling frequency and "
                     "must be reported at once.",
         evidence=ev("A", ["src7", "er2022"], "MDMER weekly sampling and monthly toxicity tests (src7); two continuous "
                                              "discharge points (er2022, section 20.4)."))
set_proc("corp-budget", cases_per_month={"low": 0.083, "mode": 0.083, "high": 0.083})
set_proc("mnt-shutdown", cases_per_month={"low": 0.33, "mode": 0.42, "high": 0.58},
         description="Once a year the mill stops for one to three weeks for major work, as in August 2021 when the cone "
                     "crusher and trash screen were replaced and the secondary ball mill inspected, and several times a "
                     "year the mill or hoist stops for one to four days to reline mills, replace pumps and complete "
                     "inspections, with extra contractors on site. Scope creep, late parts and lockout coordination "
                     "decide whether the plant restarts on time.",
         evidence=ev("A", ["er2022"], "Table 17-1 note on the August 2021 shutdown; the count of short stops is the "
                                      "original author's estimate."))
set_proc("mill-reagents",
         description="Operators receive bulk sodium cyanide, zinc dust, lead nitrate, lime, flocculant, diatomaceous "
                     "earth and hydrogen peroxide, mix and store them under the cyanide handling procedure, and track "
                     "consumption. Cyanide deliveries need trained staff, emergency kits and a clear unloading area.",
         evidence=ev("B", ["er2022"], "Reagent list from section 17; weekly deliveries are the original author's "
                                      "estimate."))
P["site-rotation-logistics"]["evidence"]["note"] = (
    "Mill crews rotate seven days in and seven out (er2016) and underground crews on longer rotations (assumed 14/14), "
    "so a crew changes about every week.")
P["site-rotation-logistics"]["evidence"]["sources"] = ["er2016"]
P["site-rotation-logistics"]["evidence"]["tier"] = "B"
log.append("processes: 16 descriptions, volumes or names corrected")

# ---------------------------------------------------------------- 9. Headcounts of units and the company
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
org["profile"]["employees"] = sum(emp.values())
log.append(f"employees recomputed from roles: {org['profile']['employees']} (contractors excluded)")

# ---------------------------------------------------------------- 10. Assumptions
asm = [a for a in org["assumptions"] if not a.startswith("Corrected on 2026-11-24")]
for i, a in enumerate(asm):
    if a.startswith("Headcounts are the author's estimates"):
        asm[i] = ("Underground headcounts follow Table 16-10 of the 2022 technical report; other headcounts are the "
                  "original author's estimates from crew sizes for a 600-1,100 tpd underground mine with 12-hour shifts. "
                  "Mill crews rotate seven days in and seven out (er2016); the underground rotation is assumed to be 14 "
                  "on and 14 off. A role's headcount includes contractor staff who do the same work, recorded in "
                  "contractor_headcount and left out of the employee count. Contractors for drilling, catering, "
                  "shutdowns and the open pit are external parties.")
    if a.startswith("The mill capacity of about 1,100 tpd"):
        asm[i] = ("The mill averaged 779 t/d in 2021-2022, with a maximum day of 1,027 t/d (er2022, Table 17-1).")
asm.append("Corrected on 2026-11-24 from the Eagle River technical reports (er2022, er2016), after the workflow "
           "authors found the original file wrong: the mill uses gravity and Merrill-Crowe, not carbon-in-pulp; it is "
           "16.6 km by road from the mine, with a surface truck haul; the shaft hoists to a dump at the 70 m level; "
           "tailings are filtered and stacked dry; the assay office is in Wawa; the fleet and underground labour follow "
           "Tables 16-9 and 16-10. Ids mill-elution-refining, loaded_carbon, tailings_slurry and elution-circuit were "
           "renamed. See tools/fixes_2026_11_24_mining.py.")
org["assumptions"] = asm

# ---------------------------------------------------------------- 11. Workflows: titles, a note on the correction, file rename
titles = {r["id"]: r["title"] for r in org["roles"]}
NOTE = ("Organisation file corrected on 2026-11-24 to match this workflow's sources: ids were renamed "
        "(mill-elution-refining to mill-gold-room-refining, loaded_carbon to gold_concentrate, tailings_slurry to "
        "filtered_tailings, elution-circuit to refinery), and roles and resources this workflow added are now in the "
        "organisation file. Notes above that describe a mismatch refer to the file before the correction.")
for path, wf in workflows.items():
    for r in wf["roles"]:
        if r["id"] in titles and r.get("layer") != "external_party":
            r["title"] = titles[r["id"]]
    for r in wf.get("resources", []):
        if r["id"] in RES:
            r["name"] = RES[r["id"]]["name"]
    if path in touched and NOTE not in wf["assumptions"]:
        wf["assumptions"].append(NOTE)

org_path.write_text(json.dumps(org, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for path, wf in workflows.items():
    target = path.with_name(RENAME[path.stem] + ".json") if path.stem in RENAME else path
    target.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if target != path:
        path.unlink()
        log.append(f"renamed {path.name} to {target.name}")
print("\n".join(log))
