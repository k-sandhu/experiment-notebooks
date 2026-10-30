"""Mock-only amendment-003 tests. No study artifacts or model calls."""
import copy
from itertools import product
from pathlib import Path
import unittest
import scale_missing_outcomes_003 as missing


class MissingOutcome003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = {"__name__": "mock_frozen_statistics"}
        exec(compile(Path(__file__).with_name("scale_experiment.py").read_text(encoding="utf-8"),
                     "scale_experiment.py", "exec"), ns)
        cls.stats = staticmethod(ns["scale_paired_statistics"])

    def fixture(self, pairs=None, unknown=None):
        pairs = pairs if pairs is not None else [(True, True), (False, True)]*3
        unknown = unknown if unknown is not None else {(i, arm) for i in (1, 4) for arm in missing.SCALE_MISSING_ARMS}
        ids = [f"mock-{i}" for i in range(len(pairs))]
        rows, unavailable = [], []
        for i, pair in enumerate(pairs):
            for arm, success in zip(missing.SCALE_MISSING_ARMS, pair):
                absent = (i, arm) in unknown
                row = {"case_id": ids[i], "arm": arm, "request_key": ids[i]+arm,
                       "response": None if absent else {"mock": True},
                       "transport_error": "controller interrupted; outcome unavailable" if absent else None,
                       "outcome_unavailable": absent,
                       "verification": {"valid_schema": not absent, "exact_fields": success and not absent}}
                rows.append(row)
                if absent: unavailable.append({key: row[key] for key in ("case_id", "arm", "request_key")})
        return {"phase": "interventions_complete"}, {"selected_case_ids": ids}, rows, unavailable

    def analyze(self, fixture=None, draws=100, envelope=True):
        return missing.scale_missing_outcome_analysis(*(fixture or self.fixture()),
            {"bootstrap_seed":246600, "bootstrap_draws":draws}, self.stats, envelope)

    def test_phase_gate_precedes_all_outcome_iteration(self):
        class Poison:
            def __iter__(self): raise AssertionError("Early efficacy access")
            def __getitem__(self, key): raise AssertionError("Early selection access")
        with self.assertRaisesRegex(ValueError, "interventions_complete"):
            missing.scale_missing_outcome_analysis({"phase":"originals_complete"}, Poison(), Poison(), Poison(), {})

    def test_completeness_determinism_no_mutation_and_all_256_assignments(self):
        f = self.fixture([(False, True)]*10, {(i, arm) for i in (1, 3, 6, 8) for arm in missing.SCALE_MISSING_ARMS})
        before = copy.deepcopy(f)
        a, b = self.analyze(f), self.analyze(f)
        self.assertEqual(f, before)
        self.assertEqual(a, b)
        self.assertEqual((a["n_scheduled_pairs"], a["n_observed_pairs"], a["n_unavailable_pairs"], a["n_unavailable_outcomes"]), (10, 6, 4, 8))
        self.assertEqual(a["n_wholly_unavailable_pairs"], 4)
        self.assertEqual(a["n_completions"], 256)
        self.assertEqual({r["completion_id"] for r in a["completion_sensitivity"]},
                         {"".join(bits) for bits in product("01", repeat=8)})
        self.assertTrue(all(r["hypothetical_only"] and len(r["hypothetical_cell_assignments"]) == 8 for r in a["completion_sensitivity"]))
        self.assertEqual(a["scheduled_difference_bounds"], [2/10, 1.])

    def test_all_completion_bootstraps_match_frozen_method_whole_and_partial(self):
        for unknown in ({(i, arm) for i in (1, 4) for arm in missing.SCALE_MISSING_ARMS},
                        {(1,"fresh_retry"), (2,"feedback_repair"), (4,"fresh_retry"), (5,"feedback_repair")}):
            f = self.fixture([(True, False), (False, True), (True, False), (False, True), (True, True), (False, False)], unknown)
            f[1]["selected_case_ids"] = ["mock-4", "mock-0", "mock-5", "mock-1", "mock-3", "mock-2"]
            a = self.analyze(f)
            rows = {(r["case_id"],r["arm"]):r for r in f[2]}
            for row in a["completion_sensitivity"]:
                assigned = {(r["case_id"],r["arm"]):r["success"] for r in row["hypothetical_cell_assignments"]}
                pairs = [tuple(assigned[cid,arm] if (cid,arm) in assigned else missing.scale_missing_good(rows[cid,arm])
                               for arm in missing.SCALE_MISSING_ARMS) for cid in f[1]["selected_case_ids"]]
                expected = self.stats(pairs,246600,100)
                for key in ("exact_mcnemar_two_sided_p", "difference_percentage_points", "paired_bootstrap_95_interval"):
                    self.assertEqual(row[key], expected[key])
            for index, endpoint in enumerate(("lower_endpoint", "upper_endpoint")):
                values = [r["paired_bootstrap_95_interval"][index] for r in a["completion_sensitivity"]]
                self.assertEqual(a["completion_bootstrap_endpoint_ranges"][endpoint], [min(values),max(values)])

    def test_partial_pair_observed_counterparts_remain_fixed_and_bounds_are_exact(self):
        f = self.fixture([(False, True), (True, False), (True, True), (False, False)],
                         {(0,"fresh_retry"), (1,"feedback_repair"), (2,"fresh_retry"), (3,"feedback_repair")})
        a = self.analyze(f)
        self.assertEqual((a["n_observed_pairs"],a["n_incomplete_pairs"],a["n_unavailable_outcomes"],a["n_wholly_unavailable_pairs"]), (0,4,4,0))
        self.assertEqual(a["paired_value_recovery"]["n_pairs"],0)
        for row in a["completion_sensitivity"]:
            assignment = {r["case_id"]:r for r in row["assignments"]}
            self.assertTrue(assignment["mock-0"]["repair_success"])
            self.assertTrue(assignment["mock-1"]["fresh_success"])
            self.assertTrue(assignment["mock-2"]["repair_success"])
            self.assertFalse(assignment["mock-3"]["fresh_success"])
        values = [r["repair_minus_fresh_difference"] for r in a["completion_sensitivity"]]
        self.assertEqual(a["scheduled_difference_bounds"], [min(values),max(values)])
        self.assertEqual(a["scheduled_difference_bounds"], [-.25,.75])

    def test_dynamic_zero_one_two_four_missing_pairs(self):
        for m in (0,1,2,4):
            unknown = {(i,arm) for i in range(m) for arm in missing.SCALE_MISSING_ARMS}
            a = self.analyze(self.fixture([(False,True)]*8, unknown))
            self.assertEqual((a["n_scheduled_pairs"],a["n_observed_pairs"],a["n_unavailable_pairs"],a["n_unavailable_outcomes"],a["n_completions"]), (8,8-m,m,2*m,4**m))

    def test_unknown_identity_validation_and_no_imputation(self):
        for change in ("wrong_key","wrong_case","wrong_arm","duplicate","empty","unmarked","answer","no_error","extra_row","missing_row"):
            f=self.fixture()
            if change=="wrong_key": f[3][0]["request_key"]="wrong"
            elif change=="wrong_case": f[3][0]["case_id"]="unexpected"
            elif change=="wrong_arm": f[3][0]["arm"]="unexpected"
            elif change=="duplicate": f[3].append(f[3][0])
            elif change=="empty": f[3].clear()
            elif change=="unmarked": f[2][2]["outcome_unavailable"]=False
            elif change=="answer": f[2][2]["response"]={"imputed":True}
            elif change=="no_error": f[2][2]["transport_error"]=None
            elif change=="extra_row": f[2].append(copy.deepcopy(f[2][0]))
            elif change=="missing_row": f[2].pop()
            with self.subTest(change=change), self.assertRaises(ValueError): self.analyze(f)

    def test_stronger_weaker_flat_and_near_boundary_claims(self):
        unknown={(i,arm) for i in range(4) for arm in missing.SCALE_MISSING_ARMS}
        patterns={"stronger":([(False,True)]*40,True), "weaker":([(True,False)]*40,False),
                  "flat":([(True,True)]*40,False), "boundary":([(False,True)]*10,False)}
        for label,(pairs,expected) in patterns.items():
            with self.subTest(label=label):
                a=self.analyze(self.fixture(pairs,unknown),envelope=False)
                self.assertEqual(a["amended_primary_decision"]["criterion_met"],expected)
                self.assertEqual(a["amended_primary_decision"]["completions_meeting_criterion"],sum(r["primary_criterion_met"] for r in a["completion_sensitivity"]))
                if label=="boundary":
                    self.assertLess(a["paired_value_recovery"]["exact_mcnemar_two_sided_p"],.05)
                    self.assertGreater(a["amended_primary_decision"]["completions_meeting_criterion"],0)

    def test_mock_600_pairs_20000_frozen_draws(self):
        a=self.analyze(self.fixture([(False,True)]*600,{(i,arm) for i in (1,7,29,502) for arm in missing.SCALE_MISSING_ARMS}),draws=20000)
        self.assertEqual((a["n_observed_pairs"],a["n_unavailable_outcomes"],a["n_completions"]),(596,8,256))
        self.assertEqual((a["bootstrap_seed"],a["bootstrap_draws"]),(246600,20000))
        self.assertEqual(a["paired_value_recovery"]["paired_bootstrap_95_interval"],[1.,1.])
        self.assertEqual(a["scheduled_difference_bounds"],[592/600,1.])
        self.assertEqual(a["amended_primary_decision"]["completions_meeting_criterion"],256)


if __name__=="__main__": unittest.main()
