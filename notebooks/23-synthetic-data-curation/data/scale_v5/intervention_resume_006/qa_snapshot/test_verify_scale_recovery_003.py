"""Temporary completion-gated metadata fixtures only."""
import hashlib,json,tempfile,unittest
from pathlib import Path
import verify_scale_delivery as qa
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.data=self.root/'data/scale_v5'
  self.write('main/manifest.json',{'phase':'interventions_complete'})
  self.write('intervention_resume/amendment_002.json',{'version':'prior'})
  for name in ['source.py','plan.json','process.json']:self.write('intervention_resume_003/'+name,{'metadata':name})
  inventory={}
  for i in range(1540):
   key=hashlib.sha256(str(i).encode()).hexdigest();p=self.data/'main/cache'/(key+'.json.gz');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'raw immutable bytes');inventory[key]=qa.scale_qa_sha(p)
  self.write('intervention_resume_003/inventory.json',{'count':1540,'requests':inventory})
  a={'protocol':'23-scale-v5','amendment_version':'23-scale-intervention-interruption-v2','predecessor':self.binding('intervention_resume/amendment_002.json'),'protected_files':[],**{k:self.binding('intervention_resume_003/'+v) for k,v in [('implementation','source.py'),('analysis_plan','plan.json'),('process_proof','process.json'),('cache_inventory','inventory.json')]}}
  self.write('intervention_resume_003/amendment_003.json',a)
 def write(self,n,v):
  p=self.data/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf-8')
 def binding(self,n):return dict(path=n,sha256=qa.scale_qa_sha(self.data/n))
 def test_prefix_and_source_bindings_pass(self):self.assertEqual(qa.scale_qa_recovery_bindings(self.root)['raw_prefix_files_verified'],1540)
 def test_raw_cache_change_blocks_delivery(self):
  next((self.data/'main/cache').glob('*')).write_bytes(b'changed')
  with self.assertRaises(RuntimeError):qa.scale_qa_recovery_bindings(self.root)
 def test_source_change_blocks_delivery(self):
  self.write('intervention_resume_003/source.py',{'changed':True})
  with self.assertRaises(RuntimeError):qa.scale_qa_recovery_bindings(self.root)
 def test_incomplete_gate_runs_first(self):
  (self.data/'main/manifest.json').unlink();(self.data/'intervention_resume_003/amendment_003.json').write_bytes(b'not json')
  with self.assertRaisesRegex(RuntimeError,'incomplete'):qa.scale_qa_recovery_bindings(self.root)
if __name__=='__main__':unittest.main()
