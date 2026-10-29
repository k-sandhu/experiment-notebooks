"""Fresh procurement reconciliation fixtures; no imports from earlier rounds."""
import copy
import datetime as dt
import decimal
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from fractions import Fraction


HIGH_VERSION = "23-procurement-v4-high"
HIGH_FIELDS = ["order_id", "sku", "quantity_units", "unit_price_cents", "currency", "ship_date", "status"]
HIGH_FAMILIES = ["shipment_revisions", "dated_uom_returns", "split_allocations", "tier_sequential_pricing", "effective_authority", "compound"]
HIGH_CUTOFF = "2026-10-26T12:00:00Z"
HIGH_TASK_INSTRUCTIONS = """Reconcile the target ORDER and LINE as of the packet cutoff. Return exactly
{case_id, answer, evidence}; answer has exactly order_id (string), sku (string),
quantity_units (integer or null), unit_price_cents (integer or null), currency
(three-letter string or null), ship_date (YYYY-MM-DD or null), status
(active/cancelled/ambiguous). evidence has the same seven keys; each value is a
nonempty list of distinct document IDs P01 through P06. A batch wrapper may ask
for a results array.

Read all tables and use only the requested order/line. The same SKU can occur
on another line or order. quantity_units is OPEN individual units: current
approved ordered demand minus NET allocated dispatched units, where accepted
returns reduce net dispatch. This packet's order remains active; shipment VOID,
REVERSAL and RETURN do not cancel the purchase order.

Commercial terms: resolve every field independently. An approved row qualifies
only if BOTH recorded and effective UTC timestamps are at or before cutoff
(inclusive). Within a field: a line override beats an order default, then higher
authority wins (3 Controller, 2 Buyer, 1 Planner), then later effective timestamp,
then higher revision. Recorded timestamp filters availability only. INHERIT or
unstated fields do not clear old values. The signed order has authority 0 and
its issue timestamp. Other-line, unapproved, recorded-late and future-effective
rows do not apply. This packet has no unresolved equal-priority conflicts.

Physical movements: group by logical Event ID across ingestion copies. Select
the HIGHEST ROW REVISION among copies recorded by cutoff; exact same-revision
copies count once. That selected row wholly replaces prior rows. Only then test
its state, order and occurred timestamp. Selected VOID, another order and
occurred-after-cutoff rows contribute zero; never fall back to an older revision.
A POSTED, timely REVERSAL removes the referenced logical shipment, including its
selected correction, ONCE. Multiple active reversals of the same shipment do not
remove it twice. A VOID reversal has no effect. It is a control record, not a
second negative quantity. Returns against removed/VOID shipments contribute zero.

For an active SHIP, select the exact SKU/UOM factor with latest effective_from
date on or before the SELECTED shipment's occurred calendar date. Select the
allocation key's latest effective_from date on or before that SAME date. Multiply
shipment quantity by individual-units-per-UOM and the target line's percent/100.
An allocation entirely to another line contributes zero. All contributions are
whole individual units; do not round allocations. Allocation shares total 100%.
A RETURN is a positive accepted quantity in its ORIGINAL shipment handling units.
Use the referenced SELECTED shipment's SKU, UOM, occurred date and allocation key,
including that date's UOM and allocation versions, irrespective of return date.
Subtract its converted allocated units from net dispatch. Do not use the original
superseded row or the return date's new packaging/allocation schedule.

Pricing: use the resolved price plan and the highest tier minimum not exceeding
CURRENT ORDERED demand, BEFORE movements. gross_cents is for an entire price pack
of pack_units individual units, independent of warehouse UOM. Divide by pack_units;
apply tier rebate A then rebate B sequentially to that gross unit amount, using
basis points (100 bps = 1%). Then ADD fee_cents per individual unit and
pack_fee_cents/pack_units and SUBTRACT credit_cents per individual unit. These fees
and credits are after rebates. Keep exact rational/decimal precision and round
ONCE at the final per-unit result to the nearest integer cent, exact halves UP.
Never round a pack conversion, rebate or fractional-cent adjustment earlier.
Currency and requested ship date come from independently resolved commercial terms.

Evidence: sources are P01 signed order/defaults/status, P02 approvals, P03 UOM,
P04 dated allocations, P05 price schedules, P06 movement history. Cite sources
needed for current fields and arithmetic. Quantity requires current ordered
terms plus P03/P04/P06; P01 is also needed if its ordered demand remains current.
Price requires the resolved plan, ordered demand for its tier and P05. SKU and
active order status are in P01. Order ID is stated in the packet header and P01.
Relevant additional P01-P06 context is allowed without penalty; cite whole source
groups, not individual row IDs. Citation ordering is irrelevant. Do not omit
needed calculation sources merely because the numeric answer is correct.
"""



def _high_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _high_hash(value):
    return hashlib.sha256(_high_json(value).encode("utf-8")).hexdigest()


def _high_at_or_before(value, cutoff=HIGH_CUTOFF):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")) <= dt.datetime.fromisoformat(cutoff.replace("Z", "+00:00"))


def _high_amount(cents):
    return format(decimal.Decimal(str(cents)) / 100, "f")


def _high_terms_gold(record):
    """Procedural term application used by constructor gold only."""
    target = next(row for row in record["lines"] if row["line_id"] == record["target_line_id"])
    values, priorities = {}, {}
    for key, value in record["defaults"].items():
        values[key], priorities[key] = value, (0, 0, record["issued_at"], 0)
    for key, value in target.items():
        if key not in {"line_id", "sku"} and value is not None:
            values[key], priorities[key] = value, (1, 0, record["issued_at"], 0)
    for amendment in record["amendments"]:
        if not amendment["approved"] or not _high_at_or_before(amendment["recorded_at"], record["cutoff"]) or not _high_at_or_before(amendment["effective_at"], record["cutoff"]):
            continue
        if amendment["line_id"] not in {"ALL", record["target_line_id"]}:
            continue
        priority = (int(amendment["line_id"] != "ALL"), amendment["authority"], amendment["effective_at"], amendment["revision"])
        for field, value in amendment["changes"].items():
            if value is not None and priority > priorities.get(field, (-1, -1, "", -1)):
                values[field], priorities[field] = value, priority
    return values, target["sku"]


