"""Temporary six-case report integration tests; mocked CLI only, no study data."""
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
import test_scale_experiment as mocked_engine
import scale_missing_outcomes_003 as missing_analysis
import refresh_scale_report as refresh


class MissingReportTests(unittest.TestCase):
    def setUp(self):
        engine=mocked_engine.ScaleExperimentTests()
        engine.setUp()
        self.addCleanup(engine.doCleanups)
        self.engine=engine
        engine.main_cfg.update(n_initial=6, collection_cap=6, target_failures=6)
        engine.wrong=set(range(6))
        engine.prepare()
        engine.ns["scale_collect_originals"](engine.root, live=True)
        self.bundle=engine.ns["scale_run_interventions"](engine.root, live=True)
        self.ns=engine.ns
        for name in ("scale_missing_outcomes_003.py", "scale_reporting.py"):
            exec(compile(Path(__file__).with_name(name).read_text(encoding="utf-8"), name, "exec"), self.ns)
        self.root=engine.root
        self.data=self.root/"data"/"scale_v5"
        self.main=self.data/"main"
        power=Path(__file__).with_name("scale_power_plan.json").read_text(encoding="utf-8-sig")
        (self.data/"source_snapshot").mkdir(exist_ok=True)
        (self.data/"source_snapshot"/"scale_power_plan.json").write_text(power, encoding="utf-8")
        for name in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py",
                     *self.ns["SCALE_CORE_SHA256"]):
            (self.data/"source_snapshot"/name).write_bytes(Path(__file__).with_name(name).read_bytes())

    def project_missing(self, missing_count=2, amendment003=False):
        b=self.bundle
        missing=set(b["selection"]["selected_case_ids"][1:1+missing_count])
        unavailable=[]
        for row in b["interventions"]:
            if row["case_id"] not in missing: continue
            row.update(response=None, outcome_unavailable=True, transport_error="controller interrupted; outcome unavailable",
                       error_kind="outcome_unavailable", verification=self.ns["scale_validate_answer"](self.engine.cases[row["case_id"]], None),
                       numeric_absolute_errors={"quantity_units": None, "unit_price_cents": None})
            unavailable.append({k: row[k] for k in ("case_id", "arm", "request_key")})
            # Deliberately invalid cache: an example cache read must fail.
            (self.main/"cache"/(row["request_key"]+".json.gz")).write_bytes(b"PENDING RAW BYTES PRESERVED")
        ledger=self.ns["scale_read_records"](self.main/"request_ledger.jsonl")
        for row in ledger:
            if row["request_key"] in {r["request_key"] for r in unavailable}:
                row.update(usage={}, subprocess_elapsed_s=None, outcome_unavailable=True)
        originals=self.ns["scale_read_records"](self.main/"candidates.jsonl")
        cfg=json.loads((self.main/"protocol.json").read_text())["config"]
        metrics=self.ns["scale_main_metrics"]([], originals, b["interventions"], b["selection"], ledger, cfg, {})
        metrics["primary_decision"]={"criterion_met": False, "rule": "frozen operational rule"}
        self.ns["scale_write_records"](self.main/"interventions.jsonl", b["interventions"])
        self.ns["scale_write_records"](self.main/"request_ledger.jsonl", ledger)
        self.ns["scale_write_json"](self.main/"metrics.json", metrics)
        manifest=json.loads((self.main/"manifest.json").read_text())
        manifest["interventions_hash"]=self.ns["scale_hash"](b["interventions"])
        self.ns["scale_write_json"](self.main/"manifest.json", manifest)
        if amendment003:
            old=[r for r in unavailable if r["case_id"] in b["selection"]["selected_case_ids"][1:3]]
            self.ns["scale_write_json"](self.data/"intervention_resume"/"amendment_002.json", {"unavailable_requests": old})
            keys=sorted(r["request_key"] for r in unavailable)
            cids=sorted(missing)
            self.ns["scale_write_json"](self.data/"intervention_resume_003"/"amendment_003.json",
                {"unavailable_requests":unavailable,"unavailable_request_keys":keys,"unavailable_case_ids":cids})
            self.ns["scale_write_json"](self.data/"intervention_resume_003"/"analysis_plan.json",
                {"unavailable_request_keys":keys,"unavailable_case_ids":cids,"scheduled_pairs":6,
                 "unavailable_outcomes":2*missing_count,"unavailable_whole_pairs":missing_count,
                 "available_pair_target":6-missing_count,"bootstrap_seed":cfg["bootstrap_seed"],"bootstrap_draws":cfg["bootstrap_draws"]})
        else:
            self.ns["scale_write_json"](self.data/"intervention_resume"/"amendment_002.json", {"unavailable_requests": unavailable})
        return missing

    def test_observed_view_examples_categories_figures_summary_and_operational_totals(self):
        missing=self.project_missing()
        report=self.ns["scale_report_load"](self.root)
        rendered=self.ns["scale_report_render"](report)
        relative=self.ns["scale_report_save_analysis"](report, self.root)
        saved=self.root/relative
        first=saved.read_bytes()
        self.ns["scale_report_save_analysis"](report, self.root)
        self.assertEqual(saved.read_bytes(), first)
        saved_analysis=json.loads(first)
        self.assertEqual((saved_analysis["n_scheduled_pairs"], saved_analysis["n_observed_pairs"]), (6, 4))
        self.assertEqual(len(saved_analysis["completion_sensitivity"]), 16)
        self.assertTrue(all(r["hypothetical_only"] for r in saved_analysis["completion_sensitivity"]))
        self.assertEqual(relative, "data/scale_v5/presentation_results/missing_outcome_analysis.json")
        summary=rendered["summary"]
        self.assertEqual((summary["n_scheduled_pairs"], summary["n_observed_pairs"], summary["n_pairs"]), (6, 4, 4))
        self.assertEqual(summary["n_unavailable_pairs"], 2)
        self.assertEqual(summary["target_shortfall"], 0)
        self.assertEqual(len(summary["completion_sensitivity"]), 16)
        self.assertEqual(len(report["operational_interventions"]), 12)
        self.assertEqual(len(report["interventions"]), 8)
        self.assertEqual(report["raw_metrics"]["paired_value_recovery"]["n_pairs"], 6)
        self.assertEqual(report["metrics"]["physical_cli_requests"], report["raw_metrics"]["physical_cli_requests"])
        self.assertEqual(report["metrics"]["usage"], report["raw_metrics"]["usage"])
        self.assertFalse(missing & {r["case_id"] for r in report["examples"]})
        self.assertFalse(missing & set().union(*(set(v) for v in report["categories"].values())))
        self.assertEqual(sum(len(v) for k,v in report["categories"].items() if k!="original_success"), 4)
        self.assertEqual(sum(r["paired_n"] for r in self.ns["scale_report_family_rows"](report)), 4)
        self.assertTrue(all(r["n"]==4 for r in self.ns["scale_report_numeric"](report)))
        self.assertIn("4 unknown responses are not model errors", rendered["markdown"])
        self.assertIn("actual physical starts are between", rendered["markdown"])
        self.assertIn("6 pairs were frozen", rendered["markdown"])
        workflow=self.ns["scale_report_workflow"](report)
        self.assertIn("freeze seeded ranking and selected 6 sources", workflow)
        self.assertIn("4 complete pairs; 2 unavailable pairs", workflow)
        specs=self.ns["scale_report_figures"](report, self.root, write=True)
        self.assertEqual(len(specs), 8)
        self.assertTrue(all((self.root/r["path"]).is_file() for r in specs))

    def test_amendment003_eight_unknown_cells_compact_report_and_dynamic_slot_bounds(self):
        missing=self.project_missing(missing_count=4,amendment003=True)
        report=self.ns["scale_report_load"](self.root)
        rendered=self.ns["scale_report_render"](report)
        analysis=report["missing_outcomes"]
        self.assertEqual((analysis["n_scheduled_pairs"],analysis["n_observed_pairs"],analysis["n_unavailable_outcomes"],analysis["n_completions"]),(6,2,8,256))
        self.assertEqual((rendered["summary"]["n_incomplete_pairs"],rendered["summary"]["n_wholly_unavailable_pairs"],
                          rendered["summary"]["n_unavailable_outcomes"],rendered["summary"]["n_completions"]),(4,4,8,256))
        self.assertEqual(report["raw_metrics"]["paired_value_recovery"]["n_pairs"],6)
        self.assertEqual(report["metrics"]["paired_value_recovery"]["n_pairs"],2)
        self.assertFalse(missing & {r["case_id"] for r in report["examples"]})
        total=report["manifest"]["total_pilot_plus_main_requests"]
        self.assertIn(f"actual physical starts are between {total-8} and {total}",rendered["markdown"])
        self.assertIn("8 unknown responses are not model errors",rendered["markdown"])
        self.assertIn("2^8 = 256",rendered["markdown"])
        self.assertIn("intervention_resume_003/amendment_003.json",rendered["markdown"])
        self.assertIn("full sensitivity results",rendered["markdown"])
        teaching=self.ns["scale_report_model_improvement_markdown"](report)
        self.assertIn("Why improving an already capable model",teaching)
        self.assertIn("6/6 genuine value failures",teaching)
        self.assertIn("8 potential main sources",teaching)
        self.assertIn("all 256 binary completions of 8 unknown outcomes",teaching)
        self.assertIn("0 other typed-field errors",teaching)
        self.assertIn("separately written generators",teaching)
        self.assertIn(f"{analysis['paired_value_recovery']['discordant_pairs']} disagreements",teaching)
        changed=copy.deepcopy(report)
        changed["metrics"]["original_collection"]["value_failure_cases"]=5
        changed["protocol"]["blocks"][0]["manifest"]["n_cases"]=11
        changed["pilot"][0]["metrics"]["value_failure_cases"]=1
        dynamic=self.ns["scale_report_model_improvement_markdown"](changed)
        self.assertIn("5/6 genuine value failures",dynamic)
        self.assertIn("13 potential main sources",dynamic)
        self.assertIn("1/2 genuine value failures at 128 shipments",dynamic)
        sensitivity=self.ns["scale_report_missing_markdown"](report)
        rows=[line for line in sensitivity.splitlines() if line.startswith("| ")]
        self.assertLessEqual(len(rows),16) # two headers + eight identities + up to four extreme rows
        path=self.root/self.ns["scale_report_save_analysis"](report,self.root)
        self.assertEqual(len(json.loads(path.read_bytes())["completion_sensitivity"]),256)

    def test_amendment003_rejects_changed_bound_metadata(self):
        self.project_missing(missing_count=4,amendment003=True)
        path=self.data/"intervention_resume_003"/"analysis_plan.json"
        original=json.loads(path.read_bytes())
        for field,value in (("unavailable_outcomes",4),("scheduled_pairs",600),("available_pair_target",596),
                            ("bootstrap_seed",1),("unavailable_request_keys",["wrong"])):
            bad={**original,field:value}
            self.ns["scale_write_json"](path,bad)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.ns["scale_report_load"](self.root)
        self.ns["scale_write_json"](path,original)
        prior=self.data/"intervention_resume"/"amendment_002.json"
        self.ns["scale_write_json"](prior,{"unavailable_requests":[{"case_id":"changed","arm":"fresh_retry","request_key":"changed"}]})
        with self.assertRaisesRegex(ValueError,"preserved"):
            self.ns["scale_report_load"](self.root)

    def project_timeout004(self, parsed_answer=True):
        self.project_missing(missing_count=4,amendment003=True)
        rows=self.ns["scale_read_records"](self.main/"interventions.jsonl")
        originals=self.ns["scale_read_records"](self.main/"candidates.jsonl")
        cid=self.bundle["selection"]["selected_case_ids"][0]
        row=next(r for r in rows if r["case_id"]==cid and r["arm"]=="feedback_repair")
        old=next(r for r in originals if r["case_id"]==cid)
        case=self.engine.cases[cid]
        answer=self.ns["scale_correct_response"](case) if parsed_answer else None
        if answer:
            answer["answer"]["quantity_units"]+=999
            answer["answer"]["unit_price_cents"]+=111
        error="Codex CLI exceeded timeout of 900 seconds"
        verification=self.ns["scale_validate_answer"](case,None)
        row.update(response=answer,verification=verification,transport_error=error,error_kind="transport_failure",
                   numeric_absolute_errors=self.ns["scale_numeric_errors"](case,answer),
                   original_wrong_fields_fixed=[],new_wrong_fields=[f for f in self.ns["SCALE_FIELDS"] if old["verification"]["field_correct"][f]],
                   worsened_numeric_fields=["quantity_units","unit_price_cents"] if answer else [],answer_unchanged=False)
        cache_path=self.main/"cache"/(row["request_key"]+".json.gz")
        with gzip.open(cache_path,"rt",encoding="utf-8") as stream: cached=json.load(stream)
        cached["attempts"][-1].update(error=error,timed_out=True,return_code=0,elapsed_s=4534.9535893,
            parsed={"results":[answer]} if answer else None,
            final_assistant_response=json.dumps({"results":[answer]}) if answer else "",usage={"input_tokens":100,"output_tokens":20})
        with gzip.open(cache_path,"wt",encoding="utf-8") as stream: json.dump(cached,stream)
        ledger=self.ns["scale_read_records"](self.main/"request_ledger.jsonl")
        for entry in ledger:
            if entry["request_key"]==row["request_key"]:
                entry.update(transport_error=error,return_code=0,subprocess_elapsed_s=4534.9535893,usage={"input_tokens":100,"output_tokens":20})
        cfg=json.loads((self.main/"protocol.json").read_bytes())["config"]
        metrics=self.ns["scale_main_metrics"]([],originals,rows,self.bundle["selection"],ledger,cfg,{})
        self.ns["scale_write_records"](self.main/"interventions.jsonl",rows)
        self.ns["scale_write_records"](self.main/"request_ledger.jsonl",ledger)
        self.ns["scale_write_json"](self.main/"metrics.json",metrics)
        manifest=json.loads((self.main/"manifest.json").read_bytes())
        manifest["interventions_hash"]=self.ns["scale_hash"](rows)
        self.ns["scale_write_json"](self.main/"manifest.json",manifest)
        item={key:row[key] for key in ("request_key","case_id","arm","stage","sample","content_hash","request_input_hash","feedback_hash")}
        item.update(cache_sha256=hashlib.sha256(cache_path.read_bytes()).hexdigest(),dispatch_index=535,error=error,
                    attempt_metadata={"timed_out":True,"return_code":0,"elapsed_s":4534.9535893},usage_present=True)
        binding=lambda path:{"path":path,"sha256":hashlib.sha256((self.data/path).read_bytes()).hexdigest()}
        amendment={"retained_transport_failures":[item],"retained_terminal_failure_request_keys":[row["request_key"]],
                   "predecessor":binding("intervention_resume_003/amendment_003.json"),
                   "analysis_plan":binding("intervention_resume_003/analysis_plan.json")}
        self.ns["scale_write_json"](self.data/"intervention_resume_004"/"amendment_004.json",amendment)
        return row,cached

    def test_timeout004_parsed_answer_policy_and_diagnostic_taxonomy(self):
        row,cached=self.project_timeout004()
        before=self.ns["scale_read_records"](self.main/"interventions.jsonl")
        report=self.ns["scale_report_load"](self.root)
        rendered=self.ns["scale_report_render"](report)
        analysis=report["missing_outcomes"]
        self.assertEqual((analysis["n_scheduled_pairs"],analysis["n_observed_pairs"],analysis["n_unavailable_outcomes"],analysis["n_completions"]),(6,2,8,256))
        raw=next(r for r in report["operational_interventions"] if r["request_key"]==row["request_key"])
        scientific=next(r for r in report["interventions"] if r["request_key"]==row["request_key"])
        self.assertEqual(raw,row)
        self.assertIsNotNone(raw["response"])
        self.assertFalse(self.ns["scale_report_good"](raw))
        self.assertTrue(raw["new_wrong_fields"])
        self.assertTrue(raw["worsened_numeric_fields"])
        self.assertEqual(scientific["new_wrong_fields"],[])
        self.assertEqual(scientific["worsened_numeric_fields"],[])
        repair=next(r for r in report["metrics"]["interventions"] if r["arm"]=="feedback_repair")
        raw_repair=next(r for r in report["raw_metrics"]["interventions"] if r["arm"]=="feedback_repair")
        self.assertGreater(raw_repair["cases_with_new_wrong_fields"],repair["cases_with_new_wrong_fields"])
        self.assertEqual(repair["error_categories"]["transport_failure"],1)
        self.assertEqual(repair["cases_with_new_wrong_fields"],0)
        self.assertEqual(repair["cases_with_worsened_numeric_error"],0)
        self.assertEqual(report["raw_metrics"]["paired_value_recovery"]["n_pairs"],6)
        self.assertEqual(report["metrics"]["paired_value_recovery"]["n_pairs"],2)
        for numeric in self.ns["scale_report_numeric"](report):
            if numeric["stage"]=="feedback_repair": self.assertEqual((numeric["n_numeric"],numeric["n"]),(1,2))
        self.assertEqual(report["metrics"]["usage"],report["raw_metrics"]["usage"])
        self.assertEqual(self.ns["scale_read_records"](self.main/"interventions.jsonl"),before)
        self.assertIn("Known transport failures",rendered["markdown"])
        self.assertIn("Transport failure; not field-scored",rendered["markdown"])
        self.assertIn("frozen policy scores non-recovery",rendered["markdown"])
        self.assertIn("intervention_resume_004/amendment_004.json",rendered["markdown"])
        self.assertIn("4534.9535893",rendered["markdown"])
        prompt_report=copy.copy(report)
        prompt_report["examples"]=[{"case_id":row["case_id"],"category":"neither_recovers"}]
        self.assertIn("retained raw answer is excluded",self.ns["scale_report_prompt_markdown"](prompt_report))
        namespace,_=refresh.scale_report_namespace(self.root)
        refreshed=namespace["scale_report_load"](self.root)
        self.assertEqual(refreshed["missing_outcomes"],analysis)

    def test_timeout004_without_parsed_answer_and_bound_identity_validation(self):
        row,_=self.project_timeout004(parsed_answer=False)
        report=self.ns["scale_report_load"](self.root)
        self.assertEqual(report["missing_outcomes"]["n_observed_pairs"],2)
        path=self.data/"intervention_resume_004"/"amendment_004.json"
        original=json.loads(path.read_bytes())
        for change in ("key","error","predecessor","analysis_plan","unknown_expansion"):
            bad=copy.deepcopy(original)
            if change=="key": bad["retained_transport_failures"][0]["request_key"]="wrong"
            elif change=="error": bad["retained_transport_failures"][0]["error"]="wrong"
            elif change in ("predecessor","analysis_plan"): bad[change]["sha256"]="wrong"
            else: bad["unavailable_request_keys"]=["new-key"]
            self.ns["scale_write_json"](path,bad)
            with self.subTest(change=change), self.assertRaises(ValueError): self.ns["scale_report_load"](self.root)

    def test_pending_loader_does_not_open_any_intervention_artifact(self):
        manifest=json.loads((self.main/"manifest.json").read_text())
        manifest["phase"]="originals_complete"
        self.ns["scale_write_json"](self.main/"manifest.json", manifest)
        original=self.ns["scale_report_rows"]
        def forbid(path):
            raise AssertionError("Pending loader read efficacy rows: "+str(path))
        self.ns["scale_report_rows"]=forbid
        try:
            report=self.ns["scale_report_load"](self.root)
            rendered=self.ns["scale_report_render"](report)
            self.assertEqual(rendered["state"], "pending")
            self.assertIsNone(report["missing_outcomes"])
            self.assertNotIn("Why improving an already capable model",rendered["markdown"])
            with self.assertRaisesRegex(ValueError,"completed results"):
                self.ns["scale_report_model_improvement_markdown"](report)
            with self.assertRaisesRegex(ValueError, "interventions_complete"):
                self.ns["scale_report_save_analysis"](report, self.root)
            self.assertFalse((self.data/"presentation_results").exists())
        finally:
            self.ns["scale_report_rows"]=original

    def test_actual_refresh_namespace_and_build_complete_mock_bundle(self):
        self.project_missing()
        namespace, helper=refresh.scale_report_namespace(self.root)
        self.assertIsNot(namespace, self.ns)
        self.assertTrue(callable(namespace["scale_paired_statistics"]))
        self.assertTrue(callable(namespace["scale_main_metrics"]))
        self.assertIn("def scale_missing_outcome_analysis", helper)
        # Forbid a subprocess or phase replay after constructing the fresh
        # namespace. Only frozen definitions and cached report reads are needed.
        def no_live(*args, **kwargs):
            raise AssertionError("Report attempted an engine phase or model call")
        for name in ("scale_call_model", "scale_collect_originals", "scale_run_interventions"):
            namespace[name]=no_live
        report=namespace["scale_report_load"](self.root)
        self.assertEqual(report["metrics"]["paired_value_recovery"]["n_pairs"], 4)
        self.assertEqual(report["missing_outcomes"]["n_scheduled_pairs"], 6)
        built=refresh.build(self.root, write=False)
        self.assertEqual(built["summary"]["n_pairs"], 4)
        self.assertEqual(built["summary"]["n_scheduled_pairs"], 6)
        self.assertEqual(len(built["cells"]), 3)
        self.assertEqual(built["state"], "complete")
        written=refresh.build(self.root, write=True)
        analysis_path=self.root/written["analysis_path"]
        self.assertEqual(json.loads(analysis_path.read_bytes())["n_observed_pairs"], 4)
        self.assertIn("scale_report_save_analysis", written["replay_code"])
        packaged=self.data/"presentation_source"/"refresh_scale_report.py"
        packaged.parent.mkdir()
        packaged.write_bytes(Path(refresh.__file__).read_bytes())
        # Importing the saved script checks only protocol-file existence. It
        # must not build or inspect any outcome file to select its default root.
        with patch.dict(os.environ):
            os.environ.pop("NOTEBOOK_REPO_ROOT", None)
            detected=runpy.run_path(str(packaged))
            self.assertEqual(detected["REPO_ROOT"], self.root)
            os.environ["NOTEBOOK_REPO_ROOT"]=str(self.root/"explicit-override")
            overridden=runpy.run_path(str(packaged))
            self.assertEqual(overridden["REPO_ROOT"], self.root/"explicit-override")
            os.environ.pop("NOTEBOOK_REPO_ROOT")
            (self.main/"protocol.json").unlink()
            fallback=runpy.run_path(str(packaged))
            self.assertEqual(fallback["REPO_ROOT"], Path(r"C:\Users\sandh\.codex\worktrees\synthetic-data-curation\experiment_notebooks"))


