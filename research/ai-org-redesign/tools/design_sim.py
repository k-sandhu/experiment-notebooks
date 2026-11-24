"""Rewrite each as-is workflow under several ways of organising AI agents, and compare the expected outcomes.

Usage:
    python design_sim.py [ROOT]

This is a sensitivity analysis, not a measurement. Nothing here observes an agent. Each design changes
who does a step, how long the step waits and how defects arise and are caught, using the assumed values
in PARAMS. The results say which processes are sensitive to which design choice under those assumptions,
and how much of the elapsed time no design can reach. Writes design_sim_results.csv (central values, one
row per workflow and design) and design_sim_sensitivity.csv (one assumption moved at a time).

Designs:
    as_is            the documented baseline, people only
    role_for_role    one agent per existing role; every handoff and every control stays
    case_owner       one agent carries the case from start to end
    shared_record    one agent per role, all working from one complete case record
    checker          one agent per role, with an independent checker at controls and at the end
The last three come in two versions: "_all" keeps a person at every control, "_legal" keeps a person only
where the control is fixed by law or needs a licensed sign-off.

How the main quantities are computed:
    Escaped defects. For each step the script finds the chance that a defect present when the case leaves
    that step reaches the end of the process uncaught, following the design's transition probabilities
    (loops included, solved by iteration). A defect made at a step escapes with that chance. A defect
    lost in a handoff escapes with the chance that the receiving step misses it and the defect then
    reaches the end uncaught. In the two checker designs the final checker then catches a share of what
    reaches the end, and that final check costs agent time, elapsed time and one extra handoff per case.
    Each defect it catches also costs repair work: a share (repair_share) of the case's hands-on time,
    split between people and agents in the proportions of that design.
    Rework. A design that changes the defect inflow or the catch rate scales the chance of sending work
    backward, but only on repair edges: a backward edge (to the same or an earlier step in list order)
    leaving a step that checks work. Every other edge keeps its documented probability, except that the
    remaining edges of a changed step are scaled so the row still sums to its original total. When the
    factor is above 1 the 0.9 cap never lowers an edge.
    Side-by-side steps. Steps that run side by side are counted by their longest member only when their
    expected visits are within 20% of each other. Otherwise they stay in sequence. Labour minutes are
    never scaled.
    Batch waits. A redesign shortens a batch wait only when the step's actor is an agent or a system, never
    for an external party or a person.
    Handoffs to retained people. In every redesign an agent step with desk_work_share below 0.9 hands part
    of its work to a person: two handoffs per visit are added.
    Case owner drift. Drift grows with the expected visits to agent steps per case in the as-is flows,
    not with the number of agent steps listed.
    Ratios. The escaped-defect ratio is written only when the as-is value is at least 1e-4, and medians use
    only the workflows where it is defined. An absolute difference is always written. A workflow is
    skipped everywhere if any probability is not finite or negative, or if its flows do not converge.
"""
import csv
import json
import math
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent

# Central value, then the low and high values used in the sweep. All are assumptions.
PARAMS = {
    "agent_time":        (0.20, 0.05, 0.50),  # agent's time on desk work as a share of the person's hands-on time
    "agent_queue":       (0.02, 0.00, 0.20),  # agent's queue wait as a share of the person's internal queue wait
    "batch_kept":        (0.25, 0.00, 1.00),  # share of batch waits that remain once a redesign runs continuously
    "agent_error":       (1.50, 0.50, 3.00),  # agent's defect rate on a step relative to the person's
    "handoff_loss":      (0.03, 0.00, 0.10),  # chance one agent-to-agent handoff introduces a defect
    "record_loss_kept":  (0.25, 0.00, 1.00),  # share of handoff loss that remains with a shared case record
    "owner_drift":       (0.10, 0.00, 0.50),  # extra error for a case owner per ten agent step visits it carries
    "shared_blind_spot": (0.50, 0.00, 0.90),  # how much a shared record lowers agents' chance of catching a defect
    "catch_person":      (0.60, 0.40, 0.80),  # chance a person's check catches a defect
    "catch_agent":       (0.40, 0.20, 0.60),  # chance an agent checking its own team's work catches a defect
    "catch_checker":     (0.75, 0.50, 0.90),  # chance an independent checker catches a defect
    "checker_time":      (0.10, 0.03, 0.30),  # final checker's agent minutes as a share of the case's as-is desk minutes
    "repair_share":      (0.15, 0.05, 0.40),  # share of the case's hands-on time redone for each defect the final checker catches
}
DESIGNS = ["as_is", "role_for_role", "case_owner_all", "case_owner_legal", "shared_record_all", "shared_record_legal",
           "checker_all", "checker_legal"]