def _high_build(rng, family, seed, level, split, index):
    order = f"PO-{rng.randrange(200000, 899999)}"
    other = f"PO-{int(order[3:]) + 11}"
    sku = f"{rng.choice(['VAL', 'GSK', 'CLP', 'RIV'])}-{rng.randrange(100, 999)}"
    target_line = rng.choice(["L02", "L03", "L04"])
    same_line = "L07"
    ordered = 60000 + level * 16000 + rng.randrange(100, 900)
    lines = []
    for i in range(1, 9):
        line = f"L{i:02d}"
        lines.append({"line_id": line, "sku": sku if line in {target_line, same_line} else f"{sku}-{i}",
                      "ordered_units": ordered if line == target_line else rng.randrange(2000, 9000),
                      "price_plan": None, "ship_date": None, "currency": None})
    defaults = {"currency": rng.choice(["CAD", "USD", "EUR"]), "ship_date": "2026-11-09", "price_plan": "PLAN-A"}
    amendments = []

    def approval(name, scope, authority, revision, effective, recorded, changes, approved=True):
        amendments.append({"approval_id": name, "line_id": scope, "authority": authority, "revision": revision,
                           "effective_at": effective, "recorded_at": recorded, "changes": changes, "approved": approved})

    approval("AP-01", "ALL", 3, 7, "2026-10-20T09:00:00Z", "2026-10-20T09:20:00Z", {"ship_date": "2026-11-14", "price_plan": "PLAN-B"})
    approval("AP-02", target_line, 2, 2, "2026-10-18T08:00:00Z", "2026-10-18T09:00:00Z", {"price_plan": "PLAN-C", "ship_date": "2026-11-12"})
    approval("AP-03", target_line, 2, 4, "2026-10-21T10:00:00Z", "2026-10-22T09:00:00Z", {"ordered_units": ordered + 2100})
    approval("AP-04", target_line, 1, 99, "2026-10-23T10:00:00Z", "2026-10-23T10:30:00Z", {"ordered_units": ordered + 6000, "ship_date": "2026-11-20"})
    approval("AP-05", target_line, 3, 9, "2026-10-23T11:00:00Z", "2026-10-26T12:30:00Z", {"price_plan": "PLAN-A", "ordered_units": ordered + 7000})
    approval("AP-06", target_line, 3, 10, "2026-10-26T13:00:00Z", "2026-10-26T11:00:00Z", {"ordered_units": ordered + 8000})
    approval("AP-07", same_line, 3, 12, "2026-10-22T10:00:00Z", "2026-10-22T11:00:00Z", {"ordered_units": 39000, "price_plan": "PLAN-A"})
    approval("AP-08", target_line, 3, 11, "2026-10-23T12:00:00Z", "2026-10-23T12:10:00Z", {"price_plan": "PLAN-B"}, False)
    if family in {"effective_authority", "compound"} or level >= 2:
        approval("AP-09", target_line, 2, 5, "2026-10-21T10:00:00Z", "2026-10-23T09:00:00Z", {"ordered_units": ordered + 2450})
        approval("AP-10", target_line, 2, 1, "2026-10-22T10:00:00Z", "2026-10-23T09:10:00Z", {"ship_date": "2026-11-13"})
    if family in {"split_allocations", "compound"}:
        approval("AP-11", target_line, 2, 6, "2026-10-22T11:00:00Z", "2026-10-22T11:30:00Z", {"price_plan": "PLAN-B"})
    rng.shuffle(amendments)
    uom = []
    skus = sorted({row["sku"] for row in lines})
    old_box, new_box = rng.choice([(12, 10), (8, 12), (20, 16)])
    for item in skus:
        uom += [{"sku": item, "uom": "EA", "effective_from": "2026-01-01", "units": 1},
                {"sku": item, "uom": "BOX", "effective_from": "2026-01-01", "units": old_box},
                {"sku": item, "uom": "BOX", "effective_from": "2026-10-20", "units": new_box},
                {"sku": item, "uom": "CASE", "effective_from": "2026-01-01", "units": 24},
                {"sku": item, "uom": "CASE", "effective_from": "2026-10-21", "units": 30}]
    allocations = {"AL-1": {target_line: 25, same_line: 75}, "AL-2": {target_line: 75, same_line: 25},
                   "AL-3": {target_line: 50, same_line: 50}, "AL-4": {same_line: 100}}
    plans = {}
    for j, name in enumerate(["PLAN-A", "PLAN-B", "PLAN-C"]):
        base = rng.randrange(350, 1850) + j * 17
        plans[name] = {"tiers": [{"minimum": minimum, "gross_cents": base - offset} for minimum, offset in [(0, 0), (76000, 31), (94000, 67), (110000, 103)]],
                       "rebate_a_bps": rng.choice([500, 750, 1250]), "rebate_b_bps": rng.choice([250, 500, 1250]),
                       "fee_cents": rng.choice(["2.75", "3.25", "4.50"]), "credit_cents": rng.choice(["0.75", "1.25", "2.50"])}
    ledger = []
    n_shipments = {1: 32, 2: 64, 3: 128, 4: 192}[level]
    for i in range(1, n_shipments + 1):
        date = "2026-10-18" if i % 3 == 1 else ("2026-10-22" if i % 3 == 2 else "2026-10-23")
        ledger.append({"event_id": f"SH-{i:02d}", "row_revision": 1, "kind": "SHIP", "order_id": order,
                       "sku": sku, "quantity": rng.randrange(2, 7) * 4, "uom": ["BOX", "CASE", "EA"][i % 3],
                       "allocation": f"AL-{1 + (i % (4 if family in {'split_allocations', 'compound'} else 3))}",
                       "reference": "-", "occurred_at": date + "T10:00:00Z", "recorded_at": date + "T11:00:00Z", "state": "POSTED"})
    originals = {row["event_id"]: copy.deepcopy(row) for row in ledger}
    # Latest correction replaces rather than adds; exact overlap copies deduplicate.
    corrected = dict(originals["SH-01"], row_revision=2, quantity=originals["SH-01"]["quantity"] + 8, recorded_at="2026-10-26T10:00:00Z")
    ledger += [corrected, copy.deepcopy(originals["SH-02"])]
    ledger.append(dict(originals["SH-06"], row_revision=2, state="VOID", recorded_at="2026-10-26T10:10:00Z"))
    ledger.append(dict(originals["SH-07"], row_revision=3, quantity=80, recorded_at="2026-10-26T12:20:00Z"))
    ledger.append(dict(originals["SH-08"], row_revision=2, occurred_at="2026-10-26T13:00:00Z", recorded_at="2026-10-26T11:30:00Z"))
    ledger.append({"event_id": "RV-01", "row_revision": 1, "kind": "REVERSAL", "order_id": order, "sku": sku,
                   "quantity": 0, "uom": "-", "allocation": "-", "reference": "SH-03", "occurred_at": "2026-10-26T09:00:00Z", "recorded_at": "2026-10-26T09:10:00Z", "state": "POSTED"})
    for j, ref in enumerate(["SH-04", "SH-01"] + (["SH-10"] if level >= 2 else []), 1):
        ledger.append({"event_id": f"RT-{j:02d}", "row_revision": 1, "kind": "RETURN", "order_id": order, "sku": sku,
                       "quantity": 4, "uom": "ORIGINAL", "allocation": "ORIGINAL", "reference": ref,
                       "occurred_at": "2026-10-26T10:15:00Z", "recorded_at": "2026-10-26T10:20:00Z", "state": "POSTED"})
    if level >= 2 or family in {"shipment_revisions", "compound"}:
        rev = {"event_id": "RV-02", "row_revision": 1, "kind": "REVERSAL", "order_id": order, "sku": sku, "quantity": 0,
               "uom": "-", "allocation": "-", "reference": "SH-05", "occurred_at": "2026-10-26T09:00:00Z", "recorded_at": "2026-10-26T09:10:00Z", "state": "POSTED"}
        ledger += [rev, dict(rev, row_revision=2, state="VOID", recorded_at="2026-10-26T11:00:00Z")]
    if family in {"shipment_revisions", "compound"}:
        ledger.append(dict(corrected, row_revision=3, quantity=corrected["quantity"] + 4, recorded_at="2026-10-26T11:20:00Z"))
        ledger.append(copy.deepcopy(corrected))
    for j in range(4 + level):
        ledger.append({"event_id": f"OT-{j:02d}", "row_revision": 1, "kind": "SHIP", "order_id": other if j % 2 else order,
                       "sku": sku, "quantity": 16 + 4 * j, "uom": "BOX", "allocation": "AL-4", "reference": "-",
                       "occurred_at": "2026-10-22T08:00:00Z", "recorded_at": "2026-10-22T09:00:00Z", "state": "POSTED"})
    rng.shuffle(ledger)
    record = {"version": HIGH_VERSION, "target_order_id": order, "other_order_id": other, "target_line_id": target_line,
              "target_sku": sku, "issued_at": "2026-10-15T08:00:00Z", "cutoff": HIGH_CUTOFF,
              "defaults": defaults, "lines": lines, "amendments": amendments, "uom": uom,
              "allocations": allocations, "plans": plans, "ledger": ledger}
    _high_enrich(record, rng, level, family)
    case_id = "account-" + _high_hash({"seed": seed, "level": level, "split": split, "index": index, "facts": record})[:20]
    record["case_id"] = case_id
    gold = _high_gold(record)
    reference, needs, trace = _high_reduce(record)
    assert gold == reference, (gold, reference)
    case = {"case_id": case_id, "family": family, "level": level, "round": level, "arm": "high-reasoning", "split": split,
            "created_at": "2026-10-26", "gold": gold, "evidence_gold": needs, "source_record": record,
            "template_group": f"v4-{'archive' if split == 'audit' else 'register'}-{family}"}
    case["document"] = _high_render(record, split == "audit")
    case["content_hash"] = hashlib.sha256(case["document"].encode("utf-8")).hexdigest()
    case["semantic_hash"] = _high_semantic(record)
    return case


