"""Per-workflow profile of where time goes: hands-on work, waiting, handoffs and mandatory controls.

Usage:
    python coordination_profile.py [ROOT]

Uses each step's most common (mode) times and the expected number of visits to each step, worked out from
the branch probabilities. Writes coordination_profile.csv and prints the medians across workflows.
Most step times are the authors' estimates, so read the output as indicative.
"""
import csv
import json
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
INTERNAL = {"queue", "batch", "calendar", "approval_availability"}
CHECK = {"review", "approval", "validation", "judgment"}
COORD = {"communication", "coordination"}
rows = []
for path in sorted((root / "workflows").glob("*.json")):
    w = json.loads(path.read_text(encoding="utf-8"))
    steps = w["steps"]
    ix = {s["id"]: i for i, s in enumerate(steps)}
    n = len(steps)
    visits, cur, handoffs = [0.0] * n, [0.0] * n, 0.0
    cur[0] = 1.0
    for _ in range(5000):                       # push probability mass through the step graph
        nxt, moved = [0.0] * n, 0.0
        for i, mass in enumerate(cur):
            if mass < 1e-12:
                continue
            visits[i] += mass
            for e in steps[i]["next"]:
                if e["to"] == "END":
                    continue
                j, m = ix[e["to"]], mass * float(e["prob"])
                nxt[j] += m
                moved += m
                if steps[j]["role"] != steps[i]["role"]:
                    handoffs += m
        cur = nxt
        if moved < 1e-9:
            break

    def total(field, keep=lambda s: True, weight=lambda s: 1.0):
        return sum(visits[i] * steps[i][field]["mode"] * weight(steps[i]) for i in range(n) if keep(steps[i]))

    touch, wait = total("touch_min"), total("wait_before_min")
    rows.append({
        "id": w["id"], "org": w["org"] or "", "steps": n,
        "roles": len({s["role"] for s in steps if s["role"] not in {"system", "external"}}),
        "hands_on_hours": round(touch / 60, 2), "elapsed_days": round((touch + wait) / 1440, 2),
        "waiting_share_of_elapsed": round(wait / max(touch + wait, 1e-9), 4),
        "internal_share_of_waiting": round(total("wait_before_min", lambda s: s["wait_cause"] in INTERNAL) / max(wait, 1e-9), 4),
        "internal_waiting_days": round(total("wait_before_min", lambda s: s["wait_cause"] in INTERNAL) / 1440, 2),
        "handoffs_per_case": round(handoffs, 2),
        "check_share_of_hands_on": round(total("touch_min", lambda s: s["kind"] in CHECK) / max(touch, 1e-9), 4),
        "coordination_share_of_hands_on": round(total("touch_min", lambda s: s["kind"] in COORD) / max(touch, 1e-9), 4),
        "desk_share_of_hands_on": round(total("touch_min", weight=lambda s: float(s["desk_work_share"])) / max(touch, 1e-9), 4),
        "controls": sum(1 for s in steps if s["control"]),
        "controls_fixed_by_law": sum(1 for s in steps if s["control"] and s["control"]["removability"] == "fixed_by_law"),
    })
with open(root / "coordination_profile.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)


def med(key):
    return statistics.median(r[key] for r in rows)


print(f"{len(rows)} workflows; medians:")
print(f"  hands-on {med('hands_on_hours'):.1f} h, elapsed {med('elapsed_days'):.1f} days, "
      f"waiting {med('waiting_share_of_elapsed'):.1%} of elapsed, of which internal {med('internal_share_of_waiting'):.0%}")
print(f"  handoffs {med('handoffs_per_case'):.1f} a case; checks {med('check_share_of_hands_on'):.0%} and "
      f"coordination {med('coordination_share_of_hands_on'):.0%} of hands-on time")
print(f"wrote coordination_profile.csv")
