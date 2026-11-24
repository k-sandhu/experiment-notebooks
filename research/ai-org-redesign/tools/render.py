"""Render organisation and workflow JSON files (format 0.2) as readable Markdown pages with Mermaid diagrams.

Usage:
    python render.py OUT_DIR FILE.json [FILE.json ...]
"""
import json
import re
import sys
from pathlib import Path


def clean(text):
    return re.sub(r"[\"\[\]{}()|<>#;`]", " ", str(text)).strip()


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def minutes(value):
    value = float(value)
    if value >= 1440:
        return f"{value / 1440:.1f} d"
    if value >= 60:
        return f"{value / 60:.1f} h"
    return f"{value:g} min"


def cite(ev):
    refs = ", ".join(f"[{r}]" for r in ev.get("sources", []))
    return f"{ev['tier']}{' ' + refs if refs else ''}"


def source_lines(doc):
    out = []
    if doc["assumptions"]:
        out += ["## Assumptions", ""] + [f"- {a}" for a in doc["assumptions"]] + [""]
    if doc["sources"]:
        out += ["## Sources", ""]
        for s in doc["sources"]:
            link = f"[{s['title']}]({s['url']})" if s["url"] else f"{s['title']} (link withheld)"
            out.append(f"- [{s['id']}] {link} ({s['publisher']}, {s['year']}). {s['supports']}")
        out.append("")
    out.append(f"Written by {doc['author']['model']} on {doc['author']['date']}.")
    return out


def render_workflow(wf):
    roles = {r["id"]: r for r in wf["roles"]}

    def role_title(rid):
        return roles[rid]["title"] if rid in roles else {"system": "Automated", "external": "Outside party"}.get(rid, rid)

    home = f" · part of `{wf['org']}`" if wf["org"] else ""
    out = [f"# {wf['name']}", "", f"`{wf['id']}` · {wf['sector']} · {wf['function']}{home}", "", wf["summary"], ""]
    base = wf["baseline"]
    vol = wf["volume"]["cases_per_month"]
    out += ["| | |", "|---|---|",
            f"| Unit of work | {cell(wf['unit_of_work'])} |",
            f"| Starts when | {cell(wf['trigger'])} |",
            f"| Done when | {cell(wf['end_state'])} |",
            f"| Organisation | {cell(base['org_archetype'])} ({base['org_size_employees']:,} employees, {base['period']}) |",
            f"| Volume | {vol['mode']:,} cases a month (range {vol['low']:,} to {vol['high']:,}) |", ""]

    iface = wf["interfaces"]
    out += ["## Where it sits", ""]
    for link in iface["triggered_by"]:
        out.append(f"- Starts with **{link['object']}** from {link['from']} ({float(link.get('share', 1)):.0%} of cases)")
    for link in iface.get("inputs", []):
        out.append(f"- Relies on **{link['object']}** from {link['from']} (a standing input; it does not start a case)")
    for link in iface["produces"]:
        out.append(f"- Sends **{link['object']}** to {link['to']} (outcome: {link['outcome']})")
    out.append("")

    out += ["## Flow", "", "```mermaid", "flowchart TD"]
    for step in wf["steps"]:
        label = f"{step['id']} {clean(step['name'])}<br/>{clean(role_title(step['role']))}"
        shape = (f'{step["id"]}{{{{"{label}"}}}}' if len(step["next"]) > 1 else f'{step["id"]}["{label}"]')
        out.append(f"    {shape}")
    ends = {}
    for step in wf["steps"]:
        for edge in step["next"]:
            target = edge["to"]
            if target == "END":
                key = clean(edge.get("outcome", "end"))
                target = ends.setdefault(key, f"end{len(ends)}")
            prob = float(edge["prob"])
            if prob >= 0.995:
                out.append(f"    {step['id']} --> {target}")
            else:
                out.append(f'    {step["id"]} -->|"{prob:.0%}"| {target}')
    for label, node in ends.items():
        out.append(f'    {node}(["{label}"])')
    out += ["```", ""]

    out += ["## Roles", "", "| Role | Department | Layer | FTE on this process | Loaded cost per hour | Evidence |",
            "|---|---|---|---:|---:|---|"]
    for r in wf["roles"]:
        out.append(f"| {cell(r['title'])} | {cell(r.get('department', ''))} | {r['layer'].replace('_', ' ')} | "
                   f"{r['fte_on_process']:g} | {r['loaded_cost_per_hour']['mode']:g} {wf['currency']} | {cite(r['evidence'])} |")
    out.append("")

    out += ["## Steps", "",
            "Hands-on time and the wait before each step show the most common value. Evidence tier A is a sourced "
            "number, B a sourced description, C the author's estimate.", "",
            "| Step | Who | Kind | Hands-on | Wait before | Control | Evidence |", "|---|---|---|---:|---:|---|---|"]
    for s in wf["steps"]:
        control = cell(s["control"]["basis"]) if s["control"] else ""
        out.append(f"| **{s['id']} {cell(s['name'])}.** {cell(s['description'])} | {cell(role_title(s['role']))} | "
                   f"{s['kind'].replace('_', ' ')} | {minutes(s['touch_min']['mode'])} | "
                   f"{minutes(s['wait_before_min']['mode'])} | {control} | {cite(s['evidence'])} |")
    out.append("")

    if wf["exceptions"]:
        out += ["## Exceptions", "", "| Exception | Share of cases | What happens |", "|---|---:|---|"]
        for e in wf["exceptions"]:
            share = e.get("share_of_cases")
            share = f"{float(share):.0%}" if isinstance(share, (int, float)) else cell(share)
            out.append(f"| {cell(e['name'])} | {share} | {cell(e['description'])} |")
        out.append("")
    if wf["benchmarks"]:
        out += ["## Benchmarks", "", "| Metric | Value | Unit | Population | Evidence |", "|---|---|---|---|---|"]
        for b in wf["benchmarks"]:
            value = b["value"]
            if isinstance(value, dict):
                value = ", ".join(f"{k} {v}" for k, v in value.items())
            out.append(f"| {cell(b['metric'])} | {cell(value)} | {cell(b.get('unit', ''))} | "
                       f"{cell(b.get('population', ''))} | {cite(b['evidence'])} |")
        out.append("")
    if wf["pain_points"]:
        out += ["## Pain points", ""]
        for p in wf["pain_points"]:
            out.append(f"- {p['description']} (steps {', '.join(p.get('steps', [])) or 'n/a'}; {cite(p['evidence'])})")
        out.append("")
    return "\n".join(out + source_lines(wf)) + "\n"


