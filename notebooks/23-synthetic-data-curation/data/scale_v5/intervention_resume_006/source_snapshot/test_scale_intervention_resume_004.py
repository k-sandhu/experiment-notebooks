"""Synthetic temporary metadata only. No study writes or model calls."""
import copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import scale_intervention_resume as core
import scale_intervention_resume_003 as third
import scale_intervention_resume_004 as fourth
from test_scale_intervention_resume_003 import Tests as ThirdFixture

class Tests(unittest.TestCase):
 def setUp(self):
  t=self.t=ThirdFixture();t.setUp();self.f=f=t.f;self.addCleanup(f.tmp.cleanup)
  for index in range(420,536):f.record(f.requests[f.plan[index]['request_key']])
  self.key=f.plan[535]['request_key'];p=f.cache/(self.key+'.json.gz');obj=core.sir_read(p);a=obj['attempts'][0]
  a.update(error=fourth.TIMEOUT_ERROR,return_code=0,timed_out=True,elapsed_s=4534.953589299985,token_usage={'input_tokens':1})
  p.write_bytes(gzip.compress(json.dumps(obj).encode(),mtime=0));f.inventory[self.key]=core.sir_sha(p)
  f.write('intervention_resume_003/continuation_start_003.json',{'gate':'frozen'})
  f.write('intervention_resume_004/inventory.json',dict(protocol='23-scale-v5',count=1656,requests=f.inventory))
  f.write('intervention_resume_004/process.json',dict(checked_at_utc='2026-01-03T02:00:00+00:00',owned_workers=0,collector_session_available=False,inaccessible_owned_candidates=0))
  f.write('main/stop_record.json',{'opaque_wave_results':'never read this payload'})
  f.write('intervention_resume_004/sleep.json',{'sleep_time_utc':'2026-01-03T00:00:00+00:00','wake_time_utc':'2026-01-03T01:00:00+00:00'})
  self.metadata=dict(request_key=self.key,cache_sha256=f.inventory[self.key],attempt_metadata={k:a[k] for k in fourth.ATTEMPT_FIELDS if k in a},token_usage_field_present=True,token_usage_nonempty=True)
  f.write('intervention_resume_004/error.json',self.metadata)
  f.write_bytes('intervention_resume_004/implementation.py',Path(fourth.__file__).read_bytes())
  plan=f.plan[535];req=f.requests[self.key]
  self.retained=dict(**self.metadata,dispatch_index=535,case_id=plan['case_id'],arm=plan['arm'],stage=plan['stage'],sample=plan['sample'],content_hash=plan['source_hash'],request_input_hash=core.sir_hash(req['case_inputs']),feedback_hash=core.sir_hash(req['feedback']),error=fourth.TIMEOUT_ERROR)
  self.a=dict(protocol='23-scale-v5',amendment_version=fourth.VERSION,declared_at_utc='2026-01-03T03:00:00+00:00',loss_observed_at_utc='2026-01-03T01:30:00+00:00',predecessor=f.binding('intervention_resume_003/amendment_003.json'),protected_files=[f.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json','intervention_resume_003/continuation_start_003.json']],implementation=f.binding('intervention_resume_004/implementation.py'),analysis_plan=t.a['analysis_plan'],process_proof=f.binding('intervention_resume_004/process.json'),cache_inventory=f.binding('intervention_resume_004/inventory.json'),stop_record=f.binding('main/stop_record.json'),sleep_event=f.binding('intervention_resume_004/sleep.json'),error_metadata=f.binding('intervention_resume_004/error.json'),retained_transport_failures=[self.retained])
  for name in ['handling_plan.json','worker.py','launcher.ps1','smoke.json','evidence.json','review.json','reporting.py']:
   f.write('intervention_resume_004/'+name,dict(metadata=name))
  self.a['handling_plan']=f.binding('intervention_resume_004/handling_plan.json')
  self.a['provenance_sha256']={('intervention_resume_004/'+n):f.binding('intervention_resume_004/'+n)['sha256'] for n in ['handling_plan.json','worker.py','launcher.ps1','smoke.json','evidence.json','review.json','reporting.py']}
  self.path=f.data/'intervention_resume_004/amendment_004.json';self.refresh()
  def call(request,cache_dir,live=False,timeout_s=900,_runner=None):
   key=core.sir_hash(request)
   if key==self.key:return dict(request_key=key,cached=True,error=fourth.TIMEOUT_ERROR)
   return f.call(request,cache_dir,live,timeout_s,_runner)
  f.ns['scale_call_model']=call
 def refresh(self):self.f.write_bytes('intervention_resume_004/amendment_004.json',json.dumps(self.a).encode())
 def install(self):
  third.scale_intervention_resume_003_install(self.f.root,self.t.path,self.f.ns)
  gate=self.f.data/'intervention_resume_004/mock-ready.json';nonce='a'*32;expected=fourth.startup_expected(core.sir_sha(self.path),nonce);gate.write_text(json.dumps(dict(**expected,worker_pid=123)),encoding='utf-8')
  return fourth.scale_intervention_resume_004_install(self.f.root,self.path,self.f.ns,startup_gate=gate,startup_nonce=nonce)
 def test_exact_prefix_terminal_timeout_and_eight_pending(self):
  s=fourth.scale_intervention_resume_004_verify(self.f.root,self.path);self.assertEqual(len(s['inventory']),1656);self.assertEqual(len(s['approved']),8);self.assertEqual(set(s['retained']),{self.key})
 def test_cached_timeout_never_resubmitted_and_row_unchanged(self):
  self.install();before=(self.f.cache/(self.key+'.json.gz')).read_bytes();response=object();verification=object()
  def invoke(j):
   r,l=self.f.invoke(j);r['response']=response;r['verification']=verification;return r,l
  rows,ledger=self.f.ns['scale_dispatch_waves']([self.f.jobs[535]],invoke,self.f.main,4)
  self.assertIs(rows[0]['response'],response);self.assertIs(rows[0]['verification'],verification);self.assertEqual(rows[0]['transport_error'],fourth.TIMEOUT_ERROR);self.assertTrue(ledger[0]['cached_this_run']);self.assertEqual(self.f.new_calls,[]);self.assertEqual(before,(self.f.cache/(self.key+'.json.gz')).read_bytes())
 def test_only664unsent_slots_eligible(self):
  self.install();self.f.ns['scale_dispatch_waves'](self.f.jobs[532:540],self.f.invoke,self.f.main,4)
  self.assertEqual(len(self.f.new_calls),4);self.assertEqual(set(self.f.new_calls),{x['request_key'] for x in self.f.jobs[536:540]})
 def test_all_eight_unknown_stay_pending_bytes(self):
  s=self.install();before={k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in s['approved']}
  for k in before:self.f.ns['scale_call_model'](self.f.requests[k],self.f.cache,live=True)
  self.assertEqual(self.f.new_calls,[]);self.assertEqual(before,{k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in before})
 def test_new_error_drains_four_and_stops(self):
  self.install();visited=[]
  def fail(j):
   visited.append(j['request_key']);r,l=self.f.invoke(j);r['transport_error']='new service error';return r,l
  with self.assertRaises(RuntimeError):self.f.ns['scale_dispatch_waves'](self.f.jobs[536:544],fail,self.f.main,4)
  self.assertEqual(len(visited),4);self.assertEqual(len(self.f.new_calls),4)
 def test_changed_any_recorded_bytes_blocks(self):
  (self.f.cache/(self.key+'.json.gz')).write_bytes(b'changed')
  with self.assertRaises(ValueError):self.install()
 def test_deleted_recorded_key_never_reissued(self):
  self.install();(self.f.cache/(self.key+'.json.gz')).unlink()
  with self.assertRaises(FileNotFoundError):self.f.ns['scale_call_model'](self.f.requests[self.key],self.f.cache,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_persistent_one_shot_blocks_even_no_new_cache(self):
  self.install();self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  with self.assertRaises(FileExistsError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_extra_recorded_key_blocks_live_start(self):
  self.install();self.f.record(self.f.requests[self.f.plan[536]['request_key']])
  with self.assertRaises(ValueError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_analysis_bytes_must_remain003(self):
  self.a['analysis_plan']=self.f.binding('intervention_resume_004/sleep.json');self.refresh()
  with self.assertRaises(ValueError):self.install()
 def test_timeout_identity_and_metadata_must_match(self):
  self.a['retained_transport_failures'][0]['attempt_metadata']['elapsed_s']=1;self.refresh()
  with self.assertRaises(ValueError):self.install()
 def test_existing_notebook003namespace_reused(self):
  third.scale_intervention_resume_003_install(self.f.root,self.t.path,self.f.ns)
  with patch.object(third,'scale_intervention_resume_003_install',side_effect=AssertionError('Do not reinstall003')):
   fourth.scale_intervention_resume_004_install(self.f.root,self.path,self.f.ns)
 def test_embedded003_and002_exact_sources(self):
  fourth.SCALE_INTERVENTION_004_PREDECESSOR_SOURCE=Path(third.__file__).read_bytes().decode('utf-8');fourth.SCALE_INTERVENTION_PREDECESSOR_SOURCE=Path(core.__file__).read_text()
  try:self.install()
  finally:del fourth.SCALE_INTERVENTION_004_PREDECESSOR_SOURCE;del fourth.SCALE_INTERVENTION_PREDECESSOR_SOURCE
 def test_changed_embedded003_rejected(self):
  fourth.SCALE_INTERVENTION_004_PREDECESSOR_SOURCE=Path(third.__file__).read_bytes().decode('utf-8')+'\n# changed\n'
  try:
   with self.assertRaises(ValueError):self.install()
  finally:del fourth.SCALE_INTERVENTION_004_PREDECESSOR_SOURCE
 def test_changed_embedded002_rejected(self):
  fourth.SCALE_INTERVENTION_PREDECESSOR_SOURCE=Path(core.__file__).read_text()+'\n# changed\n'
  try:
   with self.assertRaises(ValueError):self.install()
  finally:del fourth.SCALE_INTERVENTION_PREDECESSOR_SOURCE
 def test_offline_path_never_launches_model(self):
  self.install();self.f.ns['scale_run_interventions'](root=self.f.root,live=False);self.assertEqual(self.f.new_calls,[])
 def test_normalized_embedded003_rejected(self):
  fourth.SCALE_INTERVENTION_004_PREDECESSOR_SOURCE=Path(third.__file__).read_text()
  try:
   with self.assertRaises(ValueError):self.install()
  finally:del fourth.SCALE_INTERVENTION_004_PREDECESSOR_SOURCE
 def test_nonfailure_recorded_new_prefix_key_cannot_reissue(self):
  self.install();key=self.f.plan[500]['request_key'];(self.f.cache/(key+'.json.gz')).unlink()
  with self.assertRaises(FileNotFoundError):self.f.ns['scale_call_model'](self.f.requests[key],self.f.cache,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_live_without_worker_gate_is_rejected_before_calls(self):
  third.scale_intervention_resume_003_install(self.f.root,self.t.path,self.f.ns)
  fourth.scale_intervention_resume_004_install(self.f.root,self.path,self.f.ns)
  with self.assertRaises(ValueError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_wrong_startup_child_identity_rejected(self):
  state=self.install();gate=Path(state['startup_gate']);value=json.loads(gate.read_text());value['collector_pid']+=1;gate.write_text(json.dumps(value))
  with self.assertRaises(ValueError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_no_ready_gate_no_model_dispatch(self):
  with self.assertRaises(TimeoutError):fourth.wait_startup_gate(self.f.data/'no-ready.json',{},timeout_s=0)
  self.assertEqual(self.f.new_calls,[])
 def test_outside_main_dispatch_delegates_prior_cached_replay(self):
  self.install();result=self.f.ns['scale_dispatch_waves']([],self.f.invoke,self.f.data/'pilot/tier',2)
  self.assertEqual(result,('delegated',[]));self.assertEqual(self.f.new_calls,[])
  with self.assertRaises(ValueError):self.f.ns['scale_dispatch_waves']([],self.f.invoke,self.f.main,2)
 def test_prior_original_capacity_exception_retained(self):
  self.install();keys={p['request_key'] for p in self.f.plan};key=next(k for k in self.f.inventory if k not in keys);cid=self.f.requests[key]['expected_case_ids'][0]
  known=dict(case_id=cid,content_hash='old-source',request_input_hash='old-input',transport_error='reviewed original capacity')
  self.f.ns['SCALE_RESUME_INSTALLED']['approved'][key]=known
  job=dict(request_key=key,case={'case_id':cid},arm='original')
  def invoke(j):return dict(request_key=key,**known,arm='original',stage='generate',sample=0,split='collection',response=None),dict(request_key=key,cached_this_run=True)
  rows,_=self.f.ns['scale_dispatch_waves']([job],invoke,self.f.main,4);self.assertEqual(rows[0]['transport_error'],known['transport_error']);self.assertEqual(self.f.new_calls,[])
 def test_mixed_main_original_and_intervention_batches_rejected(self):
  self.install();jobs=[dict(self.f.jobs[0],arm='original'),self.f.jobs[1]]
  with self.assertRaises(ValueError):self.f.ns['scale_dispatch_waves'](jobs,self.f.invoke,self.f.main,4)
  self.assertEqual(self.f.new_calls,[])
 def test_every_declared_provenance_dependency_is_bound(self):
  for relative in self.a['provenance_sha256']:
   p=self.f.data/relative;raw=p.read_bytes();p.write_bytes(b'changed')
   with self.assertRaises(ValueError):fourth.scale_intervention_resume_004_verify(self.f.root,self.path)
   p.write_bytes(raw)
 def test_handling_plan_bytes_cannot_change(self):
  (self.f.data/self.a['handling_plan']['path']).write_bytes(b'changed')
  with self.assertRaises(ValueError):self.install()
 def test_provenance_path_escape_rejected(self):
  self.a['provenance_sha256']['../outside']='0'*64;self.refresh()
  with self.assertRaises(ValueError):self.install()
if __name__=='__main__':unittest.main()