CHECK = {"review", "approval", "validation", "judgment"}
AGENT_WAITS = {"queue", "approval_availability"}
FIXED_WAITS = {"external_party", "transit", "calendar"}


def mean(tri):
    return (float(tri["low"]) + float(tri["mode"]) + float(tri["high"])) / 3


def bad_probability(wf):
    """Return a short reason if any probability in the workflow is not finite or is negative, else None."""
    for s in wf["steps"]:
        values = [("introduces_defect_prob", s["error"]["introduces_defect_prob"])]
        values += [("next prob", e["prob"]) for e in s["next"]]
        for name, v in values:
            try:
                x = float(v)
            except (TypeError, ValueError):
                return f"{s['id']} {name} not a number"
            if not math.isfinite(x) or x < 0:
                return f"{s['id']} {name} = {v}"
    return None


def flows(steps, ix, probs):
    """Expected visits to each step and expected flow along each edge, for one case.
    The third value is False if mass was still moving after the last iteration, so the totals are truncated."""
    n = len(steps)
    visits, cur, edge = [0.0] * n, [0.0] * n, {}
    cur[0] = 1.0
    moved = 0.0
    for _ in range(6000):
        nxt, moved = [0.0] * n, 0.0
        for i, mass in enumerate(cur):
            if mass < 1e-13:
                continue
            visits[i] += mass
            for k, e in enumerate(steps[i]["next"]):
                if e["to"] == "END":
                    continue
                j, m = ix[e["to"]], mass * probs[i][k]
                nxt[j] += m
                moved += m
                edge[(i, j)] = edge.get((i, j), 0.0) + m
        cur = nxt
        if moved < 1e-10:
            break
    return visits, edge, moved <= 1e-6


def escape_chance(steps, ix, probs, catch):
    """esc[i]: chance a defect present when the case leaves step i reaches END uncaught.
    esc[i] = sum over edges of prob * (1 if END else (1 - catch[j]) * esc[j]), solved by iteration so loops work.
    Returns None if the iteration does not converge."""
    n = len(steps)
    esc = [0.0] * n
    for _ in range(50000):
        delta = 0.0
        for i in range(n - 1, -1, -1):
            v = 0.0
            for k, e in enumerate(steps[i]["next"]):
                if e["to"] == "END":
                    v += probs[i][k]
                else:
                    j = ix[e["to"]]
                    v += probs[i][k] * (1 - catch[j]) * esc[j]
            delta = max(delta, abs(v - esc[i]))
            esc[i] = v
        if delta < 1e-13:
            return esc
    return None


