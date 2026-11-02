"""Mock-only missing-outcome tests. Never load a study arm cache or make calls."""
import copy
from pathlib import Path
import unittest
import scale_missing_outcomes as missing


class MissingOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = {"__name__": "mock_frozen_statistics"}
        exec(compile(Path(__file__).with_name("scale_experiment.py").read_text(encoding="utf-8"),
                     "scale_experiment.py", "exec"), ns)
        cls.stats = staticmethod(ns["scale_paired_statistics"])

    def fixture(self, n=6):
        ids = [f"mock-{i}" for i in range(n)]
        rows, unavailable = [], []
        for i, cid in enumerate(ids):
            for arm in missing.SCALE_MISSING_ARMS:
                absent = i >= n-2
                success = i % 2 == 0 or arm == "feedback_repair"
                row = {"case_id": cid, "arm": arm, "request_key": cid+arm,
                       "response": None if absent else {"mock": True},
                       "transport_error": "controller interrupted, outcome unavailable" if absent else None,
                       "outcome_unavailable": absent,
                       "verification": {"valid_schema": not absent, "exact_fields": success and not absent}}
                rows.append(row)
                if absent:
                    unavailable.append({k: row[k] for k in ("case_id", "arm", "request_key")})
        return {"phase": "interventions_complete"}, {"selected_case_ids": ids}, rows, unavailable

    def run_analysis(self, fixture=None, draws=200, envelope=True):
        return missing.scale_missing_outcome_analysis(*(fixture or self.fixture()),
            {"bootstrap_seed": 246600, "bootstrap_draws": draws}, self.stats, envelope)

    def test_gate_precedes_any_outcomes(self):
        class Poison:
            def __iter__(self):
                raise AssertionError("Outcome access before final gate")
        with self.assertRaisesRegex(ValueError, "interventions_complete"):
            missing.scale_missing_outcome_analysis({"phase": "originals_complete"}, Poison(), Poison(), Poison(), {})

    def test_six_cases_complete_pair_denominators_and_all_completions(self):
        fixture = self.fixture()
        before = copy.deepcopy(fixture)
        result = self.run_analysis(fixture)
        self.assertEqual(fixture, before)
        self.assertEqual((result["n_scheduled_pairs"], result["n_observed_pairs"], result["n_unavailable_pairs"]), (6, 4, 2))
        self.assertEqual((result["fresh_recovered"], result["repair_recovered"]), (2, 4))
        self.assertEqual(len(result["completion_sensitivity"]), 16)
        self.assertEqual(result["scheduled_difference_bounds"], [0, 4/6])
        self.assertEqual(result["amended_primary_decision"]["decision"], "inconclusive")
        expected = self.stats([(True, True), (False, True)]*2, 246600, 200)
        self.assertEqual(result["paired_value_recovery"], expected)

    def test_all_completion_bootstraps_match_frozen_method_in_frozen_order(self):
        fixture = self.fixture()
        # Place missing cases in the middle, so appended-case resampling would fail.
        fixture[1]["selected_case_ids"] = ["mock-0", "mock-4", "mock-1", "mock-2", "mock-5", "mock-3"]
        result = self.run_analysis(fixture)
        rows = {(r["case_id"], r["arm"]): r for r in fixture[2]}
        for completion in result["completion_sensitivity"]:
            assigned = {r["case_id"]: (r["fresh_success"], r["repair_success"]) for r in completion["assignments"]}
            pairs = [assigned[cid] if cid in assigned else tuple(missing.scale_missing_good(rows[cid, arm])
                     for arm in missing.SCALE_MISSING_ARMS) for cid in fixture[1]["selected_case_ids"]]
            expected = self.stats(pairs, 246600, 200)
            for key in ("exact_mcnemar_two_sided_p", "difference_percentage_points", "paired_bootstrap_95_interval"):
                self.assertEqual(completion[key], expected[key])

    def test_rejects_wrong_id_duplicate_partial_and_answer_imputation(self):
        for change in ("wrong_key", "duplicate", "partial", "answer", "missing_whole_pair", "empty_allowlist", "unmarked"):
            fixture = self.fixture()
            if change == "wrong_key": fixture[3][0]["request_key"] = "wrong"
            elif change == "duplicate": fixture[3].append(fixture[3][0])
            elif change == "partial": fixture[3].pop()
            elif change == "answer": fixture[2][-1]["response"] = {"fabricated": True}
            elif change == "missing_whole_pair": fixture[3][:] = fixture[3][2:]
            elif change == "empty_allowlist": fixture[3][:] = []
            else: fixture[2][-1]["outcome_unavailable"] = False
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.run_analysis(fixture)

    def test_mock_600_frozen_20k_draws_and_repair_claim_all_16(self):
        fixture = self.fixture(600)
        for row in fixture[2]:
            if not row["outcome_unavailable"]:
                row["verification"]["exact_fields"] = row["arm"] == "feedback_repair"
        result = self.run_analysis(fixture, draws=20000)
        self.assertEqual(result["paired_value_recovery"]["n_pairs"], 598)
        self.assertEqual(result["paired_value_recovery"]["paired_bootstrap_95_interval"], [1., 1.])
        self.assertTrue(result["amended_primary_decision"]["criterion_met"])
        self.assertEqual(result["amended_primary_decision"]["completions_meeting_criterion"], 16)
        self.assertEqual(result["scheduled_difference_bounds"], [596/600, 1.])


if __name__ == "__main__":
    unittest.main()