def _high_semantic(record):
    def normalize(value):
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items() if key != "case_id"}
        if isinstance(value, list):
            normalized = [normalize(item) for item in value]
            return [json.loads(item) for item in sorted({_high_json(item) for item in normalized})]
        return value
    return _high_hash(normalize(record))


def high_make_cases(n, seed, level=1, split="pilot", start_index=0):
    if type(n) is not int or n < 0 or level not in {1, 2, 3, 4} or type(level) is not int:
        raise ValueError("n must be nonnegative and level must be 1, 2, 3 or 4")
    if split not in {"pilot", "collection", "audit"}:
        raise ValueError("Unknown split")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be a nonnegative integer")
    rng = random.Random(seed)
    families = [HIGH_FAMILIES[i % len(HIGH_FAMILIES)] for i in range(n)]
    rng.shuffle(families)
    return [_high_build(rng, family, seed, level, split, start_index + i) for i, family in enumerate(families)]


def high_correct_response(case):
    return {"case_id": case["case_id"], "answer": copy.deepcopy(case["gold"]), "evidence": copy.deepcopy(case["evidence_gold"])}


def _high_type(field, value):
    if field in {"quantity_units", "unit_price_cents"}:
        return value is None or (type(value) is int and value >= 0)
    if field in {"order_id", "sku"}:
        return type(value) is str and bool(value)
    if field == "currency":
        return value is None or (type(value) is str and re.fullmatch(r"[A-Z]{3}", value) is not None)
    if field == "ship_date":
        if value is None:
            return True
        try:
            return type(value) is str and dt.date.fromisoformat(value).isoformat() == value
        except ValueError:
            return False
    return value in {"active", "cancelled", "ambiguous"} if type(value) is str else False