def run(wf, design, P, base=None):
    """Returns (result, base). The result is None if the flows did not converge."""
    steps = wf["steps"]
    n = len(steps)
    ix = {s["id"]: i for i, s in enumerate(steps)}
    cost = {r["id"]: float(r["loaded_cost_per_hour"]["mode"]) for r in wf["roles"]}
    kind = design.rsplit("_", 1)[0] if design.endswith(("_all", "_legal")) else design
    legal_only = design.endswith("_legal")
    redesign = kind in {"case_owner", "shared_record", "checker"}

    as_is_probs = [[float(e["prob"]) for e in s["next"]] for s in steps]
    base = base if base else flows(steps, ix, as_is_probs)
    base_visits, base_edge, base_ok = base
    if not base_ok:
        return None, base

    actor, group = [], []
    for s in steps:
        if s["role"] in {"system", "external"}:
            actor.append(s["role"])
            group.append(s["role"])
            continue
        c = s["control"]
        kept = bool(c) and (not legal_only or c["removability"] == "fixed_by_law" or c["type"] == "licensed_signoff")
        is_agent = design != "as_is" and float(s["desk_work_share"]) >= 0.5 and not kept
        actor.append("agent" if is_agent else "person")
        group.append(("agent", "owner") if is_agent and kind == "case_owner" else (actor[-1], s["role"]))
    n_agent = sum(a == "agent" for a in actor)
    agent_visits_as_is = sum(base_visits[i] for i in range(n) if actor[i] == "agent")
    drift = 1 + P["owner_drift"] * agent_visits_as_is / 10 if kind == "case_owner" else 1.0

    touch_elapsed, person_min, agent_min, wait, defect, catch = [], [], [], [], [], []
    for i, s in enumerate(steps):
        t, d = mean(s["touch_min"]), float(s["desk_work_share"])
        w, cause = mean(s["wait_before_min"]), s["wait_cause"]
        p = float(s["error"]["introduces_defect_prob"])
        if actor[i] == "agent":
            a = d * P["agent_time"] * t
            touch_elapsed.append(a + (1 - d) * t)
            person_min.append((1 - d) * t)
            agent_min.append(a)
            if cause in AGENT_WAITS:
                w *= P["agent_queue"]
            p *= P["agent_error"] * drift
        else:
            touch_elapsed.append(t)
            person_min.append(t if actor[i] == "person" else 0.0)
            agent_min.append(0.0)
        if cause == "batch" and redesign and actor[i] in ("agent", "system"):
            w *= P["batch_kept"]
        wait.append(w)
        defect.append(min(p, 1.0))
        is_check = s["kind"] in CHECK or bool(s["control"])
        if not is_check:
            catch.append(0.0)
        elif actor[i] == "agent":
            if kind == "checker" and s["control"]:
                catch.append(P["catch_checker"])
            elif kind == "shared_record":
                catch.append(P["catch_agent"] * (1 - P["shared_blind_spot"]))
            else:
                catch.append(P["catch_agent"])
        else:
            catch.append(P["catch_person"])

    loss = P["handoff_loss"] * (P["record_loss_kept"] if kind == "shared_record" else 1.0)
    crossings = sum(m for (i, j), m in base_edge.items()
                    if actor[i] == "agent" and actor[j] == "agent" and group[i] != group[j])
    base_defect = [float(s["error"]["introduces_defect_prob"]) for s in steps]
    inflow_base = sum(v * p for v, p in zip(base_visits, base_defect))
    inflow = sum(v * p for v, p in zip(base_visits, defect)) + loss * crossings
    checks = [i for i in range(n) if catch[i] > 0]
    mean_catch = sum(base_visits[i] * catch[i] for i in checks) / max(sum(base_visits[i] for i in checks), 1e-9)
    if design == "as_is" or inflow_base < 1e-9:
        rework = 1.0
    else:
        rework = (inflow / inflow_base) * (mean_catch / P["catch_person"] if checks else 1.0)

    # Only defect-driven repair edges change: backward edges leaving a step that checks work.
    probs = []
    for i, s in enumerate(steps):
        row = list(as_is_probs[i])
        if rework != 1.0 and (s["kind"] in CHECK or s["control"]):
            rep = [k for k, e in enumerate(s["next"]) if e["to"] != "END" and ix[e["to"]] <= i]
            rest = sum(row[k] for k in range(len(row)) if k not in rep)
            if rep and rest > 1e-12:
                old = sum(row[k] for k in rep)
                total = old + rest
                if rework > 1:
                    new = {k: min(max(row[k], 0.9), row[k] * rework) for k in rep}
                else:
                    new = {k: row[k] * rework for k in rep}
                new_total = sum(new.values())
                cap = min(total, max(old, 0.9)) if rework > 1 else total
                if new_total > cap and new_total > 0:
                    new = {k: v * cap / new_total for k, v in new.items()}
                    new_total = cap
                f = (total - new_total) / rest
                row = [new[k] if k in new else row[k] * f for k in range(len(row))]
        probs.append(row)
    visits, edge, ok = flows(steps, ix, probs)
    if not ok:
        return None, base

    # Steps listed in sequence that really run side by side: count the longest, not the sum,
    # but only when the members are visited about equally often. Labour minutes are never scaled.
    scale = [1.0] * n
    seen = set()
    for i, s in enumerate(steps):
        if i in seen or not s.get("concurrent_with"):
            continue
        members, stack = set(), [i]
        while stack:
            k = stack.pop()
            if k in members:
                continue
            members.add(k)
            stack.extend(ix[x] for x in steps[k].get("concurrent_with", []) if x in ix)
            stack.extend(j for j, o in enumerate(steps) if steps[k]["id"] in o.get("concurrent_with", []))
        seen |= members
        lo, hi = min(visits[k] for k in members), max(visits[k] for k in members)
        if lo <= 0 or hi / lo > 1.2:
            continue
        spans = {k: touch_elapsed[k] + wait[k] for k in members}
        total = sum(spans.values())
        if total > 0:
            for k in members:
                scale[k] = max(spans.values()) / total

    esc = escape_chance(steps, ix, probs, catch)
    if esc is None:
        return None, base
    reach_end = sum(visits[i] * defect[i] * esc[i] for i in range(n))
    reach_end += sum(m * loss * (1 - catch[j]) * esc[j] for (i, j), m in edge.items()
                     if actor[i] == "agent" and actor[j] == "agent" and group[i] != group[j])
    escaped = reach_end * (1 - P["catch_checker"]) if kind == "checker" else reach_end
    caught_final = reach_end * P["catch_checker"] if kind == "checker" else 0.0

    elapsed = sum(visits[i] * (touch_elapsed[i] + wait[i]) * scale[i] for i in range(n))
    fixed = sum(visits[i] * wait[i] * scale[i] for i in range(n) if steps[i]["wait_cause"] in FIXED_WAITS)
    person_wait = sum(visits[i] * wait[i] * scale[i] for i in range(n)
                      if actor[i] == "person" and steps[i]["wait_cause"] not in FIXED_WAITS)
    person_minutes = sum(visits[i] * person_min[i] for i in range(n))
    agent_minutes = sum(visits[i] * agent_min[i] for i in range(n))
    person_cost = sum(visits[i] * person_min[i] / 60 * cost.get(steps[i]["role"], 0.0) for i in range(n))
    handoffs = sum(m for (i, j), m in edge.items() if group[i] != group[j])
    if design != "as_is":
        handoffs += sum(2 * visits[i] for i in range(n)
                        if actor[i] == "agent" and float(steps[i]["desk_work_share"]) < 0.9)
    if kind == "checker":
        # The final checker's own work, then the repair of each defect it catches.
        desk_as_is = sum(base_visits[i] * float(steps[i]["desk_work_share"]) * mean(steps[i]["touch_min"])
                         for i in range(n))
        check_min = P["checker_time"] * desk_as_is
        redo = caught_final * P["repair_share"]
        repair_elapsed = redo * sum(visits[i] * touch_elapsed[i] * scale[i] for i in range(n))
        elapsed += check_min + repair_elapsed
        person_cost += redo * person_cost
        person_minutes_new = person_minutes * (1 + redo)
        agent_minutes_new = agent_minutes * (1 + redo) + check_min
        person_minutes, agent_minutes = person_minutes_new, agent_minutes_new
        handoffs += 1
    return {
        "elapsed_days": elapsed / 1440,
        "person_minutes": person_minutes,
        "agent_minutes": agent_minutes,
        "person_cost": person_cost,
        "handoffs": handoffs,
        "agent_handoffs": sum(m for (i, j), m in edge.items()
                              if actor[i] == "agent" and actor[j] == "agent" and group[i] != group[j]),
        "step_visits": sum(visits),
        "escaped_defects": escaped,
        "fixed_wait_days": fixed / 1440,
        "person_wait_days": person_wait / 1440,
        "agent_steps": n_agent,
        "person_steps": sum(a == "person" for a in actor),
        "rework_factor": rework,
    }, base


