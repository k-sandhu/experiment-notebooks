"""Mocked continuation tests. No model subprocess or actual study writes."""
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import threading
from types import SimpleNamespace
import unittest

import scale_resume as resume


class ScaleResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / "data" / "scale_v5"
        self.main = self.data / "main"
        self.authoring = Path(__file__).parent
        self.ns = {"__name__": "mocked_scale_frozen"}
        for name in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py"):
            exec(compile((self.authoring / name).read_text(encoding="utf-8"), name, "exec"), self.ns)
        self.ns["scale_load_cores"](core_dir=self.authoring)
        names = ["scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py",
                 "collect_scale.py", *self.ns["SCALE_CORE_SHA256"]]
        hashes = {name: resume.scale_resume_sha(self.authoring / name) for name in names}
        snapshot = self.data / "source_snapshot"
        snapshot.mkdir(parents=True)
        for name in names:
            shutil.copyfile(self.authoring / name, snapshot / name)
        self.ns["SCALE_RUNTIME_SOURCE_HASHES"] = hashes
        self.ns["scale_write_json"](self.data / "source_freeze.json", {"protocol": "23-scale-v5", "source_sha256": hashes})
        self.cases, self.calls, self.events = {}, [], []
        self.audit_failure = False
        original_iter = self.ns["scale_iter_cases"]
        def iterator(*args, **kwargs):
            for case in original_iter(*args, **kwargs):
                self.cases[case["case_id"]] = case
                yield case
        self.ns["scale_iter_cases"] = iterator
        transport = self.ns["scale_call_model"]
        def call(request, cache_dir, live=False, timeout_s=900):
            return transport(request, cache_dir, live=live, timeout_s=timeout_s, _runner=self.runner)
        self.ns["scale_call_model"] = call
        self.ns["scale_run_pilot"]({"n_cases": 2, "min_value_failures": 1}, self.root, live=True)
        self.ns["scale_prepare_main"]({"n_initial": 4, "chunk_size": 4, "collection_cap": 12,
            "target_failures": 3, "n_audit": 2, "bootstrap_draws": 100}, self.root)
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_collect_originals"](self.root, live=True)
        self.stop = resume.scale_resume_read(self.main / "infrastructure_stop.json")
        failed = [r for r in self.stop["wave_results"] if r["row"]["transport_error"]]
        self.assertEqual(len(failed), 1)
        self.failed = failed[0]
        self.key = self.failed["request_key"]
        self.cache = self.main / "cache" / (self.key + ".json.gz")
        self.old_stop = (self.main / "infrastructure_stop.json").read_bytes()
        self.old_validation = (self.main / "original_chunks/chunk_000/run_validation.json").read_bytes()
        archived = self.main / "infrastructure_history/stop_001.json"
        archived.parent.mkdir()
        archived.write_bytes(self.old_stop)
        row = self.failed["row"]
        self.amendment = {"protocol": "23-scale-v5", "amendment_version": resume.SCALE_RESUME_VERSION,
            "declared_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_freeze_sha256": resume.scale_resume_sha(self.data / "source_freeze.json"),
            "original_stop_sha256": hashlib.sha256(self.old_stop).hexdigest(),
            "archived_stops": [{"path": "main/infrastructure_history/stop_001.json", "sha256": hashlib.sha256(self.old_stop).hexdigest()}],
            "reviewed_failures": [{"request_key": self.key, "cache_sha256": resume.scale_resume_sha(self.cache),
                "transport_error": row["transport_error"], "case_id": row["case_id"], "content_hash": row["content_hash"],
                "request_input_hash": row["request_input_hash"], "stop_sha256": hashlib.sha256(self.old_stop).hexdigest(),
                "profile": {"model": "gpt-6.1-sol", "reasoning_effort": "high", "stage": "generate", "sample": 0,
                            "protocol": "23-scale-v5", "timeout_s": 900}}]}
        gate = {"sha256": {name: resume.scale_resume_sha(self.data / name) for name in ("main/protocol.json", "main/allocation.json")}}
        self.ns["scale_write_json"](self.data / "main_start_declaration.json", gate)
        self.amendment["protected_files"] = [{"path": name, "sha256": resume.scale_resume_sha(self.data / name)}
            for name in ("main_start_declaration.json", "main/protocol.json", "main/allocation.json")]
        self.amendment["request_plans"] = [{"path": p.relative_to(self.data).as_posix(), "sha256": resume.scale_resume_sha(p)}
            for p in (self.main / "request_plans").glob("*.json")]
        self.amendment_path = self.data / "infrastructure_resume/amendment_001.json"
        self.refresh_inventory()
        self.write_amendment()

    def runner(self, request, timeout):
        self.calls.append(copy.deepcopy(request))
        case = self.cases[request["expected_case_ids"][0]]
        index = case["generation_index"]
        capacity = (case["split"] == "collection" and index == 4) or (self.audit_failure and case["split"] == "audit" and index % 2 == 0)
        if capacity:
            events = [{"type": "error", "message": resume.SCALE_RESUME_CAPACITY_MESSAGE},
                {"type": "turn.failed", "error": {"message": resume.SCALE_RESUME_CAPACITY_MESSAGE}}]
            return SimpleNamespace(returncode=1, stdout="\n".join(map(json.dumps, events)), stderr="")
        answer = self.ns["scale_correct_response"](case)
        if case["split"] == "pilot" or (case["split"] == "collection" and index in {0, 1, 5, 6}):
            answer["answer"]["quantity_units"] += 17
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"results": [answer]})}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20}}]
        return SimpleNamespace(returncode=0, stdout="\n".join(map(json.dumps, events)), stderr="")

    def write_amendment(self):
        self.amendment_path.parent.mkdir(parents=True, exist_ok=True)
        self.amendment_path.write_text(json.dumps(self.amendment), encoding="utf-8", newline="\n")

    def refresh_inventory(self):
        path = self.data / "infrastructure_resume/cache_inventory_001.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        requests = {p.stem.split(".")[0]: resume.scale_resume_sha(p) for p in (self.main / "cache").glob("*.json.gz")}
        path.write_text(json.dumps({"protocol": "23-scale-v5", "count": len(requests), "requests": requests}), encoding="utf-8", newline="\n")
        self.amendment["cache_inventory"] = {"path": "infrastructure_resume/cache_inventory_001.json", "sha256": resume.scale_resume_sha(path)}

    def install(self):
        return resume.scale_resume_install(self.root, self.amendment_path, self.ns)

    def inventory(self):
        return {p.relative_to(self.main).as_posix(): resume.scale_resume_sha(p) for p in self.main.rglob("*")
                if p.is_file() and "continuation_diagnostics" not in p.parts}

    def test_known_capacity_retained_healthy_continuation_budget_and_no_gold(self):
        old_cache = self.cache.read_bytes()
        before = len(self.calls)
        state = self.install()
        bundle = self.ns["scale_collect_originals"](self.root, live=True, progress=self.events.append)
        self.assertEqual(len(self.calls) - before, 2)  # Only previously uncalled audit cases.
        self.assertEqual(bundle["metrics"]["physical_cli_requests"], 10)
        self.assertEqual(bundle["selection"]["n_accrued_collection"], 8)
        self.assertEqual(bundle["selection"]["n_eligible_failures"], 4)
        self.assertEqual(len(bundle["selection"]["selected_case_ids"]), 3)
        self.assertNotIn(self.failed["row"]["candidate_id"], bundle["selection"]["eligible_candidate_ids"])
        failure = next(r for r in bundle["candidates"] if r["request_key"] == self.key)
        self.assertEqual(failure["error_kind"], "transport_failure")
        self.assertFalse(self.ns["scale_value_failure"](failure))
        self.assertIsNone(failure["response"])
        self.assertIn(self.key, state["bypassed_cached_failure_keys"])
        self.assertEqual(self.cache.read_bytes(), old_cache)
        self.assertEqual((self.main / "infrastructure_stop.json").read_bytes(), self.old_stop)
        self.assertEqual((self.main / "original_chunks/chunk_000/run_validation.json").read_bytes(), self.old_validation)
        self.assertTrue(state["diagnostic_paths"])
        self.assertEqual(sum(r["expected_case_ids"] == [self.failed["case_id"]] for r in self.calls), 1)
        for request in self.calls:
            self.assertIsNone(request["feedback"])
            self.assertEqual(set(request["case_inputs"][0]), {"case_id", "task_instructions", "documents"})
            self.assertEqual(request["stage"], "generate")
            self.assertEqual(request["sample"], 0)

    def test_offline_exact_replay_and_no_requery_after_completion(self):
        self.install()
        first = self.ns["scale_collect_originals"](self.root, live=True)
        before, calls = self.inventory(), len(self.calls)
        second = self.ns["scale_collect_originals"](self.root, live=False)
        self.assertEqual(first, second)
        self.assertEqual(before, self.inventory())
        self.assertEqual(len(self.calls), calls)
        with self.assertRaisesRegex(ValueError, "after originals_complete"):
            self.ns["scale_collect_originals"](self.root, live=True)

    def test_new_error_stops_and_never_overwrites_original_stop(self):
        state = self.install()
        self.audit_failure = True
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_collect_originals"](self.root, live=True)
        self.assertEqual((self.main / "infrastructure_stop.json").read_bytes(), self.old_stop)
        self.assertEqual(len(state["new_stop_paths"]), 1)
        new_stop = resume.scale_resume_read(state["new_stop_paths"][0])
        self.assertFalse(new_stop["phase_complete"])
        self.assertEqual(new_stop["jobs_submitted_this_dispatch"], 2)
        self.assertFalse((self.main / "original_manifest.json").exists())

    def test_wrong_hash_or_pending_refused_without_writes(self):
        before = self.inventory()
        self.amendment["reviewed_failures"][0]["cache_sha256"] = "0" * 64
        self.write_amendment()
        with self.assertRaisesRegex(ValueError, "cache bytes"):
            self.install()
        self.assertEqual(before, self.inventory())
        cached = resume.scale_resume_read(self.cache)
        cached["attempts"][0]["pending"] = True
        self.ns["scale_transport_atomic_json"](self.cache, cached)
        self.amendment["reviewed_failures"][0]["cache_sha256"] = resume.scale_resume_sha(self.cache)
        self.refresh_inventory()
        self.write_amendment()
        with self.assertRaisesRegex(ValueError, "pending"):
            self.install()

    def test_recorded_cache_deleted_after_install_never_requeried(self):
        state = self.install()
        self.cache.unlink()
        before = len(self.calls)
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_collect_originals"](self.root, live=True)
        self.assertEqual(len(self.calls), before)
        self.assertFalse(self.cache.exists())
        self.assertTrue(state["new_stop_paths"])

    def test_source_identity_and_profile_guards(self):
        for key, value in (("request_input_hash", "0" * 64), ("content_hash", "0" * 64)):
            old = self.amendment["reviewed_failures"][0][key]
            self.amendment["reviewed_failures"][0][key] = value
            self.write_amendment()
            with self.assertRaises(ValueError):
                self.install()
            self.amendment["reviewed_failures"][0][key] = old
        self.amendment["reviewed_failures"][0]["profile"]["sample"] = 1
        self.write_amendment()
        with self.assertRaisesRegex(ValueError, "profile"):
            self.install()

    def test_unfrozen_healthy_prefix_cache_substitution_refused(self):
        other = next(path for path in (self.main / "cache").glob("*.json.gz") if path != self.cache)
        before = other.read_bytes()
        other.write_bytes(before + b"changed bytes")
        with self.assertRaisesRegex(ValueError, "inventoried prior cache"):
            self.install()

    def test_protected_protocol_and_bound_plan_bytes_are_checked(self):
        for path in (self.main / "protocol.json", next((self.main / "request_plans").glob("*.json"))):
            old = path.read_bytes()
            path.write_bytes(old + b" ")
            before = self.inventory()
            with self.assertRaises(ValueError):
                self.install()
            self.assertEqual(before, self.inventory())
            path.write_bytes(old)

    def test_review_must_follow_all_inventoried_terminal_requests(self):
        self.amendment["declared_at_utc"] = "2000-01-01T00:00:00+00:00"
        self.write_amendment()
        with self.assertRaisesRegex(ValueError, "predates"):
            self.install()

    def test_completed_turn_nonfailure_exit_or_any_model_output_cannot_be_waived(self):
        original = self.cache.read_bytes()
        for field, value in (("events", [{"type": "turn.failed", "error": {"message": resume.SCALE_RESUME_CAPACITY_MESSAGE}},
                                         {"type": "turn.completed"}]),
                             ("return_code", 0), ("final_assistant_response", "usable or partial output"), ("parsed", {})):
            self.cache.write_bytes(original)
            cached = resume.scale_resume_read(self.cache)
            cached["attempts"][0][field] = value
            self.ns["scale_transport_atomic_json"](self.cache, cached)
            self.amendment["reviewed_failures"][0]["cache_sha256"] = resume.scale_resume_sha(self.cache)
            self.refresh_inventory()
            self.write_amendment()
            with self.assertRaises(ValueError, msg=field):
                self.install()

    def test_new_error_settles_four_job_wave_then_stops_and_archives_unique_receipts(self):
        state = self.install()
        jobs = [{"request_key": f"{i:064x}", "case": {"case_id": str(i)}, "arm": "original"} for i in range(8)]
        for repetition in range(2):
            barrier, calls = threading.Barrier(4), []
            def invoke(job):
                calls.append(job["case"]["case_id"])
                barrier.wait(timeout=5)
                return {"request_key": job["request_key"], "case_id": job["case"]["case_id"], "arm": "original",
                    "transport_error": "new unreviewed failure" if job["case"]["case_id"] == "0" else None}, {"cached_this_run": False}
            with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
                self.ns["scale_dispatch_waves"](jobs, invoke, self.main, 4)
            self.assertEqual(set(calls), {"0", "1", "2", "3"})
            receipt = resume.scale_resume_read(state["new_stop_paths"][-1])
            self.assertEqual(receipt["remaining_jobs_not_dispatched"], 4)
        self.assertEqual(len(set(state["new_stop_paths"])), 2)
        self.assertEqual((self.main / "infrastructure_stop.json").read_bytes(), self.old_stop)

    def test_reviewed_failure_must_really_come_from_cache(self):
        state = self.install()
        row, entry = copy.deepcopy(self.failed["row"]), copy.deepcopy(self.failed["ledger"])
        entry["cached_this_run"] = False
        job = {"request_key": self.key, "case": {"case_id": row["case_id"]}, "arm": "original"}
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_dispatch_waves"]([job], lambda _: (row, entry), self.main, 4)
        self.assertEqual(state["bypassed_cached_failure_keys"], [])

    def test_explicit_notebook_namespace_and_pilot_scope(self):
        embedded = {"__name__": "scale_notebook_reviewed_resume"}
        exec(compile(Path(resume.__file__).read_text(encoding="utf-8"), "embedded_resume", "exec"), embedded)
        self.assertNotIn("__file__", embedded)
        state = embedded["scale_resume_install"](self.root, self.amendment_path, namespace=self.ns)
        self.assertIs(embedded["scale_resume_install"](self.root, self.amendment_path, namespace=self.ns), state)
        row, entry = copy.deepcopy(self.failed["row"]), copy.deepcopy(self.failed["ledger"])
        entry["cached_this_run"] = True
        job = {"request_key": self.key, "case": {"case_id": row["case_id"]}, "arm": "original"}
        with self.assertRaises(self.ns["SCALE_InfrastructureStop"]):
            self.ns["scale_dispatch_waves"]([job], lambda _: (row, entry), self.data / "new_pilot", 4)
        self.assertEqual(state["bypassed_cached_failure_keys"], [])


if __name__ == "__main__":
    unittest.main()
