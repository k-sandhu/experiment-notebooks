"""Synthetic only: no real study artifact, answer, flag, cache or model access."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


def fixture(partner_success=True):
    ns = {"__name__": "mock_missing006"}
    for name in ("scale_missing_outcomes_003.py", "scale_missing_outcomes_006.py"):
        exec(compile(Path(__file__).with_name(name).read_text(), name, "exec"), ns)
    ids = ["mock-%03d" % i for i in range(600)]
    unknown, previous, rows = [], [], []
    for i, cid in enumerate(ids):
        for arm in ns["SCALE_MISSING_ARMS"]:
            absent = i < 4 or (i == 4 and arm == "feedback_repair")
            row = {"case_id": cid, "arm": arm, "request_key": cid + ":" + arm,
                   "outcome_unavailable": absent,
                   "transport_error": "controller outcome unavailable" if absent else None,
                   "response": None if absent else {"synthetic_fixture_only": True},
                   "verification": {"valid_schema": not absent,
                                    "exact_fields": not absent and (partner_success if i == 4 else i % 3 == 0)}}
            rows.append(row)
            if absent:
                item = {k: row[k] for k in ("case_id", "arm", "request_key")}
                unknown.append(item)
                if i < 4:
                    previous.append(item)
    partner = {"case_id": ids[4], "arm": "fresh_retry",
               "request_key": ids[4] + ":fresh_retry", "cache_sha256": "a" * 64}
    plan = {"scheduled_pairs": 600, "observed_pair_target": 595, "unknown_outcomes": 9,
            "unknown_whole_pairs": 4, "unknown_partial_pairs": 1,
            "hypothetical_completions": 512, "bootstrap_seed": 246600,
            "bootstrap_samples": 20000, "unknown_request_keys": sorted(r["request_key"] for r in unknown),
            "unknown_case_ids": ids[:5], "known_partners": [partner],
            "partial_pair_case_id": ids[4], "known_partner_request_key": partner["request_key"]}
    return ns, {"phase": "interventions_complete"}, {"selected_case_ids": ids}, rows, unknown, plan, previous


def mock_paired_statistics(pairs, seed, draws):
    """Count-only test double; 003 bootstrap correctness has separate tests."""
    return {"n_pairs": len(pairs), "bootstrap_seed": seed, "bootstrap_draws": draws}


class Missing006Tests(unittest.TestCase):
    def analyze(self, success=True):
        ns, manifest, selection, rows, unknown, plan, previous = fixture(success)
        result = ns["scale_missing_outcome_analysis_006"](
            manifest, selection, rows, unknown, {"bootstrap_seed": 246600, "bootstrap_draws": 20000},
            plan, previous, mock_paired_statistics, bootstrap_envelope=False)
        return result

    def test_all_512_completions_preserve_the_known_partial_partner(self):
        result = self.analyze(True)
        self.assertEqual(result["n_observed_pairs"], 595)
        self.assertEqual(result["n_wholly_unavailable_pairs"], 4)
        self.assertEqual(result["n_unavailable_outcomes"], 9)
        self.assertEqual(result["n_completions"], 512)
        for completion in result["completion_sensitivity"]:
            self.assertEqual(completion["n_pairs"], 600)
            partial = next(r for r in completion["assignments"] if r["case_id"] == "mock-004")
            self.assertTrue(partial["fresh_success"])
            self.assertEqual(partial["unavailable_arms"], ["feedback_repair"])
            self.assertTrue(completion["hypothetical_only"])
            self.assertEqual(len(completion["hypothetical_cell_assignments"]), 9)

    def test_known_partner_changes_all_cohort_bounds_but_not_complete_pair_inference(self):
        right, wrong = self.analyze(True), self.analyze(False)
        self.assertEqual(right["paired_value_recovery"], wrong["paired_value_recovery"])
        for a, b in zip(right["scheduled_difference_bounds"], wrong["scheduled_difference_bounds"]):
            self.assertAlmostEqual(b - a, 1 / 600)
        for a, b in zip(right["completion_sensitivity"], wrong["completion_sensitivity"]):
            self.assertAlmostEqual(b["repair_minus_fresh_difference"] - a["repair_minus_fresh_difference"], 1 / 600)

    def test_pending_gate_precedes_access_to_all_efficacy_inputs(self):
        ns, _, _, _, unknown, plan, previous = fixture()
        class Poison:
            def __iter__(self): raise AssertionError("efficacy accessed")
            def __getitem__(self, key): raise AssertionError("efficacy accessed")
        with self.assertRaisesRegex(ValueError, "interventions_complete"):
            ns["scale_missing_outcome_analysis_006"](
                {"phase": "originals_complete"}, Poison(), Poison(), unknown, Poison(), plan, previous)

    def test_identity_count_setting_and_partner_tampering_are_rejected(self):
        ns, manifest, selection, rows, unknown, plan, previous = fixture()
        changes = ["unknown_outcomes", "unknown_whole_pairs", "unknown_partial_pairs",
                   "hypothetical_completions", "bootstrap_samples", "bootstrap_seed",
                   "unknown_request_keys", "partial_pair_case_id", "known_partner_request_key", "known_partners"]
        for key in changes:
            bad = copy.deepcopy(plan)
            bad[key] = bad[key] + 1 if isinstance(bad[key], int) else [] if isinstance(bad[key], list) else "changed"
            with self.subTest(key=key), self.assertRaises(ValueError):
                ns["scale_missing_validate_plan_006"](bad, unknown, previous)
        changed = copy.deepcopy(previous)
        changed[0]["request_key"] = "changed"
        with self.assertRaises(ValueError): ns["scale_missing_validate_plan_006"](plan, unknown, changed)
        known = next(r for r in rows if r["request_key"] == plan["known_partner_request_key"])
        known["outcome_unavailable"] = True
        with self.assertRaisesRegex(ValueError, "partner"):
            ns["scale_missing_outcome_analysis_006"](
                manifest, selection, rows, unknown, {"bootstrap_seed": 246600, "bootstrap_draws": 20000},
                plan, previous, mock_paired_statistics, bootstrap_envelope=False)

    def test_reporting_binds_old_and_new_plan_and_known_partner_bytes(self):
        ns, _, _, _, unknown, plan, previous = fixture()
        source=Path(__file__).with_name("scale_reporting.py").read_text(encoding="utf-8")
        exec(compile(source,"scale_reporting.py","exec"),ns)
        with tempfile.TemporaryDirectory(prefix="missing006-report-mock-") as temp:
            data=Path(temp); main=data/"main"; (main/"cache").mkdir(parents=True)
            payload=b"synthetic observed partner cache bytes only"
            partner=plan["known_partners"][0]
            partner["cache_sha256"]=hashlib.sha256(payload).hexdigest()
            cache=main/"cache"/(partner["request_key"]+".json.gz");cache.write_bytes(payload)
            transport={"retained_transport_failures":[{"request_key":"mock-timeout"},{"request_key":"mock-capacity"}]}
            amendment={"retained_transport_failures":copy.deepcopy(transport["retained_transport_failures"])}
            for key,relative,value in (("predecessor","intervention_resume_005/amendment_005.json",transport),
                                       ("previous_analysis_plan","intervention_resume_003/analysis_plan.json",{"old8":"unchanged"}),
                                       ("analysis_plan","intervention_resume_006/analysis_plan.json",plan)):
                path=data/relative;path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(value))
                amendment[key]={"path":relative,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
            plan["previous_analysis_plan"]=copy.deepcopy(amendment["previous_analysis_plan"])
            # Rebind the exact new plan after adding its lineage declaration.
            plan_path=data/amendment["analysis_plan"]["path"];plan_path.write_text(json.dumps(plan))
            amendment["analysis_plan"]["sha256"]=hashlib.sha256(plan_path.read_bytes()).hexdigest()
            historical={"analysis_plan":copy.deepcopy(amendment["previous_analysis_plan"])}
            check=lambda a:ns["scale_report_validate_006"](data,main,a,transport,historical,plan,unknown,previous)
            self.assertEqual(check(amendment)["known_partner"],partner)
            for key in ("predecessor","previous_analysis_plan","analysis_plan"):
                bad=copy.deepcopy(amendment);bad[key]["sha256"]="changed"
                with self.subTest(binding=key),self.assertRaises(ValueError):check(bad)
            historical["analysis_plan"]["sha256"]="changed declared historical hash"
            with self.assertRaisesRegex(ValueError,"binding declared by amendment 003"):check(amendment)
            historical["analysis_plan"]=copy.deepcopy(amendment["previous_analysis_plan"])
            plan["previous_analysis_plan"]["sha256"]="changed plan historical hash"
            with self.assertRaisesRegex(ValueError,"declared analysis predecessor"):check(amendment)
            plan["previous_analysis_plan"]=copy.deepcopy(amendment["previous_analysis_plan"])
            bad=copy.deepcopy(amendment);bad["retained_transport_failures"].pop()
            with self.assertRaisesRegex(ValueError,"terminal service"):check(bad)
            cache.write_bytes(payload+b"changed")
            with self.assertRaisesRegex(ValueError,"known partner cache bytes"):check(amendment)


if __name__ == "__main__": unittest.main()
