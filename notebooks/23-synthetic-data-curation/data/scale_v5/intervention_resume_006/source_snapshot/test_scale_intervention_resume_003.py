"""Mock-only tests; no model calls or study writes."""
import copy,json,unittest
from pathlib import Path
import scale_intervention_resume as old
import scale_intervention_resume_003 as new
from test_scale_intervention_resume import ResumeTests
class Tests(unittest.TestCase):
 def setUp(self):
  f=self.f=ResumeTests();f.setUp();self.addCleanup(f.tmp.cleanup)
  f.write_bytes('intervention_resume/implementation.py',Path(old.__file__).read_bytes())
  f.amendment['implementation']=f.binding('intervention_resume/implementation.py');f.refresh_amendment()
  for index in range(120,420):f.record(f.requests[f.plan[index]['request_key']],pending=index>=416)
  f.write('main/selection.json',{'selected_case_ids':['pair-'+str(i) for i in range(600)]})
  f.write('intervention_resume_003/inventory.json',dict(protocol='23-scale-v5',count=1540,requests=f.inventory))
  f.write('intervention_resume_003/process.json',dict(checked_at_utc='2026-01-02T02:00:00+00:00',owned_workers=0,collector_session_available=False,inaccessible_owned_candidates=0))
  f.write('intervention_resume_003/analysis.json',{'precall':True})
  f.write_bytes('intervention_resume_003/implementation.py',Path(new.__file__).read_bytes())
  unknown=copy.deepcopy(f.amendment['unavailable_requests'])
  for index in range(416,420):
   key=f.plan[index]['request_key'];req=f.requests[key];p=f.plan[index]
   unknown.append(dict(request_key=key,cache_sha256=f.inventory[key],case_id=p['case_id'],content_hash=p['source_hash'],request_input_hash=old.sir_hash(req['case_inputs']),feedback_hash=old.sir_hash(req['feedback']),arm=p['arm'],stage=p['stage'],sample=p['sample'],profile=f.profile))
  self.a=dict(protocol='23-scale-v5',amendment_version=new.VERSION,declared_at_utc='2026-01-02T03:00:00+00:00',loss_observed_at_utc='2026-01-02T01:00:00+00:00',predecessor=f.binding('intervention_resume/amendment_002.json'),protected_files=[f.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json']],implementation=f.binding('intervention_resume_003/implementation.py'),analysis_plan=f.binding('intervention_resume_003/analysis.json'),process_proof=f.binding('intervention_resume_003/process.json'),cache_inventory=f.binding('intervention_resume_003/inventory.json'),unavailable_requests=unknown)
  self.path=f.data/'intervention_resume_003/amendment_003.json';self.refresh()
 def refresh(self):self.f.write_bytes('intervention_resume_003/amendment_003.json',json.dumps(self.a).encode())
 def install(self):return new.scale_intervention_resume_003_install(self.f.root,self.path,self.f.ns)
 def test_exact_inventory_eight_unknown_four_pairs(self):
  s=new.scale_intervention_resume_003_verify(self.f.root,self.path);self.assertEqual(len(s['inventory']),1540);self.assertEqual(len(s['approved']),8);self.assertEqual(len({v['case_id'] for v in s['approved'].values()}),4)
 def test_all_unknown_projection_preserves_raw_bytes(self):
  s=self.install();before={k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in s['approved']}
  for k in s['approved']:
   r=self.f.ns['scale_call_model'](self.f.requests[k],self.f.cache,live=True)
   self.assertTrue(r['outcome_unavailable']);self.assertIsNone(r['parsed']);self.assertNotIn('finished_at',r);self.assertNotIn('usage',r)
  self.assertEqual(self.f.new_calls,[]);self.assertEqual(before,{k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in before})
 def test_only_unsent_can_call_new_cli(self):
  self.install();self.f.ns['scale_dispatch_waves'](self.f.jobs[416:424],self.f.invoke,self.f.main,4)
  self.assertEqual(len(self.f.new_calls),4);self.assertEqual(set(self.f.new_calls),{x['request_key'] for x in self.f.jobs[420:424]})
 def test_new_error_drains_then_stops(self):
  self.install();visited=[]
  def fail(j):
   visited.append(j['request_key']);r,l=self.f.invoke(j);r['transport_error']='new infrastructure error';return r,l
  with self.assertRaises(RuntimeError):self.f.ns['scale_dispatch_waves'](self.f.jobs[420:428],fail,self.f.main,4)
  self.assertEqual(len(visited),4);self.assertEqual(len(self.f.new_calls),4)
 def test_any_recorded_hash_change_blocks(self):
  self.f.record(self.f.requests[self.f.plan[420]['request_key']])
  # extra cache is prohibited by live gate even if verification binds prefix
  self.install()
  with self.assertRaises(ValueError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_changed_old_prefix_rejected(self):
  k=self.f.plan[0]['request_key'];(self.f.cache/(k+'.json.gz')).write_bytes(b'changed')
  with self.assertRaises(ValueError):self.install()
 def test_post_install_delete_cannot_reissue(self):
  self.install();k=self.f.plan[200]['request_key'];(self.f.cache/(k+'.json.gz')).unlink()
  with self.assertRaises(FileNotFoundError):self.f.ns['scale_call_model'](self.f.requests[k],self.f.cache,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_persistent_one_shot_before_first_call(self):
  self.install();self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  with self.assertRaises(FileExistsError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_pending_identity_changed_rejected(self):
  self.a['unavailable_requests'][-1]['feedback_hash']='0'*64;self.refresh()
  with self.assertRaises(ValueError):self.install()
 def test_inaccessible_owned_candidate_blocks(self):
  self.f.write('intervention_resume_003/process.json',dict(checked_at_utc='2026-01-02T02:00:00+00:00',owned_workers=0,collector_session_available=False,inaccessible_owned_candidates=1));self.a['process_proof']=self.f.binding('intervention_resume_003/process.json');self.refresh()
  with self.assertRaises(ValueError):self.install()
 def test_offline_replay_launches_nothing(self):
  self.install();self.f.ns['scale_run_interventions'](root=self.f.root,live=False);self.assertEqual(self.f.new_calls,[])
 def test_embedded_predecessor_exact_hash(self):
  new.SCALE_INTERVENTION_PREDECESSOR_SOURCE=Path(old.__file__).read_text()
  try:self.install()
  finally:del new.SCALE_INTERVENTION_PREDECESSOR_SOURCE
 def test_changed_embedded_predecessor_rejected(self):
  new.SCALE_INTERVENTION_PREDECESSOR_SOURCE=Path(old.__file__).read_text()+'\n# changed\n'
  try:
   with self.assertRaises(ValueError):self.install()
  finally:del new.SCALE_INTERVENTION_PREDECESSOR_SOURCE
if __name__=='__main__':unittest.main()

