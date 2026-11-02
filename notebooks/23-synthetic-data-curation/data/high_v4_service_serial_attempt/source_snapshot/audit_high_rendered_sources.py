"""Independent, text-only solvability audit for the high-reasoning v4 packets.

This module intentionally does not import high_fixtures.py. `audit_cases` reads
only each rendered `document` field to derive the answer, then compares that
independent result with the separately stored expected answer. It never uses a
constructor record, fixture reducer, or model output.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from fractions import Fraction
import hashlib
import json
import re


FIELDS = ("order_id", "sku", "quantity_units", "unit_price_cents", "currency", "ship_date", "status")
TABLES = {
    "P01": ("line_id", "sku", "ordered_units", "price_plan", "ship_date", "currency"),
    "P02": ("approval_id", "line_id", "authority", "revision", "effective_at", "recorded_at", "approved", "ordered_units", "price_plan", "ship_date", "currency"),
    "P03": ("sku", "uom", "effective_from", "units"),
    "P04": ("key", "effective_from", "line_id", "share"),
    "P05": ("plan", "pack_units", "minimum", "gross_cents", "rebate_a_bps", "rebate_b_bps", "fee_cents", "credit_cents", "pack_fee_cents"),
    "P06": ("event_id", "row_revision", "kind", "order_id", "sku", "quantity", "uom", "allocation", "reference", "occurred_at", "recorded_at", "state"),
}
INTS = {"ordered_units", "authority", "revision", "units", "share", "pack_units", "minimum", "gross_cents", "rebate_a_bps", "rebate_b_bps", "row_revision", "quantity"}


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError(f"Timestamp lacks UTC offset: {value}")
    return parsed


def _date(value: str) -> date:
    return date.fromisoformat(value)


def parse_packet(text: str) -> dict:
    """Parse the visible header and P01-P06 pipe tables, rejecting ambiguity."""
    if not isinstance(text, str) or "\r" in text:
        raise ValueError("Expected LF-only rendered text")
    lines = text.splitlines()
    header_map = {
        "Case-ID": "case_id", "Format-version": "version", "Target-order": "target_order_id",
        "Target-line": "target_line_id", "Target-SKU": "target_sku", "Other-order": "other_order_id",
        "Issued-UTC": "issued_at", "Cutoff-UTC": "cutoff",
    }
    parsed = {}
    for label, key in header_map.items():
        rows = [line[len(label) + 2:] for line in lines if line.startswith(label + ": ")]
        if len(rows) != 1 or not rows[0]:
            raise ValueError(f"Header missing/repeated: {label}")
        parsed[key] = rows[0]
    defaults = {}
    for label, key in (("Default-currency", "currency"), ("Default-ship-date", "ship_date"), ("Default-price-plan", "price_plan")):
        rows = [line[len(label) + 2:] for line in lines if line.startswith(label + ": ")]
        if len(rows) != 1 or not rows[0]:
            raise ValueError(f"Default missing/repeated: {label}")
        defaults[key] = rows[0]
    parsed["defaults"] = defaults
    parsed_tables = {}
    for name, columns in TABLES.items():
        begin, end = f"BEGIN TABLE {name}", f"END TABLE {name}"
        if lines.count(begin) != 1 or lines.count(end) != 1:
            raise ValueError(f"Missing/repeated delimiters for {name}")
        start, stop = lines.index(begin), lines.index(end)
        if stop <= start + 1 or tuple(lines[start + 1].split(" | ")) != columns:
            raise ValueError(f"Unexpected columns in {name}")
        rows = []
        for line in lines[start + 2:stop]:
            cells = line.split(" | ")
            if len(cells) != len(columns):
                raise ValueError(f"Malformed row in {name}: {line}")
            row = {}
            for col, raw in zip(columns, cells):
                if raw == "INHERIT":
                    row[col] = None
                elif col in INTS:
                    if re.fullmatch(r"\d+", raw) is None:
                        raise ValueError(f"Invalid integer in {name}.{col}: {raw}")
                    row[col] = int(raw)
                elif col == "approved":
                    if raw not in {"YES", "NO"}:
                        raise ValueError(f"Invalid approval value: {raw}")
                    row[col] = raw == "YES"
                else:
                    row[col] = raw
            rows.append(row)
        if not rows:
            raise ValueError(f"Empty table {name}")
        parsed_tables[name] = rows
    parsed["lines"] = parsed_tables["P01"]
    parsed["amendments"] = parsed_tables["P02"]
    parsed["uom"] = parsed_tables["P03"]
    parsed["allocations"] = parsed_tables["P04"]
    parsed["prices"] = parsed_tables["P05"]
    parsed["ledger"] = parsed_tables["P06"]
    return parsed


def _resolve_terms(packet: dict) -> tuple[dict, dict]:
    target_id = packet["target_line_id"]
    target_rows = [r for r in packet["lines"] if r["line_id"] == target_id]
    if len(target_rows) != 1:
        raise ValueError("Target line is missing or duplicated")
    target = target_rows[0]
    if target["sku"] != packet["target_sku"]:
        raise ValueError("Target header and P01 SKU disagree")
    cutoff = _utc(packet["cutoff"])
    source_by_field = {}
    priorities = {}
    values = {}
    for field, val in packet["defaults"].items():
        values[field], priorities[field], source_by_field[field] = val, (0, 0, _utc(packet["issued_at"]), 0), "P01"
    if target["ordered_units"] is not None:
        values["ordered_units"] = target["ordered_units"]
        priorities["ordered_units"] = (1, 0, _utc(packet["issued_at"]), 0)
        source_by_field["ordered_units"] = "P01"
    for field in ("price_plan", "ship_date", "currency"):
        if target[field] is not None:
            values[field] = target[field]
            priorities[field] = (1, 0, _utc(packet["issued_at"]), 0)
            source_by_field[field] = "P01"
    candidates = defaultdict(list)
    for field in values:
        candidates[field].append((priorities[field], values[field], source_by_field[field]))
    for row in packet["amendments"]:
        if not row["approved"]:
            continue
        recorded, effective = _utc(row["recorded_at"]), _utc(row["effective_at"])
        if recorded > cutoff or effective > cutoff or row["line_id"] not in {"ALL", target_id}:
            continue
        priority = (int(row["line_id"] != "ALL"), row["authority"], effective, row["revision"])
        for field in ("ordered_units", "price_plan", "ship_date", "currency"):
            if row[field] is not None:
                candidates[field].append((priority, row[field], "P02"))
    resolved, sources = {}, {}
    for field in ("ordered_units", "price_plan", "ship_date", "currency"):
        options = candidates[field]
        if not options:
            raise ValueError(f"No current value for {field}")
        top = max(item[0] for item in options)
        winners = [item for item in options if item[0] == top]
        if len({str(item[1]) for item in winners}) != 1:
            raise ValueError(f"Tied, conflicting governing values for {field}")
        resolved[field], sources[field] = winners[0][1], winners[0][2]
    return resolved, sources


def _select_events(packet: dict) -> dict:
    cutoff = _utc(packet["cutoff"])
    grouped = defaultdict(list)
    for row in packet["ledger"]:
        recorded = _utc(row["recorded_at"])
        if recorded <= cutoff:
            grouped[row["event_id"]].append(row)
    selected = {}
    for event, rows in grouped.items():
        rev = max(r["row_revision"] for r in rows)
        latest = [r for r in rows if r["row_revision"] == rev]
        canonical = {json.dumps(r, sort_keys=True) for r in latest}
        if len(canonical) != 1:
            raise ValueError(f"Conflicting maximum revisions for {event}")
        selected[event] = latest[0]
    return selected


def _event_reconciliation(packet: dict) -> tuple[int, dict]:
    cutoff, target_order = _utc(packet["cutoff"]), packet["target_order_id"]
    selected = _select_events(packet)
    posted = {event: row for event, row in selected.items()
              if row["state"] == "POSTED" and _utc(row["occurred_at"]) <= cutoff and row["order_id"] == target_order}
    removed_shipments = {row["reference"] for row in posted.values() if row["kind"] == "REVERSAL"}
    ships = {event: row for event, row in posted.items()
             if row["kind"] == "SHIP" and event not in removed_shipments}

    def base_contribution(quantity: int, row: dict):
        when = _date(row["occurred_at"][:10])
        uom = [r for r in packet["uom"] if r["sku"] == row["sku"] and r["uom"] == row["uom"]
               and _date(r["effective_from"]) <= when]
        alloc_groups = defaultdict(dict)
        for r in packet["allocations"]:
            if r["key"] == row["allocation"] and _date(r["effective_from"]) <= when:
                alloc_groups[_date(r["effective_from"])][r["line_id"]] = r["share"]
        if not uom or not alloc_groups:
            raise ValueError(f"Missing dated UOM/allocation for {row['event_id']}")
        rate = max(uom, key=lambda r: _date(r["effective_from"]))
        asof_alloc = max(alloc_groups)
        share = alloc_groups[asof_alloc].get(packet["target_line_id"], 0)
        contribution = Fraction(quantity * rate["units"] * share, 100)
        if contribution.denominator != 1:
            raise ValueError(f"Nonintegral allocation for {row['event_id']}: {contribution}")
        return int(contribution), {"uom_source": "P03", "allocation_source": "P04"}

    events, totals = [], 0
    for event, row in sorted(selected.items()):
        units, why = 0, "excluded"
        if row["order_id"] != target_order:
            why = "other order"
        elif _utc(row["occurred_at"]) > cutoff:
            why = "after cutoff"
        elif row["state"] == "VOID":
            why = "selected VOID"
        elif row["kind"] == "SHIP":
            if event in removed_shipments:
                why = "active reversal removes shipment"
            else:
                units, _ = base_contribution(row["quantity"], row)
                why = "shipment"
        elif row["kind"] == "RETURN":
            original = ships.get(row["reference"])
            if original is None:
                why = "return on inactive shipment"
            else:
                units, _ = base_contribution(row["quantity"], original)
                units = -units
                why = "return on referenced shipment"
        elif row["kind"] == "REVERSAL":
            why = "reversal control"
        totals += units
        events.append({"event_id": event, "revision": row["row_revision"], "kind": row["kind"],
                       "quantity": row["quantity"], "reference": row["reference"], "net_units": units, "rule": why})
    return totals, {"events": events, "selected_event_count": len(selected), "active_reversals": sorted(removed_shipments)}


def _price(packet: dict, terms: dict) -> tuple[int, dict]:
    plan_name = terms["price_plan"]
    rows = [r for r in packet["prices"] if r["plan"] == plan_name]
    tiers = [r for r in rows if r["minimum"] <= terms["ordered_units"]]
    if not tiers:
        raise ValueError(f"No eligible tier in selected plan {plan_name}")
    tier = max(tiers, key=lambda r: r["minimum"])
    pack_units = tier["pack_units"]
    gross = Fraction(tier["gross_cents"], pack_units)
    after_a = gross * Fraction(10000 - tier["rebate_a_bps"], 10000)
    after_b = after_a * Fraction(10000 - tier["rebate_b_bps"], 10000)
    unit_fee = Fraction(tier["fee_cents"])
    pack_fee = Fraction(tier["pack_fee_cents"]) / pack_units
    unit_credit = Fraction(tier["credit_cents"])
    final = after_b + unit_fee + pack_fee - unit_credit
    whole, rem = divmod(final.numerator, final.denominator)
    rounded = whole + int(rem * 2 >= final.denominator)
    return rounded, {"plan": plan_name, "ordered_tier_minimum": tier["minimum"], "gross_cents_per_pack": tier["gross_cents"],
                     "pack_units": pack_units, "gross_cents_per_unit": str(gross), "rebate_a_bps": tier["rebate_a_bps"],
                     "after_a": str(after_a), "rebate_b_bps": tier["rebate_b_bps"], "after_b": str(after_b),
                     "unit_fee_cents": str(unit_fee), "pack_fee_per_unit_cents": str(pack_fee),
                     "unit_credit_cents": str(unit_credit), "unrounded_final_cents": str(final), "rounded_half_up": rounded}


def derive_from_text(document: str) -> tuple[dict, dict]:
    """Compute seven answer values solely from visible packet text."""
    packet = parse_packet(document)
    terms, term_sources = _resolve_terms(packet)
    net, ledger_trace = _event_reconciliation(packet)
    price, price_trace = _price(packet, terms)
    evidence_needs = {
        "order_id": ["P01"],
        "sku": ["P01"],
        "quantity_units": sorted({"P03", "P04", "P06", term_sources["ordered_units"]}),
        "unit_price_cents": sorted({"P05", term_sources["ordered_units"], term_sources["price_plan"]}),
        "currency": [term_sources["currency"]],
        "ship_date": [term_sources["ship_date"]],
        "status": ["P01"],
    }
    answer = {"order_id": packet["target_order_id"], "sku": packet["target_sku"],
              "quantity_units": terms["ordered_units"] - net, "unit_price_cents": price,
              "currency": terms["currency"], "ship_date": terms["ship_date"], "status": "active"}
    if type(answer["quantity_units"]) is not int or answer["quantity_units"] < 0:
        raise ValueError("Computed open units are invalid")
    audit = {"parsed_header": {k: packet[k] for k in ("case_id", "target_order_id", "target_line_id", "target_sku", "cutoff")},
             "term_sources": term_sources, "resolved_terms": terms, "ledger": ledger_trace,
             "price": price_trace, "evidence_needs_from_rendered_text": evidence_needs,
             "answer_from_rendered_text": answer}
    return answer, audit


def validate_packet_integrity(document: str) -> dict:
    """Check reference, uniqueness, date, and table invariants from visible text."""
    packet = parse_packet(document)
    cutoff = _utc(packet["cutoff"])
    if len({r["line_id"] for r in packet["lines"]}) != len(packet["lines"]):
        raise ValueError("P01 has duplicate line IDs")
    if len([r for r in packet["lines"] if r["line_id"] == packet["target_line_id"]]) != 1:
        raise ValueError("Target line is not unique")

    uom_keys = [(r["sku"], r["uom"], _date(r["effective_from"])) for r in packet["uom"]]
    if len(set(uom_keys)) != len(uom_keys) or any(r["units"] <= 0 for r in packet["uom"]):
        raise ValueError("P03 duplicate or invalid UOM rows")
    allocs = defaultdict(dict)
    for row in packet["allocations"]:
        key = (row["key"], _date(row["effective_from"]))
        if row["line_id"] in allocs[key]:
            raise ValueError("Duplicate P04 line within allocation version")
        allocs[key][row["line_id"]] = row["share"]
    if any(sum(shares.values()) != 100 or any(not 0 <= n <= 100 for n in shares.values())
           for shares in allocs.values()):
        raise ValueError("P04 shares must sum to 100 for every dated key")

    price_keys, plan_attrs = set(), {}
    for row in packet["prices"]:
        key = row["plan"], row["minimum"]
        if key in price_keys:
            raise ValueError("Duplicate P05 plan tier")
        price_keys.add(key)
        attrs = tuple(row[k] for k in ("pack_units", "fee_cents", "credit_cents", "pack_fee_cents"))
        if row["pack_units"] <= 0 or any(not 0 <= row[k] < 10000 for k in ("rebate_a_bps", "rebate_b_bps")):
            raise ValueError("Invalid P05 units or rebate")
        if row["plan"] in plan_attrs and plan_attrs[row["plan"]] != attrs:
            raise ValueError("P05 plan-level terms vary across tiers")
        plan_attrs[row["plan"]] = attrs
    for plan in plan_attrs:
        minima = sorted(k[1] for k in price_keys if k[0] == plan)
        if not minima or minima[0] != 0:
            raise ValueError("P05 plan lacks a zero-minimum tier")

    all_versions = {}
    for row in packet["ledger"]:
        if row["kind"] not in {"SHIP", "RETURN", "REVERSAL"} or row["state"] not in {"POSTED", "VOID"}:
            raise ValueError("Invalid P06 kind/state")
        _utc(row["recorded_at"])
        _utc(row["occurred_at"])
        identity = row["event_id"], row["row_revision"]
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        if identity in all_versions and all_versions[identity] != canonical:
            raise ValueError("Conflicting duplicate P06 event revision")
        all_versions[identity] = canonical
    selected = _select_events(packet)
    returns_by_shipment = defaultdict(int)
    references = []
    for row in selected.values():
        if row["kind"] not in {"RETURN", "REVERSAL"}:
            continue
        ref = selected.get(row["reference"])
        if ref is None or ref["kind"] != "SHIP":
            raise ValueError(f"P06 unresolved shipment reference: {row['event_id']}")
        if (ref["order_id"], ref["sku"]) != (row["order_id"], row["sku"]):
            raise ValueError(f"P06 reference order/SKU mismatch: {row['event_id']}")
        if _utc(row["occurred_at"]) < _utc(ref["occurred_at"]):
            raise ValueError(f"P06 return/reversal precedes referenced shipment: {row['event_id']}")
        if row["kind"] == "RETURN" and row["quantity"] <= 0:
            raise ValueError("P06 return magnitude must be positive")
        if row["kind"] == "REVERSAL" and row["quantity"] != 0:
            raise ValueError("P06 reversal has a nonzero quantity")
        if (row["kind"] == "RETURN" and row["state"] == "POSTED" and _utc(row["occurred_at"]) <= cutoff
                and _utc(row["recorded_at"]) <= cutoff):
            returns_by_shipment[row["reference"]] += row["quantity"]
        references.append({"event_id": row["event_id"], "reference": row["reference"], "resolved": True})
    for event, quantity in returns_by_shipment.items():
        if quantity > selected[event]["quantity"]:
            raise ValueError(f"P06 eligible returns exceed selected shipment: {event}")

    if "Status active; no order cancellation notice" not in document:
        raise ValueError("P01 does not establish the active order status")
    return {"selected_logical_events": len(selected), "referenced_events": references,
            "allocation_versions": len(allocs), "price_plans": len(plan_attrs),
            "target_status_evidence": "P01 says active; no cancellation notice"}


def audit_cases(cases: list[dict]) -> dict:
    """Audit a complete case list; gold is only read for the final equality check."""
    rows, failures = [], []
    seen_ids = set()
    for case in cases:
        cid, document = case.get("case_id"), case.get("document")
        if not isinstance(cid, str) or cid in seen_ids:
            raise ValueError(f"Missing or duplicate case ID: {cid}")
        seen_ids.add(cid)
        integrity = validate_packet_integrity(document)
        answer, detail = derive_from_text(document)
        expected = case.get("gold")
        mismatch = [field for field in FIELDS if not isinstance(expected, dict) or answer[field] != expected.get(field)]
        hidden_evidence = case.get("evidence_gold")
        evidence_mismatch = []
        if hidden_evidence is not None:
            evidence_mismatch = [field for field in FIELDS
                                 if set(detail["evidence_needs_from_rendered_text"][field]) != set(hidden_evidence.get(field, []))]
        row = {"case_id": cid, "document_sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
               "document_words": len(document.split()), "independent_answer": answer, "gold_match": not mismatch,
               "mismatch_fields": mismatch, "evidence_gold_match": not evidence_mismatch,
               "evidence_mismatch_fields": evidence_mismatch, "integrity": integrity, "audit": detail}
        rows.append(row)
        if mismatch or evidence_mismatch:
            failures.append({"case_id": cid, "mismatch_fields": mismatch, "evidence_mismatch_fields": evidence_mismatch,
                             "independent_answer": answer, "stored_gold": expected, "stored_evidence": hidden_evidence})
    return {"n_cases": len(cases), "n_unique_cases": len(seen_ids), "n_answer_or_evidence_key_mismatches": len(failures),
            "all_rendered_text_answers_and_evidence_needs_match_keys": not failures,
            "failures": failures, "cases": rows}


if __name__ == "__main__":
    raise SystemExit("Import audit_cases and pass generated cases; no model calls are made by this module.")
