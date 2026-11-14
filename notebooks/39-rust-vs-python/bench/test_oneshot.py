import datetime
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bench import config as C
from bench import oneshot as O

class OneShotTests(unittest.TestCase):
    def test_prompt(self):
        text = O.prompt_for("heat", "plain")
        for name in ("language", "language_block", "file", "spec", "examples"):
            self.assertNotIn("{" + name + "}", text)
        self.assertIn("Example `s1` input:", text)
        self.assertNotIn("Example `s1` input:", O.prompt_for("heat", "plain", limit=0))
        self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"))
        self.assertNotIn("\r", text)

    def test_extract(self):
        self.assertEqual(O.extract("```python\nprint(1)\n```\n")[0], "print(1)\n")
        code, meta = O.extract("```\na\n```\n~~~python\nlonger\n~~~\n")
        self.assertEqual((code, meta["blocks"]), ("longer\n", 2))
        self.assertEqual(O.extract("no code")[1]["status"], "no_code_block")
        self.assertTrue(O.extract("")[1]["empty"])

    def test_hash_and_skip(self):
        request = O.request_for("sol", "heat", "plain")
        self.assertEqual(O.request_hash(request), "cced574d20a4478655b4d474e41aad2bb57e0f9dd4c910c653e159795442077e")
        with tempfile.TemporaryDirectory(dir=C.ROOT) as root:
            with patch.object(C, "ONESHOT", Path(root)):
                path = Path(root) / "calls/sol/heat.plain.json"
                path.parent.mkdir(parents=True)
                O.write_json(path, {"request_hash": O.request_hash(request)})
                with patch.object(O.shutil, "which", side_effect=AssertionError("must not call CLI")):
                    O.run_one("sol", "heat", "plain")

    def test_empty_tools_argument(self):
        flags = O.flags_for("haiku")
        self.assertEqual(flags[flags.index("--tools") + 1], "")
        import subprocess
        quoted = subprocess.list2cmdline(["claude.cmd"] + flags)
        self.assertIn('--tools ""', quoted)
        with patch.object(O.os, "name", "nt"):
            self.assertIn('--tools ""', O.shim_command(["claude.cmd"] + flags))

