import hashlib
import json
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

import test_high_experiment as high_core_tests


class HighParallelTests(unittest.TestCase):
    def setUp(self):
        self.harness = high_core_tests.HighExperimentTests()
        self.harness.setUp()
        self.addCleanup(self.harness.temp.cleanup)
        self.ns = self.harness.ns
        self.root = self.harness.root
        self.ns["high_run_pilot"](self.harness.pilot_cfg, self.root, live=True)
        self.pilot_bytes = {path: path.read_bytes() for path in (self.root / "data" / "high_v4" / "pilot").rglob("*") if path.is_file()}
        exec(compile(Path(__file__).with_name("high_parallel.py").read_text(encoding="utf-8"), "high_parallel.py", "exec"), self.ns)

    def prepare(self):
        return self.ns["high_prepare_main"](self.harness.main_cfg, self.root)

    def test_only_infrastructure_metadata_and_bounded_config_change(self):
        cfg = self.ns["high_config"]()
        self.assertEqual(cfg["protocol"], "23-high-v4e")
        self.assertEqual(cfg["max_workers"], 2)
        for field, value in self.ns["HIGH_MAIN_CONFIG"].items():
            if field not in ("protocol", "max_workers"):
                self.assertEqual(cfg[field], value)
        for bad in (0, 3, 4, True):
            with self.assertRaises(ValueError):
                self.ns["high_config"]({"max_workers": bad})
        with self.assertRaises(ValueError):
            self.ns["high_config"](pilot=True)
        prepared = self.prepare()
        protocol = prepared["protocol"]
        self.assertEqual(protocol["max_workers"], 2)
        self.assertIn("At most 2", protocol["infrastructure_stop_policy"])
        self.assertEqual(protocol["protocol_dispatch_fork"]["maximum_wave_size"], 2)
        for name, frozen in self.ns["HIGH_PARALLEL_CORE_SOURCE_SHA256"].items():
            self.assertEqual(hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest(), frozen)

    def test_success_preserves_exact_core_rows_and_paired_design(self):
        prepared = self.prepare()
        originals = self.ns["high_collect_originals"](self.root, live=True)
        result = self.ns["high_run_interventions"](self.root, live=True)
        self.assertEqual(result["metrics"]["paired_value_recovery"]["both_success"], 3)
        self.assertEqual(result["metrics"]["paired_value_recovery"]["repair_only"], 1)
        self.assertEqual(len(result["interventions"]), 8)
        jobs = [self.ns["high_make_job"](case) for case in originals["cases"]]
        expected_rows, expected_ledger = self.ns["HIGH_PARALLEL_CORE_RUN_JOBS"](
            jobs, prepared["directory"], {**prepared["config"], "max_workers": 1}, False)
        self.assertEqual(expected_rows, originals["candidates"])
        before = len(self.harness.physical)
        replay = self.ns["high_collect_originals"](self.root)
        self.assertEqual(replay["manifest"], originals["manifest"])
        replay = self.ns["high_run_interventions"](self.root)
        self.assertEqual(replay["metrics"], result["metrics"])
        self.assertEqual(len(self.harness.physical), before)
        for path, frozen in self.pilot_bytes.items():
            self.assertEqual(path.read_bytes(), frozen)

    def failing_wave(self, failures):
        prepared = self.prepare()
        original_runner = self.harness.runner
        rendezvous = threading.Barrier(2)
        active = [0, 0]
        lock = threading.Lock()
        def run(request, timeout):
            with lock:
                active[0] += 1
                active[1] = max(active)
            rendezvous.wait(timeout=5)
            try:
                case = self.harness.cases[request["expected_case_ids"][0]]
                index = self.harness.collection_index(case)
                if index in failures:
                    self.harness.physical.append(request)
                    return SimpleNamespace(returncode=1, stdout=json.dumps({"type": "turn.failed", "error": {"message": "429 service failure"}}), stderr="")
                return original_runner(request, timeout)
            finally:
                with lock:
                    active[0] -= 1
        self.harness.runner = run
        before = len(self.harness.physical)
        with self.assertRaisesRegex(RuntimeError, "V4e infrastructure stop"):
            self.ns["high_collect_originals"](self.root, live=True)
        self.assertEqual(len(self.harness.physical) - before, 2)
        self.assertEqual(active[1], 2)
        directory = prepared["directory"]
        stop = json.loads((directory / "infrastructure_stop_parallel.json").read_text(encoding="utf-8"))
        self.assertEqual(stop["remaining_jobs_not_dispatched"], 4)
        self.assertEqual(len(stop["wave_results"]), 2)
        self.assertEqual(len(stop["failed_request_keys"]), len(failures))
        self.assertFalse((directory / "infrastructure_stop.json").exists())
        self.assertEqual(len(list(directory.glob("infrastructure_stop_single_*.json"))), len(failures))
        self.assertFalse((directory / "selection.json").exists())
        for row in stop["wave_results"]:
            self.assertIsNotNone(row["row"])
            raw = json.loads((directory / "cache" / (row["request_key"] + ".json")).read_text(encoding="utf-8"))
            self.assertFalse(raw["attempts"][-1]["pending"])
            self.assertTrue(raw["attempts"][-1]["stdout"])
        count = len(self.harness.physical)
        with self.assertRaisesRegex(RuntimeError, "V4e infrastructure stop"):
            self.ns["high_collect_originals"](self.root)
        self.assertEqual(len(self.harness.physical), count)

    def test_one_failure_waits_for_sibling_and_stops_next_wave(self):
        self.failing_wave({0})

    def test_two_failures_preserve_both_raw_records_without_stop_race(self):
        self.failing_wave({0, 1})

    def test_offline_missing_cache_stops_without_model_calls(self):
        prepared = self.prepare()
        before = len(self.harness.physical)
        with self.assertRaisesRegex(RuntimeError, "V4e infrastructure stop"):
            self.ns["high_collect_originals"](self.root)
        self.assertEqual(len(self.harness.physical), before)
        stop = json.loads((prepared["directory"] / "infrastructure_stop_parallel.json").read_text(encoding="utf-8"))
        self.assertEqual(len(stop["wave_results"]), 2)
        self.assertTrue(all(row["exception"] for row in stop["wave_results"]))
        self.assertEqual(stop["remaining_jobs_not_dispatched"], 4)


if __name__ == "__main__":
    unittest.main()
