"""Post-freeze reporting tests; synthetic responses only, no study artifacts."""
from pathlib import Path
import copy
import unittest
from test_scale_missing_outcomes_006 import fixture


class Observed006Tests(unittest.TestCase):
    def namespace(self):
        ns,*rest=fixture()
        exec(compile(Path(__file__).with_name('scale_reporting.py').read_text(encoding='utf-8'),'scale_reporting.py','exec'),ns)
        return ns,rest

    def test_curation_keeps_an_accepted_observed_partner_of_an_unknown_answer(self):
        ns,(_,_,rows,unknown,plan,_)=self.namespace()
        unknown_ids={r['case_id'] for r in unknown}
        for row in rows:
            row.update(split='collection',semantic_hash=row['case_id'])
            row['verification']['accepted']=row['verification']['exact_fields']
        report={'originals':[], 'interventions':[r for r in rows if r['case_id'] not in unknown_ids],
                'operational_interventions':rows}
        fresh=sum(ns['scale_report_accepted'](r) for r in rows if r['arm']=='fresh_retry')
        repair=sum(ns['scale_report_accepted'](r) for r in rows if r['arm']=='feedback_repair')
        self.assertEqual(sum(not r['outcome_unavailable'] for r in rows if r['arm']=='fresh_retry'),596)
        self.assertEqual(sum(not r['outcome_unavailable'] for r in rows if r['arm']=='feedback_repair'),595)
        text=ns['scale_report_coverage_markdown'](report)
        self.assertIn(f'fresh retry contributes {fresh} accepted',text)
        self.assertIn(f'repair {repair}.',text)
        partner=next(r for r in rows if r['request_key']==plan['known_partner_request_key'])
        partner['verification']['accepted']=False
        changed=ns['scale_report_coverage_markdown'](report)
        self.assertIn(f'fresh retry contributes {fresh-1} accepted',changed)
        self.assertIn(f'repair {repair}.',changed)

    def test_usage_uses_all_scheduled_records_instead_of_complete_pair_subset(self):
        ns,_=self.namespace()
        report={'metrics':{'usage':{'by_arm':{},'requests_with_usage':0,'requests_missing_usage':0}},
                'raw_metrics':{'usage':{'by_arm':{},'requests_with_usage':1191,'requests_missing_usage':9}},
                'manifest':{'physical_cli_requests':2320,'total_pilot_plus_main_requests':2336},
                'missing_outcomes':{'n_unavailable_outcomes':9}}
        text=ns['scale_report_usage_markdown'](report)
        self.assertIn('Usage is present for 1191 main requests and missing for 9.',text)

    def test_result_table_counts_observed_partial_partner_without_changing_pairs(self):
        from test_scale_reporting_missing import MissingReportTests
        mock=MissingReportTests();mock.setUp();self.addCleanup(mock.doCleanups)
        report=mock.ns['scale_report_load'](mock.root)
        paired_n=report['metrics']['paired_value_recovery']['n_pairs']
        rows=copy.deepcopy(report['interventions'])
        extra=copy.deepcopy(next(r for r in rows if r['arm']=='fresh_retry' and mock.ns['scale_report_accepted'](r)))
        extra.update(case_id='synthetic-partial-source',semantic_hash='synthetic-new-semantic-source',
                     request_key='synthetic-known-partner',outcome_unavailable=False)
        absent=copy.deepcopy(extra)
        absent.update(arm='feedback_repair',request_key='synthetic-unknown-partner',
                      response=None,transport_error='controller outcome unavailable',outcome_unavailable=True)
        report['operational_interventions']=rows+[extra,absent]
        text=mock.ns['scale_report_results_markdown'](report)
        observed=text.split('| All-observed arm |',1)[1]
        self.assertIn(f'| fresh retry | {paired_n+1} |',observed)
        self.assertIn(f'| feedback repair | {paired_n} |',observed)
        self.assertEqual(report['metrics']['paired_value_recovery']['n_pairs'],paired_n)
        baseline_union={r['semantic_hash'] for r in report['originals']+rows
                        if r['split']=='collection' and mock.ns['scale_report_accepted'](r)}
        frontier=mock.ns['scale_report_model_improvement_markdown'](report)
        coverage=mock.ns['scale_report_coverage_markdown'](report)
        self.assertIn(f'three arms provide {len(baseline_union)+1} distinct accepted collection sources',frontier)
        self.assertIn(f'Deduplicating all three arms yields {len(baseline_union)+1} distinct accepted collection sources',coverage)


if __name__=='__main__':unittest.main()
