"""Disposable metadata fixtures only; no real study outcomes are opened."""
import hashlib
import unittest

import verify_scale_delivery as qa
import replay_scale_notebook as replay
import test_verify_scale_recovery_005 as fifth_tests


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fifth_tests.DeliveryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.data = self.fixture.root, self.fixture.data
        write, bind = self.fixture.fixture.f.write, self.fixture.fixture.f.binding
        fifth = qa.scale_qa_read(self.data / 'intervention_resume_005/amendment_005.json')
        inventory = qa.scale_qa_read(self.data / 'intervention_resume_005/inventory.json')['requests']
        for index in range(2124, 2268):
            key = hashlib.sha256(str(index).encode()).hexdigest()
            path = self.data / 'main/cache' / (key + '.json.gz')
            path.write_bytes(b'sixth-prefix-raw-fixture')
            inventory[key] = qa.scale_qa_sha(path)
        self.new_key = key
        write('intervention_resume_006/inventory.json', {'count': 2268, 'requests': inventory})
        for name in ('source.py', 'analysis.json', 'process.json', 'stop.json', 'review.json', 'handling.json'):
            write('intervention_resume_006/' + name, {'metadata': name})
        self.amendment = dict(
            protocol='23-scale-v5', amendment_version='23-scale-intervention-interruption-v3',
            predecessor=bind('intervention_resume_005/amendment_005.json'),
            previous_analysis_plan=fifth['analysis_plan'],
            analysis_plan=bind('intervention_resume_006/analysis.json'), protected_files=[],
            **{field: bind('intervention_resume_006/' + name) for field, name in (
                ('implementation', 'source.py'), ('process_proof', 'process.json'),
                ('cache_inventory', 'inventory.json'), ('stop_record', 'stop.json'),
                ('recovery_review', 'review.json'), ('handling_plan', 'handling.json'))})
        self.amendment['provenance_sha256'] = {
            self.amendment['handling_plan']['path']: self.amendment['handling_plan']['sha256']}
        self.save()

    def save(self):
        self.fixture.fixture.f.write('intervention_resume_006/amendment_006.json', self.amendment)

    def test_all2268_prefix_bytes_and_new_plan_bound(self):
        value = qa.scale_qa_recovery_bindings(self.root)
        self.assertEqual(value['raw_prefix_files_verified'], 2268)
        self.assertEqual(value['current_analysis_plan_sha256'], self.amendment['analysis_plan']['sha256'])

    def test_new_prefix_mutation_rejected(self):
        (self.data / 'main/cache' / (self.new_key + '.json.gz')).write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            qa.scale_qa_recovery_bindings(self.root)

    def test_historical_plan_lineage_mutation_rejected(self):
        self.amendment['previous_analysis_plan'] = self.amendment['analysis_plan']
        self.save()
        with self.assertRaises(RuntimeError):
            qa.scale_qa_recovery_bindings(self.root)

    def test_missing_fifth_predecessor_rejected(self):
        (self.data / 'intervention_resume_005/amendment_005.json').unlink()
        with self.assertRaises(RuntimeError):
            qa.scale_qa_recovery_bindings(self.root)

    def test_new_plan_bytes_mutation_rejected(self):
        (self.data / 'intervention_resume_006/analysis.json').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            qa.scale_qa_recovery_bindings(self.root)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fifth_tests.ReplayTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.data = self.fixture.root, self.fixture.data
        write, bind = self.fixture.fixture.write, self.fixture.fixture.binding
        fifth = qa.scale_qa_read(self.data / 'intervention_resume_005/amendment_005.json')
        write('intervention_resume_005/continuation_start_005.json', {'metadata': 'frozen fifth gate'})
        for name in ('source.py', 'analysis.json', 'process.json', 'inventory.json', 'stop.json', 'review.json', 'handling.json'):
            write('intervention_resume_006/' + name, {'metadata': name})
        protected = ('source_freeze.json', 'intervention_start_declaration.json', 'main/dispatch.json',
                     'main/selection.json', 'intervention_resume_005/continuation_start_005.json')
        self.amendment = dict(
            protocol='23-scale-v5', amendment_version='23-scale-intervention-interruption-v3',
            predecessor=bind('intervention_resume_005/amendment_005.json'),
            previous_analysis_plan=fifth['analysis_plan'], analysis_plan=bind('intervention_resume_006/analysis.json'),
            protected_files=[bind(path) for path in protected],
            **{field: bind('intervention_resume_006/' + name) for field, name in (
                ('implementation', 'source.py'), ('process_proof', 'process.json'),
                ('cache_inventory', 'inventory.json'), ('stop_record', 'stop.json'),
                ('recovery_review', 'review.json'), ('handling_plan', 'handling.json'))})
        self.amendment['provenance_sha256'] = {item['path']: item['sha256'] for item in self.amendment['protected_files']}
        self.save()
        digest = qa.scale_qa_sha(self.data / 'intervention_resume_006/amendment_006.json')
        self.receipt_value = dict(self.fixture.fixture.value,
                                  new_cli_subprocesses_this_run=0, replayed_requests_this_run=1200, offline=True)
        self.fixture.fixture.add_receipt(
            self.receipt_value,
            'main/intervention_continuation_diagnostics/' + digest[:12]
            + '/validation_' + replay.scale_qa_hash(self.receipt_value)[:12] + '.json')

    def save(self):
        self.fixture.fixture.write('intervention_resume_006/amendment_006.json', self.amendment)

    def test_sixth_operational_receipt_bound(self):
        self.assertEqual(len(self.fixture.fixture.read()), 5)

    def test_historical_analysis_cannot_be_replaced(self):
        self.amendment['previous_analysis_plan'] = self.amendment['analysis_plan']
        self.save()
        with self.assertRaises(RuntimeError):
            self.fixture.fixture.read()

    def test_fifth_gate_mutation_rejected(self):
        (self.data / 'intervention_resume_005/continuation_start_005.json').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            self.fixture.fixture.read()

    def test_sixth_new_analysis_bytes_mutation_rejected(self):
        (self.data / 'intervention_resume_006/analysis.json').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            self.fixture.fixture.read()

    def test_partial_offline_replay_receipt_rejected(self):
        digest = qa.scale_qa_sha(self.data / 'intervention_resume_006/amendment_006.json')
        value = dict(self.receipt_value, replayed_requests_this_run=1199)
        self.fixture.fixture.add_receipt(
            value, 'main/intervention_continuation_diagnostics/' + digest[:12]
            + '/validation_' + replay.scale_qa_hash(value)[:12] + '.json')
        with self.assertRaises(RuntimeError):
            self.fixture.fixture.read()


if __name__ == '__main__':
    unittest.main()