def central(P):
    return {k: v[0] for k, v in P.items()}


def evaluate(wf, P):
    """All designs for one workflow, or None if any design did not converge."""
    base, out = None, {}
    for design in DESIGNS:
        out[design], base = run(wf, design, P, base)
        if out[design] is None:
            return None
    return out


loaded = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "workflows").glob("*.json"))]
workflows, skipped = [], []
rows = []
P0 = central(PARAMS)
for wf in loaded:
    reason = bad_probability(wf)
    out = None if reason else evaluate(wf, P0)
    if out is None:
        skipped.append((wf["id"], reason or "flows did not converge"))
        continue
    workflows.append(wf)
    a = out["as_is"]
    for design in DESIGNS:
        r = out[design]
        row = {"id": wf["id"], "org": wf["org"] or "general", "design": design}
        row.update({k: round(v, 8) for k, v in r.items()})
        row["elapsed_vs_as_is"] = round(r["elapsed_days"] / max(a["elapsed_days"], 1e-9), 4)
        row["person_minutes_vs_as_is"] = round(r["person_minutes"] / max(a["person_minutes"], 1e-9), 4)
        row["person_cost_vs_as_is"] = round(r["person_cost"] / max(a["person_cost"], 1e-9), 4)
        row["handoffs_vs_as_is"] = round(r["handoffs"] / max(a["handoffs"], 1e-9), 4)
        row["escaped_vs_as_is"] = (round(r["escaped_defects"] / a["escaped_defects"], 4)
                                   if a["escaped_defects"] >= 1e-4 else "")
        row["escaped_minus_as_is"] = round(r["escaped_defects"] - a["escaped_defects"], 8)
        row["as_is_fixed_wait_share"] = round(a["fixed_wait_days"] / max(a["elapsed_days"], 1e-9), 4)
        rows.append(row)