class ProtocolV2Tests(unittest.TestCase):
    def test_export_stages_and_replaces_only_when_forced(self):
        import hashlib
        from bench import oneshot_v2 as V
        with tempfile.TemporaryDirectory(dir=C.ROOT) as tmp:
            root = Path(tmp)
            oneshot, dest, programs = root / "oneshot", root / "dest", root / "source"
            for variant, relative, code in (("plain", "plain.py", b"print(1)\n"),
                                             ("rust", "rust/src/main.rs", b"fn main() {}\n")):
                path = programs / "fake/heat" / relative
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(code)
                V.write_json(oneshot / "calls/fake" / f"heat.{variant}.json", {"request_hash": variant + "-hash"})
            cfg = {"fake": dict(model="fake-model", cli="fake-cli", effort="high")}
            files = {"rust/Cargo.toml": b"[package]\n", "rust/src/main.rs": b"template"}
            with (patch.object(C, "PROGRAMS", dest), patch.object(C, "ONESHOT_V2", oneshot),
                  patch.object(C, "ONESHOT_AUTHORS", {"fake-oneshot": "fake"}),
                  patch.object(C, "ONESHOT_V2_MODELS", cfg), patch.object(C, "ONESHOT_V2_TASKS", ("heat",)),
                  patch.object(C, "ONESHOT_V2_VARIANTS", ("plain", "rust", "fast")),
                  patch.object(V.sessions, "session_files", return_value=files)):
                V.export(["fake"], programs=programs)
                target = dest / "fake-oneshot/heat"
                snapshot = {p.relative_to(target).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in target.rglob("*") if p.is_file()}
                self.assertEqual(set(snapshot), {"plain.py", "rust/Cargo.toml", "rust/src/main.rs", "meta.json"})
                meta = json.loads((target / "meta.json").read_text())
                self.assertEqual(meta["programs"]["plain"], dict(path="plain.py", sha256=hashlib.sha256(b"print(1)\n").hexdigest(), request_hash="plain-hash"))
                self.assertEqual(set(meta["programs"]), {"plain", "rust"})
                V.export(["fake"], programs=programs)
                self.assertEqual(snapshot, {p.relative_to(target).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in target.rglob("*") if p.is_file()})
                (programs / "fake/heat/plain.py").write_bytes(b"print(2)\n")
                with self.assertRaisesRegex(FileExistsError, "--force"):
                    V.export(["fake"], programs=programs)
                self.assertEqual((target / "plain.py").read_bytes(), b"print(1)\n")
                V.export(["fake"], force=True, programs=programs)
                self.assertEqual((target / "plain.py").read_bytes(), b"print(2)\n")

    def test_prompts(self):
        from bench import oneshot_v2 as V
        walkers = V.prompt_for("walkers", "plain")
        self.assertIn("plain.py INPUT_PATH WORKERS", walkers)
        self.assertIn("Run with `WORKERS` = 4.", walkers)
        ledger = V.prompt_for("ledger", "plain")
        self.assertIn((C.BENCH / "oneshot_contracts/ledger.md").read_text(encoding="utf-8").strip().replace("\r\n", "\n"), ledger)
        self.assertIn("Example `e1` input:", ledger)
        for path in (C.DATA / "samples/ledger").glob("*.in"):
            if path.stat().st_size > C.ONESHOT_V2_SAMPLE_LIMIT:
                self.assertNotIn(f"Example `{path.stem}` input:", ledger)

    def test_claude_stream_and_usage(self):
        from bench import oneshot_v2 as V
        with tempfile.TemporaryDirectory(dir=C.ROOT) as folder:
            p = Path(folder) / "stream.jsonl"
            p.write_text('warning\n{"type":"assistant","message":{"content":[{"type":"text","text":"first"}]}}\n{"type":"assistant","message":{"content":[{"type":"text","text":"second"}]}}\n', encoding="utf-8")
            self.assertEqual(V.claude_reply(p), "firstsecond")
        self.assertEqual(V.token_values({"prompt_tokens": 20, "prompt_tokens_details": {"cached_tokens": 4}, "completion_tokens": 9, "completion_tokens_details": {"reasoning_tokens": 3}}, "openrouter-batch"), dict(input_tokens=20, cached_input_tokens=4, output_tokens=9, reasoning_tokens=3))

    def test_claim_skips(self):
        from bench import oneshot_v2 as V
        with tempfile.TemporaryDirectory(dir=C.ROOT) as folder, patch.object(C, "ONESHOT_WORK", Path(folder)):
            first = V.claim("sol", "heat", "plain")
            self.assertIsNotNone(first)
            with patch.object(V, "_run_one", side_effect=AssertionError("must not call")):
                V.run_one("sol", "heat", "plain")
            first.unlink()

    def test_claude_reply_gz_matches_cached_reply(self):
        from bench import oneshot_v2 as V
        folder = C.DATA / "oneshot_test/calls/haiku"
        log, cached = folder / "heat.plain.jsonl.gz", folder / "heat.plain.json"
        if not (log.is_file() and cached.is_file()): self.skipTest("v1 haiku log not present")
        self.assertEqual(V.claude_reply(log), V.read_json(cached)["reply"])