def high_validate_answer(case, response):
    obj = response if type(response) is dict else {}
    schema = type(response) is dict and set(response) == {"case_id", "answer", "evidence"} and obj.get("case_id") == case["case_id"]
    reasons, categories = [], []
    if not schema:
        reasons.append("Invalid top-level schema or case ID")
    answer, evidence = obj.get("answer", {}), obj.get("evidence", {})
    if type(answer) is not dict or set(answer) != set(HIGH_FIELDS):
        schema = False
        answer = answer if type(answer) is dict else {}
        reasons.append("Answer must contain exactly seven fields")
    if type(evidence) is not dict or set(evidence) != set(HIGH_FIELDS):
        schema = False
        evidence = evidence if type(evidence) is dict else {}
        reasons.append("Evidence must contain exactly seven field lists")
    _, needs, _ = _high_reduce(case["source_record"])
    fields, citations = {}, {}
    for field in HIGH_FIELDS:
        typed = field in answer and _high_type(field, answer[field])
        if not typed:
            schema = False
            reasons.append(f"Invalid type or missing field: {field}")
            categories.append({"field": field, "category": "schema"})
        fields[field] = bool(typed and answer[field] == case["gold"][field])
        if typed and not fields[field]:
            reasons.append(f"Wrong value: {field}")
            categories.append({"field": field, "category": "value"})
        cited = evidence.get(field)
        citation_schema = type(cited) is list and bool(cited) and all(type(item) is str for item in cited) and len(cited) == len(set(cited))
        if not citation_schema:
            schema = False
            citations[field] = False
            reasons.append(f"Invalid evidence list: {field}")
            categories.append({"field": field, "category": "evidence_schema"})
        else:
            sufficient = bool(set(cited) & {"P01", "P02", "P04", "P06"}) if field == "order_id" else set(needs[field]) <= set(cited)
            citations[field] = sufficient and set(cited) <= {"P01", "P02", "P03", "P04", "P05", "P06"}
            if not citations[field]:
                reasons.append(f"Insufficient current support or unrelated evidence: {field}")
                categories.append({"field": field, "category": "evidence"})
    exact = all(fields.values())
    return {"valid_schema": schema, "field_correct": fields, "evidence_correct": citations, "exact_fields": exact,
            "accepted": schema and exact and all(citations.values()), "reasons": reasons, "reason_categories": categories,
            "has_value_error": any(item["category"] == "value" for item in categories),
            "evidence_only_failure": schema and exact and not all(citations.values())}


def high_make_verifier_controls(cases):
    controls = []
    for case in cases:
        correct = high_correct_response(case)
        variants = [("correct", correct, True)]
        for field in ["quantity_units", "unit_price_cents"]:
            bad = copy.deepcopy(correct)
            bad["answer"][field] += 1
            variants.append(("wrong_" + field, bad, False))
        bad = copy.deepcopy(correct)
        bad["answer"]["quantity_units"] = True
        variants.append(("boolean_integer", bad, False))
        bad = copy.deepcopy(correct)
        bad["evidence"]["quantity_units"] = ["P01"]
        variants.append(("missing_ledger_support", bad, False))
        bad = copy.deepcopy(correct)
        bad["extra"] = "not allowed"
        variants.append(("extra_key", bad, False))
        for label, response, expected in variants:
            controls.append({"case_id": case["case_id"], "control_type": label, "response": response,
                             "expected_accepted": expected, "is_model_result": False})
    return controls


def _high_enrich(record, rng, level, family):
    """Controlled warehouse lifecycle variations, not arbitrary row noise."""
    target = record["target_line_id"]
    allocations = []
    for key, old in record["allocations"].items():
        share = {"AL-1": 50, "AL-2": 25, "AL-3": 75, "AL-4": 0}[key]
        new = {target: share, "L07": 100 - share} if share else {"L07": 100}
        allocations.extend([{"key": key, "effective_from": "2026-01-01", "shares": old},
                            {"key": key, "effective_from": "2026-10-21", "shares": new}])
    record["allocations"] = allocations
    # The base shipment IDs are the ladder's logical movement count.
    base = {row["event_id"]: copy.deepcopy(row) for row in record["ledger"]
            if row["kind"] == "SHIP" and row["event_id"].startswith("SH-") and row["row_revision"] == 1}
    for i, (eid, original) in enumerate(sorted(base.items()), 1):
        if i % 7 == 0:
            record["ledger"].append(dict(original, row_revision=2, quantity=original["quantity"] + 8,
                                          allocation="AL-2", occurred_at="2026-10-22T10:00:00Z",
                                          recorded_at="2026-10-25T10:00:00Z"))
        if i % 11 == 0:
            record["ledger"].append(dict(original, row_revision=4, state="VOID", recorded_at="2026-10-25T10:15:00Z"))
            if i % 22 == 0:
                record["ledger"].append(dict(original, row_revision=5, quantity=original["quantity"] + 4,
                                              recorded_at="2026-10-26T09:00:00Z"))
        if i % 13 == 0:
            rv = dict(original, event_id="RX-" + eid[3:], kind="REVERSAL", reference=eid,
                      quantity=0, uom="-", allocation="-", occurred_at="2026-10-25T09:00:00Z",
                      recorded_at="2026-10-25T09:30:00Z")
            record["ledger"].append(rv)
            if i % 26 == 0:
                record["ledger"].append(dict(rv, row_revision=2, state="VOID", recorded_at="2026-10-26T09:15:00Z"))
        if i % 9 == 0:
            rt = dict(original, event_id="RB-" + eid[3:], kind="RETURN", reference=eid,
                      quantity=4, uom="ORIGINAL", allocation="ORIGINAL",
                      occurred_at="2026-10-25T11:00:00Z", recorded_at="2026-10-25T11:30:00Z")
            record["ledger"].append(rt)
            if i % 18 == 0:
                record["ledger"].append(dict(rt, row_revision=2, quantity=8, recorded_at="2026-10-26T10:00:00Z"))
        if i % 5 == 0:
            record["ledger"].append(copy.deepcopy(original))
        if i % 17 == 0:
            record["ledger"].append(dict(original, row_revision=9, quantity=original["quantity"] + 100,
                                          recorded_at="2026-10-26T12:01:00Z"))
    # Every scenario has changing price-pack bases and tier-specific sequential rebates.
    for j, (name, plan) in enumerate(sorted(record["plans"].items())):
        plan["pack_units"] = [12, 24, 10][j]
        plan["pack_fee_cents"] = ["7.50", "12.25", "9.75"][j]
        for t, tier in enumerate(plan["tiers"]):
            tier["gross_cents"] *= plan["pack_units"]
            tier["rebate_a_bps"] = plan["rebate_a_bps"] + t * 25
            tier["rebate_b_bps"] = plan["rebate_b_bps"] + (t % 2) * 50
        del plan["rebate_a_bps"], plan["rebate_b_bps"]
    # Carry forward the named scenario while changing all sources freshly.
    if family in {"dated_uom_returns", "compound"}:
        record["uom"].append({"sku": record["target_sku"], "uom": "CASE",
                              "effective_from": "2026-10-23", "units": 36})
    if family in {"effective_authority", "compound"}:
        record["amendments"].append({
            "approval_id": "AP-12", "line_id": target, "authority": 3, "revision": 1,
            "effective_at": "2026-10-22T12:00:00Z", "recorded_at": "2026-10-25T08:00:00Z",
            "approved": True, "changes": {"ordered_units": next(r["ordered_units"] for r in record["lines"] if r["line_id"] == target) + 3200}
        })
    rng.shuffle(record["ledger"])


