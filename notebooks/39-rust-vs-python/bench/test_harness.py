"""Focused regression checks for grammars, isolation and Windows accounting."""

import gzip
import itertools
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import psutil

from bench import config as C
from bench.common import manifest, read_csv, read_json, sha256, shim_command, write_json, write_text
from bench.compare import Unreadable, compare, parse
from bench.generate import generate
from bench.measure import ACCOUNT_FIELDS, Harness, dependencies, python_code_lines, rust_without_comments, toml_value, c_code_lines, build_rule
from bench.sessions import event_metadata, prepare, refresh_metadata, request_hash, render_template, harvest_files
from bench.winjob import Heartbeat, Job, cpu_sets, on_mains, run, sleep_clock, slept_seconds


class LanguageTests(unittest.TestCase):
    def test_main_hashes(self):
        ledger = {(r["author"], r["task"]): r["request_hash"] for r in json.loads((C.DATA / "preparation_hashes.json").read_text())}
        self.assertEqual(len(ledger), 16)
        for author in sorted({a for a, _ in ledger}):  # authors added later have no ledger rows
            for task in C.TASKS:
                with self.subTest(author=author, task=task):
                    self.assertEqual(request_hash(author, task), ledger[author, task])
                    self.assertEqual(request_hash(author, task), json.loads((C.PROGRAMS / author / task / "meta.json").read_text())["request_hash"])

    def test_render(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            path = Path(folder) / "test.tmpl"
            path.write_text("{{JAVA}}\n{{GO}}\n", encoding="utf-8")
            self.assertEqual(render_template(path), (str(C.TOOLCHAINS["JAVA"]) + "\r\n" + str(C.TOOLCHAINS["GO"]) + "\r\n").encode())

    def test_harvest(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            root = Path(folder)
            for name in ("cpp/main.cpp", "cpp/include/nlohmann/json.hpp", "csharp/bin/x.cs", "csharp/A.cs", "go/.gocache/a.go", "go/a.go", "java/src/A.java", "java/lib/A.java", "js/a.mjs"):
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("x")
            files = harvest_files(root, "langs")
            for name in ("cpp/main.cpp", "csharp/A.cs", "go/a.go", "java/src/A.java", "js/a.mjs"): self.assertIn(name, files)
            for name in ("cpp/include/nlohmann/json.hpp", "csharp/bin/x.cs", "go/.gocache/a.go", "java/lib/A.java"): self.assertNotIn(name, files)

    def test_lexer(self):
        self.assertEqual(c_code_lines("\"// not a comment\"; // x\n'/*';\n`// text`;\n/* only\ncomment */\n"), 3)

    def test_rules(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            root = Path(folder)
            (root / "solution.csproj").write_text('<Project><ItemGroup><PackageReference Include="x" /></ItemGroup></Project>')
            (root / "go.mod").write_text('module x\nrequire example.com/x v1.0.0\n')
            self.assertTrue(build_rule("csharp", root))
            self.assertTrue(build_rule("go", root))


class GrammarTests(unittest.TestCase):
    def test_expected_outputs_and_normalisation(self):
        for entry in manifest():
            task, name = entry["task"], entry["name"]
            path = C.DATA / "expected" / task / f"{name}.out"
            if not path.exists():
                continue
            text = path.read_text()
            with self.subTest(task=task, name=name):
                self.assertEqual(compare(task, text, text)[0], "correct")
                windows = "\r\n".join(line + "   " for line in text.splitlines()) + "\r\n\r\n  \r\n"
                self.assertEqual(compare(task, windows, text)[0], "correct")
                self.assertEqual(compare(task, "diagnostic\n" + text, text)[0], "unreadable")
                self.assertEqual(compare(task, text.replace(" ", "  ", 1), text)[0], "unreadable")

    def test_wrong_versus_unreadable(self):
        expected = "sum 10\nmax 5 0 1\nchecksum 20\n"
        self.assertEqual(compare("heat", expected.replace("sum 10", "sum 11"), expected)[0], "wrong")
        for bad in ("SUM 10\nmax 5 0 1\nchecksum 20", "sum ten\nmax 5 0 1\nchecksum 20", expected + "extra\n"):
            self.assertEqual(compare("heat", bad, expected)[0], "unreadable")

    def test_float_tolerance(self):
        expected = "kinetic 1.0\npotential 0\nposition -2\nfastest 0\n"
        self.assertEqual(compare("springs", expected.replace("1.0", "1.0000000001"), expected)[0], "correct")
        self.assertEqual(compare("springs", expected.replace("1.0", "1.00000001"), expected)[0], "wrong")
        self.assertEqual(compare("springs", expected.replace("potential 0", "potential 1e-300"), expected)[0], "wrong")
        self.assertEqual(compare("springs", expected.replace("1.0", "nan"), expected)[0], "unreadable")

    def test_trailing_carriage_return_is_rejected(self):
        with self.assertRaises(Unreadable):
            parse("heat", "sum 0\r\nmax 0 0 0\nchecksum 0\r")


class HarnessTests(unittest.TestCase):
    def test_frozen_hashes(self):
        for entry in manifest():
            with self.subTest(task=entry["task"], name=entry["name"]):
                path = C.input_path(entry["task"], entry["name"])
                self.assertEqual(sha256(path), entry["sha256"])
                self.assertEqual(path.stat().st_size, entry["bytes"])

    def test_sample_determinism(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            for entry in manifest():
                if entry["name"] not in C.TINY[entry["task"]]:
                    continue
                destination = Path(folder) / entry["task"] / f'{entry["name"]}.in'
                generate(entry["task"], entry["scale"], entry["seed"], destination)
                self.assertEqual(sha256(destination), entry["sha256"])

    def test_full_sizes_do_not_depend_on_filename(self):
        for task in C.TASKS:
            for name in C.TINY[task]:
                self.assertEqual(C.parameters(task, 1.0, name), C.FULL[task])

    def test_loc(self):
        text = '# comment\n"""doc\nstring"""\nimport os # x\ndef f():\n    """function doc"""\n    return "hello"\n'
        self.assertEqual(python_code_lines(text), (3, ""))
        self.assertEqual(python_code_lines('(\n "first "\n "second"\n)\nx = 1\n'), (1, ""))
        rust = '/* outer\n /* inner */ end */\n// comment\nfn main() { println!("// hi"); }\n'
        self.assertEqual(sum(bool(line.strip()) for line in rust_without_comments(rust).splitlines()), 1)
        self.assertIn('"// hi"', rust_without_comments(rust))

    def test_dependency_tables(self):
        document = {"dependencies": {"serde": "1"}, "target": {"cfg(windows)": {"build-dependencies": {"bad": "2"}}}}
        self.assertEqual(dependencies(document), [{"serde": "1"}, {"bad": "2"}])
        import tomllib
        self.assertEqual(tomllib.loads("config=" + toml_value(document))["config"], document)

    def test_prepare_never_launches_a_cli(self):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("No process may be launched")):
            folder, digest = prepare("terra", "heat")
            self.assertEqual(digest, request_hash("terra", "heat"))
            self.assertEqual(sorted(p.name for p in folder.iterdir()), ["SPEC.md", "rust", "samples"])
            self.assertEqual(digest, prepare("terra", "heat")[1])

    def test_event_streams(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            path = Path(folder) / "events.gz"
            events = [dict(type="turn.completed", usage={"input_tokens": 10, "output_tokens": 4}),
                      dict(type="turn.completed", usage={"input_tokens": 20, "output_tokens": 8}),
                      dict(type="item.completed", item=dict(type="agent_message", text="done"))]
            with gzip.open(path, "wt") as f:
                f.write("\n".join(map(json.dumps, events)))
            meta = event_metadata(path)
            self.assertEqual(meta["usage"], dict(input_tokens=30, output_tokens=12))
            self.assertEqual(meta["turns"], 2)
            self.assertEqual(meta["final_message"], "done")
            with gzip.open(path, "wt") as f:
                f.write(json.dumps(dict(type="result", total_cost_usd=1.25, usage={"input_tokens": 10}, num_turns=3, result="done")))
            self.assertEqual(event_metadata(path)["cost_usd"], 1.25)

    @staticmethod
    def write_events(path, events):
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt") as f:
            f.write("\n".join(map(json.dumps, events)))

    def test_several_result_events_are_added_up(self):
        first = dict(type="result", total_cost_usd=2.5, num_turns=67, result="answer",
                     usage={"input_tokens": 100, "output_tokens": 68806, "service_tier": "standard",
                            "cache_creation": {"ephemeral_5m_input_tokens": 7, "ephemeral_1h_input_tokens": 0}})
        second = dict(type="result", total_cost_usd=2.9, num_turns=2, result="after",
                      usage={"input_tokens": 5, "output_tokens": 385, "service_tier": "batch",
                             "cache_creation": {"ephemeral_5m_input_tokens": 3}, "output_tokens_details": {"thinking": 1}})
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            path = Path(folder) / "events.gz"
            self.write_events(path, [dict(type="assistant", message=dict(content=[dict(type="tool_use")])), first, second])
            meta = event_metadata(path)
            self.assertEqual(meta["turns"], 69)
            self.assertEqual(meta["usage"], dict(input_tokens=105, output_tokens=69191, service_tier="batch",
                                                 cache_creation=dict(ephemeral_5m_input_tokens=10, ephemeral_1h_input_tokens=0),
                                                 output_tokens_details=dict(thinking=1)))
            self.assertEqual(meta["cost_usd"], 2.9)
            self.assertEqual((meta["result_events"], meta["tool_calls"], meta["final_message"]), (2, 1, "after"))
            self.write_events(path, [first])
            meta = event_metadata(path)
            self.assertEqual((meta["turns"], meta["usage"], meta["cost_usd"], meta["result_events"]), (67, first["usage"], 2.5, 1))

    def test_refresh_metadata_changes_only_the_listed_fields(self):
        first = dict(type="result", total_cost_usd=1.0, num_turns=10, usage={"output_tokens": 100}, result="a")
        second = dict(type="result", total_cost_usd=1.5, num_turns=2, usage={"output_tokens": 20}, result="b")
        old = dict(author="x", task="heat", request_hash="abc", request={"k": 1}, files=[{"path": "p"}], wall_seconds=3.5,
                   start_utc="s", turns=2, usage={"output_tokens": 20}, tool_calls=0, cost_usd=1.5, final_message="b")
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            data = Path(folder)
            self.write_events(data / "sessions" / "x" / "heat.jsonl.gz", [first, second])
            self.write_events(data / "sessions" / "x" / "heat.langs.jsonl.gz", [first])
            self.write_events(data / "failed_sessions" / "x" / "heat.main.jsonl.gz", [first, second])
            self.write_events(data / "sessions" / "y" / "heat.jsonl.gz", [first, second])
            for path, meta in {data / "programs" / "x" / "heat" / "meta.json": old,
                               data / "programs" / "x" / "heat" / "meta_langs.json": dict(old, turns=10, usage=first["usage"], cost_usd=1.0),
                               data / "failed_sessions" / "x" / "heat.main.meta.json": old,
                               data / "programs" / "y" / "heat" / "meta.json": dict(old, openrouter={"cost_usd": 0.01}, cost_usd=0.01,
                                                                                       claude_code_reported_cost_usd=1.5)}.items():
                write_json(path, meta)
            main_path = data / "programs" / "x" / "heat" / "meta.json"
            snapshot = main_path.read_text(encoding="utf-8")
            with mock.patch("builtins.print"):
                refresh_metadata(data, dry_run=True)
            self.assertEqual(main_path.read_text(encoding="utf-8"), snapshot)
            with mock.patch("builtins.print"):
                changed = refresh_metadata(data)
                self.assertEqual(len(changed), 4)
                self.assertEqual(refresh_metadata(data), [])  # nothing left to change
            expected = dict(old, turns=12, usage={"output_tokens": 120}, result_events=2)
            self.assertEqual(read_json(main_path), expected)
            self.assertEqual(main_path.read_text(encoding="utf-8"), json.dumps(expected, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
            self.assertEqual(read_json(data / "failed_sessions" / "x" / "heat.main.meta.json"), expected)
            self.assertEqual(read_json(data / "programs" / "x" / "heat" / "meta_langs.json"), dict(old, turns=10, usage=first["usage"], cost_usd=1.0, result_events=1))
            routed = read_json(data / "programs" / "y" / "heat" / "meta.json")
            self.assertEqual((routed["cost_usd"], routed["claude_code_reported_cost_usd"], routed["turns"]), (0.01, 1.5, 12))

    def test_cmd_shim_preserves_quotes_and_spaces(self):
        with tempfile.TemporaryDirectory(prefix="shim with spaces ", dir=C.WORK) as folder:
            folder = Path(folder)
            script, shim = folder / "echo.py", folder / "echo.cmd"
            write_text(script, "import json,sys; print(json.dumps(sys.argv[1:]))\n")
            write_text(shim, f'@echo off\n"{C.PYTHON}" "{script}" %*\n')
            arguments = ["exec", "-c", 'model_reasoning_effort="high"', "-C", str(folder), "-"]
            result = subprocess.run(shim_command([str(shim)] + arguments), capture_output=True,
                                    text=True, encoding="utf-8", timeout=10, check=True)
            self.assertEqual(json.loads(result.stdout), arguments)

    def test_job_kills_descendants_and_records_memory(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            path = Path(folder)
            child = "import time; memory=bytearray(64*1024*1024); time.sleep(60)"
            parent = f"import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c',{child!r}]); print(p.pid,flush=True); time.sleep(60)"
            result = run([str(C.PYTHON), "-X", "utf8", "-c", parent], path, path / "out", path / "err", 2,
                         processors=cpu_sets()["p_cores"])
            self.assertTrue(result["timed_out"])
            self.assertGreaterEqual(result["processes"], 2)
            self.assertGreater(result["peak_job_commit"], 64*1024*1024)
            self.assertGreater(result["peak_working_set"], 1024*1024)
            child_pid = int((path / "out").read_text())
            # Windows can retain an exited PID while another process holds its handle.
            try:
                self.assertEqual(psutil.Process(child_pid).wait(timeout=3), 124)
            except psutil.NoSuchProcess:
                pass
            write_json(C.WORK / "selftest_results/job_probe.json", result)

    def test_job_affinity_is_applied_to_the_process(self):
        processors = cpu_sets()["p_cores"]
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder, Job(processors) as job:
            folder = Path(folder)
            with (folder / "stdout").open("wb") as stream:
                process = job.launch([str(C.PYTHON), "-X", "utf8", "-c", "import time; time.sleep(1)"],
                                     stdout=stream, stderr=stream)
                actual = psutil.Process(process.pid).cpu_affinity()
                self.assertEqual(sorted(actual), sorted(processors))
                process.wait(timeout=5)
                process._handle.Close()
            write_json(C.WORK / "selftest_results/affinity_probe.json", dict(requested=processors, actual=actual))

    def test_disallowed_dependencies_never_build(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            folder = Path(folder)
            h = Harness(selftest=True, tasks=["heat"], authors=["probe"])
            h.programs, h.results = folder / "programs", folder / "results"
            h.build_root, h.run_root = folder / "build", folder / "runs"
            source = h.programs / "probe/heat/rust"
            write_text(source / "src/main.rs", "fn main() {}\n")
            write_text(source / "Cargo.toml", '[package]\nname="solution"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nreqwest="1"\n')
            with mock.patch("bench.measure.run", side_effect=AssertionError("Disallowed dependency launched cargo")):
                h.build()
            self.assertEqual(h.rows("builds")[0]["status"], "disallowed_dependency")

    def test_unpruned_fallback_and_build_resume(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            folder = Path(folder)
            h = Harness(selftest=True, tasks=["heat"], authors=["probe"])
            h.programs, h.results = folder / "programs", folder / "results"
            h.build_root, h.run_root = folder / "build", folder / "runs"
            source = h.programs / "probe/heat/rust"
            write_text(source / "src/main.rs", 'fn main() { println!("probe"); }\n')
            # The source never names serde; removing it leaves an invalid feature.
            write_text(source / "Cargo.toml", '[package]\nname="solution"\nversion="0.1.0"\nedition="2024"\n'
                       '[dependencies]\nserde={version="1.0.229",optional=true}\n'
                       '[features]\ndefault=["dep:serde"]\n')
            h.build()
            row = h.rows("builds")[0]
            self.assertEqual(row["status"], "ok", row["compiler_errors"])
            self.assertEqual(row["unpruned_fallback"], "True")
            self.assertEqual(json.loads(row["crates_kept"]), ["serde"])
            self.assertEqual(len(json.loads(row["clean_seconds"])), C.BUILD_REPEATS)
            with mock.patch("bench.measure.run", side_effect=AssertionError("Cached build repeated")):
                h.build()
            self.assertEqual(len(h.rows("builds")), 1)


class PowerGuardTests(unittest.TestCase):
    def harness(self, folder):
        h = Harness(selftest=True, tasks=["heat"], authors=["probe"])
        h.programs, h.results = folder / "programs", folder / "results"
        h.build_root, h.run_root = folder / "build", folder / "runs"
        write_text(h.programs / "probe/heat/plain.py", "print('probe')\n")
        h.verified_inputs.add(("heat", "t1"))
        return h

    def fake_run(self, command, scratch, stdout, stderr, timeout, **kwargs):
        stdout.parent.mkdir(parents=True, exist_ok=True)
        stdout.write_bytes((C.DATA / "expected/heat/t1.out").read_bytes())
        stderr.write_bytes(b"")
        return dict.fromkeys(ACCOUNT_FIELDS, 0) | dict(wall_seconds=0.25, timed_out=False)

    def fake_heartbeat(self, gaps):
        """A Heartbeat stand-in that reports the next largest gap from `gaps` for each guarded run."""
        gaps = iter(gaps)

        class FakeHeartbeat:
            def __enter__(self):
                self.max_gap = next(gaps)
                return self

            def __exit__(self, *exc):
                pass

        return FakeHeartbeat

    def guarded_run_one(self, h, table, clocks, mains, sleeper=None, gaps=None):
        """Run one job with fake clocks, power state and heartbeat gaps; returns the mock standing in for the real run."""
        with (mock.patch("bench.measure.run", side_effect=self.fake_run) as launched,
              mock.patch("bench.measure.sleep_clock", side_effect=clocks),
              mock.patch("bench.measure.on_mains", side_effect=mains),
              mock.patch("bench.measure.time.sleep", sleeper or mock.Mock()),
              mock.patch("bench.measure.Heartbeat", self.fake_heartbeat(gaps) if gaps else Heartbeat)):
            h.run_one(table, "probe", "heat", "plain", "t1", 1, 0, 10)
        return launched

    def events(self, h):
        return read_csv(h.results / "power_events.csv")

    def test_anchor_tables_and_validation(self):
        import argparse
        from bench.measure import is_timed_table, anchor_label
        for table in ("runs", "anchor_20261112", "anchor_20261112_warmups"):
            self.assertTrue(is_timed_table(table))
        self.assertFalse(is_timed_table("correctness"))
        with self.assertRaises(argparse.ArgumentTypeError):
            anchor_label("../x")

    def test_anchor_rows_have_distinct_keys_and_slow_repeats(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            h.verified_inputs.add(("heat", "full"))
            def fake_run(*args, **kwargs):
                result = self.fake_run(*args, **kwargs)
                result["wall_seconds"] = C.SLOW_SECONDS + 1
                return result
            with (mock.patch.object(h, "correct_programs", return_value=[("probe", "plain")]),
                  mock.patch("bench.measure.run", side_effect=fake_run),
                  mock.patch("bench.measure.compare", return_value=("correct", "")),
                  mock.patch("bench.measure.sleep_clock", return_value=(0, 0)),
                  mock.patch("bench.measure.on_mains", return_value=True)):
                h.bench()
                h.anchor("20261112")
            runs, anchors = h.rows("runs"), h.rows("anchor_20261112")
            self.assertEqual(len(runs), C.SLOW_REPEATS)
            self.assertEqual(len(anchors), C.SLOW_REPEATS)
            self.assertTrue((h.results / "anchor_20261112.csv").is_file())
            self.assertTrue({r["key"] for r in runs}.isdisjoint({r["key"] for r in anchors}))

    def test_run_with_a_sleep_is_discarded_logged_and_repeated(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            # First run: 10 s of ticks but no unbiased time, i.e. asleep. Second run: 0.5 s of both.
            clocks = [(0, 0), (10_000, 0), (10_000, 0), (10_500, 5_000_000)]
            launched = self.guarded_run_one(h, "runs", clocks, itertools.repeat(True))
            self.assertEqual(launched.call_count, 2)
            self.assertEqual(len(h.rows("runs")), 1)
            events = self.events(h)
            self.assertEqual([e["event"] for e in events], ["discarded"])
            self.assertEqual((events[0]["reason"], float(events[0]["slept_seconds"])), ("slept", 10.0))
            self.assertEqual((events[0]["table"], events[0]["author"], events[0]["task"], events[0]["workers"]), ("runs", "probe", "heat", "1"))

    def test_heartbeat_gap_discards_the_run_as_suspended(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            # The unbiased clock saw nothing (Modern Standby), but the heartbeat saw a 30 s gap in the first run only.
            launched = self.guarded_run_one(h, "runs", itertools.repeat((0, 0)), itertools.repeat(True), gaps=[30.0, 0.5])
            self.assertEqual(launched.call_count, 2)
            self.assertEqual(len(h.rows("runs")), 1)
            events = self.events(h)
            self.assertEqual([e["event"] for e in events], ["discarded"])
            self.assertEqual((events[0]["reason"], float(events[0]["max_heartbeat_gap"])), ("suspended", 30.0))

    def test_slept_takes_precedence_over_suspended(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            clocks = [(0, 0), (10_000, 0), (10_000, 0), (10_500, 5_000_000)]
            self.guarded_run_one(h, "runs", clocks, itertools.repeat(True), gaps=[30.0, 0.5])
            events = self.events(h)
            self.assertEqual((events[0]["reason"], float(events[0]["slept_seconds"]), float(events[0]["max_heartbeat_gap"])),
                             ("slept", 10.0, 30.0))

    def test_small_heartbeat_gap_is_kept(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            launched = self.guarded_run_one(h, "runs", itertools.repeat((0, 0)), itertools.repeat(True), gaps=[1.0])
            self.assertEqual(launched.call_count, 1)
            self.assertEqual(len(h.rows("runs")), 1)
            self.assertEqual(self.events(h), [])

    def test_heartbeat_records_the_largest_gap(self):
        with Heartbeat(interval=0.01) as quiet:
            time.sleep(0.1)
        self.assertLess(quiet.max_gap, 1)
        self.assertFalse(quiet.thread.is_alive())
        # Jump the clock by 30 s after the first reading, as a suspend would.
        readings = itertools.chain([100.0], itertools.count(130.0, 0.01))
        with mock.patch("bench.winjob.time.perf_counter", side_effect=lambda: next(readings)):
            with Heartbeat(interval=0.01) as jumped:
                time.sleep(0.1)
        self.assertGreaterEqual(jumped.max_gap, 30)

    def test_timed_run_on_battery_waits_for_mains(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            sleeper = mock.Mock()
            launched = self.guarded_run_one(h, "runs_warmups", itertools.repeat((0, 0)),
                                            itertools.chain([False, False], itertools.repeat(True)), sleeper)
            sleeper.assert_called_once_with(30)
            self.assertEqual(launched.call_count, 1)
            self.assertEqual(len(h.rows("runs_warmups")), 1)
            self.assertEqual([e["event"] for e in self.events(h)], ["wait_start", "wait_end"])

    def test_mains_lost_discards_timed_runs_but_not_correctness_runs(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            # Timed: mains before the run, battery after it. The repeat is clean.
            launched = self.guarded_run_one(h, "sweep", itertools.repeat((0, 0)),
                                            itertools.chain([True, True, False], itertools.repeat(True)))
            self.assertEqual(launched.call_count, 2)
            self.assertEqual(len(h.rows("sweep")), 1)
            events = self.events(h)
            self.assertEqual([(e["event"], e["reason"], e["mains_before"], e["mains_after"]) for e in events],
                             [("discarded", "mains_lost", "True", "False")])
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            launched = self.guarded_run_one(h, "correctness", itertools.repeat((0, 0)), itertools.repeat(False))
            self.assertEqual(launched.call_count, 1)
            self.assertEqual(len(h.rows("correctness")), 1)
            self.assertEqual(self.events(h), [])

    def test_gives_up_after_five_discards(self):
        with tempfile.TemporaryDirectory(dir=C.WORK) as folder:
            h = self.harness(Path(folder))
            clocks = itertools.accumulate(itertools.repeat((10_000, 0)), lambda a, b: (a[0] + b[0], a[1] + b[1]), initial=(0, 0))
            with self.assertRaisesRegex(RuntimeError, "5 runs discarded"):
                self.guarded_run_one(h, "correctness", clocks, itertools.repeat(True))
            self.assertEqual(len(self.events(h)), 5)
            self.assertEqual(h.rows("correctness"), [])

    def test_slept_seconds(self):
        self.assertEqual(slept_seconds((0, 0), (10_000, 0)), 10)
        self.assertEqual(slept_seconds((5_000, 100), (8_500, 100 + 10_000_000)), 2.5)
        self.assertEqual(slept_seconds((0, 0), (5_000, 50_000_000)), 0)
        self.assertEqual(slept_seconds((0, 0), (1_000, 20_000_000)), 0)  # never negative
        self.assertIn(on_mains(), (True, False, None))
        before = sleep_clock()
        self.assertLess(slept_seconds(before, sleep_clock()), 2)


if __name__ == "__main__":
    unittest.main()