class HiddenTests(unittest.TestCase):
    def setUp(self):
        import hashlib
        from bench import oneshot_v2 as V
        self.V = V
        temp = tempfile.TemporaryDirectory(dir=C.ROOT); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name, value in (("ONESHOT_V2", self.root / "oneshot"), ("ONESHOT_WORK", self.root / "work"),
                            ("INPUTS", self.root / "inputs"), ("DATA", self.root / "data")):
            patcher = patch.object(C, name, value); patcher.start(); self.addCleanup(patcher.stop)
        self.entries = []
        for task in ("heat", "walkers"):
            for name in ("t1", "full"):
                path = C.INPUTS / task / f"{name}.in"; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(name, encoding="utf-8")
                self.entries.append(dict(task=task, name=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        patcher = patch.object(V, "manifest", side_effect=lambda: self.entries)
        patcher.start(); self.addCleanup(patcher.stop)

    def make_program(self, model, code):
        import hashlib
        source = C.ONESHOT_V2 / "programs" / model / "heat/plain.py"
        source.parent.mkdir(parents=True, exist_ok=True); source.write_text(code, encoding="utf-8")
        built = C.ONESHOT_WORK / "check" / model / "heat/plain/plain.py"
        built.parent.mkdir(parents=True, exist_ok=True); built.write_text(code, encoding="utf-8")
        return dict(model=model, task="heat", variant="plain", program_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), built=True)

    def test_hidden_statuses_and_replacement(self):
        import csv, subprocess
        V = self.V
        rows = [self.make_program("ok", 'print("sum 1\\nmax 1 1 1\\nchecksum 1")\n'),
                self.make_program("fail", 'import sys; sys.exit(3)\n')]
        V.write_csv(C.ONESHOT_V2 / "checks.csv", rows, ["model", "task", "variant", "program_sha256", "built"])
        expected = C.DATA / "expected/heat"; expected.mkdir(parents=True)
        (expected / "t1.out").write_text("sum 1\nmax 1 1 1\nchecksum 1\n", encoding="utf-8")
        (expected / "full.out").write_text("sum 2\nmax 1 1 1\nchecksum 1\n", encoding="utf-8")
        old = dict(model="other", task="heat", variant="plain", input="t1", workers=1, program_sha256="x", status="pass", message="", wall_seconds=1)
        V.write_csv(C.ONESHOT_V2 / "checks_hidden.csv", [old], V.HIDDEN_FIELDS)
        def run(command, folder, stdout, stderr, timeout):
            result = subprocess.run(command, cwd=folder, capture_output=True, timeout=timeout)
            stdout.write_bytes(result.stdout); stderr.write_bytes(result.stderr)
            return dict(exit_code=result.returncode, timed_out=False, wall_seconds=0.1)
        with patch.object(V, "job_run", side_effect=run): V.hidden(["ok", "fail"], ["heat"], ["plain"], jobs=2)
        with (C.ONESHOT_V2 / "checks_hidden.csv").open(newline="", encoding="utf-8") as f: actual = list(csv.DictReader(f))
        statuses = {(r["model"], r["input"]): r["status"] for r in actual}
        self.assertEqual(statuses, {("other", "t1"): "pass", ("ok", "t1"): "pass", ("ok", "full"): "wrong", ("fail", "t1"): "error", ("fail", "full"): "error"})
        self.assertTrue(all(r["message"].startswith("exit 3:") for r in actual if r["model"] == "fail"))
        (C.ONESHOT_V2 / "programs/ok/heat/plain.py").write_text("changed", encoding="utf-8")
        with patch.object(V, "job_run", side_effect=AssertionError("must not run")): V.hidden(["ok"], ["heat"], ["plain"])
        with (C.ONESHOT_V2 / "checks_hidden.csv").open(newline="", encoding="utf-8") as f: actual = list(csv.DictReader(f))
        self.assertTrue(all(r["message"] == "not built" for r in actual if r["model"] == "ok"))
        self.assertEqual(len(actual), 5)

    def test_summary_uses_only_current_program(self):
        import csv
        V = self.V
        check = self.make_program("sol", "print(1)\n")
        V.write_json(C.ONESHOT_V2 / "calls/sol/heat.plain.json", {"usage": {}, "parse": {"status": "ok"}})
        rows = [dict(model="sol", task="heat", variant="plain", input="t1", workers=1,
                     program_sha256=check["program_sha256"], status="pass", message="", wall_seconds=1),
                dict(model="sol", task="heat", variant="plain", input="full", workers=1,
                     program_sha256=check["program_sha256"], status="wrong", message="x", wall_seconds=1)]
        V.write_csv(C.ONESHOT_V2 / "checks_hidden.csv", rows, V.HIDDEN_FIELDS)
        V.summary()
        with (C.ONESHOT_V2 / "summary.csv").open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f); result = next(reader)
            self.assertEqual(reader.fieldnames[-3:], ["hidden_passed", "hidden_total", "hidden_first_failure"])
        self.assertEqual((result["hidden_passed"], result["hidden_total"], result["hidden_first_failure"]), ("1", "2", "wrong"))
        (C.ONESHOT_V2 / "programs/sol/heat/plain.py").write_text("changed", encoding="utf-8")
        V.summary()
        with (C.ONESHOT_V2 / "summary.csv").open(newline="", encoding="utf-8") as f: result = next(csv.DictReader(f))
        self.assertEqual((result["hidden_passed"], result["hidden_total"], result["hidden_first_failure"]), ("", "", ""))

    def test_input_hash_and_walkers_jobs(self):
        jobs = self.V.hidden_jobs(["m"], ["walkers"], ["plain"])
        self.assertEqual([(j[3], j[4]) for j in jobs], [("t1", 4), ("t1", 1), ("t1", 16), ("full", 4)])
        (C.INPUTS / "walkers/t1.in").write_text("modified", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Input hash differs"): self.V.hidden_jobs(["m"], ["walkers"], ["plain"])


def _usage(prompt, completion, reasoning=0, cached=0):
    return {"prompt_tokens": prompt, "completion_tokens": completion, "prompt_tokens_details": {"cached_tokens": cached}, "completion_tokens_details": {"reasoning_tokens": reasoning}}


def _item(custom_id, content=None, usage=None, error=None):
    if error: return {"custom_id": custom_id, "error": error}
    body = {"model": "google/gemini-4-carbon-20261110", "provider": "Google", "choices": [{"message": {"content": content, "reasoning": "thought"}, "finish_reason": "stop"}], "usage": usage}
    return {"custom_id": custom_id, "response": {"status_code": 200, "body": body}}


class BatchTests(unittest.TestCase):
    tasks = ("heat", "ledger", "walkers")

    def setUp(self):
        from bench import oneshot_v2 as V
        self.V = V
        folder = tempfile.TemporaryDirectory(dir=C.ROOT); self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        # The batch path is generic; no batch model is configured for real runs, so the tests add a fake one.
        fake = dict(cli="openrouter-batch", model="google/gemini-4-carbon:batch", canonical="google/gemini-4-carbon-20261110", effort="high")
        for patcher in (patch.object(C, "ONESHOT_V2", self.root / "oneshot"), patch.object(C, "ONESHOT_WORK", self.root / "work"),
                        patch.dict(C.ONESHOT_BATCH, poll_seconds=0), patch.dict(C.ONESHOT_V2_EXTRA_MODELS, carbon=fake)):
            patcher.start(); self.addCleanup(patcher.stop)
        self.jobs = {t: V.request_for("carbon", t, "plain") for t in self.tasks}
        self.cids = {t: f"nb39-v2-carbon-{t}-plain-{O.request_hash(r)[:12]}" for t, r in self.jobs.items()}

    def final(self, batch_id="batch_1"):
        c = self.cids
        results = [_item(c["heat"], "Here:\n```python\nprint(1)\n```\n", _usage(1000, 200, 50, 100)),
                   _item(c["ledger"], "I cannot write this.", _usage(1000, 600)),
                   _item(c["walkers"], error={"message": "boom"})]
        return {"id": batch_id, "status": "completed", "created_at": 1_800_000_000, "finalized_at": 1_800_000_600, "usage": {"cost": 0.006},
                "request_counts": {"total": 3, "completed": 2, "failed": 1}, "results": results}

    def test_batch_run(self):
        V = self.V
        batches = C.ONESHOT_V2 / "batches"
        seen = []
        def get(batch_id):
            seen.append(sorted(p.name for p in batches.glob("carbon-*.json")))
            return {"id": batch_id, "status": "in_progress", "request_counts": {"total": 3, "completed": 0}} if len(seen) == 1 else self.final(batch_id)
        with patch.object(V, "_post_batch", return_value={"id": "batch_1", "status": "validating"}) as post, \
                patch.object(V, "_get_batch", side_effect=get), patch.object(V, "trace_call") as trace:
            V.run_batch("carbon", self.tasks, ["plain"])
            payload = post.call_args.args[0]
            self.assertEqual(payload["endpoint"], "/v1/chat/completions")
            self.assertEqual(payload["model"], "google/gemini-4-carbon-20261110")
            self.assertEqual(payload["provider"], C.ONESHOT_BATCH["provider"])
            self.assertEqual([r["custom_id"] for r in payload["requests"]], [self.cids[t] for t in self.tasks])
            self.assertEqual(payload["requests"][0]["body"], self.jobs["heat"]["body"])
            self.assertEqual(len(seen), 2)
            self.assertTrue(all(len(s) == 1 for s in seen), "submission file must exist before polling")
            submission = V.read_json(batches / seen[0][0])
            self.assertEqual(submission["response"]["id"], "batch_1")
            self.assertEqual([j["task"] for j in submission["jobs"]], list(self.tasks))
            self.assertEqual(len((batches / "batch_1.polls.jsonl").read_text(encoding="utf-8").splitlines()), 2)
            self.assertNotIn("results", (batches / "batch_1.polls.jsonl").read_text(encoding="utf-8"))
            with gzip.open(batches / "batch_1.result.json.gz") as f: self.assertEqual(len(json.load(f)["results"]), 3)
            calls = C.ONESHOT_V2 / "calls/carbon"
            heat, ledger, walkers = (V.read_json(calls / f"{t}.plain.json") for t in self.tasks)
            self.assertEqual(heat["request"], self.jobs["heat"])
            self.assertEqual(heat["request_hash"], O.request_hash(self.jobs["heat"]))
            self.assertEqual((heat["batch_id"], heat["custom_id"], heat["batch_status"]), ("batch_1", self.cids["heat"], "completed"))
            self.assertEqual((heat["created_at"], heat["finalized_at"]), (1_800_000_000, 1_800_000_600))
            self.assertTrue(heat["created_utc"].startswith("2027-01-15T08:00:00"))
            self.assertEqual((heat["status_code"], heat["finish_reason"], heat["reasoning_text"]), (200, "stop", "thought"))
            self.assertEqual((heat["response_model"], heat["response_provider"]), ("google/gemini-4-carbon-20261110", "Google"))
            self.assertEqual(heat["parse"]["status"], "ok")
            self.assertAlmostEqual(heat["cost_usd"], 0.002); self.assertAlmostEqual(ledger["cost_usd"], 0.004)
            self.assertIsNone(heat["error"])
            self.assertEqual(ledger["parse"]["status"], "no_code_block")
            self.assertEqual(walkers["parse"]["status"], "no_code_block")
            self.assertEqual((walkers["reply"], walkers["error"], walkers["cost_usd"]), ("", {"message": "boom"}, None))
            programs = C.ONESHOT_V2 / "programs/carbon"
            self.assertEqual((programs / "heat/plain.py").read_text(encoding="utf-8"), "print(1)\n")
            self.assertFalse((programs / "ledger/plain.py").exists() or (programs / "walkers/plain.py").exists())
            self.assertEqual(trace.call_count, 3)
            args = trace.call_args_list[0]
            self.assertEqual(args.args[0], heat["request_hash"]); self.assertEqual(args.args[2], "google/gemini-4-carbon-20261110")
            self.assertEqual(args.kwargs["usage"], dict(input=900, input_cache_read=100, output=150, output_reasoning=50))
            self.assertEqual(args.kwargs["session_id"], "oneshot/carbon")
            self.assertEqual(args.args[6] - args.args[5], datetime.timedelta(seconds=600))
            self.assertEqual(list((C.ONESHOT_WORK / "claims/v2/carbon").glob("*")), [])
            # Everything is cached now: no second batch.
            post.reset_mock()
            V.run_batch("carbon", self.tasks, ["plain"])
            post.assert_not_called()

    def test_claims_released_on_failure(self):
        V = self.V
        with patch.object(V, "_post_batch", side_effect=RuntimeError("down")):
            with self.assertRaises(RuntimeError): V.run_batch("carbon", self.tasks, ["plain"])
        self.assertEqual(list((C.ONESHOT_WORK / "claims/v2/carbon").glob("*")), [])

    def test_claimed_jobs_are_skipped(self):
        V = self.V
        held = V.claim("carbon", "heat", "plain")
        with patch.object(V, "_post_batch", return_value={"id": "batch_2"}) as post, patch.object(V, "_get_batch", return_value=self.final("batch_2")):
            V.run_batch("carbon", ["heat", "ledger"], ["plain"])
        self.assertEqual([r["custom_id"] for r in post.call_args.args[0]["requests"]], [self.cids["ledger"]])
        self.assertTrue(held.exists()); held.unlink()

    def test_resume_polls_existing_batch(self):
        V = self.V
        batches = C.ONESHOT_V2 / "batches"
        jobs = [dict(custom_id=self.cids[t], task=t, variant="plain", request_hash=O.request_hash(self.jobs[t])) for t in self.tasks]
        V.write_json(batches / "carbon-20270115T080000Z.json", dict(model="carbon", submitted_at=1_800_000_000, submitted_utc="x", response={"id": "batch_9"}, jobs=jobs))
        with patch.object(V, "_post_batch", side_effect=AssertionError("must not submit")), \
                patch.object(V, "_get_batch", return_value=self.final("batch_9")) as get, patch.object(V, "trace_call"):
            V.run_batch("carbon", self.tasks, ["plain"])
        get.assert_called_once_with("batch_9")
        self.assertTrue((batches / "batch_9.result.json.gz").exists())
        self.assertEqual(V.read_json(C.ONESHOT_V2 / "calls/carbon/heat.plain.json")["batch_id"], "batch_9")

    def test_terminal_submission_is_not_resumed(self):
        V = self.V
        batches = C.ONESHOT_V2 / "batches"
        jobs = [dict(custom_id=self.cids["heat"], task="heat", variant="plain", request_hash="x")]
        V.write_json(batches / "carbon-20270115T080000Z.json", dict(model="carbon", response={"id": "batch_old"}, jobs=jobs))
        (batches / "batch_old.result.json.gz").write_bytes(b"")
        with patch.object(V, "_post_batch", return_value={"id": "batch_new"}) as post, patch.object(V, "_get_batch", return_value=self.final("batch_new")), patch.object(V, "trace_call"):
            V.run_batch("carbon", ["heat"], ["plain"], force=True)
        post.assert_called_once()

    def test_poll_failures_tolerated_then_give_up(self):
        V = self.V
        answers = [RuntimeError("503")] * 2 + [self.final("batch_3")]
        with patch.object(V, "_get_batch", side_effect=answers):
            self.assertEqual(V._poll("carbon", "batch_3")["status"], "completed")
        with patch.object(V, "_get_batch", side_effect=RuntimeError("503")) as get:
            with self.assertRaises(RuntimeError): V._poll("carbon", "batch_4")
        self.assertEqual(get.call_count, 20)

    def test_http_errors_report_status_and_body(self):
        V = self.V
        class Response:
            ok, status_code, text = False, 429, "slow down" * 100
        with patch.object(V.requests, "post", return_value=Response()), patch.object(V.openrouter_proxy, "api_key", return_value="secret-key"):
            with self.assertRaises(RuntimeError) as caught: V._post_batch({})
        self.assertIn("429", str(caught.exception)); self.assertLess(len(str(caught.exception)), 400)
        self.assertNotIn("secret-key", str(caught.exception))

if __name__ == "__main__": unittest.main()
