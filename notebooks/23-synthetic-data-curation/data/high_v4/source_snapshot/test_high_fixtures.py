"""Deterministic, independent-equation, visible-source and verifier tests."""
import copy
import hashlib
import json
import unittest
from fractions import Fraction
import high_fixtures as h


def tiny_record():
    r = copy.deepcopy(h.high_make_cases(1, 761, level=1)[0]["source_record"])
    target, sku, order = r["target_line_id"], r["target_sku"], r["target_order_id"]
    r["lines"] = [{"line_id": target, "sku": sku, "ordered_units": 1000, "price_plan": "PLAN-A",
                   "ship_date": None, "currency": None},
                  {"line_id": "L07", "sku": sku, "ordered_units": 9999, "price_plan": None,
                   "ship_date": None, "currency": None}]
    r["amendments"] = [{"approval_id": "A0", "line_id": target, "authority": 3, "revision": 1,
                        "effective_at": "2026-10-20T00:00:00Z", "recorded_at": "2026-10-20T01:00:00Z",
                        "approved": False, "changes": {"ordered_units": 12345}}]
    r["uom"] = [{"sku": sku, "uom": "CASE", "effective_from": "2026-01-01", "units": 24},
                {"sku": sku, "uom": "CASE", "effective_from": "2026-10-21", "units": 30},
                {"sku": sku, "uom": "EA", "effective_from": "2026-01-01", "units": 1}]
    r["allocations"] = [{"key": "AL-1", "effective_from": "2026-01-01", "shares": {target: 25, "L07": 75}},
                         {"key": "AL-1", "effective_from": "2026-10-21", "shares": {target: 50, "L07": 50}}]
    r["plans"] = {"PLAN-A": {"pack_units": 24, "fee_cents": "1.25", "credit_cents": "0.50", "pack_fee_cents": "6",
                            "tiers": [{"minimum": 0, "gross_cents": 12000, "rebate_a_bps": 1000, "rebate_b_bps": 2000}]}}
    def ship(eid, qty, date, uom="CASE", **kw):
        return dict({"event_id": eid, "row_revision": 1, "kind": "SHIP", "order_id": order, "sku": sku,
                     "quantity": qty, "uom": uom, "allocation": "AL-1", "reference": "-",
                     "occurred_at": date + "T10:00:00Z", "recorded_at": date + "T11:00:00Z", "state": "POSTED"}, **kw)
    s1 = ship("S1", 8, "2026-10-18")
    s2 = ship("S2", 8, "2026-10-22")
    s3 = ship("S3", 8, "2026-10-22", "EA")
    s4 = ship("S4", 8, "2026-10-22", "EA")
    correction = dict(s1, row_revision=2, quantity=12, recorded_at="2026-10-25T00:00:00Z")
    returned = dict(s1, event_id="R1", kind="RETURN", quantity=4, reference="S1", uom="ORIGINAL", allocation="ORIGINAL",
                    occurred_at="2026-10-25T10:00:00Z", recorded_at="2026-10-25T11:00:00Z")
    reversal = dict(s2, event_id="V1", kind="REVERSAL", quantity=0, reference="S2", uom="-", allocation="-",
                    occurred_at="2026-10-25T10:00:00Z", recorded_at="2026-10-25T11:00:00Z")
    r["ledger"] = [s1, correction, copy.deepcopy(correction), s2, reversal, s3,
                   dict(s3, row_revision=2, state="VOID", recorded_at="2026-10-25T01:00:00Z"), s4, returned]
    return r


def tiny_case(r):
    answer, needs, _ = h._high_reduce(r)
    document = h._high_render(r)
    return {"case_id": r["case_id"], "gold": answer, "evidence_gold": needs,
            "document": document, "source_record": r}


