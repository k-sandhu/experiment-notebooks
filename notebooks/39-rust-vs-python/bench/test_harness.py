"""Focused regression checks for grammars, isolation and Windows accounting."""

import gzip
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import psutil

from bench import config as C
from bench.common import manifest, sha256, shim_command, write_json, write_text
from bench.compare import Unreadable, compare, parse
from bench.generate import generate
from bench.measure import Harness, dependencies, python_code_lines, rust_without_comments, toml_value, c_code_lines, build_rule
from bench.sessions import event_metadata, prepare, request_hash, render_template, harvest_files
from bench.winjob import Job, cpu_sets, run


class LanguageTests(unittest.TestCase):
    def test_main_hashes(self):
        ledger = {(r["author"], r["task"]): r["request_hash"] for r in json.loads((C.DATA / "preparation_hashes.json").read_text())}
        self.assertEqual(len(ledger), 16)
        for author in C.AUTHORS:
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


if __name__ == "__main__":
    unittest.main()
