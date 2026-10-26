"""Stage section 13 without changing notebook/README unless write=True is explicit."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from pathlib import Path


AUTHORING = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("NOTEBOOK_REPO_ROOT", r"C:\Users\sandh\.codex\worktrees\synthetic-data-curation\experiment_notebooks"))
NOTEBOOK_REL = Path("notebooks/23-synthetic-data-curation/23_synthetic_data_curation.ipynb")
HIGH_SECTION_TITLE = "13. Larger source packs and higher reasoning"
HIGH_CORE_HELPERS = ["high_transport.py", "high_fixtures.py", "high_material_audit.py", "high_experiment.py"]


def _high_cell(source, kind="markdown"):
    cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    cell["id"] = "high-v4-" + hashlib.sha256(source.encode()).hexdigest()[:14]
    return cell


def _high_namespace():
    ns = {"__name__": "notebook_23_high_builder"}
    for name in HIGH_CORE_HELPERS + ["high_reporting.py"]:
        exec(compile((AUTHORING / name).read_text(encoding="utf-8-sig"), name, "exec"), ns)
    return ns


def _high_table(ns, headers, rows):
    return ns["high_report_table"](headers, rows)


def _high_source_excerpt(case, trace):
    """Literal rows from the rendered source, selected for the worked calculation."""
    lines = case["document"].splitlines()
    keys = {
        "P01": [case["source_record"]["target_line_id"]],
        "P02": [trace["term_winners"]["ordered_units"]["approval"], trace["term_winners"]["price_plan"]["approval"]],
        "P03": [case["source_record"]["target_sku"]],
        "P04": [],
        "P05": [trace["price"]["plan"]],
        "P06": [],
    }
    returns = [r for r in trace["events"] if r["reason"] == "accepted_return" and r["net_dispatched_units"]]
    if returns:
        row = returns[0]
        keys["P06"] = [row["event_id"], row["reference"]]
        original = next(r for r in case["source_record"]["ledger"] if r["event_id"] == row["reference"])
        keys["P04"] = [original["allocation"]]
    chosen = []
    for doc, starts in keys.items():
        a, b = lines.index("BEGIN TABLE " + doc), lines.index("END TABLE " + doc)
        rows = [s for s in lines[a + 2:b] if s.split(" | ", 1)[0] in starts]
        if doc == "P05":
            rows = [s for s in rows if int(s.split(" | ")[2]) == trace["price"]["tier_minimum"]]
        if rows:
            chosen += ["[" + doc + "] Literal source rows", lines[a + 1], *rows]
    return "\n".join(chosen)


def _high_workflow(report):
    complete = report["state"] == "complete"
    actual = ("Completed paired comparison" if complete else "Not reached: service-blocked")
    return """\x60\x60\x60mermaid