with open(root / "design_sim_results.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

skipped_in_sweep = {}


def summarise(P, label):
    acc = {d: {"elapsed": [], "person": [], "escaped": []} for d in DESIGNS}
    for wf in workflows:
        out = evaluate(wf, P)
        if out is None:
            skipped_in_sweep.setdefault(wf["id"], set()).add(label)
            continue
        a = out["as_is"]
        for design in DESIGNS:
            r = out[design]
            acc[design]["elapsed"].append(r["elapsed_days"] / max(a["elapsed_days"], 1e-9))
            acc[design]["person"].append(r["person_minutes"] / max(a["person_minutes"], 1e-9))
            if a["escaped_defects"] >= 1e-4:
                acc[design]["escaped"].append(r["escaped_defects"] / a["escaped_defects"])
    med = {d: {k: (statistics.median(v) if v else float("nan")) for k, v in m.items()} for d, m in acc.items()}
    for d in DESIGNS:
        med[d]["escaped_n"] = len(acc[d]["escaped"])
    return med


def rounded(m):
    return {k: (v if k == "escaped_n" else round(v, 4)) for k, v in m.items()}


sens = []
mid = summarise(P0, "central")
for design in DESIGNS:
    sens.append({"parameter": "central", "value": "", "design": design, **rounded(mid[design])})
for name, (c, lo, hi) in PARAMS.items():
    for value in (lo, hi):
        P = dict(P0)
        P[name] = value
        res = summarise(P, f"{name}={value}")
        for design in DESIGNS:
            sens.append({"parameter": name, "value": value, "design": design, **rounded(res[design])})
with open(root / "design_sim_sensitivity.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(sens[0]))
    writer.writeheader()
    writer.writerows(sens)

print(f"{len(workflows)} workflows, {len(DESIGNS)} designs. Median across workflows, relative to as-is (central assumptions):")
print(f"{'design':22}{'elapsed':>9}{'person time':>13}{'escaped defects':>17}{'n escaped':>11}")
for design in DESIGNS:
    m = mid[design]
    print(f"{design:22}{m['elapsed']:>9.2f}{m['person']:>13.2f}{m['escaped']:>17.2f}{m['escaped_n']:>11d}")
print("escaped ratio is the median over workflows whose as-is escaped defects are at least 1e-4")
print(f"skipped workflows: {len(skipped)}")
for wid, reason in skipped:
    print(f"  {wid}: {reason}")
if skipped_in_sweep:
    print(f"workflows skipped at some sweep settings only: {len(skipped_in_sweep)}")
    for wid, labels in sorted(skipped_in_sweep.items()):
        print(f"  {wid}: {sorted(labels)}")
print("wrote design_sim_results.csv and design_sim_sensitivity.csv")