# All record fields are represented below. The parser does not consult source_record.
_HIGH_SCHEMAS = {
    "P01": ["line_id", "sku", "ordered_units", "price_plan", "ship_date", "currency"],
    "P02": ["approval_id", "line_id", "authority", "revision", "effective_at", "recorded_at", "approved",
            "ordered_units", "price_plan", "ship_date", "currency"],
    "P03": ["sku", "uom", "effective_from", "units"],
    "P04": ["key", "effective_from", "line_id", "share"],
    "P05": ["plan", "pack_units", "minimum", "gross_cents", "rebate_a_bps", "rebate_b_bps",
            "fee_cents", "credit_cents", "pack_fee_cents"],
    "P06": ["event_id", "row_revision", "kind", "order_id", "sku", "quantity", "uom", "allocation",
            "reference", "occurred_at", "recorded_at", "state"],
}
_HIGH_TABLE_MEMOS = {
    "P01": ("Signed purchase order", "Each line is a separate demand account. L07 may have the same SKU as the target; its demand remains separate. INHERIT cells retain order defaults. Status active; no order cancellation notice is in this packet."),
    "P02": ("Commercial approval register", "APPROVED rows amend only their populated fields. A line override outranks order defaults. Within that scope authority 3 outranks 2 outranks 1, then effective timestamp, then revision. Recorded timestamp is availability only."),
    "P03": ("Effective-dated item handling master", "Units are individual units per handling unit. Use the selected shipment's occurred calendar date. Returns inherit their original selected shipment's date, SKU and UOM."),
    "P04": ("Effective-dated allocation schedule", "Select the latest effective-from date on or before shipment occurrence for its allocation key. Each dated key totals 100 percent across lines. A return inherits this original allocation version."),
    "P05": ("Approved price schedule", "gross_cents is the total gross price in cents per price pack, containing pack_units individual units. Tier minimum is current ordered individual units before shipments. Apply the tier's two rebates sequentially to gross/pack_units, then add fee_cents and pack_fee_cents/pack_units and subtract credit_cents. These adjustments are after rebates. Round only the final unit price half-up to an integer cent."),
    "P06": ("Warehouse movement revision register", "Event ID is logical identity; ingestion copies are not additive. Select maximum row revision recorded by cutoff before testing occurrence/state. A selected VOID withdraws that event. Active reversals remove their referenced logical shipment once; a VOID reversal has no effect. Returns are positive magnitudes in ORIGINAL handling units and reopen demand. A reversal is not an order cancellation."),
}


def _high_render(record, audit=False):
    output = [
        "Fictional supplier reconciliation packet",
        "Case-ID: " + record["case_id"],
        "Format-version: " + record["version"],
        "Target-order: " + record["target_order_id"],
        "Target-line: " + record["target_line_id"],
        "Target-SKU: " + record["target_sku"],
        "Other-order: " + record["other_order_id"],
        "Issued-UTC: " + record["issued_at"],
        "Cutoff-UTC: " + record["cutoff"],
        "Default-currency: " + record["defaults"]["currency"],
        "Default-ship-date: " + record["defaults"]["ship_date"],
        "Default-price-plan: " + record["defaults"]["price_plan"],
        "Prepared by a fictional purchasing operations team. All times UTC. This extract includes archival and planning rows for account reconciliation.",
    ]
    tables = {"P01": record["lines"], "P02": [], "P03": record["uom"], "P04": [], "P05": [], "P06": record["ledger"]}
    for row in record["amendments"]:
        flat = {k: v for k, v in row.items() if k != "changes"}
        flat.update(row["changes"])
        tables["P02"].append(flat)
    for row in record["allocations"]:
        for line, share in sorted(row["shares"].items()):
            tables["P04"].append({"key": row["key"], "effective_from": row["effective_from"], "line_id": line, "share": share})
    for name, plan in sorted(record["plans"].items()):
        for tier in plan["tiers"]:
            tables["P05"].append(dict(tier, plan=name, **{k: v for k, v in plan.items() if k != "tiers"}))
    for doc, schema in _HIGH_SCHEMAS.items():
        title, memo = _HIGH_TABLE_MEMOS[doc]
        output.extend(["", (f"Document-ID: {doc} | Archive table: {title}" if audit else f"[{doc}] {title}"), memo, "BEGIN TABLE " + doc])
        output.append(" | ".join(schema))
        for row in tables[doc]:
            values = []
            for key in schema:
                value = row.get(key)
                values.append("INHERIT" if value is None else ("YES" if value is True else "NO" if value is False else str(value)))
            output.append(" | ".join(values))
        output.append("END TABLE " + doc)
    return "\n".join(output) + "\n"