class AmendedDecisionTest(unittest.TestCase):
    def test_complete_case_significance_cannot_override_missing_outcome_sensitivity(self):
        ns=mocked_engine.scale_test_namespace()
        ids=[f"mock-{i}" for i in range(8)]
        rows=[]; unavailable=[]
        for i, cid in enumerate(ids):
            for arm in missing_analysis.SCALE_MISSING_ARMS:
                absent=i>=6
                row={"case_id": cid, "arm": arm, "request_key": cid+arm,
                     "outcome_unavailable": absent, "transport_error": "interrupted" if absent else None,
                     "response": None if absent else {"mock": True},
                     "verification": {"valid_schema": not absent,
                                      "exact_fields": not absent and arm=="feedback_repair"}}
                rows.append(row)
                if absent: unavailable.append({k:row[k] for k in ("case_id", "arm", "request_key")})
        result=missing_analysis.scale_missing_outcome_analysis(
            {"phase":"interventions_complete"}, {"selected_case_ids":ids}, rows, unavailable,
            {"bootstrap_seed":246600,"bootstrap_draws":200}, ns["scale_paired_statistics"])
        self.assertLess(result["paired_value_recovery"]["exact_mcnemar_two_sided_p"], .05)
        self.assertGreater(result["paired_value_recovery"]["repair_minus_fresh_difference"], 0)
        self.assertFalse(result["amended_primary_decision"]["criterion_met"])
        self.assertEqual(result["amended_primary_decision"]["decision"], "inconclusive")
        self.assertGreater(result["amended_primary_decision"]["completions_meeting_criterion"], 0)
        self.assertLess(result["amended_primary_decision"]["completions_meeting_criterion"], 16)


if __name__=="__main__":
    unittest.main()
