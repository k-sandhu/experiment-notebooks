"""Freeze a reviewed metadata-only, unsent-only continuation. Never launches calls."""
from datetime import datetime,timezone
import gzip,hashlib,json
from pathlib import Path
import psutil

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent/'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA=ROOT/'data/scale_v5'
PUBLIC='intervention_resume_006/'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
 raw=Path(path).read_bytes();return json.loads(gzip.decompress(raw) if Path(path).suffix=='.gz' else raw)
def encode(value):return (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()

def absence_proof():
 matches=[];inaccessible=[]
 scripts={'scale_intervention_resume_005.py','scale_detached_worker_005.py','monitor_scale_intervention_005.py','scale_intervention_resume_006.py','scale_detached_worker_006.py','monitor_scale_intervention_006.py'}
 for proc in psutil.process_iter(['pid','name']):
  if not (proc.info['name'] or '').lower().startswith(('python','pythonw')):continue
  try:
   cmd=proc.cmdline()
   if any(Path(x).name in scripts for x in cmd):matches.append(dict(pid=proc.pid,command_line=cmd,created_at_utc=datetime.fromtimestamp(proc.create_time(),timezone.utc).isoformat()))
  except psutil.NoSuchProcess:pass
  except psutil.AccessDenied:inaccessible.append(proc.pid)
 assert not matches and not inaccessible,'Owned/candidate process still present or inaccessible'
 return dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),owned_workers=0,collector_session_available=False,inaccessible_owned_candidates=0,matching_script_processes=matches,expected005_worker_pid=50248,expected005_collector_pid=83296,expected005_monitor_pid=17096)

