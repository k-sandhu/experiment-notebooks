import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


def high_test_namespace():
    namespace = {"__name__": "high_test_helpers"}
    for filename in ("high_transport.py", "high_fixtures.py", "high_material_audit.py", "high_experiment.py"):
        exec(compile(Path(__file__).with_name(filename).read_text(encoding="utf-8"), filename, "exec"), namespace)
    return namespace


class HighExperimentTests(unittest.TestCase):
    def setUp(self):
        self.ns = high_test_namespace()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = {}
        self.requests = []
        self.physical = []
        original_make = self.ns["high_make_cases"]
        def make(*args, **kwargs):
            rows = original_make(*args, **kwargs)
            self.cases.update({r["case_id"]: r for r in rows})
            return rows
        self.ns["high_make_cases"] = make
        original_call = self.ns["high_call_model"]
        def call(request, directory, live=False, timeout_s=900):
            self.requests.append(copy.deepcopy(request))
            return original_call(request, directory, live, timeout_s, _runner=self.runner)
        self.ns["high_call_model"] = call
        self.pilot_cfg = {"n_cases": 2, "min_value_failures": 1}
        self.main_cfg = {"n_initial": 6, "n_expansion": 3, "n_audit": 2, "max_selected": 4,
                         "expand_below_value_failures": 3, "bootstrap_draws": 200}

    def runner(self, request, timeout):
        self.physical.append(copy.deepcopy(request))
        case = self.cases[request["expected_case_ids"][0]]
        base = self.root / "data" / "high_v4" / ("pilot" if case["split"] == "pilot" else "main")
        self.assertTrue((base / "protocol.json").exists())
        audit = json.loads((base / "material_audit.json").read_text(encoding="utf-8"))
        self.assertTrue(audit["passed"])
        if case["split"] == "audit":
            self.assertTrue((base / "selection.json").exists())
        answer = self.ns["high_correct_response"](case)
        if request["stage"] == "generate" and request["sample"] == 0:
            if (case["split"] == "pilot" and case["level"] >= 2) or (case["split"] == "collection" and self.collection_index(case) in (0, 1, 6, 7)):
                answer["answer"]["quantity_units"] += 17
        elif request["sample"] == 1 and self.collection_index(case) == 1:
            answer["answer"]["quantity_units"] += 4
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"results": [answer]})}},
                  {"type": "turn.completed", "usage": {"input_tokens": 101, "output_tokens": 31}}]
        return SimpleNamespace(returncode=0, stdout="\n".join(map(json.dumps, events)), stderr="")

    def collection_index(self, case):
        allocation_path = self.root / "data" / "high_v4" / "main" / "allocation.json"
        if not allocation_path.exists() or case["split"] != "collection":
            return -1
        allocation = json.loads(allocation_path.read_text(encoding="utf-8"))
        return (allocation["initial_case_ids"] + allocation["expansion_case_ids"]).index(case["case_id"])

    def prepare(self):
        pilot = self.ns["high_run_pilot"](self.pilot_cfg, self.root, live=True)
        self.assertEqual(pilot["selected_level"], 2)
        self.assertTrue(pilot["threshold_met"])
        return self.ns["high_prepare_main"](self.main_cfg, self.root)

    def test_primary_eligibility_excludes_schema_transport_and_evidence(self):
        case = self.ns["high_make_cases"](1, 123)[0]
        correct = self.ns["high_correct_response"](case)
        wrong = copy.deepcopy(correct)
        wrong["answer"]["quantity_units"] += 1
        verification = self.ns["high_validate_answer"](case, wrong)
        row = {"response": wrong, "transport_error": None, "verification": verification}
        self.assertTrue(self.ns["high_value_failure"](row))
        self.assertFalse(self.ns["high_value_failure"]({**row, "transport_error": "failed"}))
        self.assertFalse(self.ns["high_value_failure"]({**row, "verification": {**verification, "valid_schema": False}}))
        correct["evidence"]["quantity_units"] = ["P99"]
        row["response"] = correct
        row["verification"] = self.ns["high_validate_answer"](case, correct)
        self.assertFalse(self.ns["high_value_failure"](row))
        self.assertTrue(self.ns["high_value_success"](row))

    def test_pilot_preflight_stop_and_replay(self):
        first = self.ns["high_run_pilot"](self.pilot_cfg, self.root, live=True)
        self.assertEqual(first["selected_level"], 2)
        self.assertEqual(first["ladder"]["physical_cli_requests"], 4)
        self.assertEqual(len(first["ladder"]["uncalled_potential_case_ids"]), 4)
        count = len(self.physical)
        replay = self.ns["high_run_pilot"](self.pilot_cfg, self.root)
        self.assertEqual(replay["ladder"], first["ladder"])
        self.assertEqual(len(self.physical), count)

    def test_full_phase_boundary_pairing_exports_and_replay(self):
        old = self.root / "data" / "sol_v3" / "unchanged.json"
        old.parent.mkdir(parents=True)
        old.write_bytes(b"historical bytes\n")
        prepared = self.prepare()
        self.assertEqual(len(prepared["cases"]), 11)
        self.assertEqual(len(self.physical), 4)
        originals = self.ns["high_collect_originals"](self.root, live=True)
        self.assertTrue(originals["selection"]["expanded"])
        self.assertEqual(len(originals["selection"]["selected_case_ids"]), 4)
        self.assertEqual(originals["metrics"]["collection"]["n_attempted_cases"], 9)
        self.assertFalse(any(r["stage"] == "repair" or r["sample"] == 1 for r in self.physical))
        out = self.ns["high_run_interventions"](self.root, live=True)
        self.assertEqual(len(out["interventions"]), 8)
        self.assertEqual(out["metrics"]["paired_value_recovery"]["repair_only"], 1)
        self.assertEqual(out["metrics"]["paired_value_recovery"]["both_success"], 3)
        self.assertEqual(out["metrics"]["physical_cli_requests"], 19)
        # Model-visible inputs are exactly identical across all paired arms.
        original_requests = {r["expected_case_ids"][0]: r for r in self.physical if r["stage"] == "generate" and r["sample"] == 0}
        for request in self.physical:
            cid = request["expected_case_ids"][0]
            self.assertEqual(request["case_inputs"], original_requests[cid]["case_inputs"])
            self.assertEqual(set(request["case_inputs"][0]), {"case_id", "task_instructions", "documents"})
            self.assertEqual(request["case_inputs"][0]["documents"], self.cases[cid]["document"])
            if request["stage"] == "repair":
                feedback = request["feedback"][cid]
                self.assertEqual(set(feedback["validator_feedback"]), {"wrong_fields", "schema_failed", "evidence_failed_fields"})
                self.assertEqual(feedback["validator_feedback"]["wrong_fields"], ["quantity_units"])
            elif request["sample"] == 1:
                self.assertIsNone(request["feedback"])
        audit_ids = {c["case_id"] for c in out["cases"] if c["split"] == "audit"}
        for arm, files in out["exports"].items():
            for rows in files.values():
                self.assertFalse({r["case_id"] for r in rows} & audit_ids)
            for pair in files["value_preference_pairs"]:
                case = self.cases[pair["case_id"]]
                self.assertTrue(self.ns["high_validate_answer"](case, pair["chosen"])["accepted"])
                self.assertFalse(self.ns["high_validate_answer"](case, pair["rejected"])["exact_fields"])
        before = len(self.physical)
        replay = self.ns["high_collect_originals"](self.root)
        self.assertEqual(replay["manifest"], originals["manifest"])
        replay = self.ns["high_run_interventions"](self.root)
        self.assertEqual(replay["manifest"], out["manifest"])
        self.assertEqual(replay["metrics"], out["metrics"])
        self.assertEqual(len(self.physical), before)
        self.assertEqual(old.read_bytes(), b"historical bytes\n")
        for path in (self.root / "data" / "high_v4").rglob("*.json*"):
            self.assertNotIn(b"\r\n", path.read_bytes())

    def test_unused_expansion_excluded_and_frozen_inputs(self):
        self.main_cfg["expand_below_value_failures"] = 2
        prepared = self.prepare()
        out = self.ns["high_collect_originals"](self.root, live=True)
        self.assertFalse(out["selection"]["expanded"])
        self.assertEqual(len(out["cases"]), 8)
        self.assertEqual(len(out["selection"]["unused_expansion_case_ids"]), 3)
        uncalled = set(out["selection"]["unused_expansion_case_ids"])
        self.assertFalse(uncalled & {r["expected_case_ids"][0] for r in self.physical})
        with self.assertRaises(ValueError):
            self.ns["high_prepare_main"]({**self.main_cfg, "seed_initial": 911}, self.root)

    def test_statistics_and_empty_paired_cohort(self):
        stats = self.ns["high_paired_statistics"]([(False, True)] * 4, 9, 200)
        self.assertEqual(stats["repair_minus_fresh_difference"], 1)
        self.assertEqual(stats["paired_bootstrap_95_interval"], [1, 1])
        self.assertEqual(stats["exact_mcnemar_two_sided_p"], .125)
        stats = self.ns["high_paired_statistics"]([(False, True)] * 3 + [(True, False)], 9, 200)
        self.assertEqual(stats["exact_mcnemar_two_sided_p"], .625)
        self.assertIsNone(self.ns["high_paired_statistics"]([], 9, 200)["repair_minus_fresh_difference"])

    def test_transport_stop_prevents_remaining_dispatch_and_ladder_selection(self):
        def fail(request, timeout):
            self.physical.append(copy.deepcopy(request))
            return SimpleNamespace(returncode=1, stdout=json.dumps({"type": "turn.failed", "error": {"message": "429 service failure"}}), stderr="")
        self.runner = fail
        with self.assertRaisesRegex(RuntimeError, "infrastructure stop"):
            self.ns["high_run_pilot"](self.pilot_cfg, self.root, live=True)
        self.assertEqual(len(self.physical), 1)
        folder = self.root / "data" / "high_v4" / "pilot"
        self.assertFalse((folder / "ladder.json").exists())
        record = json.loads((folder / "level_1" / "infrastructure_stop.json").read_text(encoding="utf-8"))
        self.assertFalse(record["phase_complete"])
        self.assertEqual(record["remaining_requests_not_dispatched"], 1)
        self.assertTrue((folder / "level_1" / "cache" / (record["request_key"] + ".json")).exists())
        with self.assertRaisesRegex(RuntimeError, "infrastructure stop"):
            self.ns["high_run_pilot"](self.pilot_cfg, self.root)
        self.assertEqual(len(self.physical), 1)


if __name__ == "__main__":
    unittest.main()
