"""Temporary gates/mock namespaces only. No actual study outcomes or model calls."""
from contextlib import redirect_stdout
from datetime import datetime,timezone
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_scale_interventions_reviewed as runner


class ReviewedInterventionRunner(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix="scale_intervention_runner_control_")
        self.root=Path(self.temporary.name);self.data=self.root/"data"/"scale_v5"
        self.amendment=self.data/runner.AMENDMENT_ARCHIVE
        self.required=[runner.RUNNER_ARCHIVE,runner.COMPANION_ARCHIVE,runner.AMENDMENT_ARCHIVE,
            runner.SOURCE_REVIEW,runner.RUNNER_REVIEW,"source_freeze.json","main/protocol.json",
            "main/allocation.json","main/original_manifest.json","main/selection.json"]
        self.write(runner.RUNNER_ARCHIVE,Path(runner.__file__).read_bytes())
        self.write(runner.COMPANION_ARCHIVE,b"# Mock reviewed implementation; never executed by these gate tests.\n")
        for name in ["source_freeze.json","main/protocol.json","main/allocation.json","main/selection.json"]:
            self.write_json(name,{"CONTROL_ONLY":True})
        self.write_json("main/original_manifest.json",{"phase":"originals_complete"})
        self.write_json(runner.SOURCE_REVIEW,{"passed":True,"model_calls":0,"issues":[]})
        self.write_json(runner.RUNNER_REVIEW,{"passed":True,"live_model_calls":0,"issues":[]})
        self.write_json(runner.AMENDMENT_ARCHIVE,{"protocol":"23-scale-v5","amendment_version":"23-scale-capacity-continuation-v1",
            "declared_at_utc":"2000-01-01T00:00:00+00:00","implementation":{"path":runner.COMPANION_ARCHIVE,"sha256":runner.sha256(self.data/runner.COMPANION_ARCHIVE)}})
        self.bind()

    def tearDown(self):self.temporary.cleanup()

    def write(self,name,raw):
        path=self.data/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return path

    def write_json(self,name,value):return self.write(name,(json.dumps(value,sort_keys=True)+"\n").encode())

    def bind(self,**overrides):
        self.gate={"protocol":"23-scale-v5","phase":runner.GATE_PHASE,"material_review_passed":True,
            "declared_at_utc":"2001-01-01T00:00:00+00:00","sha256":{name:runner.sha256(self.data/name) for name in self.required}}
        self.gate.update(overrides);self.write_json("intervention_start_declaration.json",self.gate)

    def mock_companion(self,events,exception=None):
        namespace={"SCALE_ARMS":["fresh_retry","feedback_repair"],"scale_dispatch_waves":"FROZEN_DISPATCH"}
        def phase(**kwargs):
            events.append(("phase",kwargs))
            self.assertEqual(namespace["scale_dispatch_waves"],"APPROVED_DISPATCH")
            if exception:raise exception
            return {"manifest":{"phase":"interventions_complete"},"metrics":{"CONTROL_ONLY":True}}
        namespace["scale_run_interventions"]=phase
        namespace["scale_collect_originals"]=lambda **k:(_ for _ in ()).throw(AssertionError("Original collector must never run"))
        def load(root):events.append(("load",root));return namespace
        def install(root,amendment,ns):
            self.assertIs(ns,namespace);events.append(("install",root,amendment));ns["scale_dispatch_waves"]="APPROVED_DISPATCH"
        return {"scale_resume_load":load,"scale_resume_install":install}

    def test_offline_default_uses_fresh_namespace_then_installs_before_direct_arm_call(self):
        events=[];stdout=io.StringIO();callback=lambda event:None
        with patch.object(runner,"load_approved_companion",return_value=self.mock_companion(events)),redirect_stdout(stdout):
            result=runner.run(self.root,self.amendment,progress=callback)
        self.assertEqual([e[0] for e in events],["load","install","phase"])
        self.assertIs(events[-1][1]["live"],False);self.assertIs(events[-1][1]["progress"],callback)
        self.assertEqual(result["manifest"]["phase"],"interventions_complete")
        provenance=json.loads(stdout.getvalue().splitlines()[0])
        self.assertEqual(provenance["gate_sha256"],runner.sha256(self.data/"intervention_start_declaration.json"))
        self.assertEqual(provenance["runner_sha256"],runner.sha256(runner.__file__))
        self.assertEqual(provenance["companion_sha256"],runner.sha256(self.data/runner.COMPANION_ARCHIVE))

    def test_explicit_initial_live_flag_is_passed_without_retries(self):
        events=[]
        with patch.object(runner,"load_approved_companion",return_value=self.mock_companion(events)),redirect_stdout(io.StringIO()):
            runner.run(self.root,self.amendment,live=True)
        self.assertIs(events[-1][1]["live"],True)
        self.assertEqual(sum(e[0]=="phase" for e in events),1)

    def test_wrong_gate_phase_or_review_flag_blocks_before_loading(self):
        for change in [{"phase":"originals"},{"material_review_passed":False},{"protocol":"OTHER"}]:
            with self.subTest(change=change):
                self.bind(**change)
                with patch.object(runner,"load_approved_companion") as load,self.assertRaises(ValueError):runner.run(self.root,self.amendment)
                load.assert_not_called()

    def test_missing_or_changed_binding_blocks(self):
        self.gate["sha256"].pop(runner.RUNNER_REVIEW);self.write_json("intervention_start_declaration.json",self.gate)
        with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment)
        self.bind();self.write("main/selection.json",b"changed")
        with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment)

    def test_executing_runner_must_match_archived_bytes(self):
        self.write(runner.RUNNER_ARCHIVE,Path(runner.__file__).read_bytes()+b"\n# Different runner\n");self.bind()
        with self.assertRaisesRegex(ValueError,"Executing runner bytes"):runner.verify_gate(self.root,self.amendment)

    def test_companion_must_match_amendment_and_gate(self):
        self.write(runner.COMPANION_ARCHIVE,b"# Different implementation\n");self.bind()
        with self.assertRaisesRegex(ValueError,"byte-reviewed implementation"):runner.verify_gate(self.root,self.amendment)

    def test_both_reviews_must_pass_without_model_calls_or_issues(self):
        cases=[(runner.SOURCE_REVIEW,{"passed":False,"model_calls":0}),
               (runner.SOURCE_REVIEW,{"passed":True,"model_calls":1}),
               (runner.SOURCE_REVIEW,{"passed":True,"model_calls":False}),
               (runner.SOURCE_REVIEW,{"passed":True,"model_calls":0,"issues":["unresolved"]}),
               (runner.RUNNER_REVIEW,{"passed":True,"live_model_calls":1}),
               (runner.RUNNER_REVIEW,{"passed":False,"live_model_calls":0})]
        for name,value in cases:
            with self.subTest(name=name,value=value):
                self.write_json(runner.SOURCE_REVIEW,{"passed":True,"model_calls":0,"issues":[]})
                self.write_json(runner.RUNNER_REVIEW,{"passed":True,"live_model_calls":0,"issues":[]})
                self.write_json(name,value);self.bind()
                with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment)

    def test_timestamp_timezone_future_and_amendment_order(self):
        for timestamp in ["2001-01-01T00:00:00","2099-01-01T00:00:00+00:00","1999-01-01T00:00:00+00:00"]:
            with self.subTest(timestamp=timestamp):
                self.bind(declared_at_utc=timestamp)
                with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment)

    def test_originals_and_audit_must_be_complete(self):
        self.write_json("main/original_manifest.json",{"phase":"audit_pending"});self.bind()
        with self.assertRaisesRegex(ValueError,"originals and audit"):runner.verify_gate(self.root,self.amendment)

    def test_live_refuses_completed_manifest_but_offline_remains_available(self):
        self.write_json("main/manifest.json",{"phase":"interventions_complete"})
        with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment,live=True)
        self.assertIn("gate_sha256",runner.verify_gate(self.root,self.amendment,live=False))

    def test_live_refuses_any_fresh_or_repair_cache(self):
        path=self.data/"main/cache/CONTROL.json.gz"
        for stage,sample in [("generate",1),("repair",0)]:
            with self.subTest(stage=stage):
                self.write("main/cache/CONTROL.json.gz",gzip.compress(json.dumps({"request":{"stage":stage,"sample":sample}}).encode()))
                with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment,live=True)
                runner.verify_gate(self.root,self.amendment,live=False)
        path.unlink()
        self.write("main/cache/CONTROL.json.gz",gzip.compress(json.dumps({"request":{"stage":"generate","sample":0}}).encode()))
        runner.verify_gate(self.root,self.amendment,live=True)

    def test_exception_propagates_without_restart_or_final_metrics(self):
        events=[];stdout=io.StringIO()
        with patch.object(runner,"load_approved_companion",return_value=self.mock_companion(events,RuntimeError("NEW CONTROL ERROR"))),redirect_stdout(stdout):
            with self.assertRaisesRegex(RuntimeError,"NEW CONTROL ERROR"):runner.run(self.root,self.amendment,live=True)
        self.assertEqual(sum(e[0]=="phase" for e in events),1)
        self.assertNotIn('"metrics"',stdout.getvalue())

    def test_cli_progress_filters_answer_or_efficacy_fields(self):
        def fake_run(root,amendment,live=False,progress=None):
            self.assertFalse(live)
            progress({"arm":"fresh_retry","case_id":"CONTROL","cached":False,"transport_failure":False,"answer":"FORBIDDEN","score":.99})
            return {"manifest":{"phase":"interventions_complete"},"metrics":{"CONTROL_ONLY":True}}
        args=[runner.__file__,"--root",str(self.root),"--amendment",str(self.amendment)]
        stdout=io.StringIO()
        with patch("sys.argv",args),patch.object(runner,"run",side_effect=fake_run),redirect_stdout(stdout):runner.main()
        first=json.loads(stdout.getvalue().splitlines()[0])
        self.assertEqual(set(first),{"event","completed_this_phase","arm","case_id","cached","transport_failure"})
        self.assertNotIn("FORBIDDEN",stdout.getvalue());self.assertNotIn('"score"',stdout.getvalue())

    def test_gate_paths_cannot_escape_data_root(self):
        for name in ["../outside.json",str(self.root/"outside.json")]:
            self.gate["sha256"][name]="0"*64;self.write_json("intervention_start_declaration.json",self.gate)
            with self.assertRaises(ValueError):runner.verify_gate(self.root,self.amendment)
            self.bind()

    def test_real_approved_dispatcher_drains_new_arm_error_and_preserves_original_stop(self):
        # Real companion code, but fake gate/root/namespace/invoke. Zero model calls.
        companion_source=Path(runner.__file__).with_name("scale_resume.py").read_bytes()
        self.write(runner.COMPANION_ARCHIVE,companion_source)
        amendment=runner.read_json(self.amendment);amendment["implementation"]["sha256"]=runner.sha256(self.data/runner.COMPANION_ARCHIVE)
        self.write_json(runner.AMENDMENT_ARCHIVE,amendment);self.bind()
        companion=runner.load_approved_companion(runner.verify_gate(self.root,self.amendment))
        original_stop=self.write("main/infrastructure_stop.json",b"ORIGINAL RETAINED STOP CONTROL\n")
        before=original_stop.read_bytes();calls=[];phase_calls=[];known_key="a"*64
        class ControlStop(RuntimeError):pass
        namespace={"SCALE_PROTOCOL":"23-scale-v5","SCALE_ARMS":["fresh_retry","feedback_repair"],
                   "SCALE_InfrastructureStop":ControlStop,"scale_dispatch_waves":lambda *a,**k:None,
                   "scale_write_json":lambda *a,**k:None,"scale_collect_originals":lambda *a,**k:None}
        state={"root":self.root.resolve(),"data":self.data,"main":self.data/"main","amendment_sha256":"1"*64,
               "amendment":{},"freeze":{},"cache_hashes":{},"approved":{known_key:{"case_id":"CONTROL-0","transport_error":"CAPACITY CONTROL",
                   "request_input_hash":"input-control","content_hash":"content-control"}}}
        companion["scale_resume_verify"]=lambda *a,**k:state
        companion["scale_resume_load"]=lambda root:namespace
        jobs=[{"case":{"case_id":"CONTROL-"+str(i)},"arm":"fresh_retry" if i%2==0 else "feedback_repair",
               "request_key":known_key if i==0 else format(i,"064x")} for i in range(6)]
        def invoke(job):
            calls.append(job["case"]["case_id"]);bad=job["case"]["case_id"]=="CONTROL-0"
            row={"case_id":job["case"]["case_id"],"arm":job["arm"],"request_key":job["request_key"],
                 "transport_error":"CAPACITY CONTROL" if bad else None,"stage":"generate" if job["arm"]=="fresh_retry" else "repair",
                 "sample":1 if job["arm"]=="fresh_retry" else 0,"split":"collection","request_input_hash":"input-control",
                 "content_hash":"content-control","response":None}
            return row,{"request_key":row["request_key"],"cached_this_run":True}
        def phase(**kwargs):
            phase_calls.append(True)
            return namespace["scale_dispatch_waves"](jobs,invoke,self.data/"main",max_workers=4,progress=kwargs["progress"])
        namespace["scale_run_interventions"]=phase
        with patch.object(runner,"load_approved_companion",return_value=companion),redirect_stdout(io.StringIO()):
            with self.assertRaises(ControlStop):runner.run(self.root,self.amendment,live=True)
        self.assertEqual(len(calls),4);self.assertEqual(len(phase_calls),1)
        self.assertEqual(original_stop.read_bytes(),before)
        self.assertEqual(state["bypassed_cached_failure_keys"],[])
        stops=list((self.data/"main").glob("infrastructure_stop_resume_*.json"));self.assertEqual(len(stops),1)
        self.assertEqual(runner.read_json(stops[0])["remaining_jobs_not_dispatched"],2)


if __name__=="__main__":unittest.main()
