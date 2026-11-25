"""Only disposable metadata fixtures are used; no study outcomes are read."""
import hashlib
import unittest
import verify_scale_delivery as qa
import replay_scale_notebook as replay
from test_verify_scale_recovery_004 import Tests as FourthFixture
from test_replay_scale_intervention_diagnostics import DiagnosticsTests as ReplayFixture


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FourthFixture(); self.fixture.setUp()
        self.addCleanup(self.fixture.f.tmp.cleanup)
        self.root, self.data = self.fixture.root, self.fixture.data
        write, bind = self.fixture.f.write, self.fixture.f.binding
        fourth = qa.scale_qa_read(self.data/'intervention_resume_004/amendment_004.json')
        inventory = qa.scale_qa_read(self.data/'intervention_resume_004/inventory.json')['requests']
        for i in range(1656, 2124):
            key = hashlib.sha256(str(i).encode()).hexdigest()
            path = self.data/'main/cache'/(key+'.json.gz')
            path.write_bytes(b'fifth-prefix-raw-fixture'); inventory[key] = qa.scale_qa_sha(path)
        self.new_key = key
        write('intervention_resume_005/inventory.json', {'count':2124,'requests':inventory})
        for name in ('source.py','process.json','stop.json','error.json','handling.json'):
            write('intervention_resume_005/'+name, {'metadata':name})
        self.amendment = dict(protocol='23-scale-v5', amendment_version='23-scale-intervention-transport-continuation-v2',
            predecessor=bind('intervention_resume_004/amendment_004.json'), analysis_plan=fourth['analysis_plan'], protected_files=[],
            **{key:bind('intervention_resume_005/'+name) for key,name in (
                ('implementation','source.py'),('process_proof','process.json'),('cache_inventory','inventory.json'),
                ('stop_record','stop.json'),('error_metadata','error.json'),('handling_plan','handling.json'))})
        self.amendment['provenance_sha256'] = {'intervention_resume_005/handling.json':self.amendment['handling_plan']['sha256']}
        self.save()
    def save(self): self.fixture.f.write('intervention_resume_005/amendment_005.json',self.amendment)
    def test_all2124_prefix_bytes_bound(self):
        self.assertEqual(qa.scale_qa_recovery_bindings(self.root)['raw_prefix_files_verified'],2124)
    def test_new_prefix_bytes_changed_rejected(self):
        (self.data/'main/cache'/(self.new_key+'.json.gz')).write_bytes(b'changed')
        with self.assertRaises(RuntimeError): qa.scale_qa_recovery_bindings(self.root)
    def test_analysis_plan_cannot_change(self):
        self.amendment['analysis_plan']=self.amendment['error_metadata']; self.save()
        with self.assertRaises(RuntimeError): qa.scale_qa_recovery_bindings(self.root)
    def test_predecessor_required(self):
        (self.data/'intervention_resume_004/amendment_004.json').unlink()
        with self.assertRaises(RuntimeError): qa.scale_qa_recovery_bindings(self.root)
    def test_fifth_provenance_mutation_rejected(self):
        (self.data/'intervention_resume_005/handling.json').write_bytes(b'changed')
        with self.assertRaises(RuntimeError): qa.scale_qa_recovery_bindings(self.root)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ReplayFixture(); self.fixture.setUp()
        self.addCleanup(self.fixture.tmp.cleanup)
        self.root, self.data = self.fixture.root,self.fixture.data
        fourth = self.fixture.fourth()
        self.fixture.write('intervention_resume_004/continuation_start_004.json',{'metadata':'frozen gate'})
        for name in ('source.py','process.json','inventory.json','stop.json','error.json','handling.json'):
            self.fixture.write('intervention_resume_005/'+name,{'metadata':name})
        self.amendment = dict(protocol='23-scale-v5',amendment_version='23-scale-intervention-transport-continuation-v2',
            predecessor=self.fixture.binding('intervention_resume_004/amendment_004.json'),analysis_plan=fourth['analysis_plan'],
            protected_files=[self.fixture.binding(p) for p in ('source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json','intervention_resume_004/continuation_start_004.json')],
            **{key:self.fixture.binding('intervention_resume_005/'+name) for key,name in (
                ('implementation','source.py'),('process_proof','process.json'),('cache_inventory','inventory.json'),
                ('stop_record','stop.json'),('error_metadata','error.json'),('handling_plan','handling.json'))})
        self.amendment['provenance_sha256']={item['path']:item['sha256'] for item in self.amendment['protected_files']}
        self.save()
        digest = qa.scale_qa_sha(self.data/'intervention_resume_005/amendment_005.json')
        self.fixture.add_receipt(self.fixture.value,'main/intervention_continuation_diagnostics/'+digest[:12]+'/validation_'+replay.scale_qa_hash(self.fixture.value)[:12]+'.json')
    def save(self):self.fixture.write('intervention_resume_005/amendment_005.json',self.amendment)
    def test_fifth_operational_receipt_bound(self):self.assertEqual(len(self.fixture.read()),4)
    def test_fifth_analysis_cannot_change(self):
        self.amendment['analysis_plan']=self.amendment['error_metadata']; self.save()
        with self.assertRaises(RuntimeError):self.fixture.read()
    def test_fifth_protected_bytes_cannot_change(self):
        (self.data/'intervention_resume_004/continuation_start_004.json').write_bytes(b'changed')
        with self.assertRaises(RuntimeError):self.fixture.read()


if __name__=='__main__':unittest.main()
