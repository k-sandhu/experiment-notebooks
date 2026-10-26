import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


HIGH_TEST_NS = {}
exec(compile(Path(__file__).with_name("high_transport.py").read_text(encoding="utf-8"), "high_transport.py", "exec"), HIGH_TEST_NS)


class HighTransportTests(unittest.TestCase):
    def setUp(self):
        self.ns = HIGH_TEST_NS
        self.case = {"case_id": "opaque", "task_instructions": "Extract", "documents": "source only"}
        self.request = self.ns["high_make_request"]("gpt-6.1-sol", "generate", [self.case])

    def runner(self, request, timeout):
        self.assertEqual(timeout, 900)
        payload = {"results": [{"case_id": "opaque", "answer": {}, "evidence": {}}]}
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(payload)}},
                  {"type": "turn.completed", "usage": {"input_tokens": 11, "output_tokens": 3}}]
        return SimpleNamespace(returncode=0, stdout="\n".join(map(json.dumps, events)), stderr="")

    def test_profile_inputs_and_full_hash(self):
        self.assertEqual(self.request["reasoning_effort"], "high")
        self.assertIn('model_reasoning_effort="high"', self.request["cli_options"])
        for cases in ([self.case, self.case], [{**self.case, "gold": {}}]):
            with self.assertRaises(ValueError):
                self.ns["high_make_request"]("gpt-6.1-sol", "generate", cases)
        changed = copy.deepcopy(self.request)
        changed["sample"] = 1
        self.assertNotEqual(self.ns["high_request_key"](changed), self.ns["high_request_key"](self.request))
        with self.assertRaises(ValueError):
            self.ns["high_make_request"]("gpt-6-luna", "generate", [self.case])

    def test_feedback_is_exact_case_generic_fields(self):
        flags = {"wrong_fields": ["quantity_units"], "schema_failed": False, "evidence_failed_fields": []}
        feedback = {"opaque": {"original_output": {}, "validator_feedback": flags}}
        self.ns["high_make_request"]("gpt-6.1-sol", "repair", [self.case], feedback=feedback)
        for wrong in ({**feedback, "unrelated": {"gold": 17}}, {"opaque": {"original_output": {}, "validator_feedback": {**flags, "gold": 17}}}):
            with self.assertRaises(ValueError):
                self.ns["high_make_request"]("gpt-6.1-sol", "repair", [self.case], feedback=wrong)

    def test_offline_pending_and_no_implicit_retries(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                self.ns["high_call_model"](self.request, folder)
            first = self.ns["high_call_model"](self.request, folder, live=True, _runner=self.runner)
            self.assertFalse(first["cached"])
            replay = self.ns["high_call_model"](self.request, folder, live=True, _runner=lambda *a: self.fail("requeried"))
            self.assertTrue(replay["cached"])
            self.assertEqual(first["stdout"], replay["stdout"])
            cache = Path(folder) / (first["key"] + ".json")
            record = json.loads(cache.read_text())
            record["attempts"][-1]["pending"] = True
            self.ns["high_transport_atomic_json"](cache, record)
            for live in (False, True):
                with self.assertRaises(self.ns["HIGH_IncompleteCacheError"]):
                    self.ns["high_call_model"](self.request, folder, live=live, _runner=self.runner)

    def test_warnings_reconnect_and_terminal_failure(self):
        for warning, failed in (("CLI warning", False), ("Reconnecting retry 1", False), ("terminal", True)):
            def run(req, timeout):
                proc = self.runner(req, timeout)
                event = {"type": "turn.failed" if failed else "error", "message": warning}
                proc.stdout += "\n" + json.dumps(event)
                return proc
            row = self.ns["high_transport_attempt_record"](self.request, 900, run)
            self.assertEqual(bool(row["error"]), failed)
            self.assertEqual(bool(row["observed_reconnect_events"]), "Reconnecting" in warning)
            self.assertIsNotNone(row["parsed"])
            self.assertTrue(row["cli_error_events"])

    def test_timeout_profile_is_frozen(self):
        with tempfile.TemporaryDirectory() as folder:
            altered = copy.deepcopy(self.request)
            altered["runner_limits"]["timeout_s"] = 20
            with self.assertRaises(ValueError):
                self.ns["high_call_model"](altered, folder, timeout_s=20)

    def test_missing_successful_completion_is_failure(self):
        def run(request, timeout):
            proc = self.runner(request, timeout)
            proc.stdout = proc.stdout.splitlines()[0]
            return proc
        row = self.ns["high_transport_attempt_record"](self.request, 900, run)
        self.assertIn("turn.completed", row["error"])
        self.assertIsNotNone(row["parsed"])
        self.assertEqual(self.request["protocol"], "23-high-v4b")


if __name__ == "__main__":
    unittest.main()
