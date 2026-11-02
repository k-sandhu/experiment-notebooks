"""Standalone presentation checks using temporary synthetic CLI fixtures only.

No study outcome file is read, no notebook cell is executed, and no model or
engine phase runs outside the existing mocked experiment fixture.

The repository's README aim is 25–50 KB. Synthetic size is informative: the
50 KB ceiling below catches accidental full-prompt duplication, rather than
approving the final real presentation. Its size and teaching quality still
require review after collection completes.
"""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

import finalize_scale as finalizer
import refresh_scale_report as refresh
import test_scale_reporting_missing as report_fixtures


class StandaloneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=report_fixtures.MissingReportTests()
        cls.fixture.setUp()
        cls.addClassCleanup(cls.fixture.doCleanups)
        cls.temporary=tempfile.TemporaryDirectory(prefix="scale-standalone-mock-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.repo=Path(cls.temporary.name)/"repository"
        cls.root=cls.repo/"notebooks"/"23-synthetic-data-curation"
        shutil.copytree(cls.fixture.root,cls.root)
        cls.data=cls.root/"data"/"scale_v5"
        for name in ("scale_main_material_review.json","scale_original_failure_review.json"):
            (cls.data/name).write_text(json.dumps({"passed":True,"synthetic_test_fixture_only":True}),encoding="utf-8")
        # The finalizer archives this source, but never imports or executes it.
        shutil.copy2(Path(__file__).with_name("test_scale_experiment.py"),cls.data/"source_snapshot"/"test_scale_experiment.py")
        (cls.root/"README.md").write_text("OLD READER BODY MUST DISAPPEAR\n",encoding="utf-8")
        (cls.repo/"README.md").write_text("# Mock index\n\n| 23 | [Synthetic data generation and curation](notebooks/23-synthetic-data-curation/) | old | old |\n| 23 | Preserve data row |\n| 23 | [Running instructions](notebooks/23-synthetic-data-curation/) | Preserve running row |\n",encoding="utf-8")
        cls.proposal=refresh.build(cls.root,write=False)
        # Exercise optional final-companion embedding without reading a real
        # amendment or executing any runtime cell. Scientific fixture stays
        # synthetic and its existing derived outcomes are not replaced.
        cls.proposal["report"]["intervention_interruption_amendment_006"]={"synthetic_embedding_test_only":True}
        cls.build_calls=[]
        def mock_build(root,write=False):
            if Path(root).resolve()!=cls.root.resolve():
                raise AssertionError("Finalizer attempted a non-fixture report read")
            cls.build_calls.append(write)
            return cls.proposal
        cls.stdout=io.StringIO()
        cls.finalizer_error=None
        with patch.multiple(finalizer,ROOT=cls.root,DATA=cls.data,REPO=cls.repo),patch.object(finalizer,"build",mock_build),contextlib.redirect_stdout(cls.stdout):
            try:
                finalizer.main()
            except Exception as exc:
                cls.finalizer_error=exc
        cls.readme=(cls.root/"README.md").read_text(encoding="utf-8")
        Path(__file__).with_name("finalize_scale_mock_README.md").write_text(cls.readme,encoding="utf-8",newline="\n")
        cls.notebook=json.loads((cls.root/"23_synthetic_data_curation.ipynb").read_bytes())
        cls.narrative="\n\n".join("".join(c["source"]) for c in cls.notebook["cells"] if c["cell_type"]=="markdown")
        cls.summary={"synthetic_fixture_only":True,"real_study_outcome_reads":0,"notebook_cells_executed":0,
                     "model_calls":0,"readme_utf8_bytes":len((cls.root/"README.md").read_bytes()),
                     "repository_readme_aim_bytes":[25000,50000],"mock_prompt_regression_ceiling_bytes":50000,
                     "final_real_presentation_review_still_required":True,
                     "measured_fixture_examples":len(re.findall(r"^#### Case \d+:",cls.readme,re.M)),
                     "numbered_sections":len(re.findall(r"^## \d+\. ",cls.readme,re.M)),
                     "notebook_cells":len(cls.notebook["cells"]),
                     "finalizer_error":repr(cls.finalizer_error) if cls.finalizer_error else None}
        Path(__file__).with_name("finalize_scale_standalone_mock_summary.json").write_text(json.dumps(cls.summary,indent=2)+"\n",encoding="utf-8")

    def test_main_finishes_and_writes_only_the_mock_destination(self):
        self.assertIsNone(self.finalizer_error,repr(self.finalizer_error))
        self.assertEqual(self.build_calls,[False,True])
        self.assertTrue((self.data/"presentation_source"/"scale_reporting.py").is_file())
        self.assertNotIn("OLD READER BODY MUST DISAPPEAR",self.readme)
        self.assertIn("Fresh retry recovered",(self.repo/"README.md").read_text(encoding="utf-8"))
        self.assertIn("| 23 | Preserve data row |",(self.repo/"README.md").read_text(encoding="utf-8"))
        self.assertIn("| Preserve running row |",(self.repo/"README.md").read_text(encoding="utf-8"))

    def test_current_report_headings_are_grouped_and_ten_sections_have_contents(self):
        for text in (self.readme,self.narrative):
            self.assertEqual([int(n) for n in re.findall(r"^## (\d+)\. ",text,re.M)],list(range(1,11)))
            self.assertIn("## Contents",text)
            self.assertIn("### Model and settings",text)
            self.assertIn("### Original accuracy and failure-only recovery",text)
            self.assertIn("### Scenario variants and descriptive sensitivity",text)
            self.assertIn("## 10. Future work and further reading",text)
            self.assertNotIn("Ungrouped narrative",text)
        for heading in re.findall(r"^## (\d+\. [^\n]+)",self.narrative,re.M):
            slug=re.sub(r"[^\w -]","",heading).lower().replace(" ","-")
            self.assertIn('id="'+slug+'"',self.narrative)
            self.assertIn("](#"+slug+")",self.narrative)

    def test_workflow_and_call_graph_precede_the_first_code_cell(self):
        first_code=next(i for i,c in enumerate(self.notebook["cells"]) if c["cell_type"]=="code")
        before_code="\n".join("".join(c["source"]) for c in self.notebook["cells"][:first_code])
        for text in (self.readme,before_code):
            self.assertIn("```mermaid",text)
            self.assertIn("flowchart TD",text)
            self.assertIn("fresh retry via codex exec",text)
            self.assertIn("repair package via codex exec",text)
            self.assertIn("wait for final availability before efficacy",text)

    def test_gradual_opening_examples_and_document_size(self):
        opening=self.readme.split("## The study in brief",1)[0]
        self.assertIn("50 notebooks",opening)
        self.assertIn("sends 20",opening)
        self.assertIn("six delivered notebooks are returned",opening)
        self.assertIn("owed 36 notebooks",opening)
        self.assertGreaterEqual(len([p for p in opening.split("\n\n") if p and not p.startswith("#")]),6)
        self.assertNotIn("gpt-6.1-sol",opening)
        self.assertEqual(len(re.findall(r"^#### Case \d+:",self.readme,re.M)),5)
        self.assertIn("| Field | Expected | Original | Fresh retry | Feedback repair |",self.readme)
        self.assertIn("Verbatim output instruction supplied to every arm",self.readme)
        self.assertIn("raw final assistant response",self.readme)
        self.assertIn("No new CLI calls", "\n".join("".join(c["source"]) for c in self.notebook["cells"]))
        self.assertGreaterEqual(len(self.readme.encode("utf-8")),25000)
        self.assertLessEqual(len(self.readme.encode("utf-8")),50000)

    def test_code_compiles_and_embedded_companions_keep_exact_raw_bytes(self):
        assignments={}
        repository_modules={"scale_experiment","scale_fixtures","scale_transport","scale_parallel","scale_reporting",
                            "high_fixtures","high_material_audit","audit_high_rendered_sources","refresh_scale_report"}
        for index,c in enumerate(self.notebook["cells"]):
            if c["cell_type"]!="code":continue
            source="".join(c["source"])
            compile(source,"mock-notebook-cell-"+str(index),"exec")
            tree=ast.parse(source)
            for node in ast.walk(tree):
                modules=([node.module] if isinstance(node,ast.ImportFrom) else
                         [item.name for item in node.names] if isinstance(node,ast.Import) else [])
                self.assertFalse({name.split(".")[0] for name in modules if name}&repository_modules)
            for node in tree.body:
                if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
                    for target in node.targets:
                        if isinstance(target,ast.Name):assignments[target.id]=node.value.value
        for number in ("003","004","005","006"):
            variable="SCALE_INTERVENTION_RESUME_"+number+"_SOURCE"
            raw=(finalizer.BASE/("scale_intervention_resume_"+number+".py")).read_bytes()
            self.assertEqual(hashlib.sha256(assignments[variable].encode("utf-8")).hexdigest(),hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.notebook["metadata"]["kernelspec"]["name"],"python3")
        self.assertEqual(self.notebook["metadata"]["language_info"]["name"],"python")
        self.assertTrue(all(c.get("outputs")==[] and c.get("execution_count") is None for c in self.notebook["cells"] if c["cell_type"]=="code"))
        self.assertEqual(len({c["id"] for c in self.notebook["cells"]}),len(self.notebook["cells"]))


if __name__=="__main__":
    unittest.main()