def render_org(org):
    units = {u["id"]: u for u in org["units"]}
    kids = {}
    for u in org["units"]:
        kids.setdefault(u["parent"], []).append(u)

    def top(uid):
        while units[uid]["parent"] is not None:
            uid = units[uid]["parent"]
        return uid

    prof = org["profile"]
    model = f" · modelled on public information about {org['modelled_on']}" if org["modelled_on"] else ""
    out = [f"# {org['name']}", "", f"`{org['id']}` · {org['sector']}{model}", "", org["summary"], "",
           "| | |", "|---|---|", f"| Employees | {prof['employees']:,} |", f"| Country | {cell(prof['country'])} |",
           f"| Ownership | {cell(prof['ownership'])} |", f"| Regulators | {cell(', '.join(prof.get('regulators', [])))} |"]
    for item in prof.get("scale", []):
        value = f"{item['value']:,}" if isinstance(item["value"], (int, float)) else item["value"]
        out.append(f"| {cell(item['name'])} | {value} {cell(item.get('unit', ''))} ({item['evidence']['tier']}) |")
    out += ["", "## Units", ""]

    def walk(parent, depth):
        for u in kids.get(parent, []):
            out.append(f"{'  ' * depth}- **{u['name']}** ({u['headcount']:,} people, {u['kind'].replace('_', ' ')}): "
                       f"{u['purpose']}")
            walk(u["id"], depth + 1)

    walk(None, 0)
    out += ["", "## Demand drivers", "", "| Driver | Per month | Unit | Evidence |", "|---|---:|---|---|"]
    for d in org["demand_drivers"]:
        out.append(f"| {cell(d['name'])} | {d['per_month']['mode']:,} | {cell(d['unit'])} | {cite(d['evidence'])} |")

    procs = {p["id"]: p for p in org["process_map"]}
    parties = {p["id"]: p for p in org["external_parties"]}
    core = {pid for pid, p in procs.items() if p["category"] == "core"}
    node = {pid: f"p{i}" for i, pid in enumerate(procs)}
    node.update({pid: f"x{i}" for i, pid in enumerate(parties)})
    edges = []
    for pid in procs:
        if pid not in core:
            continue
        for link in procs[pid]["produces"]:
            if link["to"] in core or link["to"] in parties:
                edges.append((pid, link["to"]))
        for link in procs[pid]["triggered_by"]:
            if link["from"] in parties:
                edges.append((link["from"], pid))
    edges = list(dict.fromkeys(edges))
    shown = {x for edge in edges for x in edge}
    out += ["", "## How the core processes connect", "", "```mermaid", "flowchart LR"]
    by_top = {}
    for pid in procs:
        if pid in shown and pid in core:
            by_top.setdefault(top(procs[pid]["owner_unit"]), []).append(pid)
    for i, (uid, pids) in enumerate(by_top.items()):
        out.append(f'    subgraph g{i}["{clean(units[uid]["name"])}"]')
        for pid in pids:
            out.append(f'        {node[pid]}["{clean(procs[pid]["name"])}"]')
        out.append("    end")
    for pid in parties:
        if pid in shown:
            out.append(f'    {node[pid]}(["{clean(parties[pid]["name"])}"])')
    for a, b in edges:
        out.append(f"    {node[a]} --> {node[b]}")
    out += ["```", "", "## Process map", ""]

    def name_of(ref):
        return (procs.get(ref) or parties[ref])["name"]

    for u in kids.get(None, []):
        rows = [p for p in org["process_map"] if top(p["owner_unit"]) == u["id"]]
        if not rows:
            continue
        out += [f"### {u['name']}", "",
                "| Process | Owner | Type | Unit of work | Per month | Priority | Receives from | Sends to |",
                "|---|---|---|---|---:|---:|---|---|"]
        for p in sorted(rows, key=lambda p: (p["detail_priority"], p["name"])):
            src = ", ".join(sorted({name_of(t["from"]) for t in p["triggered_by"] + p.get("inputs", [])}))
            dst = ", ".join(sorted({name_of(t["to"]) for t in p["produces"]}))
            out.append(f"| **{cell(p['name'])}.** {cell(p['description'])} | {cell(units[p['owner_unit']]['name'])} | "
                       f"{p['category']} | {cell(p['unit_of_work'])} | {p['cases_per_month']['mode']:,} | "
                       f"{p['detail_priority']} | {cell(src)} | {cell(dst)} |")
        out.append("")
    titles = {r["id"]: r["title"] for r in org["roles"]}
    out += ["## Roles", "", "| Role | Unit | Layer | Reports to | Headcount | Loaded cost per hour |",
            "|---|---|---|---|---:|---:|"]
    for r in org["roles"]:
        out.append(f"| {cell(r['title'])} | {cell(units[r['unit']]['name'])} | {r['layer'].replace('_', ' ')} | "
                   f"{cell(titles.get(r['reports_to'], ''))} | {r['headcount']:,} | "
                   f"{r['loaded_cost_per_hour']['mode']:g} {org['currency']} |")
    out += ["", "## Systems", ""] + [f"- **{s['name']}** ({s['kind'].replace('_', ' ')})" for s in org["systems"]]
    out += ["", "## Outside parties", ""] + [f"- **{p['name']}**: {p['description']}" for p in org["external_parties"]]
    out += ["", "## Things that pass between processes", ""]
    out += [f"- **{o['name']}**: {o['description']}" for o in org["business_objects"]] + [""]
    return "\n".join(out + source_lines(org)) + "\n"


def main():
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[2:]:
        path = Path(name)
        doc = json.loads(path.read_text(encoding="utf-8"))
        text = render_org(doc) if "process_map" in doc else render_workflow(doc)
        (out_dir / f"{path.stem}.md").write_text(text, encoding="utf-8")
        print(f"rendered {path.stem}.md")


if __name__ == "__main__":
    main()