class HighFixtureTests(unittest.TestCase):
    def test_hand_equations(self):
        r = tiny_record()
        # Selected S1 12*24*.25=72, original-date return4*24*.25=-24; S2 reversed,
        # S3 VOID, S4 8EA*.50=4. Net52, remaining948.
        expected = {"order_id": r["target_order_id"], "sku": r["target_sku"], "quantity_units": 948,
                    "unit_price_cents": 361, "currency": r["defaults"]["currency"],
                    "ship_date": r["defaults"]["ship_date"], "status": "active"}
        self.assertEqual(h._high_gold(r), expected)
        self.assertEqual(h._high_reduce(r)[0], expected)
        self.assertEqual(h.high_independent_reference(tiny_case(r)), expected)
        h._high_check_record(r)

    def test_all_levels_all_families_and_json_roundtrip(self):
        for level in range(1, 5):
            cases = h.high_make_cases(12, 8880 + level, level=level)
            self.assertEqual(set(c["family"] for c in cases), set(h.HIGH_FAMILIES))
            reloaded = json.loads(json.dumps(cases, sort_keys=True))
            result = h.high_audit_fixtures(reloaded)
            self.assertTrue(result["rendered_text_roundtrip_matches"])
            self.assertEqual(result["logical_movement_counts"], [[32], [64], [128], [192]][level - 1])
            for c in reloaded:
                self.assertEqual(h.high_parse_document(c["document"]), c["source_record"])
                self.assertEqual(h.high_calculation_trace(c)["open_units"], c["gold"]["quantity_units"])

    def test_audit_format_same_semantics(self):
        r = tiny_record()
        self.assertEqual(h.high_parse_document(h._high_render(r, True)), r)
        self.assertNotEqual(h._high_render(r, True), h._high_render(r, False))

    def test_determinism_identity_split_disjoint(self):
        a = h.high_make_cases(6, 51)
        self.assertEqual(a, h.high_make_cases(6, 51))
        ids = {c["case_id"] for c in a}
        for kw in [{"seed": 52}, {"seed": 51, "split": "audit"}, {"seed": 51, "start_index": 9}]:
            self.assertFalse(ids & {c["case_id"] for c in h.high_make_cases(6, **kw)})

    def test_zero_and_bad_controls(self):
        self.assertEqual(h.high_make_cases(0, 0), [])
        self.assertEqual(h.high_audit_fixtures([])["n_cases"], 0)
        for args in [(-1, 0, 1), (1, 0, 0), (1, 0, 5), (1, 0, True)]:
            with self.assertRaises(ValueError):
                h.high_make_cases(args[0], args[1], level=args[2])

    def test_instruction_price_units_and_operations(self):
        instructions = h.HIGH_TASK_INSTRUCTIONS
        for fact in ["entire price pack", "pack_fee_cents/pack_units", "basis points", "ONCE", "halves UP"]:
            self.assertIn(fact, instructions)
        self.assertNotIn("Gross tier prices are per individual unit", instructions)
        memo = h._HIGH_TABLE_MEMOS["P05"][1]
        self.assertIn("per price pack", memo)
        self.assertIn("pack_fee_cents/pack_units", memo)
        self.assertIn("after rebates", memo)

    def test_selected_revision_before_occurrence_filter_no_fallback(self):
        r = tiny_record()
        s4 = next(x for x in r["ledger"] if x["event_id"] == "S4")
        r["ledger"].append(dict(s4, row_revision=2, occurred_at="2026-10-26T13:00:00Z", recorded_at="2026-10-26T11:00:00Z"))
        self.assertEqual(h._high_reduce(r)[0]["quantity_units"], 952)
        r["ledger"][-1]["recorded_at"] = "2026-10-26T12:01:00Z"
        self.assertEqual(h._high_reduce(r)[0]["quantity_units"], 948)

    def test_duplicate_and_reversal_idempotence_and_void_reversal(self):
        r = tiny_record()
        rv = next(x for x in r["ledger"] if x["event_id"] == "V1")
        r["ledger"].extend([copy.deepcopy(rv), dict(rv, event_id="V2")])
        self.assertEqual(h._high_reduce(r)[0]["quantity_units"], 948)
        r["ledger"] = [x for x in r["ledger"] if x["event_id"] != "V2"]
        r["ledger"].append(dict(rv, row_revision=2, state="VOID", recorded_at="2026-10-26T01:00:00Z"))
        self.assertEqual(h._high_reduce(r)[0]["quantity_units"], 828)

    def test_return_uses_original_date_uom_allocation_and_selected_correction(self):
        r = tiny_record()
        trace = h._high_reduce(r)[2]
        returned = next(t for t in trace["events"] if t["event_id"] == "R1")
        self.assertEqual(returned["net_dispatched_units"], -24)
        self.assertEqual(returned["units_per_uom"], 24)
        self.assertEqual(returned["target_share_percent"], 25)
        selected = next(t for t in trace["events"] if t["event_id"] == "S1")
        self.assertEqual(selected["selected_revision"], 2)
        self.assertEqual(selected["net_dispatched_units"], 72)

    def test_return_on_reversed_shipment_no_effect(self):
        r = tiny_record()
        rt = next(x for x in r["ledger"] if x["event_id"] == "R1")
        r["ledger"].append(dict(rt, event_id="R2", reference="S2"))
        self.assertEqual(h._high_reduce(r)[0]["quantity_units"], 948)

    def test_approval_scope_authority_partial_effective_and_inclusive_cutoff(self):
        r = tiny_record()
        template = dict(r["amendments"][0], approved=True)
        r["amendments"] = [
            dict(template, approval_id="A1", line_id="ALL", authority=3, changes={"ordered_units": 2000}),
            dict(template, approval_id="A2", authority=2, changes={"ordered_units": 1100}),
            dict(template, approval_id="A3", authority=1, revision=99, effective_at=r["cutoff"], changes={"ordered_units": 9000}),
            dict(template, approval_id="A4", authority=2, revision=2, effective_at=r["cutoff"], recorded_at=r["cutoff"],
                 changes={"ordered_units": 1200}),
            dict(template, approval_id="A5", authority=3, recorded_at="2026-10-26T12:00:01Z", changes={"ordered_units": 8000}),
        ]
        result = h._high_reduce(r)
        self.assertEqual(result[0]["quantity_units"], 1148)
        self.assertEqual(result[0]["unit_price_cents"], 361)
        self.assertEqual(result[2]["term_winners"]["ordered_units"]["approval"], "A4")
        self.assertEqual(h._high_gold(r), result[0])

    def test_tier_uses_ordered_not_remaining(self):
        r = tiny_record()
        t = r["plans"]["PLAN-A"]["tiers"][0]
        r["plans"]["PLAN-A"]["tiers"].append(dict(t, minimum=1000, gross_cents=9600))
        self.assertEqual(h._high_reduce(r)[2]["price"]["tier_minimum"], 1000)
        self.assertEqual(h._high_gold(r), h._high_reduce(r)[0])

    def test_half_up_and_no_intermediate_rounding(self):
        r = tiny_record()
        p = r["plans"]["PLAN-A"]
        p.update(pack_units=1, fee_cents="0.50", credit_cents="0", pack_fee_cents="0")
        p["tiers"] = [{"minimum": 0, "gross_cents": 100, "rebate_a_bps": 0, "rebate_b_bps": 0}]
        self.assertEqual(h._high_gold(r)["unit_price_cents"], 101)
        self.assertEqual(h._high_reduce(r)[0]["unit_price_cents"], 101)
        p.update(pack_units=3, fee_cents="0", pack_fee_cents="0.50")
        p["tiers"][0].update(gross_cents=301, rebate_a_bps=1000, rebate_b_bps=2000)
        # 301/3*.9*.8 + .5/3 = 72.406666...; exact Fraction, no intermediate rounding.
        self.assertEqual(h._high_reduce(r)[2]["price"]["unrounded_unit_cents"], str(Fraction(10861, 150)))
        self.assertEqual(h._high_gold(r)["unit_price_cents"], 72)

    def test_solvability_rejects_conflict_missing_reference_and_overreturn(self):
        for kind in ["conflict", "reference", "overreturn", "allocation", "uom", "terms"]:
            r = tiny_record()
            if kind == "conflict":
                row = next(x for x in r["ledger"] if x["event_id"] == "S4")
                r["ledger"].append(dict(row, quantity=row["quantity"] + 4))
            elif kind == "reference":
                next(x for x in r["ledger"] if x["event_id"] == "R1")["reference"] = "ABSENT"
            elif kind == "overreturn":
                next(x for x in r["ledger"] if x["event_id"] == "R1")["quantity"] = 1000
            elif kind == "allocation":
                r["allocations"][0]["shares"][r["target_line_id"]] += 1
            elif kind == "uom":
                r["uom"].append(dict(r["uom"][0], units=99))
            else:
                a = dict(r["amendments"][0], approved=True)
                r["amendments"] = [a, dict(a, approval_id="OTHER", changes={"ordered_units": 200})]
            with self.assertRaises(ValueError, msg=kind):
                h._high_check_record(r)

    def test_visible_parser_completeness_and_tampering(self):
        c = h.high_make_cases(1, 998)[0]
        for text in [c["document"].replace("BEGIN TABLE P03", "MISSING"),
                     c["document"].replace("Target-line:", "Lost-line:"),
                     c["document"].replace("line_id | sku", "bad_column | sku", 1)]:
            with self.assertRaises(ValueError):
                h.high_parse_document(text)
        broken = copy.deepcopy(c)
        broken["document"] = broken["document"].replace("Default-currency: " + c["source_record"]["defaults"]["currency"], "Default-currency: JPY")
        with self.assertRaises(ValueError):
            h.high_audit_fixtures([broken])

    def test_verifier_schema_values_and_evidence_separate(self):
        c = h.high_make_cases(1, 712)[0]
        controls = h.high_make_verifier_controls([c])
        for ctrl in controls:
            self.assertEqual(h.high_validate_answer(c, ctrl["response"])["accepted"], ctrl["expected_accepted"])
            self.assertFalse(ctrl["is_model_result"])
        good = h.high_correct_response(c)
        for field in h.HIGH_FIELDS:
            good["evidence"][field] = ["P01", "P02", "P03", "P04", "P05", "P06"]
        self.assertTrue(h.high_validate_answer(c, good)["accepted"])
        bad = copy.deepcopy(good)
        bad["answer"]["quantity_units"] -= 1
        judged = h.high_validate_answer(c, bad)
        self.assertTrue(judged["valid_schema"])
        self.assertTrue(judged["has_value_error"])
        self.assertFalse(judged["exact_fields"])
        self.assertTrue(all(judged["evidence_correct"].values()))
        no_cite = h.high_correct_response(c)
        no_cite["evidence"]["quantity_units"] = ["P01"]
        judged = h.high_validate_answer(c, no_cite)
        self.assertTrue(judged["exact_fields"])
        self.assertTrue(judged["evidence_only_failure"])

    def test_semantic_hash_ignores_display_order_and_duplicate_copies(self):
        r = tiny_record()
        s = copy.deepcopy(r)
        s["ledger"] = list(reversed(s["ledger"])) + [copy.deepcopy(s["ledger"][0])]
        s["lines"].reverse()
        s["case_id"] = "other-id"
        self.assertEqual(h._high_semantic(r), h._high_semantic(s))
        s["lines"][0]["ordered_units"] += 1
        self.assertNotEqual(h._high_semantic(r), h._high_semantic(s))


if __name__ == "__main__":
    unittest.main()