def main():
 from scale_intervention_resume_006 import scale_intervention_resume_006_verify,VERSION
 from scale_intervention_resume_005 import scale_intervention_resume_005_verify
 amendment_path=DATA/PUBLIC/'amendment_006.json'
 if amendment_path.exists():
  state=scale_intervention_resume_006_verify(ROOT,amendment_path)
  print(json.dumps(dict(existing_amendment_verified=True,sha256=state['amendment_sha256'],model_calls=0)));return
 assert not (DATA/'main/manifest.json').exists()
 prior=scale_intervention_resume_005_verify(ROOT,DATA/'intervention_resume_005/amendment_005.json')
 review=read(BASE/'scale_intervention_resume_006_review.json')
 assert review['passed'] is True and review['issues']==[] and review['model_calls']==0 and review['efficacy_reads'] is False
 reviewed={
  'source_sha256':'scale_intervention_resume_006.py','tests_sha256':'test_scale_intervention_resume_006.py',
  'test_log_sha256':'scale_intervention_resume_006_unit_tests.log','worker_sha256':'scale_detached_worker_006.py',
  'worker_tests_sha256':'test_scale_detached_worker_006.py','launcher_sha256':'launch_scale_intervention_resume_006.ps1',
  'launcher_smoke_sha256':'scale_detached_launcher_006_smoke.json','declaration_sha256':Path(__file__).name,
  'analysis_plan_sha256':'scale_analysis_plan_006.json','missing_helper_sha256':'scale_missing_outcomes_006.py'}
 for field,name in reviewed.items():assert review[field]==sha((BASE/name).read_bytes()),'Reviewed bytes changed: '+name
 log=(BASE/'scale_intervention_resume_006_unit_tests.log').read_text(encoding='utf-8-sig')
 assert '\nOK\n' in log and 'FAILED' not in log
 smoke=read(BASE/'scale_detached_launcher_006_smoke.json')
 assert smoke['passed'] is True and smoke['model_calls']==0 and smoke['probes']==3
 assert smoke['worker_sha256']==review['worker_sha256'] and smoke['launcher_sha256']==review['launcher_sha256']
 assert smoke['evidence_sha256']==sha((BASE/'scale_detached_launcher_006_evidence.json').read_bytes())
 recovery=read(BASE/'scale_intervention_005_recovery_review_20261030.json')
 assert recovery['counts']==dict(scheduled_arm_slots=1200,terminal_arm_records=1139,pending_arm_slots=9,unrecorded_arm_slots=52,invalid_attempt_records=0)
 assert recovery['finished_receipt_present'] is False and recovery['manifest_present'] is False and recovery['export_files_present']==0
 assert recovery['prefix_files_checked']==2124 and recovery['prefix_hash_mismatches']==[]
 assert recovery['stdout_metadata']['new_transport_failure_events']==0 and recovery['stdout_metadata']['new_terminal_slots']==143
 assert all(recovery[name] is False for name in ('model_outputs_accessed','verification_flags_accessed','arm_recovery_rates_accessed','completion_barrier_passed'))
 current={p.name.removesuffix('.json.gz'):sha(p.read_bytes()) for p in (DATA/'main/cache').glob('*.json.gz')}
 inventory=read(BASE/'scale_intervention_005_postloss_cache_inventory_20261030.json')
 assert len(current)==2268 and current==inventory['requests']
 assert all(current.get(k)==v for k,v in prior['inventory'].items())
 dispatch=read(DATA/'main/dispatch.json')['jobs'];armkeys=[j['request_key'] for j in dispatch]
 assert len(armkeys)==1200 and len(set(armkeys))==1200 and set(current).intersection(armkeys)==set(armkeys[:1148])
 plans={row['request_key']:row for binding in prior['prior']['prior']['predecessor_state']['amendment']['request_plans'] for row in read(DATA/binding['path'])}
 approved=dict(prior['approved']);newkeys=set(recovery['pending_request_keys'])-set(approved)
 assert len(newkeys)==1
 for key in newkeys:
  cache=read(DATA/'main/cache'/(key+'.json.gz'));req=cache['request'];plan=plans[key]
  assert len(cache['attempts'])==1 and cache['attempts'][0]['pending'] is True
  approved[key]=dict(request_key=key,cache_sha256=current[key],case_id=plan['case_id'],arm=plan['arm'],stage=plan['stage'],sample=plan['sample'],content_hash=plan['source_hash'],request_input_hash=next(j['input_hash'] for j in dispatch if j['request_key']==key),feedback_hash=next(j['feedback_hash'] for j in dispatch if j['request_key']==key),profile=dict(model='gpt-6.1-sol',reasoning_effort='high',protocol='23-scale-v5',timeout_s=900))
 assert len(approved)==9 and set(approved)==set(recovery['pending_request_keys'])
 proof=absence_proof();now=datetime.now(timezone.utc).isoformat()
 stop=dict(protocol='23-scale-v5',reason='controller_disappeared_without_finished_receipt',observed_at_utc=recovery['checked_at_utc'],finished_receipt_present=False,manifest_present=False,export_files_present=0,new_transport_failure_events=0,new_terminal_slots=143,recorded_main_cache_files=2268,terminal_arm_records=1139,pending_arm_slots=9,unrecorded_arm_slots=52,unknown_physical_launch_and_outcome_request_keys=sorted(approved),scientific_outcomes_accessed=False,automatic_restart=False)
 handling=dict(protocol='23-scale-v5',declared_at_utc=now,scheduled_pairs=600,observed_pair_target=595,unknown_outcomes=9,unknown_whole_pairs=4,unknown_partial_pairs=1,hypothetical_completions=512,collection_policy='Continue only the 52 genuinely unsent frozen slots once. Preserve all 2268 raw cache bytes and 9 pending artifacts. Every new infrastructure failure drains the current four-job wave and stops. No automatic restart or recorded-key resubmission.',unknown_policy='Controller disappearance adds one repair slot of unknown physical launch and outcome to eight prior unknown slots. Keep the observed fresh partner in all 600 sensitivity completions; do not invent responses, labels or training data. The new 006 analysis plan replaces the 003 missingness counts prospectively; 003 and all ancestor bytes remain intact.',endpoint_policy='Both exact known terminal errors remain operational non-recoveries. Nonempty request error controls endpoint even if a body, usage or zero return code exists. Do not treat transport-derived verification flags as new wrong values.',spend_policy='USD cost remains unavailable. Nine pending artifacts have unknown physical launch, outcome and usage. Preserve all observed metadata; never equate missing usage with zero cost.',runtime_policy='Same gpt-6.1-sol with high reasoning, tools disabled and CLI access; 900-second request limit; fixed requests, sources, feedback, scoring, 600 pairs, 1200 slots and four-job waves. Reuse reviewed 005 mechanics in a path-bound 006 companion with temporary same-thread 16-hour SYSTEM_REQUIRED lease and owned job 0x2000 startup gate. Forced user sleep remains possible.',efficacy_access='No intervention answer, verification flag, recovery rate or arm comparison has been inspected.')
 launch_path=BASE/'detached_operational_logs/scale005_20261029T161036076Z_74c5e7e1.launch.json';launch=read(launch_path)
 assert not Path(launch['finished']).exists(),'Do not replace a missing-finished loss record with a successful completion'
 copies={PUBLIC+'prior_cache_inventory_006.json':encode(dict(protocol='23-scale-v5',count=2268,requests=current)),PUBLIC+'process_absence_006.json':encode(proof),PUBLIC+'stop_record.json':encode(stop),PUBLIC+'handling_plan.json':encode(handling),PUBLIC+'recovery_review.json':(BASE/'scale_intervention_005_recovery_review_20261030.json').read_bytes(),PUBLIC+'missing_pair_metadata.json':(BASE/'scale_missing_pair_metadata_006.json').read_bytes(),PUBLIC+'analysis_plan.json':(BASE/'scale_analysis_plan_006.json').read_bytes(),PUBLIC+'postloss_cache_inventory.json':(BASE/'scale_intervention_005_postloss_cache_inventory_20261030.json').read_bytes(),PUBLIC+'previous_receipts/launch.json':launch_path.read_bytes()}
 for name in ('started','startup_gate','payload','lease','stdout','stderr'):
  suffix={'startup_gate':'ready.json','lease':'lease.jsonl','stdout':'stdout.log','stderr':'stderr.log'}.get(name,name+'.json')
  copies[PUBLIC+'previous_receipts/'+suffix]=Path(launch[name]).read_bytes()
 # There is deliberately no previous finished receipt: its absence is evidence.
 for name in ('scale_intervention_resume_006.py','test_scale_intervention_resume_006.py','scale_detached_worker_006.py','test_scale_detached_worker_006.py','launch_scale_intervention_resume_006.ps1','probe_scale_containment_child_006.py','smoke_scale_worker_006.py','monitor_scale_intervention_006.py',Path(__file__).name):copies[PUBLIC+'source_snapshot/'+name]=(BASE/name).read_bytes()
 for name in ('scale_intervention_resume.py','test_scale_intervention_resume.py','scale_intervention_resume_003.py','test_scale_intervention_resume_003.py','scale_intervention_resume_004.py','test_scale_intervention_resume_004.py','scale_intervention_resume_005.py','test_scale_intervention_resume_005.py'):copies[PUBLIC+'source_snapshot/'+name]=(DATA/'intervention_resume_005/source_snapshot'/name).read_bytes()
 for name in ('scale_intervention_resume_006_review.json','scale_intervention_resume_006_review.md','scale_intervention_resume_006_unit_tests.log','scale_detached_launcher_006_smoke.json','scale_detached_launcher_006_evidence.json'):copies[PUBLIC+name]=(BASE/name).read_bytes()
 for name in ('scale_missing_outcomes_006.py','test_scale_missing_outcomes_006.py','scale_missing_outcomes_003.py','scale_reporting.py','refresh_scale_report.py','test_scale_reporting_missing.py'):copies[PUBLIC+'reporting_snapshot/'+name]=(BASE/name).read_bytes()
 for name in ('scale_transport.py','scale_fixtures.py','scale_parallel.py','scale_experiment.py','high_fixtures.py','high_material_audit.py','audit_high_rendered_sources.py','test_scale_experiment.py','scale_power_plan.json'):copies[PUBLIC+'reporting_snapshot/'+name]=(DATA/'source_snapshot'/name).read_bytes()
 def binding(name):return dict(path=name,sha256=sha(copies[name]) if name in copies else sha((DATA/name).read_bytes()))
 protected=['source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json','main/original_manifest.json','main/protocol.json','main/allocation.json','intervention_resume_005/amendment_005.json','intervention_resume_005/continuation_start_005.json']
 amendment=dict(protocol='23-scale-v5',amendment_version=VERSION,declared_at_utc=now,loss_observed_at_utc=recovery['checked_at_utc'],predecessor=binding('intervention_resume_005/amendment_005.json'),implementation=binding(PUBLIC+'source_snapshot/scale_intervention_resume_006.py'),analysis_plan=binding(PUBLIC+'analysis_plan.json'),previous_analysis_plan=prior['amendment']['analysis_plan'],handling_plan=binding(PUBLIC+'handling_plan.json'),process_proof=binding(PUBLIC+'process_absence_006.json'),cache_inventory=binding(PUBLIC+'prior_cache_inventory_006.json'),stop_record=binding(PUBLIC+'stop_record.json'),recovery_review=binding(PUBLIC+'recovery_review.json'),protected_files=[binding(n) for n in protected],tests=[binding(PUBLIC+'source_snapshot/test_scale_intervention_resume_006.py'),binding(PUBLIC+'source_snapshot/test_scale_detached_worker_006.py')],provenance_sha256={name:sha(raw) for name,raw in copies.items()},retained_transport_failures=prior['retained_transport_failures'],retained_terminal_failure_request_keys=sorted(prior['retained']),unavailable_requests=list(approved.values()),unavailable_request_keys=sorted(approved),unavailable_case_ids=sorted({r['case_id'] for r in approved.values()}),remaining_unsent_jobs=52,recorded_arm_requests=1148,retained_terminal_arm_requests=1139,scope='One continuation of52 truly unsent frozen slots only; all 2268 recorded raw caches, nine unknowns and two exact terminal errors preserved. No automatic restart.',scientific_handling='595 complete pairs; five incomplete cases, including one observed fresh partner; all 512 binary completions of nine unknown cells in 600 pairs; 20,000 paired bootstrap samples with seed 246600. No efficacy was accessed before this plan.')
 copies[PUBLIC+'amendment_006.json']=encode(amendment)
 for name,raw in copies.items():assert not (DATA/name).exists() or (DATA/name).read_bytes()==raw,'Existing artifact differs: '+name
 for name,raw in copies.items():
  target=DATA/name;target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():
   with target.open('xb') as stream:stream.write(raw)
 state=scale_intervention_resume_006_verify(ROOT,amendment_path)
 print(json.dumps(dict(passed=True,model_calls=0,efficacy_reads=False,raw_cache_prefix_preserved=len(state['inventory']),unknown_outcomes=len(state['approved']),unsent_jobs=52,amendment_sha256=state['amendment_sha256'],declared_at_utc=now)))

if __name__=='__main__':main()