flowchart LR
    source["Code-generated procurement packs<br/>32 pilot + 1056 potential main sources"] --> audit["Visible-text reconstruction<br/>independent SQL/Decimal and Fraction audits"]
    audit --> pilot["Planned high-reasoning Sol ladder<br/>8 cases per level, up to 4 levels"]
    pilot --> level["First level with 3 valid-schema value failures<br/>or declared level-4 fallback"]
    level --> original["160 original collection calls<br/>+80 only if fewer than 40 genuine failures"]
    original --> select["Freeze random cap of 80 original value failures"]
    select --> sealed["24 separate audit calls<br/>excluded from selection"]
    select --> pair["Fresh retry and feedback repair<br/>same cases, one high-reasoning call per arm"]
    pair --> score["Paired value recovery, evidence, usage<br/>""" + actual + """ "]
    pilot -. "service status kept separate" .-> status["HTTP 429 and pending attempts<br/>are not extraction errors"]
\x60\x60\x60"""


def _high_call_graph():
    return """\x60\x60\x60mermaid
flowchart TD
    packet["Same complete source pack + exact task instructions"] --> first["GPT-6.1 Sol via codex exec<br/>high reasoning, one case<br/>returns seven fields + citations"]
    first --> check["Deterministic checker<br/>valid-schema wrong-value cases only"]
    check -->|"Selected original failure"| branch["Two planned independent calls on this case"]
    packet --> fresh["GPT-6.1 Sol via codex exec<br/>fresh retry, high reasoning"]
    branch --> fresh
    packet --> repair["GPT-6.1 Sol via codex exec<br/>feedback repair, high reasoning"]
    branch -->|"Exact old output + failed field names<br/>no expected values"| repair
    fresh --> paired["Compare the same case's two outcomes"]
    repair --> paired
\x60\x60\x60

The two intervention jobs are dispatched in a frozen shuffled order, and the completed runner waits for both arms before reporting paired outcomes. A fresh retry sees the source again. Feedback repair also sees the original answer and generic field-name flags. This compares that repair package with another attempt, rather than isolating feedback from exposure to the previous answer. The service-blocked state has no completed intervention pairs.
"""


def _high_outcomes(report, ns):
    if report["state"] != "complete":
        counts = report["status_counts"]
        rows = [[key, value] for key, value in [
            ("Usable model answers across preserved protocols", counts["usable_answer"]),
            ("Terminal HTTP 429 failures", counts["http_429"]),
            ("Other terminal failures", counts["other_terminal_failure"]),
            ("Interrupted/pending records", counts["pending"]),
            ("All recorded CLI subprocess attempts", report["n_started_requests"]),
        ]]
        available = len(report["usable_answers"])
        ladder = report.get("pilot_ladder")
        level_note = (f"The pilot selected level {ladder['selected_level']}; its declared threshold was {ladder['threshold_met']}. " if ladder else
                      "No completed replacement ladder has selected a difficulty level. ")
        return ("The high-reasoning follow-up has not completed its paired comparison. "
                "The raw preserved attempts currently have the following service outcomes:\n\n" +
                _high_table(ns, ["Raw service outcome", "Attempts"], rows) +
                "\n\nHTTP 429 means the service rejected the request. A pending record was interrupted before a terminal answer was saved. "
                "Neither supplies an extracted quantity or price, so neither can be counted as a model value error. "
                f"The {available} usable answers are real observations; representative records are shown below. Archived interrupted protocols remain excluded "
                "from replacement difficulty selection. Unanswered requests cannot estimate performance on higher levels or a feedback advantage. "
                + level_note + "There is no complete paired main comparison, repair rate, fresh-retry rate or paired accuracy difference to report.")
    bundle, metrics = report["bundle"], report["bundle"]["metrics"]
    main = metrics["original_collection"]
    rows = [["Original collection", main["n_attempted_cases"], main["value_correct_valid_schema"], main["accepted"]]]
    rows += [[r["arm"].replace("_", " "), r["n_attempted_cases"], r["value_correct_valid_schema"], r["accepted"]]
             for r in metrics["interventions"]]
    pair = metrics["paired_value_recovery"]
    if not pair["n_pairs"]:
        return (_high_table(ns, ["Stage", "Attempted cases", "Valid schema and seven exact values", "Values and citations accepted"], rows) +
                "\n\nNo genuine original value failure was selected. No paired recovery rate or repair advantage can be estimated.")
    return ("The complete main run separates all-value correctness from full acceptance, which also requires sufficient citations:\n\n" +
            _high_table(ns, ["Stage", "Attempted cases", "Valid schema and seven exact values", "Values and citations accepted"], rows) +
            f"\n\nOn {pair['n_pairs']} paired selected source cases, repair alone recovered {pair['repair_only']}, "
            f"fresh retry alone recovered {pair['fresh_only']}, both recovered {pair['both_success']}, "
            f"and neither recovered {pair['neither_success']}. The repair-minus-fresh difference is "
            f"{pair['difference_percentage_points']} percentage points; its case-paired bootstrap 95% interval is "
            f"{pair['paired_bootstrap_95_interval_percentage_points']}. The exact conditional two-sided McNemar p-value is "
            f"{pair['exact_mcnemar_two_sided_p']}. These are descriptive results conditional on pilot difficulty and original-failure selection. "
            "Shared templates, a selected sample and few discordant pairs can limit inference; even a degenerate interval is not proof of equivalence.")


def _high_observed_examples(report, ns):
    text = ["### Actual saved answers and their limits\n"]
    if report["state"] == "complete":
        bundle = report["bundle"]
        originals = sorted([r for r in bundle["candidates"] if r["split"] == "collection"], key=lambda r: r["case_id"])
        failures = [r for r in originals if r["error_kind"] == "value_failure"]
        successes = [r for r in originals if r["error_kind"] == "accepted"]
        selected = failures[:3] + successes[:2]
        if len(selected) < 5:
            seen = {r["case_id"] for r in selected}
            selected += [r for r in originals if r["case_id"] not in seen][:5 - len(selected)]
        by_case = {c["case_id"]: c for c in bundle["cases"]}
        for row in selected:
            case = by_case[row["case_id"]]
            trace = ns["high_calculation_trace"](case)
            text += [f"#### Measured original: {case['case_id']}\n",
                     "Selected from genuine original failures (up to three), then ordinary accepted originals (up to two), in stable ID order. "
                     "This selection illustrates boundaries; aggregate counts above describe frequency.\n",
                     "\x60\x60\x60text\n" + _high_source_excerpt(case, trace) + "\n\x60\x60\x60\n",
                     _high_table(ns, ["Field", "Expected", "Observed"], [[f, case["gold"][f], row["response"]["answer"].get(f)] for f in ns["HIGH_FIELDS"]]) if row["response"] else "No usable model answer was returned.",
                     f"\nChecker outcome: {row['error_kind']}. Request: [{row['request_key']}](data/high_v4/main/cache/{row['request_key']}.json).\n"]
            for intervention in bundle["interventions"]:
                if intervention["case_id"] == row["case_id"]:
                    text.append(f"{intervention['arm'].replace('_', ' ')} returned "
                                f"{json.dumps(intervention['response'].get('answer'), ensure_ascii=False) if intervention['response'] else 'no usable answer'}; "
                                f"outcome {intervention['error_kind']}.\n")
            text.append(ns["high_source_worked_example"](case, trace, heading="Source calculation for this measured case"))
        return "\n\n".join(text)
    if not report["usable_answers"]:
        return "\n".join(text) + "\nNo usable model answer has been saved. Source-audit examples below are not model outcomes.\n"
    available = sorted(report["usable_answers"], key=lambda r: (r["directory"], r["case_id"], r["request_key"]))
    shown = available
    if len(available) > 5:
        failures = [r for r in available if r["verification"] and r["verification"]["valid_schema"] and not r["verification"]["exact_fields"]]
        successes = [r for r in available if r["verification"] and r["verification"]["accepted"]]
        shown = failures[:3] + successes[:2]
        keys = {r["request_key"] for r in shown}
        shown += [r for r in available if r["request_key"] not in keys][:5 - len(shown)]
    text.append(f"Showing {len(shown)} of {len(available)} usable saved answers. When at most five exist, all are shown; otherwise examples use up to three genuine value failures and two ordinary accepted replies in stable order. "
                "Archived service-interrupted protocols are excluded from replacement difficulty selection. "
                "The examples cannot replace a completed paired comparison.\n")
    for row in shown:
        case = report["sources"].get(row["case_id"])
        if case is None:
            continue
        trace = ns["high_calculation_trace"](case)
        verification = row["verification"] or ns["high_validate_answer"](case, row["response"])
        archived = row["directory"] != "high_v4"
        scope = "archived service attempt" if archived else "current replacement protocol"
        text += [f"#### Saved model answer: {case['case_id']}\n",
                 f"This is an actual level-{case['level']} answer from {row['protocol']}, using model {row['model']} "
                 f"with reasoning effort {row['reasoning_effort']}, from the {scope}.\n",
                 "\x60\x60\x60text\n" + _high_source_excerpt(case, trace) + "\n\x60\x60\x60\n",
                 _high_table(ns, ["Field", "Expected from source", "Observed answer"], [[f, case["gold"][f], row["response"]["answer"].get(f)] for f in ns["HIGH_FIELDS"]]),
                 f"\nAll seven values correct: {verification['exact_fields']}; values and citations accepted: {verification['accepted']}. "
                 f"Source balance is {trace['ordered_units']:,} ordered - {trace['net_dispatched_units']:,} net dispatched "
                 f"= {trace['open_units']:,} open units. The exact final price is {trace['price']['unrounded_unit_cents']} cents, "
                 f"rounded half-up to {trace['price']['rounded_unit_cents']} cents. This field comparison "
                 "is one record's outcome; it says nothing about unsolved service-rejected packets.\n",
                 "Actual raw assistant response:\n\n\x60\x60\x60json\n" + row["raw_response"].strip() + "\n\x60\x60\x60\n",
                 f"Full source and exact request: [{row['request_key']}]({row['source_path']}).\n"]
    return "\n\n".join(text)


def high_render_extension(report, ns):
    cfg = (report.get("pilot_protocol") or {}).get("config", {})
    preflight = report.get("preflight")
    n_main = preflight["n_unique_main_sources"] if preflight else 0
    n_pilot = len({c["case_id"] for c in report["sources"].values() if c["split"] == "pilot"})
    title = "## " + HIGH_SECTION_TITLE
    if report["state"] == "complete":
        headline = f"The higher-reasoning follow-up completed {report['bundle']['metrics']['n_selected']} paired selected cases; see the separate v4 results."
    else:
        label = "service-blocked" if report["state"] == "service_blocked" else "incomplete"
        headline = (f"The higher-reasoning follow-up is {label}: {report['n_started_requests']} recorded requests yielded "
                    f"{report['status_counts']['usable_answer']} usable saved answers, so no repair-versus-retry conclusion is available.")
    intro = """A purchasing team often receives several exports for the same order. One contains the approved order quantity; another contains warehouse movements, including corrections and returns. The useful number is the amount still open on one purchase line. A repeated export row must not count twice, and a returned carton must use the packaging and line allocation that applied to its shipment.

The previous follow-up found three original Sol misses under low reasoning and recovered the same three with both a fresh retry and feedback repair. That leaves a practical uncertainty: would the repair package help beyond another attempt when the model has more reasoning effort and longer, realistic source histories?

This separate follow-up keeps the seven-field task but increases the source history and explicitly requests high reasoning. Its records are newly generated fictional purchasing packs. Exact ground truth is available from the generating events, and independent readers and calculations check the rendered documents before any model call. More rows do not guarantee errors, and a completed source audit is not model performance.
"""
    summary = ("### Question, planned comparison and current evidence\n\n" + headline + "\n\n"
        "The planned pilot visits up to four levels with eight cases each and 32, 64, 128 or 192 logical shipment IDs per source. "
        "It selects the first level with at least three usable, schema-valid wrong-value answers, or transparently records the maximum-level fallback if none crosses. "
        "The main plan starts with 160 fresh collection sources and adds a fixed 80-source expansion only if the first 160 yield fewer than 40 genuine value failures. "
        "A pre-outcome seeded ranking caps intervention selection at 80. Each selected case receives one fresh retry and one feedback repair, both one-case high-reasoning Sol calls. "
        "Another 24 source cases form a separate audit that cannot influence selection. These are planned sample sizes unless a complete main bundle is present.\n\n"
        "Primary success means a usable reply with valid schema and all seven field values correct. Full acceptance also needs sufficient evidence groups. "
        "For example, a correct quantity with missing ledger citations passes the value check but fails full acceptance. A service failure has no model answer and enters neither as an extraction error.\n\n")
    rules = """### Source rules and why the answer is determined

P01 identifies the order and target line, which can share its SKU with another line. P02 changes individual approved commercial fields. A line override beats an order default; within that scope, higher authority wins, then later effective time and higher revision. Both effective and recorded times must be available by the inclusive cutoff. A partial change leaves other fields intact.

P06 is an ingestion history. Select the highest available revision of each logical event before testing its state or occurrence. Exact ingestion copies count once. A selected VOID withdraws the event; a valid reversal removes its referenced shipment once. P03 and P04 supply dated packaging factors and allocation shares. A return uses its selected original shipment's date for both lookups, so today's packaging or allocation cannot silently change an old return.

Open units equal approved ordered demand minus net allocated dispatch. P05 tiers use ordered demand before shipments. Its gross price is per price pack, not per warehouse carton or individual unit. Divide by pricing pack size; apply two tier rebates in sequence; then add the unit fee and converted pack fee and subtract the unit credit. Retain exact precision until one final half-up rounding to integer cents. The orders in this follow-up remain active: a shipment withdrawal is not an order cancellation.

These rules resolve one intended answer per packet. Families share most rules and are scenario variants, not isolated causal ablations. Audit sources change heading format within the same semantics; they are not an unseen task-family holdout.
"""
    validation = (f"### Solvability checks before model calls\n\n"
        f"The saved preflight material contains {n_main:,} potential main packets across all four levels and {n_pilot:,} pilot packets. "
        "A text parser reconstructs every source fact, including obsolete rows and irrelevant accounts; reconstructed records must equal structured records exactly. "
        "A procedural Decimal calculation and a separate Fraction reducer agree on answers. A third implementation independently reads visible text, joins warehouse histories in SQL and prices in Decimal. "
        "A separate reader's Fraction parser audits the same packets. Saved source/instruction reviews check that the wording agrees with units and arithmetic, rather than trusting agreement between two copies of one mistaken rule.\n\n"
        "Checks cover unique current approvals, exact event/revision identities, valid references, complete dated UOM/allocation joins, 100% shares, integral individual-unit contributions, return bounds and nonnegative outputs. "
        "Seventeen fixture tests include hand-calculated controls, cutoff/revision boundaries, historical return lookups, exact half-cent rounding, source tampering and separate value/evidence checks. "
        "The five preflight examples below show the saved packets and computed expectations; they were not model predictions. "
        "Source/key consistency does not prove that every fictional rule matches real procurement practice.\n\n")
    if preflight:
        validation += "Saved audit summaries:\n\n" + _high_table(ns, ["Independent audit", "Saved result"], [[k, json.dumps(v, sort_keys=True)] for k, v in preflight["independent_checks"].items()]) + "\n\n"
    prompt = ("### Exact task instruction and call graph\n\n"
        "The following task instruction is shared across original, fresh-retry and repair calls. "
        "Each cached request also contains the complete rendered packet and the fixed response-format preamble. Models receive no gold, source_record, family, level or trace fields.\n\n"
        "\x60\x60\x60text\n" + ns["HIGH_TASK_INSTRUCTIONS"].strip() + "\n\x60\x60\x60\n\n" + _high_call_graph())
    examples = "\n\n".join(
        "\x60\x60\x60text\n" + _high_source_excerpt(case, ns["high_calculation_trace"](case)) + "\n\x60\x60\x60\n\n" +
        ns["high_source_worked_example"](case, heading=f"Preflight-only source audit {i}") +
        f"\nFull frozen source cohort: [level {case['level']} preflight packets](data/high_v4/preflight/potential_main_level_{case['level']}.jsonl.gz); find stable case ID {case['case_id']}.\n"
        for i, case in enumerate(ns["high_choose_source_examples"](report, 5), 1))
    figs = ("### Reading the planned ladder and observed service status\n\n"
        "The first chart describes the planned number of logical shipments in each source. The second counts raw CLI attempt statuses across preserved protocols. "
        "Read the second as service availability, not an accuracy denominator.\n\n"
        "![Planned source size across four levels](figures/high_v4/planned_ladder.png)\n\n"
        "Source histories grow from 32 to 192 logical shipments. Corrections, return/reversal records and distractor shipments add rows beyond those labels. "
        "The chart makes no claim that model error rates increase with level.\n\n"
        "![Raw service status, with usable answers separate from HTTP 429 and pending attempts](figures/high_v4/service_status.png)\n\n"
        f"Of {report['n_started_requests']} recorded attempts, {report['status_counts']['usable_answer']} have usable answers, "
        f"{report['status_counts']['http_429']} ended in HTTP 429, {report['status_counts']['other_terminal_failure']} have another terminal failure, "
        f"and {report['status_counts']['pending']} remain interrupted/pending. An unavailable answer is not a wrong numeric value. "
        "Concurrent and serial protocol attempts are preserved separately rather than silently mixing successful requests into a replacement ladder.\n\n")
    if report["state"] == "complete" and report["bundle"]["metrics"]["n_selected"]:
        figs += ("![Recovery on paired original failures](figures/high_v4/paired_recovery.png)\n\n"
                 "Both arms use the same selected original value failures. The bars count valid-schema answers with all values correct, while citations remain a separate reported outcome. "
                 "The paired result table below shows whether the methods recovered the same cases, which aggregate bars alone cannot reveal.\n\n")
    limits = """### What this can and cannot establish

The intended contrast is an old-answer-plus-failed-field repair package versus another fresh attempt on the same selected failure. The verifier has privileged knowledge of exact synthetic truth, but sends field names rather than expected values. Equal request counts do not equalize prompt length, reasoning tokens, latency or compute. Original failures are selected after a small pilot and share source templates, so results would be conditional on this difficulty-enriched sample.

No weights are trained or updated. Corrected responses would be candidate correction data, not evidence of training benefit. Clean generated tables omit OCR, missing contracts, malformed rows and real organizational disputes. All gold statuses are active. Source length and high reasoning are changed together relative to v3, so a cross-round difference could not isolate one cause.

In the blocked state, there is no measured repair advantage, no higher-level model error rate and no completed audit performance. The usable answers show only their own source reconciliations. A future live restart needs an explicitly versioned protocol and service review; ordinary notebook execution never retries failed or pending requests.
"""
    usage = report["recorded_usage"]
    cost = (f"### Requests, caches and reproduction\n\n"
        f"The raw read-only inventory contains {report['n_started_requests']} recorded subprocess attempts. Known cached usage is "
        f"{usage.get('input_tokens', 0):,} input tokens and {usage.get('output_tokens', 0):,} output tokens. "
        f"Reasoning-output tokens are recorded as a component ({usage.get('reasoning_output_tokens', 0):,}), not added again to output tokens. "
        f"Usage is present for {report['n_requests_with_usage']}/{report['n_started_requests']} requests and missing for {report['n_requests_missing_usage']}. "
        "Dollar spend is unavailable, not zero. Requests without terminal usage, including pending attempts and failed service requests, have unknown token/billing usage; recorded totals are incomplete whenever any request lacks usage.\n\n"
        "A cache is keyed by the full request, including model, explicit high effort, tool-disabled CLI profile, source, stage and feedback. "
        "The original service-interrupted attempt is under data/high_v4_service_attempt, the first serial replacement under data/high_v4_service_serial_attempt, and the final replacement under data/high_v4. "
        "Preflight compressed sources, hashes and independent audit results are under data/high_v4/preflight. "
        "These are preserved evidence, not replaceable failures. The v4b and v4c replacements use one worker and stop on the first transport failure; CLI-internal reconnects are not independently disabled or verified.\n\n"
        "Run the embedded read-only inspection below to regenerate status tables and figures. It reads even pending cache entries directly without calling high_run_pilot, "
        "high_collect_originals, high_run_interventions or high_call_model. The four core helpers are embedded for self-containment, followed by the presentation helper. "
        "Their presence does not enable an automatic live branch. Earlier notebook sections and cached findings remain separate.\n")
    text = "\n\n".join([title, intro, summary, _high_workflow(report), rules, validation, prompt, figs,
                         "### Recorded outcomes\n\n" + _high_outcomes(report, ns),
                         _high_observed_examples(report, ns),
                         "### Five preflight-only source calculations\n\n"
                         "These deterministic saved sources were chosen to cover scenario variants and all four lengths. "
                         "The input excerpts are literal source rows; all arithmetic uses the full packet, not only the excerpt. "
                         "They demonstrate solvability checks and do not substitute for five measured model cases.\n\n" + examples,
                         limits, cost])
    return text, headline


def _high_update_notebook(notebook, extension):
    result = copy.deepcopy(notebook)
    cells = result["cells"]
    if any("## " + HIGH_SECTION_TITLE in "".join(c.get("source", [])) for c in cells):
        raise ValueError("Section 13 already exists; refuse to overwrite it automatically")
    anchor = next(i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and
                  "## 13. Future work and further reading" in "".join(c["source"]))
    for cell in cells:
        if cell["cell_type"] != "markdown":
            continue
        source = "".join(cell["source"])
        source = source.replace("## 13. Future work and further reading", "## 14. Future work and further reading")
        source = source.replace("- [13. Future work and further reading](#13-future-work-and-further-reading)",
                                "- [" + HIGH_SECTION_TITLE + "](#13-larger-source-packs-and-higher-reasoning)\n"
                                "- [14. Future work and further reading](#14-future-work-and-further-reading)")
        cell["source"] = source.splitlines(keepends=True)
    additions = [_high_cell(extension)]
    for name in HIGH_CORE_HELPERS:
        additions += [_high_cell("### Embedded " + name.replace("_", " ").replace(".py", "") +
                                "\n\nThis frozen helper is included for reproduction; the reporting cell does not call its live collection functions."),
                      _high_cell((AUTHORING / name).read_text(encoding="utf-8-sig"), "code")]
    additions += [_high_cell("### Embedded offline reporting helper"),
                  _high_cell((AUTHORING / "high_reporting.py").read_text(encoding="utf-8-sig"), "code"),
                  _high_cell("### Inspect preserved artifacts without any model calls\n\n"
                             "This code handles incomplete and pending records by direct read-only inspection. It never resumes a cached request."),
                  _high_cell('''HIGH_REPORT_ROOT = Path.cwd()
HIGH_REPORT_OFFLINE = True
if not HIGH_REPORT_OFFLINE:
    raise RuntimeError("This reporting path is read-only; live collection needs a separately reviewed protocol.")
HIGH_REPORT = high_load_report(HIGH_REPORT_ROOT)
HIGH_REPORT_FIGURES = high_plot_report(HIGH_REPORT, root=HIGH_REPORT_ROOT, write=True)
print("State:", HIGH_REPORT["state"])
print("Service statuses:", HIGH_REPORT["status_counts"])
print("Known usage components:", HIGH_REPORT["recorded_usage"])
print("Usable saved answers are not an accuracy estimate for the interrupted pilot.")
print("Figures:", [row["path"] for row in HIGH_REPORT_FIGURES])
if HIGH_REPORT["state"] == "complete":
    print("Paired recovery:", HIGH_REPORT["bundle"]["metrics"]["paired_value_recovery"])
''', "code")]
    cells[anchor:anchor] = additions
    return result


def build(root=REPO_ROOT, write=False):
    """Return the proposed appendix/notebook; never write or call models by default."""
    root = Path(root)
    notebook_path = root / NOTEBOOK_REL
    notebook_dir = notebook_path.parent
    ns = _high_namespace()
    report = ns["high_load_report"](notebook_dir)
    extension, headline = high_render_extension(report, ns)
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    proposal = _high_update_notebook(notebook, extension)
    if write:
        ns["high_plot_report"](report, root=notebook_dir, write=True)
        notebook_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return {"notebook": notebook_path, "notebook_data": proposal, "extension": extension,
            "readme_appendix": extension, "headline": headline, "state": report["state"],
            "service_status": report["status_counts"], "recorded_requests": report["n_started_requests"],
            "preflight_example_case_ids": [c["case_id"] for c in ns["high_choose_source_examples"](report, 5)],
            "model_example_case_ids": [r["case_id"] for r in report["usable_answers"]],
            "written": write}


if __name__ == "__main__":
    raise SystemExit("Import build_high_extension.build; build() is read-only unless write=True is explicit.")

