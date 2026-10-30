import copy
import gzip
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace


def scale_test_namespace():
    namespace = {"__name__": "scale_mocked_test_helpers"}
    source = Path(__file__).parent
    for name in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py"):
        exec(compile((source / name).read_text(encoding="utf-8"), name, "exec"), namespace)
    namespace["scale_load_cores"](core_dir=source)
    return namespace


class ScaleExperimentTests(unittest.TestCase):
    def setUp(self):
        self.ns = scale_test_namespace()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cases, self.physical, self.events = {}, [], []
        self.wrong = {0, 1, 4, 5}
        self.pilot_wrong_tiers = {192}
        self.special = {}
        original_iterator = self.ns["scale_iter_cases"]
        def iterator(*args, **kwargs):
            for case in original_iterator(*args, **kwargs):
                self.cases[case["case_id"]] = case
                yield case
        self.ns["scale_iter_cases"] = iterator
        original_call = self.ns["scale_call_model"]
        def call(request, directory, live=False, timeout_s=900):
            return original_call(request, directory, live, timeout_s, _runner=self.runner)
        self.ns["scale_call_model"] = call
        self.pilot_cfg = {"n_cases": 2, "min_value_failures": 1}
        self.main_cfg = {"n_initial": 4, "chunk_size": 2, "collection_cap": 10, "target_failures": 3,
            "n_audit": 2, "bootstrap_draws": 200}

    def runner(self, request, timeout):
        self.physical.append(copy.deepcopy(request))
        case = self.cases[request["expected_case_ids"][0]]
        directory = self.root / "data" / "scale_v5" / ("pilot" if case["split"] == "pilot" else "main")
        self.assertTrue((directory / "protocol.json").exists())
        protocol = json.loads((directory / "protocol.json").read_text())
        for block in protocol["blocks"]:
            self.assertTrue((directory / block["source_path"]).exists())
            self.assertTrue(block["manifest"]["all_passed"])
        if case["split"] == "audit":
            self.assertTrue((directory / "selection.json").exists())
        answer = self.ns["scale_correct_response"](case)
        index = case["generation_index"]
        if request["stage"] == "generate" and request["sample"] == 0:
            if (case["split"] == "pilot" and case["base_shipments"] in self.pilot_wrong_tiers) or (case["split"] == "collection" and index in self.wrong):
                answer["answer"]["quantity_units"] += 17
            if case["split"] == "collection" and self.special.get(index) == "schema":
                answer["answer"]["quantity_units"] = "wrong type"
            if case["split"] == "collection" and self.special.get(index) == "citation":
                answer = self.ns["scale_correct_response"](case)
                answer["evidence"]["quantity_units"] = ["P05"]
        elif request["sample"] == 1 and index % 2:
            answer["answer"]["quantity_units"] += 4
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"results": [answer]})}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20}}]
        return SimpleNamespace(returncode=0, stdout="\n".join(map(json.dumps, events)), stderr="")

    def prepare(self):
        pilot = self.ns["scale_run_pilot"](self.pilot_cfg, self.root, live=True)
        self.assertEqual(pilot["selected_tier"], 192)
        return self.ns["scale_prepare_main"](self.main_cfg, self.root)

    def test_full_accumulation_paired_dispatch_exports_and_exact_replay(self):
        marker = self.root / "data" / "high_v4" / "marker.bin"
        marker.parent.mkdir(parents=True)
        marker.write_bytes(b"frozen historical files")
        prepared = self.prepare()
        self.assertEqual(sum(block["manifest"]["n_cases"] for block in prepared["blocks"]), 12)
        self.assertEqual(len(self.physical), 4)
        original = self.ns["scale_collect_originals"](self.root, live=True, progress=self.events.append)
        selection = original["selection"]
        self.assertEqual(selection["n_accrued_collection"], 6)
        self.assertEqual(selection["n_eligible_failures"], 4)
        self.assertEqual(len(selection["selected_case_ids"]), 3)
        self.assertEqual(len(selection["uncalled_collection_case_ids"]), 4)
        self.assertTrue(selection["target_reached"])
        self.assertTrue(all(request["sample"] == 0 and request["stage"] == "generate" for request in self.physical))
        result = self.ns["scale_run_interventions"](self.root, live=True, progress=self.events.append)
        self.assertEqual(len(result["interventions"]), 6)
        self.assertEqual(result["metrics"]["physical_cli_requests"], 14)
        dispatch = json.loads((prepared["directory"] / "dispatch.json").read_text())
        for start in range(0, len(dispatch["jobs"]), 4):
            wave = dispatch["jobs"][start:start + 4]
            for cid in {row["case_id"] for row in wave}:
                self.assertEqual({row["arm"] for row in wave if row["case_id"] == cid}, {"fresh_retry", "feedback_repair"})
        by_key = {self.ns["scale_request_key"](request): request for request in self.physical}
        originals = {row["candidate_id"]: row for row in original["candidates"]}
        for row in result["interventions"]:
            request = by_key[row["request_key"]]
            old = originals[row["original_candidate_id"]]
            self.assertEqual(request["case_inputs"], by_key[old["request_key"]]["case_inputs"])
            self.assertEqual(row["request_input_hash"], old["request_input_hash"])
            self.assertEqual(set(request["case_inputs"][0]), {"case_id", "task_instructions", "documents"})
            if row["arm"] == "fresh_retry":
                self.assertIsNone(request["feedback"])
            else:
                flags = request["feedback"][row["case_id"]]["validator_feedback"]
                self.assertEqual(flags, {"wrong_fields": ["quantity_units"], "schema_failed": False, "evidence_failed_fields": []})
        self.assertTrue(self.events)
        self.assertTrue(all(set(event) == {"arm", "case_id", "cached", "transport_failure"} for event in self.events))
        audit_ids = {row["case_id"] for row in original["candidates"] if row["split"] == "audit"}
        for path in (prepared["directory"] / "exports").rglob("*.jsonl.gz"):
            for row in self.ns["scale_read_records"](path):
                self.assertNotIn(row["case_id"], audit_ids)
                if "chosen" in row:
                    case = self.cases[row["case_id"]]
                    self.assertTrue(self.ns["scale_validate_answer"](case, row["chosen"])["accepted"])
                    self.assertFalse(self.ns["scale_validate_answer"](case, row["rejected"])["exact_fields"])
        count = len(self.physical)
        self.assertEqual(self.ns["scale_collect_originals"](self.root)["manifest"], original["manifest"])
        replay = self.ns["scale_run_interventions"](self.root)
        self.assertEqual(replay["manifest"], result["manifest"])
        self.assertEqual(replay["metrics"], result["metrics"])
        self.assertEqual(len(self.physical), count)
        self.assertEqual(marker.read_bytes(), b"frozen historical files")
        self.assertFalse(list((self.root / "data" / "scale_v5").rglob("*cases.jsonl")))
        for path in (self.root / "data" / "scale_v5").rglob("cache/*.json.gz"):
            raw = gzip.decompress(path.read_bytes())
            self.assertNotIn(b"\r\n", raw)
            self.assertIn(b'"documents"', raw)
            self.assertIn(b'"stdout"', raw)

    def test_cap_shortfall_and_nonvalue_failures_do_not_accrue(self):
        self.main_cfg["target_failures"] = 6
        self.special = {0: "schema", 1: "citation"}
        self.prepare()
        result = self.ns["scale_collect_originals"](self.root, live=True)
        self.assertEqual(result["selection"]["n_accrued_collection"], 10)
        self.assertEqual(result["selection"]["n_eligible_failures"], 2)
        self.assertEqual(result["selection"]["target_shortfall"], 4)
        self.assertFalse(result["selection"]["target_reached"])
        self.assertEqual(result["metrics"]["collection"]["error_categories"]["schema_failure"], 1)
        self.assertEqual(result["metrics"]["collection"]["error_categories"]["evidence_only_failure"], 1)

    def test_first_threshold_and_fixed_fallback(self):
        self.pilot_wrong_tiers = {128, 192}
        result = self.ns["scale_run_pilot"](self.pilot_cfg, self.root, live=True)
        self.assertEqual(result["selected_tier"], 128)
        self.assertTrue(result["threshold_met"])
        self.assertEqual(len(self.physical), 2)
        with tempfile.TemporaryDirectory() as other:
            self.root = Path(other)
            self.pilot_wrong_tiers = set()
            result = self.ns["scale_run_pilot"](self.pilot_cfg, self.root, live=True)
            self.assertEqual(result["selected_tier"], 192)
            self.assertFalse(result["threshold_met"])

    def test_empty_failure_pool_has_valid_empty_paired_results(self):
        self.wrong = set()
        self.prepare()
        self.ns["scale_collect_originals"](self.root, live=True)
        before = len(self.physical)
        result = self.ns["scale_run_interventions"](self.root, live=True)
        self.assertEqual(result["interventions"], [])
        self.assertEqual(result["metrics"]["n_selected"], 0)
        self.assertIsNone(result["metrics"]["paired_value_recovery"]["repair_minus_fresh_difference"])
        self.assertEqual(len(self.physical), before)

    def test_four_worker_failure_wave_stops_without_next_dispatch(self):
        prepared = self.prepare()
        original = self.runner
        rendezvous = threading.Barrier(4)
        def fail(request, timeout):
            rendezvous.wait(timeout=5)
            case = self.cases[request["expected_case_ids"][0]]
            if case["generation_index"] == 0:
                self.physical.append(copy.deepcopy(request))
                return SimpleNamespace(returncode=1, stdout=json.dumps({"type": "turn.failed", "error": {"message": "429"}}), stderr="")
            return original(request, timeout)
        self.runner = fail
        before = len(self.physical)
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_collect_originals"](self.root, live=True)
        self.assertEqual(len(self.physical) - before, 4)
        self.assertFalse((prepared["directory"] / "selection.json").exists())
        stop = json.loads((prepared["directory"] / "infrastructure_stop.json").read_text())
        self.assertEqual(len(stop["wave_results"]), 4)
        self.assertEqual(len(list((prepared["directory"] / "cache").glob("*.json.gz"))), 4)
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_collect_originals"](self.root)
        self.assertEqual(len(self.physical) - before, 4)

    def test_mutated_compressed_sources_refuse_before_any_calls(self):
        prepared = self.prepare()
        path = prepared["directory"] / prepared["blocks"][0]["source_path"]
        path.write_bytes(path.read_bytes() + b"tamper")
        count = len(self.physical)
        with self.assertRaises(ValueError):
            self.ns["scale_collect_originals"](self.root, live=True)
        self.assertEqual(len(self.physical), count)

    def test_ignored_smoke_and_checkpoint_sources_do_not_change_prior_freeze(self):
        prepared = self.ns["scale_prepare_pilot"](self.pilot_cfg, self.root)
        protocol = prepared["protocol"]
        old = self.ns["scale_make_cases"](1, 9999, tier=128, split="collection")[0]
        ignored = [self.root / "data" / "tmp" / "smoke" / "cases.jsonl",
            self.root / "data" / "historical" / "__pycache__" / "cases.jsonl",
            self.root / "data" / "historical" / ".ipynb_checkpoints" / "cases.jsonl"]
        for path in ignored:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(old) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(self.ns["scale_prior_source_paths"](self.root), [])
        replay = self.ns["scale_prepare_pilot"](self.pilot_cfg, self.root)
        self.assertEqual(replay["protocol"], protocol)
        self.assertEqual(self.physical, [])
        genuine = self.root / "data" / "historical" / "cases.jsonl"
        genuine.write_text(json.dumps(old) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(self.ns["scale_prior_source_paths"](self.root), [genuine])

    def test_existing_source_pack_must_match_every_generation_parameter(self):
        path = self.root / "sources" / "cases.jsonl.gz"
        spec = {"n": 1, "seed": 987, "tier": 128, "split": "collection", "start_index": 0}
        first = self.ns["scale_prepare_source"](path, spec)
        self.assertEqual(self.ns["scale_prepare_source"](path, spec), first)
        for field, changed in (("n", 2), ("seed", 988), ("tier", 192), ("split", "pilot"), ("start_index", 1)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.ns["scale_prepare_source"](path, {**spec, field: changed})
        self.assertEqual(self.physical, [])


if __name__ == "__main__":
    unittest.main()
