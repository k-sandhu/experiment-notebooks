"""Disposable completion-gated metadata fixtures, never actual study data."""
import hashlib,json,unittest
import verify_scale_delivery as qa
from test_verify_scale_recovery_003 import Tests as Fixture
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=Fixture();self.f.setUp();self.addCleanup(self.f.tmp.cleanup);self.data=self.f.data;self.root=self.f.root
  old=qa.scale_qa_read(self.data/'intervention_resume_003/amendment_003.json');inventory=qa.scale_qa_read(self.data/'intervention_resume_003/inventory.json')['requests']
  for i in range(1540,1656):
   key=hashlib.sha256(str(i).encode()).hexdigest();p=self.data/'main/cache'/(key+'.json.gz');p.write_bytes(b'raw fourth prefix');inventory[key]=qa.scale_qa_sha(p)
  self.new_key=key
  self.f.write('intervention_resume_004/inventory.json',{'count':1656,'requests':inventory})
  for name in ['source.py','process.json','stop.json','sleep.json','error.json','handling.json']:self.f.write('intervention_resume_004/'+name,{'metadata':name})
  self.a=dict(protocol='23-scale-v5',amendment_version='23-scale-intervention-timeout-continuation-v1',predecessor=self.f.binding('intervention_resume_003/amendment_003.json'),analysis_plan=old['analysis_plan'],protected_files=[],**{k:self.f.binding('intervention_resume_004/'+v) for k,v in [('implementation','source.py'),('process_proof','process.json'),('cache_inventory','inventory.json'),('stop_record','stop.json'),('sleep_event','sleep.json'),('error_metadata','error.json'),('handling_plan','handling.json')]})
  self.a['provenance_sha256']={'intervention_resume_004/handling.json':self.a['handling_plan']['sha256']}
  self.f.write('intervention_resume_004/amendment_004.json',self.a)
 def test_all1656prefix_and_predecessor_bindings(self):self.assertEqual(qa.scale_qa_recovery_bindings(self.root)['raw_prefix_files_verified'],1656)
 def test_new_prefix_raw_bytes_cannot_change(self):
  (self.data/'main/cache'/(self.new_key+'.json.gz')).write_bytes(b'changed')
  with self.assertRaises(RuntimeError):qa.scale_qa_recovery_bindings(self.root)
 def test_fourth_analysis_must_reuse003_bytes(self):
  self.a['analysis_plan']=self.a['error_metadata'];self.f.write('intervention_resume_004/amendment_004.json',self.a)
  with self.assertRaises(RuntimeError):qa.scale_qa_recovery_bindings(self.root)
 def test_fourth_requires003_predecessor(self):
  (self.data/'intervention_resume_003/amendment_003.json').unlink()
  with self.assertRaises(RuntimeError):qa.scale_qa_recovery_bindings(self.root)
if __name__=='__main__':unittest.main()