def high_parse_document(document):
    """Reconstruct the complete source record using only the visible packet."""
    if type(document) is not str or "\r" in document:
        raise ValueError("Expected LF-only text packet")
    lines = document.splitlines()
    labels = {
        "Case-ID": "case_id", "Format-version": "version", "Target-order": "target_order_id",
        "Target-line": "target_line_id", "Target-SKU": "target_sku", "Other-order": "other_order_id",
        "Issued-UTC": "issued_at", "Cutoff-UTC": "cutoff",
    }
    record, defaults, tables = {}, {}, {}
    for label, key in labels.items():
        values = [line[len(label) + 2:] for line in lines if line.startswith(label + ": ")]
        if len(values) != 1 or not values[0]:
            raise ValueError("Missing or repeated header: " + label)
        record[key] = values[0]
    for label, key in [("Default-currency", "currency"), ("Default-ship-date", "ship_date"), ("Default-price-plan", "price_plan")]:
        values = [line[len(label) + 2:] for line in lines if line.startswith(label + ": ")]
        if len(values) != 1:
            raise ValueError("Missing or repeated default: " + label)
        defaults[key] = values[0]
    integer_columns = {"ordered_units", "authority", "revision", "units", "share", "pack_units", "minimum",
                       "gross_cents", "rebate_a_bps", "rebate_b_bps", "row_revision", "quantity"}
    for doc, schema in _HIGH_SCHEMAS.items():
        begin, end = "BEGIN TABLE " + doc, "END TABLE " + doc
        if lines.count(begin) != 1 or lines.count(end) != 1:
            raise ValueError("Missing or repeated table markers: " + doc)
        a, b = lines.index(begin), lines.index(end)
        if b <= a + 1 or lines[a + 1].split(" | ") != schema:
            raise ValueError("Invalid table header: " + doc)
        rows = []
        for line in lines[a + 2:b]:
            cells = line.split(" | ")
            if len(cells) != len(schema):
                raise ValueError("Incomplete table row: " + doc)
            row = {}
            for key, value in zip(schema, cells):
                if value == "INHERIT":
                    row[key] = None
                elif key in integer_columns:
                    if not re.fullmatch(r"\d+", value):
                        raise ValueError("Invalid integer cell: " + key)
                    row[key] = int(value)
                elif key == "approved":
                    if value not in {"YES", "NO"}:
                        raise ValueError("Invalid approval cell")
                    row[key] = value == "YES"
                else:
                    row[key] = value
            rows.append(row)
        if not rows:
            raise ValueError("Empty source table: " + doc)
        tables[doc] = rows
    record["defaults"], record["lines"], record["uom"], record["ledger"] = defaults, tables["P01"], tables["P03"], tables["P06"]
    record["amendments"] = []
    for row in tables["P02"]:
        changes = {k: row[k] for k in ["ordered_units", "price_plan", "ship_date", "currency"] if row[k] is not None}
        record["amendments"].append({**{k: row[k] for k in _HIGH_SCHEMAS["P02"][:7]}, "changes": changes})
    groups = {}
    for row in tables["P04"]:
        key = row["key"], row["effective_from"]
        item = groups.setdefault(key, {"key": key[0], "effective_from": key[1], "shares": {}})
        if row["line_id"] in item["shares"]:
            raise ValueError("Repeated allocation line")
        item["shares"][row["line_id"]] = row["share"]
    record["allocations"] = list(groups.values())
    record["plans"] = {}
    for row in tables["P05"]:
        attrs = {k: row[k] for k in ["pack_units", "fee_cents", "credit_cents", "pack_fee_cents"]}
        plan = record["plans"].setdefault(row["plan"], dict(attrs, tiers=[]))
        if any(plan[k] != v for k, v in attrs.items()):
            raise ValueError("Inconsistent plan adjustments")
        plan["tiers"].append({k: row[k] for k in ["minimum", "gross_cents", "rebate_a_bps", "rebate_b_bps"]})
    return record


def _high_gold(record):
    """Procedural constructor calculation: Decimal with a direct latest-row map."""
    terms, sku = _high_terms_gold(record)
    latest = {}
    for row in record["ledger"]:
        if _high_at_or_before(row["recorded_at"], record["cutoff"]):
            if row["event_id"] not in latest or row["row_revision"] > latest[row["event_id"]]["row_revision"]:
                latest[row["event_id"]] = row
    eligible = {k: r for k, r in latest.items() if r["state"] == "POSTED"
                and r["order_id"] == record["target_order_id"] and _high_at_or_before(r["occurred_at"], record["cutoff"])}
    removed = {r["reference"] for r in eligible.values() if r["kind"] == "REVERSAL"}
    ships = {k: r for k, r in eligible.items() if r["kind"] == "SHIP" and k not in removed}

    def amount(qty, ship):
        rate = max((r for r in record["uom"] if r["sku"] == ship["sku"] and r["uom"] == ship["uom"] and r["effective_from"] <= ship["occurred_at"][:10]), key=lambda r: r["effective_from"])["units"]
        alloc = max((r for r in record["allocations"] if r["key"] == ship["allocation"] and r["effective_from"] <= ship["occurred_at"][:10]), key=lambda r: r["effective_from"])["shares"].get(record["target_line_id"], 0)
        return decimal.Decimal(qty) * rate * alloc / 100

    net = sum((amount(r["quantity"], r) for r in ships.values()), decimal.Decimal(0))
    net -= sum((amount(r["quantity"], ships[r["reference"]]) for r in eligible.values() if r["kind"] == "RETURN" and r["reference"] in ships), decimal.Decimal(0))
    assert net == int(net)
    plan = record["plans"][terms["price_plan"]]
    tier = max((t for t in plan["tiers"] if t["minimum"] <= terms["ordered_units"]), key=lambda t: t["minimum"])
    with decimal.localcontext() as ctx:
        ctx.prec = 70
        price = decimal.Decimal(tier["gross_cents"]) / plan["pack_units"]
        price *= decimal.Decimal(10000 - tier["rebate_a_bps"]) / 10000
        price *= decimal.Decimal(10000 - tier["rebate_b_bps"]) / 10000
        price += decimal.Decimal(plan["fee_cents"]) + decimal.Decimal(plan["pack_fee_cents"]) / plan["pack_units"] - decimal.Decimal(plan["credit_cents"])
        cents = int(price.quantize(decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP))
    return {"order_id": record["target_order_id"], "sku": sku, "quantity_units": terms["ordered_units"] - int(net),
            "unit_price_cents": cents, "currency": terms["currency"], "ship_date": terms["ship_date"], "status": "active"}


