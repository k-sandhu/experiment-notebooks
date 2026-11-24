"""Synthetic metadata/caches only. No study answers or model calls."""
import copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import scale_intervention_resume as core
import scale_intervention_resume_005 as fifth
import scale_intervention_resume_006 as sixth
import test_scale_intervention_resume_005 as fixture

class Tests(unittest.TestCase):
 def setUp(self):
  self.t=t=fixture.Tests();t.setUp();self.f=f=t.f;self.addCleanup(f.tmp.cleanup)
  prior=fifth.scale_intervention_resume_005_verify(f.root,t.path)
  for index in range(1004,1148):f.record(f.requests[f.plan[index]['request_key']],pending=index==1147)
  self.newkey=f.plan[1147]['request_key'];self.partner=f.plan[1146]['request_key']
  new=dict(request_key=self.newkey,cache_sha256=f.inventory[self.newkey],case_id=f.plan[1147]['case_id'],arm='feedback_repair',stage='repair',sample=0,content_hash=f.plan[1147]['source_hash'],request_input_hash=core.sir_hash(f.requests[self.newkey]['case_inputs']),feedback_hash=core.sir_hash(f.requests[self.newkey]['feedback']),profile=f.profile)
  approved=dict(prior['approved']);approved[self.newkey]=new;self.approved=approved
  f.write('intervention_resume_005/continuation_start_005.json',{'gate':'frozen005'})
  f.write('intervention_resume_006/inventory.json',dict(protocol='23-scale-v5',count=2268,requests=f.inventory))
  f.write('intervention_resume_006/process.json',dict(checked_at_utc='2026-01-05T02:00:00+00:00',owned_workers=0,collector_session_available=False,inaccessible_owned_candidates=0))
  f.write('intervention_resume_006/stop.json',dict(reason='controller_disappeared_without_finished_receipt',finished_receipt_present=False,manifest_present=False,export_files_present=0,new_transport_failure_events=0))
  self.plan=dict(scheduled_pairs=600,observed_pair_target=595,unknown_outcomes=9,unknown_whole_pairs=4,unknown_partial_pairs=1,hypothetical_completions=512,bootstrap_samples=20000,bootstrap_seed=246600,unknown_request_keys=sorted(approved),unknown_case_ids=sorted({x['case_id'] for x in approved.values()}),partial_pair_case_id=new['case_id'],known_partner_request_key=self.partner,known_partners=[dict(case_id=new['case_id'],arm='fresh_retry',request_key=self.partner,cache_sha256=f.inventory[self.partner])])
  f.write('intervention_resume_006/analysis_plan.json',self.plan)
  for name in ('handling_plan.json','review.json','worker.py','launcher.ps1','smoke.json'):
   f.write('intervention_resume_006/'+name,dict(metadata=name))
  f.write_bytes('intervention_resume_006/implementation.py',Path(sixth.__file__).read_bytes())
  self.a=dict(protocol='23-scale-v5',amendment_version=sixth.VERSION,declared_at_utc='2026-01-05T03:00:00+00:00',loss_observed_at_utc='2026-01-05T01:30:00+00:00',predecessor=f.binding('intervention_resume_005/amendment_005.json'),implementation=f.binding('intervention_resume_006/implementation.py'),analysis_plan=f.binding('intervention_resume_006/analysis_plan.json'),previous_analysis_plan=prior['amendment']['analysis_plan'],process_proof=f.binding('intervention_resume_006/process.json'),cache_inventory=f.binding('intervention_resume_006/inventory.json'),stop_record=f.binding('intervention_resume_006/stop.json'),recovery_review=f.binding('intervention_resume_006/review.json'),handling_plan=f.binding('intervention_resume_006/handling_plan.json'),protected_files=[f.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json','intervention_resume_005/amendment_005.json','intervention_resume_005/continuation_start_005.json']],retained_transport_failures=copy.deepcopy(prior['retained_transport_failures']),unavailable_requests=list(approved.values()),unavailable_request_keys=sorted(approved),unavailable_case_ids=self.plan['unknown_case_ids'],remaining_unsent_jobs=52,recorded_arm_requests=1148,retained_terminal_arm_requests=1139,provenance_sha256={'intervention_resume_006/worker.py':f.binding('intervention_resume_006/worker.py')['sha256']})
  self.path=f.data/'intervention_resume_006/amendment_006.json';self.refresh()
 def refresh(self):self.f.write_bytes('intervention_resume_006/amendment_006.json',json.dumps(self.a).encode())
 def install(self):
  self.t.install();gate=self.f.data/'intervention_resume_006/mock-ready.json';nonce='b'*32;gate.write_text(json.dumps(dict(**sixth.startup_expected(core.sir_sha(self.path),nonce),worker_pid=123)),encoding='utf-8')
  return sixth.scale_intervention_resume_006_install(self.f.root,self.path,self.f.ns,startup_gate=gate,startup_nonce=nonce)
 def test_exact2268_prefix_nine_pending_two_retained_52unsent(self):
  s=sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
  self.assertEqual((len(s['inventory']),len(s['approved']),len(s['retained']),len(s['unsent_request_keys'])),(2268,9,2,52))
 def test_all1148_recorded_replay_no_calls_or_changed_bytes(self):
  s=self.install();before={k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in s['inventory']}
  with patch('subprocess.Popen',side_effect=AssertionError('No subprocess')):rows,ledger=self.f.ns['scale_dispatch_waves'](self.f.jobs[:1148],self.f.invoke,self.f.main,4)
  self.assertEqual(len(rows),1148);self.assertEqual(sum(bool(r.get('outcome_unavailable')) for r in rows),9);self.assertTrue(all(e['cached_this_run'] for e in ledger));self.assertEqual(self.f.new_calls,[])
  self.assertEqual(before,{k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in before})
 def test_only52_unsent_calls_once_all9pending_preserved(self):
  s=self.install();before={k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in s['inventory']}
  self.f.ns['scale_dispatch_waves'](self.f.jobs,self.f.invoke,self.f.main,4)
  self.assertEqual(set(self.f.new_calls),s['unsent_request_keys']);self.assertEqual(len(self.f.new_calls),52)
  self.f.ns['scale_dispatch_waves'](self.f.jobs,self.f.invoke,self.f.main,4);self.assertEqual(len(self.f.new_calls),52)
  self.assertEqual(before,{k:(self.f.cache/(k+'.json.gz')).read_bytes() for k in before})
 def test_each9_unknown_direct_call_projects_no_fake_telemetry(self):
  s=self.install()
  for key in s['approved']:
   r=self.f.ns['scale_call_model'](self.f.requests[key],self.f.cache,live=True)
   self.assertTrue(r['cached']);self.assertTrue(r['outcome_unavailable'])
   for name in ('finished_at','elapsed_s','return_code','events','usage'):self.assertNotIn(name,r)
  self.assertEqual(self.f.new_calls,[])
 def test_recorded005_newterminal_and_newpending_cannot_disappear(self):
  self.install()
  for key in (self.newkey,self.partner):
   p=self.f.cache/(key+'.json.gz');raw=p.read_bytes();p.unlink()
   with self.assertRaises(FileNotFoundError):self.f.ns['scale_call_model'](self.f.requests[key],self.f.cache,live=True)
   p.write_bytes(raw)
  self.assertEqual(self.f.new_calls,[])
 def test_new_failure_drains_four_then_stops(self):
  self.install();visited=[]
  def fail(j):
   visited.append(j['request_key']);row,entry=self.f.invoke(j);row['transport_error']='new terminal failure';return row,entry
  with self.assertRaises(RuntimeError):self.f.ns['scale_dispatch_waves'](self.f.jobs[1148:1156],fail,self.f.main,4)
  self.assertEqual(len(visited),4);self.assertEqual(len(self.f.new_calls),4)
 def test_new_exception_drains_four_then_stops(self):
  self.install();visited=[]
  def fail(j):visited.append(j['request_key']);raise OSError('mocked request failure')
  with self.assertRaises(RuntimeError):self.f.ns['scale_dispatch_waves'](self.f.jobs[1148:1156],fail,self.f.main,4)
  self.assertEqual(len(visited),4);self.assertEqual(self.f.new_calls,[])
 def test_persistent_one_shot_and_frozen_ancestor_start_bypass(self):
  self.install();self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  with self.assertRaises(FileExistsError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  self.assertEqual(self.f.new_calls,[])
 def test_added_currentcache_blocks_live_start(self):
  self.install();self.f.record(self.f.requests[self.f.plan[1148]['request_key']])
  with self.assertRaises(ValueError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
 def test_missing_gate_and_wrong_gate_identity_block(self):
  s=self.install();p=Path(s['startup_gate']);v=json.loads(p.read_bytes());v['collector_pid']+=1;p.write_text(json.dumps(v))
  with self.assertRaises(ValueError):self.f.ns['scale_run_interventions'](root=self.f.root,live=True)
  with self.assertRaises(TimeoutError):sixth.wait_startup_gate(self.f.data/'absent-ready.json',{},timeout_s=0)
  self.assertEqual(self.f.new_calls,[])
 def test_unknown_profile_or_feedback_hash_changed_rejected(self):
  self.a['unavailable_requests'][-1]['profile']['reasoning_effort']='low';self.refresh()
  with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
 def test_plan_cannot_omit_observedpartner_or_reuse003counts(self):
  for field,value in [('known_partners',[]),('hypothetical_completions',256),('observed_pair_target',596),('bootstrap_seed',1)]:
   original=self.plan[field];self.plan[field]=value;self.f.write('intervention_resume_006/analysis_plan.json',self.plan);self.a['analysis_plan']=self.f.binding('intervention_resume_006/analysis_plan.json');self.refresh()
   with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
   self.plan[field]=original
 def test_prior_analysis_binding_still_exact003(self):
  self.a['previous_analysis_plan']=self.a['analysis_plan'];self.refresh()
  with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
 def test_preserved_retained_error_metadata_cannot_change(self):
  self.a['retained_transport_failures'][1]['error']='modified';self.refresh()
  with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
 def test_third_terminal_error_not_bypassed(self):
  key=self.partner;p=self.f.cache/(key+'.json.gz');v=core.sir_read(p);v['attempts'][0]['error']='new unapproved error';p.write_bytes(gzip.compress(json.dumps(v).encode(),mtime=0));self.f.inventory[key]=core.sir_sha(p)
  self.f.write('intervention_resume_006/inventory.json',dict(protocol='23-scale-v5',count=2268,requests=self.f.inventory));self.a['cache_inventory']=self.f.binding('intervention_resume_006/inventory.json');self.refresh()
  with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
 def test_outside52_request_and_timeout_change_rejected(self):
  self.install();request=copy.deepcopy(self.f.requests[self.partner]);request['model']='another-model'
  with self.assertRaises(ValueError):self.f.ns['scale_call_model'](request,self.f.cache,live=True)
  with self.assertRaises(ValueError):self.f.ns['scale_call_model'](self.f.requests[self.partner],self.f.cache,live=True,timeout_s=901)
  self.assertEqual(self.f.new_calls,[])
 def test_bound_sources_and_paths_cannot_change(self):
  self.a['provenance_sha256']['../outside']='0'*64;self.refresh()
  with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
 def test_embedded005_004_003_002_source_exact_bytes(self):
  modules=[('SCALE_INTERVENTION_006_PREDECESSOR_SOURCE',fifth),('SCALE_INTERVENTION_005_PREDECESSOR_SOURCE',fixture.fourth),('SCALE_INTERVENTION_004_PREDECESSOR_SOURCE',fixture.third),('SCALE_INTERVENTION_PREDECESSOR_SOURCE',core)]
  for name,module in modules:setattr(sixth,name,Path(module.__file__).read_bytes().decode())
  try:
   sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
   sixth.SCALE_INTERVENTION_006_PREDECESSOR_SOURCE+='\n# changed'
   with self.assertRaises(ValueError):sixth.scale_intervention_resume_006_verify(self.f.root,self.path)
  finally:
   for name,_ in modules:delattr(sixth,name)
 def test_pilot_delegation_and_mixed_arms_rejected(self):
  self.install();self.assertEqual(self.f.ns['scale_dispatch_waves']([],self.f.invoke,self.f.data/'pilot',2),('delegated',[]))
  with self.assertRaises(ValueError):self.f.ns['scale_dispatch_waves']([],self.f.invoke,self.f.main,2)
  with self.assertRaises(ValueError):self.f.ns['scale_dispatch_waves']([dict(self.f.jobs[0],arm='original'),self.f.jobs[1]],self.f.invoke,self.f.main,4)
 def test_offline_replay_never_invokes_runner(self):
  self.install();self.f.ns['scale_run_interventions'](root=self.f.root,live=False);self.assertEqual(self.f.new_calls,[])

if __name__=='__main__':unittest.main()