def _high_reduce(record):
    """Independent grouped Fraction reducer; returns exact, JSON-safe audit traces."""
    target_rows = [r for r in record["lines"] if r["line_id"] == record["target_line_id"]]
    if len(target_rows) != 1:
        raise ValueError("Target line must be unique")
    target = target_rows[0]
    candidates = defaultdict(list)
    for key, value in record["defaults"].items():
        candidates[key].append(((0, 0, record["issued_at"], 0), value, "P01", "ORDER"))
    for key in ["ordered_units", "price_plan", "ship_date", "currency"]:
        if target.get(key) is not None:
            candidates[key].append(((1, 0, record["issued_at"], 0), target[key], "P01", target["line_id"]))
    for row in record["amendments"]:
        if row["approved"] and row["line_id"] in {"ALL", target["line_id"]} and max(row["effective_at"], row["recorded_at"]) <= record["cutoff"]:
            priority = (row["line_id"] != "ALL", row["authority"], row["effective_at"], row["revision"])
            for field, value in row["changes"].items():
                if value is not None:
                    candidates[field].append((priority, value, "P02", row["approval_id"]))
    winners = {}
    for key, options in candidates.items():
        maximum = max(r[0] for r in options)
        finalists = [r for r in options if r[0] == maximum]
        if len({_high_json(r[1]) for r in finalists}) != 1:
            raise ValueError("Nonunique commercial winner: " + key)
        winners[key] = finalists[0]
    terms = {k: r[1] for k, r in winners.items()}
    groups = defaultdict(list)
    for row in record["ledger"]:
        if row["recorded_at"] <= record["cutoff"]:
            groups[row["event_id"]].append(row)
    selected = {}
    for eid, rows in groups.items():
        revision = max(r["row_revision"] for r in rows)
        choices = {_high_json(r): r for r in rows if r["row_revision"] == revision}
        if len(choices) != 1:
            raise ValueError("Conflicting physical row revision: " + eid)
        selected[eid] = next(iter(choices.values()))
    posted = {eid: r for eid, r in selected.items() if r["state"] == "POSTED" and r["occurred_at"] <= record["cutoff"] and r["order_id"] == record["target_order_id"]}
    removed = {r["reference"] for r in posted.values() if r["kind"] == "REVERSAL"}
    shipments = {eid: r for eid, r in posted.items() if r["kind"] == "SHIP" and eid not in removed}

    def contribution(qty, ship):
        rate_rows = [r for r in record["uom"] if (r["sku"], r["uom"]) == (ship["sku"], ship["uom"]) and r["effective_from"] <= ship["occurred_at"][:10]]
        if not rate_rows:
            raise ValueError("Missing UOM rate")
        rate = sorted(rate_rows, key=lambda r: r["effective_from"])[-1]
        alloc_rows = [r for r in record["allocations"] if r["key"] == ship["allocation"] and r["effective_from"] <= ship["occurred_at"][:10]]
        if not alloc_rows:
            raise ValueError("Missing allocation version")
        alloc = sorted(alloc_rows, key=lambda r: r["effective_from"])[-1]
        share = alloc["shares"].get(target["line_id"], 0)
        amount = Fraction(qty * rate["units"] * share, 100)
        if amount.denominator != 1:
            raise ValueError("Nonintegral individual-unit contribution")
        return amount, {"uom_effective_from": rate["effective_from"], "units_per_uom": rate["units"],
                        "allocation_effective_from": alloc["effective_from"], "target_share_percent": share}

    traces = []
    for eid, row in sorted(selected.items()):
        units, details, why = Fraction(0), {}, "excluded"
        if row["order_id"] != record["target_order_id"]:
            why = "other_order"
        elif row["occurred_at"] > record["cutoff"]:
            why = "future_occurrence"
        elif row["state"] == "VOID":
            why = "void"
        elif row["kind"] == "SHIP":
            if eid in removed:
                why = "reversed_shipment"
            else:
                units, details = contribution(row["quantity"], row)
                why = "shipment" if units else "other_line_allocation"
        elif row["kind"] == "RETURN":
            if row["reference"] in shipments:
                units, details = contribution(row["quantity"], shipments[row["reference"]])
                units = -units
                why = "accepted_return"
            else:
                why = "return_on_inactive_shipment"
        else:
            why = "reversal_control"
        traces.append({"event_id": eid, "selected_revision": row["row_revision"], "kind": row["kind"],
                       "selected_quantity": row["quantity"], "reference": row["reference"],
                       "net_dispatched_units": int(units), "reason": why, **details})
    net = sum(r["net_dispatched_units"] for r in traces)
    plan = record["plans"][terms["price_plan"]]
    eligible_tiers = [r for r in plan["tiers"] if r["minimum"] <= terms["ordered_units"]]
    tier = sorted(eligible_tiers, key=lambda r: r["minimum"])[-1]
    gross = Fraction(tier["gross_cents"], plan["pack_units"])
    after_a = gross * Fraction(10000 - tier["rebate_a_bps"], 10000)
    after_b = after_a * Fraction(10000 - tier["rebate_b_bps"], 10000)
    pack_fee = Fraction(plan["pack_fee_cents"]) / plan["pack_units"]
    final = after_b + Fraction(plan["fee_cents"]) + pack_fee - Fraction(plan["credit_cents"])
    price = (2 * final.numerator + final.denominator) // (2 * final.denominator)
    answer = {"order_id": record["target_order_id"], "sku": target["sku"], "quantity_units": terms["ordered_units"] - net,
              "unit_price_cents": price, "currency": terms["currency"], "ship_date": terms["ship_date"], "status": "active"}
    needs = {"order_id": ["P01"], "sku": ["P01"], "quantity_units": sorted({"P03", "P04", "P06", winners["ordered_units"][2]}),
             "unit_price_cents": sorted({"P05", winners["ordered_units"][2], winners["price_plan"][2]}),
             "currency": [winners["currency"][2]], "ship_date": [winners["ship_date"][2]], "status": ["P01"]}
    price_trace = {"plan": terms["price_plan"], "tier_ordered_units": terms["ordered_units"], "tier_minimum": tier["minimum"],
                   "gross_pack_cents": tier["gross_cents"], "pack_units": plan["pack_units"], "gross_unit_cents": str(gross),
                   "rebate_a_bps": tier["rebate_a_bps"], "after_rebate_a_cents": str(after_a), "rebate_b_bps": tier["rebate_b_bps"],
                   "after_rebate_b_cents": str(after_b), "fee_unit_cents": plan["fee_cents"], "pack_fee_unit_cents": str(pack_fee),
                   "credit_unit_cents": plan["credit_cents"], "unrounded_unit_cents": str(final), "rounded_unit_cents": price}
    trace = {"ordered_units": terms["ordered_units"], "net_dispatched_units": net, "open_units": answer["quantity_units"],
             "term_winners": {k: {"value": v[1], "source": v[2], "approval": v[3], "priority": list(v[0])} for k, v in winners.items()},
             "events": traces, "price": price_trace}
    return answer, needs, trace


def high_independent_reference(case):
    """Reference from rendered text, without reading source_record or stored gold."""
    return _high_reduce(high_parse_document(case["document"]))[0]


def high_calculation_trace(case):
    return _high_reduce(high_parse_document(case["document"]))[2]


def _high_check_record(record):
    """Material solvability checks, independent of any model response."""
    if record["version"] != HIGH_VERSION:
        raise ValueError("Unexpected format version")
    for key in ["issued_at", "cutoff"]:
        dt.datetime.fromisoformat(record[key].replace("Z", "+00:00"))
    lines = {r["line_id"]: r for r in record["lines"]}
    if len(lines) != len(record["lines"]) or record["target_line_id"] not in lines:
        raise ValueError("Nonunique or absent target line")
    if lines[record["target_line_id"]]["sku"] != record["target_sku"]:
        raise ValueError("Target SKU mismatch")
    if len({r["approval_id"] for r in record["amendments"]}) != len(record["amendments"]):
        raise ValueError("Duplicate approval ID")
    uom_keys = [(r["sku"], r["uom"], r["effective_from"]) for r in record["uom"]]
    if len(set(uom_keys)) != len(uom_keys) or any(r["units"] <= 0 for r in record["uom"]):
        raise ValueError("Nonunique or nonpositive UOM rate")
    alloc_keys = [(r["key"], r["effective_from"]) for r in record["allocations"]]
    if len(set(alloc_keys)) != len(alloc_keys):
        raise ValueError("Nonunique allocation version")
    for row in record["allocations"]:
        dt.date.fromisoformat(row["effective_from"])
        if sum(row["shares"].values()) != 100 or any(k not in lines or not 0 <= v <= 100 for k, v in row["shares"].items()):
            raise ValueError("Incomplete allocation shares")
    for plan in record["plans"].values():
        if plan["pack_units"] <= 0 or len({r["minimum"] for r in plan["tiers"]}) != len(plan["tiers"]) or min(r["minimum"] for r in plan["tiers"]) != 0:
            raise ValueError("Incomplete or duplicate price tiers")
        for tier in plan["tiers"]:
            if not all(0 <= tier[k] < 10000 for k in ["rebate_a_bps", "rebate_b_bps"]):
                raise ValueError("Invalid rebate")
    grouped = defaultdict(list)
    all_revisions = {}
    for row in record["ledger"]:
        if row["kind"] not in {"SHIP", "RETURN", "REVERSAL"} or row["state"] not in {"POSTED", "VOID"}:
            raise ValueError("Invalid movement kind/state")
        for key in ["recorded_at", "occurred_at"]:
            dt.datetime.fromisoformat(row[key].replace("Z", "+00:00"))
        identity = row["event_id"], row["row_revision"]
        if identity in all_revisions and all_revisions[identity] != row:
            raise ValueError("Conflicting ingestion copies")
        all_revisions[identity] = row
        if row["recorded_at"] <= record["cutoff"]:
            grouped[row["event_id"]].append(row)
    selected = {k: max(rows, key=lambda r: r["row_revision"]) for k, rows in grouped.items()}
    return_totals = Counter()
    for row in selected.values():
        if row["kind"] in {"RETURN", "REVERSAL"}:
            ref = selected.get(row["reference"])
            if ref is None or ref["kind"] != "SHIP" or ref["order_id"] != row["order_id"] or ref["sku"] != row["sku"]:
                raise ValueError("Missing or inconsistent movement reference")
            if row["occurred_at"] < ref["occurred_at"]:
                raise ValueError("Return/reversal precedes referenced selected shipment")
            if row["kind"] == "RETURN" and row["state"] == "POSTED" and row["occurred_at"] <= record["cutoff"]:
                return_totals[row["reference"]] += row["quantity"]
    if any(q > selected[eid]["quantity"] for eid, q in return_totals.items()):
        raise ValueError("Return exceeds original shipment")
    # Independent reducer proves a unique applicable term, UOM and allocation and integral arithmetic.
    answer, _, trace = _high_reduce(record)
    if min(answer["quantity_units"], answer["unit_price_cents"]) < 0:
        raise ValueError("Negative output outside the task contract")
    return trace


def high_audit_fixtures(cases):
    if len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Repeated case identity")
    words, movements = [], []
    for case in cases:
        parsed = high_parse_document(case["document"])
        if parsed != case["source_record"]:
            raise ValueError("Rendered text does not reconstruct every source fact")
        trace = _high_check_record(parsed)
        if _high_gold(case["source_record"]) != case["gold"] or high_independent_reference(case) != case["gold"]:
            raise ValueError("Independent arithmetic/gold mismatch")
        if _high_render(parsed, case["split"] == "audit") != case["document"]:
            raise ValueError("Rendered roundtrip mismatch")
        if _high_semantic(parsed) != case["semantic_hash"] or hashlib.sha256(case["document"].encode("utf-8")).hexdigest() != case["content_hash"]:
            raise ValueError("Frozen hash mismatch")
        if not high_validate_answer(case, high_correct_response(case))["accepted"]:
            raise ValueError("Gold response fails checker")
        count = len({r["event_id"] for r in parsed["ledger"] if r["kind"] == "SHIP" and r["event_id"].startswith("SH-")})
        if count != {1: 32, 2: 64, 3: 128, 4: 192}[case["level"]]:
            raise ValueError("Ladder movement count mismatch")
        words.append(len(case["document"].split()))
        movements.append(count)
    return {"version": HIGH_VERSION, "n_cases": len(cases), "family_counts": dict(Counter(c["family"] for c in cases)),
            "min_document_words": min(words, default=0), "max_document_words": max(words, default=0),
            "logical_movement_counts": sorted(set(movements)),
            "n_distinct_semantic_cases": len({c["semantic_hash"] for c in cases}),
            "independent_reference_matches": True, "rendered_text_roundtrip_matches": True,
            "source_solvability_checks_pass": True, "gold_responses_accepted": True, "cutoff": HIGH_CUTOFF}

